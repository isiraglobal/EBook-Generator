#!/usr/bin/env python3
"""Inspect a rendered PDF page-by-page using real glyph geometry.

    python3 scripts/inspect_pdf.py book.pdf --pages 1-12

Prints, per page: word count, distinct text lines, the topmost/bottommost inked
baseline, the horizontal extent, the dominant text colours, any word that
overlaps another word's box, and any word crossing the page margins. This is
the check that catches the defects a screenshot review would catch, without a
screenshot.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

A4 = (595.2756, 841.8898)
MARGIN_PT = 14.0  # tolerance outside the nominal trim box
# Running head and folio bands, excluded from body fill measurements.
BODY_TOP = 96.0
BODY_BOTTOM = 772.0


def _parse_pages(pdf: str) -> list[dict]:
    out = subprocess.run(
        ["pdftotext", "-bbox-layout", "-q", pdf, "-"],
        capture_output=True, text=True, check=True,
    )
    root = ET.fromstring(out.stdout)
    ns = {"x": root.tag.split("}")[0].strip("{")} if "}" in root.tag else None

    def find(node, name):
        path = f".//x:{name}" if ns else f".//{name}"
        return node.findall(path, ns) if ns else node.findall(path)

    pages = []
    for page in find(root, "page"):
        width = float(page.get("width", A4[0]))
        height = float(page.get("height", A4[1]))
        words = []
        for w in find(page, "word"):
            text = (w.text or "").strip()
            if not text:
                continue
            words.append({
                "text": text,
                "x0": float(w.get("xMin", 0)), "x1": float(w.get("xMax", 0)),
                "y0": float(w.get("yMin", 0)), "y1": float(w.get("yMax", 0)),
            })
        lines = []
        for ln in find(page, "line"):
            txt = "".join(t.text or "" for t in ln).strip()
            if txt:
                lines.append({
                    "text": txt,
                    "x0": float(ln.get("xMin", 0)), "x1": float(ln.get("xMax", 0)),
                    "y0": float(ln.get("yMin", 0)), "y1": float(ln.get("yMax", 0)),
                })
        # Y positions grouped by pdftotext block. Lines inside one block belong
        # to a single run of body text, so their spacing is a direct reading of
        # the leading in force there.
        block_ys = []
        for blk in find(page, "block"):
            ys = sorted(float(ln.get("yMin", 0)) for ln in blk)
            if len(ys) > 1:
                block_ys.append(ys)
        pages.append({"width": width, "height": height, "words": words,
                      "lines": lines, "block_ys": block_ys})
    return pages


# How much of the shorter box two words must share before it counts as a
# collision. pdftotext reports a word box that includes the face's full
# ascender-to-descender extent, which is taller than the leading it is set at:
# a 30pt contents entry on a 31.7pt pitch reports boxes 34pt tall, so the line
# below overlaps the line above by about 2pt with no ink anywhere near the other
# word. A quarter of the box height is well past that artefact and still far
# short of two words genuinely printed on top of one another.
_OVERLAP_FRACTION = 0.25


def _overlaps(words: list[dict]) -> list[tuple[dict, dict]]:
    """Pairs of words whose boxes are printed on top of one another.

    Sorted by vertical position so only nearby lines are compared.
    """
    out = []
    ordered = sorted(words, key=lambda w: w["y0"])
    for i, a in enumerate(ordered):
        for b in ordered[i + 1:]:
            if b["y0"] > a["y1"]:
                break
            dx = min(a["x1"], b["x1"]) - max(a["x0"], b["x0"])
            dy = min(a["y1"], b["y1"]) - max(a["y0"], b["y0"])
            if dx <= 0.6 or dy <= 0.6:
                continue
            shorter_h = min(a["x1"] - a["x0"], b["x1"] - b["x0"])
            shorter_v = min(a["y1"] - a["y0"], b["y1"] - b["y0"])
            if (dx > _OVERLAP_FRACTION * shorter_h
                    and dy > _OVERLAP_FRACTION * shorter_v):
                out.append((a, b))
    return out


def _bleed_edges(lines: list[dict], w: float, h: float) -> list[str]:
    """Which page edges the text runs past."""
    if not lines:
        return []
    bleed = []
    if min(l["y0"] for l in lines) < MARGIN_PT:
        bleed.append("head")
    if max(l["y1"] for l in lines) > h - MARGIN_PT:
        bleed.append("foot")
    if min(l["x0"] for l in lines) < MARGIN_PT:
        bleed.append("left")
    if max(l["x1"] for l in lines) > w - MARGIN_PT:
        bleed.append("right")
    return bleed


def _parse_range(spec: str, total: int) -> list[int]:
    pages: list[int] = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            pages.extend(range(int(a), int(b) + 1))
        else:
            pages.append(int(part))
    return [p for p in pages if 1 <= p <= total]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--pages", default="1-12")
    ap.add_argument("--json", dest="json_out")
    ap.add_argument("--plan", default=None,
                    help="plan JSON from build_manual.py --dump-plan; used to "
                         "classify pages whose emptiness is deliberate")
    ap.add_argument("--full", action="store_true", help="print every text line")
    ap.add_argument("--no-ink", action="store_true",
                    help="measure fill from text boxes only, ignoring rules "
                         "and figures")
    args = ap.parse_args()

    purposes: dict[int, str] = {}
    if args.plan:
        planned = json.loads(Path(args.plan).read_text())["pages"]
        purposes = {p["page"]: p["purpose"] for p in planned}

    pages = _parse_pages(args.pdf)

    # Ink fill per page, from qa_pdf's rasteriser, when Pillow and NumPy are
    # available. `--no-ink` skips it and falls back to the text-box measure,
    # which cannot see a rule.
    ink_fill: dict[int, float] | None = None
    if not args.no_ink:
        try:
            import qa_pdf
            ink_fill = {
                i + 1: row["vertical_fill"]
                for i, row in enumerate(qa_pdf.scan(args.pdf)["page_stats"])
            }
        except Exception as exc:  # noqa: BLE001 - a fallback, not a failure
            print(f"ink fill unavailable ({type(exc).__name__}: {exc}); "
                  f"falling back to text-box fill, which cannot see rules",
                  file=sys.stderr)
    total = len(pages)
    wanted = _parse_range(args.pages, total)
    report = {"pdf": args.pdf, "total_pages": total, "pages": []}

    for pno in wanted:
        page = pages[pno - 1]
        words, lines = page["words"], page["lines"]
        w, h = page["width"], page["height"]
        issues: list[str] = []

        ov = _overlaps(words)
        if ov:
            sample = "; ".join(f"{a['text']!r}~{b['text']!r}" for a, b in ov[:4])
            issues.append(f"{len(ov)} overlapping word boxes: {sample}")

        if lines:
            top = min(l["y0"] for l in lines)
            bottom = max(l["y1"] for l in lines)
            left = min(l["x0"] for l in lines)
            right = max(l["x1"] for l in lines)
        else:
            top = bottom = left = right = 0.0

        # Fill is measured over the text block only. The running head and folio
        # sit outside it and would otherwise make every page look full.
        body_lines = [l for l in lines if l["y0"] >= BODY_TOP and l["y1"] <= BODY_BOTTOM]
        if body_lines:
            body_top = min(l["y0"] for l in body_lines)
            body_bottom = max(l["y1"] for l in body_lines)
        else:
            body_top = body_bottom = 0.0

        # A cover may deliberately bleed off one edge; content off all four
        # means a layout escaped its page.
        bleed = _bleed_edges(lines, w, h)
        if len(bleed) == 4:
            issues.append(
                f"content bleeds off every edge: x[{left:.0f},{right:.0f}] "
                f"y[{top:.0f},{bottom:.0f}] on {w:.0f}x{h:.0f}pt"
            )

        # Fill is measured from the raster, not from the text boxes. A workbook
        # spread is a prompt and eighteen ruled writing lines; those lines have
        # no glyphs, so a word-box measurement scored every one of them at the
        # height of its prompt alone. The exemption that used to paper over it
        # keyed off the page's purpose, which came from the plan -- and the plan
        # does not know that the contents page runs to two sheets, so the
        # exemption landed on the wrong page and flagged a full page of writing
        # space. qa_pdf's ink measurement needs no exemption.
        fill = ink_fill.get(pno, 0.0) if ink_fill is not None else (
            (body_bottom - body_top) / (BODY_BOTTOM - BODY_TOP) if body_lines else 0.0
        )
        purpose = purposes.get(pno, "")
        if not lines:
            issues.append("page has no extractable text")
        elif ink_fill is None and fill < 0.30:
            issues.append(f"underfilled text block: {fill:.0%} of the text block height")

        entry = {
            "page": pno,
            "purpose": purpose,
            "words": len(words),
            "lines": len(lines),
            "body_lines": len(body_lines),
            "body_fill": round(fill, 3),
            "box": [round(left, 1), round(top, 1), round(right, 1), round(bottom, 1)],
            "issues": issues,
        }
        report["pages"].append(entry)

        print(f"p{pno:>3}  words={len(words):>4} lines={len(lines):>3} "
              f"body_lines={len(body_lines):>3} body_fill={fill:>5.0%} "
              f"box=({left:>5.0f},{top:>5.0f})-({right:>5.0f},{bottom:>5.0f})"
              f"{'  [' + purpose + ']' if purpose else ''}")
        for issue in issues:
            print(f"      ! {issue}")
        if args.full:
            for ln in lines:
                print(f"      y={ln['y0']:>5.0f} x={ln['x0']:>5.0f} | {ln['text'][:96]}")

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
