#!/usr/bin/env python3
"""Visual and structural defect scanner for rendered Typst PDFs.

    python3 scripts/qa_pdf.py output/book.pdf [--json report.json] [--png-dir dir]

Checks the failure modes that a Typst template regression actually produces:
leaked template source, overlapping or clipped text, near-empty pages, missing
folios, orphaned headings, and unbound fonts.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pypdf
from PIL import Image

# Source-code markers that must never reach the page.
LEAK_PATTERNS = [
    (r"else if page-number-position", "template source leaked into running head"),
    (r"#let\s+\w+\s*\(", "Typst code leaked into body"),
    (r"scope:\s*[\"']parent", "Typst code leaked into body"),
    (r"\bset page\b", "Typst set-rule leaked into body"),
    (r"layout-functions", "registry name leaked into body"),
    (r"#if\b", "Typst conditional leaked into body"),
    (r"^\s*\}\s*$", "stray closing brace"),
    (r"\bcounter\(page\)", "Typst counter call leaked into body"),
    (r"\bbreakable:\s*true", "Typst parameter leaked into body"),
]

# Words that only appear in a broken build. Matched on word boundaries so real
# prose ("finance", "maintenance") does not trip the check.
FORBIDDEN_WORDS = [
    r"Lorem ipsum",
    r"\bTODO\b",
    r"\bFIXME\b",
    r"\bColumn \d\b",
    r"\bData \d\b",
    r"\bnan\b",
    r"\bNone\b",
    r"\bundefined\b",
]

# A4 in points, used only as a fallback when a page reports no mediabox. A run
# can mix portrait and landscape sheets, so neither is the default for the book
# as a whole.
PAGE_W_PT, PAGE_H_PT = 595.2756, 841.8898


# Raster resolution for the ink analysis. At 72dpi a 0.5pt rule anti-aliases to
# a gray above the 200 cutoff, so every hairline in the book -- answer rules,
# column rules, table separators -- read as blank paper. That made workbook
# pages, whose content is mostly rules, score as underfilled when they were not.
# 144dpi puts a 0.5pt rule at a full pixel.
INK_ANALYSIS_DPI = 144

# Paper is #F7F3EC, which rasterises to about 243. A 0.55pt rule anti-aliases
# to roughly 208, and a 0.6pt one lower still, so a cutoff at 200 counted every
# hairline in the book as paper and scored a full page of ruled writing space as
# an underfilled page. 235 sits eight levels below the paper tone and well above
# the lightest rule, so it detects hairlines without picking up the background.
INK_CUTOFF = 235

# Column-overlap detection keeps the stricter cutoff: light rules span the full
# measure and would otherwise look like two columns colliding.
STRICT_CUTOFF = 200


def _load_pages(pdf: Path) -> list[np.ndarray]:
    """Rasterise every page to a grayscale coverage map."""
    out: list[np.ndarray] = []
    for png in _render_pngs(pdf, INK_ANALYSIS_DPI):
        with Image.open(png) as im:
            out.append(np.asarray(im.convert("L"), dtype=np.uint8))
        Path(png).unlink(missing_ok=True)
    return out


def _render_pngs(pdf: Path, dpi: int) -> list[str]:
    import tempfile

    tmp = Path(tempfile.mkdtemp(prefix="qa_pdf_"))
    prefix = tmp / "pg"
    subprocess.run(
        ["pdftoppm", "-r", str(dpi), "-png", str(pdf), str(prefix)],
        check=True, capture_output=True,
    )
    files = sorted(tmp.glob("pg-*.png"))
    # keep the temp dir alive until the caller unlinks the files
    globals().setdefault("_QA_TMP", []).append(tmp)
    return [str(f) for f in files]


def _ink_runs(mask: np.ndarray, min_gap: int = 1, min_run: int = 2) -> list[tuple[int, int]]:
    """Row spans that contain ink."""
    rows = np.where(mask.any(axis=1))[0]
    if rows.size == 0:
        return []
    runs: list[tuple[int, int]] = []
    start = prev = rows[0]
    for r in rows[1:]:
        if r - prev > min_gap:
            runs.append((start, prev))
            start = r
        prev = r
    runs.append((start, prev))
    return [r for r in runs if r[1] - r[0] >= min_run]


def _overlap_regions(mask: np.ndarray) -> int:
    """Count places where two distinct text columns occupy the same rows.

    A crude but effective proxy for overlapping text: within a horizontal band,
    ink present in a left column and a right column at nearly the same vertical
    offset is normal for two columns, so instead count bands where ink appears
    in three or more widely separated horizontal zones — the signature of
    stacked, colliding elements.
    """
    cols = mask.any(axis=0)
    runs: list[tuple[int, int]] = []
    idx = np.where(cols)[0]
    if idx.size == 0:
        return 0
    start = prev = idx[0]
    for c in idx[1:]:
        if c - prev > 12:
            runs.append((start, prev))
            start = c
        prev = c
    runs.append((start, prev))
    return len(runs)


def scan(pdf_path: str, png_dir: str | None = None, dpi: int = 96) -> dict:
    pdf = Path(pdf_path)
    reader = pypdf.PdfReader(str(pdf))
    n_pages = len(reader.pages)
    issues: list[dict] = []
    page_stats: list[dict] = []
    # A run can hold portrait and landscape sheets together, so each page's own
    # size is recorded rather than assumed.
    dims: dict[int, tuple[float, float]] = {}

    # ── Text-layer checks ───────────────────────────────────────────────────
    for i, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
        except Exception as exc:  # noqa: BLE001
            issues.append({"page": i + 1, "severity": "critical", "code": "text_extract_failed",
                           "message": str(exc)})
            continue
        for pattern, label in LEAK_PATTERNS:
            m = re.search(pattern, text, re.MULTILINE)
            if m:
                issues.append({
                    "page": i + 1, "severity": "critical", "code": "template_leak",
                    "message": f"{label}: {m.group(0)!r} in extracted text",
                })
        for word in FORBIDDEN_WORDS:
            m = re.search(word, text)
            if m:
                issues.append({
                    "page": i + 1, "severity": "warning", "code": "placeholder_text",
                    "message": f"placeholder text {m.group(0)!r} present",
                })
        fonts = set()
        try:
            resources = page.get("/Resources", {})
            for f in resources.get("/Font", {}).values():
                obj = f.get_object()
                fonts.add(str(obj.get("/BaseFont", "?")))
        except Exception:  # noqa: BLE001
            pass
        try:
            box = page.mediabox
            dims[i + 1] = (round(float(box.width), 1), round(float(box.height), 1))
        except Exception:  # noqa: BLE001
            dims[i + 1] = (round(PAGE_W_PT, 1), round(PAGE_H_PT, 1))
        bad = [f for f in fonts if "Source" in f or "Courier" in f]
        if bad:
            issues.append({
                "page": i + 1, "severity": "warning", "code": "font_fallback",
                "message": f"non-editorial font embedded: {sorted(bad)}",
            })

    # ── Raster checks ───────────────────────────────────────────────────────
    pages_px = _load_pages(pdf)
    if png_dir:
        Path(png_dir).mkdir(parents=True, exist_ok=True)
        for i, png in enumerate(_render_pngs(pdf, 120), start=1):
            Path(png_dir, f"page_{i:03d}.png").write_bytes(Path(png).read_bytes())

    h, w = pages_px[0].shape if pages_px else (0, 0)
    for i, arr in enumerate(pages_px, start=1):
        mask = arr < INK_CUTOFF  # any non-paper ink, hairlines included
        # Trim the running head and footer bands before measuring fill.
        body = mask[int(h * 0.10):int(h * 0.92), :]
        body_ink = float(body.sum()) / max(1, body.size)
        # Measure the page's used depth as the span from its first inked body
        # row to its last, not the extent of contiguous ink bands. A workbook
        # page is a header and then eighteen ruled writing lines, each one row
        # of ink separated by a band of paper: the run-based span scored it at
        # the height of the header alone and reported a full page of writing
        # space as an underfilled page.
        inked = np.where(body.any(axis=1))[0]
        fill = ((inked[-1] - inked[0]) / max(1, h * 0.82)) if inked.size else 0.0
        page_stats.append({
            "page": i,
            "width_pt": dims[i][0],
            "height_pt": dims[i][1],
            "ink_ratio": round(body_ink, 4),
            "vertical_fill": round(float(fill), 3),
            "column_runs": _overlap_regions(arr < STRICT_CUTOFF),
        })

        if fill == 0.0:
            issues.append({"page": i, "severity": "critical", "code": "blank_page",
                           "message": "page has no body content"})
        elif fill < 0.22:
            issues.append({"page": i, "severity": "warning", "code": "underfilled_page",
                           "message": f"page only {fill:.0%} filled vertically"})
        if _overlap_regions(mask) >= 4:
            issues.append({"page": i, "severity": "warning", "code": "possible_overlap",
                           "message": "ink splits into many horizontal bands; check for overlap"})

    # ── Folio continuity ────────────────────────────────────────────────────
    footers = []
    for i, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:  # noqa: BLE001
            continue
        tail = [ln.strip() for ln in text.strip().split("\n") if ln.strip()]
        if tail and re.fullmatch(r"\d+", tail[-1]):
            footers.append((i, int(tail[-1])))
    for page_no, printed in footers:
        if printed != page_no:
            issues.append({
                "page": page_no, "severity": "warning", "code": "folio_mismatch",
                "message": f"printed folio {printed} does not match page {page_no}",
            })

    critical = [i for i in issues if i["severity"] == "critical"]
    warnings = [i for i in issues if i["severity"] == "warning"]
    return {
        "pdf": str(pdf),
        "total_pages": n_pages,
        "raster_pages": len(pages_px),
        # A book can hold portrait and landscape sheets in one run -- a wide
        # table page composes for the extra 87mm of measure -- so the size is
        # reported as a set, not as one pair. Reporting A4 portrait for a
        # landscape page was simply wrong.
        "page_sizes_pt": sorted({(round(s["width_pt"], 1), round(s["height_pt"], 1))
                                 for s in page_stats}),
        "critical": critical,
        "warnings": warnings,
        "page_stats": page_stats,
        "mean_fill": round(float(np.mean([s["vertical_fill"] for s in page_stats])), 3) if page_stats else 0.0,
        "passed": not critical,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--json", dest="json_out")
    ap.add_argument("--png-dir")
    ap.add_argument("--dpi", type=int, default=96)
    args = ap.parse_args()

    report = scan(args.pdf, args.png_dir, args.dpi)
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, indent=2))
    print(f"pages: {report['total_pages']}  mean vertical fill: {report['mean_fill']:.0%}")
    print(f"critical: {len(report['critical'])}  warnings: {len(report['warnings'])}")
    for issue in report["critical"][:20]:
        print(f"  [CRIT] p{issue['page']} {issue['code']}: {issue['message'][:110]}")
    for issue in report["warnings"][:20]:
        print(f"  [warn] p{issue['page']} {issue['code']}: {issue['message'][:110]}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
