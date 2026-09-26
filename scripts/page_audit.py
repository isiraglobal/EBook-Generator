#!/usr/bin/env python3
"""Measure a rendered page from its raster, and print a density map.

This model cannot read images, so "look at the page" is done numerically. The
analyser reports the things a book designer actually checks -- the text block and
its margins, the measure in characters, the baseline pitch, the size of every
gap between inked rows, the alignment of the left edge -- and prints a coarse
ink-density map so the composition can be read as a picture in the terminal.

    python3 scripts/page_audit.py BOOK.pdf                 # audit every page
    python3 scripts/page_audit.py BOOK.pdf --pages 1-6     # a range
    python3 scripts/page_audit.py BOOK.pdf --map 12        # density map of p12
    python3 scripts/page_audit.py BOOK.pdf --pages 5-40 --summary
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

# The map is the page divided into a grid; each cell becomes one character whose
# darkness is the fraction of the cell that carries ink. PAPER is a blank cell.
RAMP = " .:-=+*#%@"
PAPER = " "


def render(pdf: Path, dpi: int, first: int, last: int) -> list[Path]:
    """Rasterise a page range to PNGs and return their paths, in order."""
    out = Path(tempfile.mkdtemp(prefix="page_audit_"))
    subprocess.run(
        ["pdftoppm", "-r", str(dpi), "-png", "-f", str(first), "-l", str(last),
         str(pdf), str(out / "p")],
        check=True, capture_output=True,
    )
    return sorted(out.glob("p-*.png"))


def _box(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    """Bounding box of all ink, as (x0, y0, x1, y1)."""
    cols = np.where(mask.any(axis=0))[0]
    rows = np.where(mask.any(axis=1))[0]
    if not cols.size or not rows.size:
        return None
    return int(cols[0]), int(rows[0]), int(cols[-1]), int(rows[-1])


def _runs(rows: np.ndarray, min_run: int = 1) -> list[tuple[int, int]]:
    """Contiguous True spans in a boolean row vector."""
    out, start = [], None
    for i, v in enumerate(rows):
        if v and start is None:
            start = i
        elif not v and start is not None:
            if i - start >= min_run:
                out.append((start, i))
            start = None
    if start is not None and len(rows) - start >= min_run:
        out.append((start, len(rows)))
    return out


def _column_clusters(mask: np.ndarray, gap: int) -> list[tuple[int, int]]:
    """Column spans of ink, merging bands separated by less than `gap` px."""
    return _runs(mask.any(axis=0), min_run=1)


def audit(png: Path, dpi: int) -> dict:
    """Layout metrics for one rendered page."""
    img = Image.open(png).convert("L")
    a = np.asarray(img, dtype=np.uint8)
    h, w = a.shape
    # Paper is about 243 at 144dpi; the cutoff sits below it and above the
    # lightest hairline, so a 0.5pt rule counts as ink.
    mask = a < 235
    box = _box(mask)
    m = dict(
        width=w, height=h,
        ink_ratio=round(float(mask.mean()), 4),
    )
    if box is None:
        m.update(blank=True, fill=0.0, box=None, gaps=[], rows=0)
        return m

    x0, y0, x1, y1 = box
    m["box"] = [x0, y0, x1, y1]
    # Margins as a fraction of the sheet. A book is legible at a glance: the
    # left margin should barely move from page to page.
    m["margin_left"] = round(x0 / w, 4)
    m["margin_right"] = round(1 - x1 / w, 4)
    m["margin_top"] = round(y0 / h, 4)
    m["margin_bottom"] = round(1 - y1 / h, 4)

    # Trim the running head and folio bands, then measure what is left.
    body = mask[int(h * 0.10):int(h * 0.92), :]
    inked = np.where(body.any(axis=1))[0]
    m["fill"] = round(float(inked[-1] - inked[0]) / max(1, h * 0.82), 3) if inked.size else 0.0
    m["rows"] = int(inked.size)

    # Every gap between inked bands. A gap much larger than the leading is a
    # hole; a gap of zero at a band edge is a collision.
    bands = _runs(body.any(axis=1), min_run=1)
    gaps = [bands[i + 1][0] - bands[i][1] for i in range(len(bands) - 1)]
    m["gaps"] = [int(g) for g in gaps]
    m["max_gap"] = int(max(gaps)) if gaps else 0
    m["n_bands"] = len(bands)

    # Text column: the widest cluster of inked columns that is not full measure.
    clusters = _column_clusters(body, gap=max(6, w // 60))
    m["columns"] = len(clusters)
    m["column_spans"] = [[int(a0), int(a1)] for a0, a1 in clusters]
    return m


def _words(pdf: Path, first: int, last: int) -> dict[int, list[dict]]:
    """Word boxes per page, from pdftotext, for the typographic metrics."""
    out: dict[int, list[dict]] = {}
    for pno in range(first, last + 1):
        xml = subprocess.run(
            ["pdftotext", "-bbox-layout", "-q", "-f", str(pno), "-l", str(pno),
             str(pdf), "-"],
            check=True, capture_output=True, text=True,
        ).stdout
        page = re.search(r'<page width="([\d.]+)" height="([\d.]+)"', xml)
        words = [
            {"x0": float(x), "y0": float(y), "x1": float(x2), "y1": float(y2),
             "text": t}
            for x, y, x2, y2, t in re.findall(
                r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" '
                r'yMax="([\d.]+)">([^<]*)</word>', xml)
        ]
        out[pno] = {
            "width": float(page.group(1)) if page else 0.0,
            "height": float(page.group(2)) if page else 0.0,
            "words": words,
        }
    return out


def typography(pdf: Path, page: dict) -> dict:
    """Measure, leading pitch and left-edge alignment for one page."""
    words = page["words"]
    if not words:
        return {}
    # Body words only: drop the running head and folio bands.
    body = [w for w in words
            if page["height"] * 0.10 < w["y0"] < page["height"] * 0.92]
    if not body:
        return {}
    # Lines: group by baseline (y0), then only keep groups of real text.
    by_line: dict[int, list[dict]] = {}
    for w in body:
        by_line.setdefault(int(round(w["y0"] * 2) / 2), []).append(w)
    lines = [v for v in by_line.values() if len(v) >= 3]
    if len(lines) < 2:
        return {}
    lines.sort(key=lambda v: v[0]["y0"])
    tops = [v[0]["y0"] for v in lines]
    deltas = sorted(round(b - a, 2) for a, b in zip(tops, tops[1:]))
    pitch = deltas[len(deltas) // 2]
    heights = [max(w["y1"] for w in v) - min(w["y0"] for w in v) for v in lines]
    sizes = [max(w["y1"] for w in v) - min(w["y0"] for w in v) for v in lines]
    lefts = [min(w["x0"] for w in v) for v in lines]
    # Characters per line, from the widest lines only, so a short last line of a
    # paragraph does not drag the mean down.
    full = [v for v in lines if len(v) >= 6]
    cpl = [sum(len(w["text"]) for w in v) for v in full]
    return {
        "lines": len(lines),
        "pitch": pitch,
        "pitch_spread": round(deltas[-1] - deltas[0], 2),
        "mean_chars": round(sum(cpl) / len(cpl), 1) if cpl else 0,
        "min_chars": min(cpl) if cpl else 0,
        "max_chars": max(cpl) if cpl else 0,
        "left_edge_mode": Counter(round(x, 1) for x in lefts).most_common(1),
        "left_edge_spread": round(max(lefts) - min(lefts), 1),
        "size_min": round(min(sizes), 1),
        "size_max": round(max(sizes), 1),
    }


def density_map(mask: np.ndarray, cols: int = 60, rows: int = 40) -> list[str]:
    """Coarse ink-density map of a page, one character per cell."""
    h, w = mask.shape
    cw, ch = w / cols, h / rows
    out = []
    for r in range(rows):
        line = []
        for c in range(cols):
            cell = mask[int(r * ch):max(int((r + 1) * ch), int(r * ch) + 1),
                        int(c * cw):max(int((c + 1) * cw), int(c * cw) + 1)]
            f = float(cell.mean()) if cell.size else 0.0
            if f <= 0.004:
                line.append(PAPER)
            else:
                idx = min(len(RAMP) - 1, 1 + int(f * 22))
                line.append(RAMP[idx])
        out.append("".join(line).rstrip())
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--pages", default="1-")
    ap.add_argument("--dpi", type=int, default=144)
    ap.add_argument("--map", type=int, help="print the density map of this page")
    ap.add_argument("--summary", action="store_true",
                    help="report only the aggregate spread across the range")
    args = ap.parse_args()
    pdf = Path(args.pdf)

    from pypdf import PdfReader
    total = len(PdfReader(str(pdf)).pages)
    m = re.fullmatch(r"(\d+)-(\d*)", args.pages)
    if m:
        first = int(m.group(1))
        last = int(m.group(2)) if m.group(2) else total
    else:
        first = last = int(args.pages)
    last = min(last, total)

    if args.map:
        pngs = render(pdf, args.dpi, args.map, args.map)
        a = np.asarray(Image.open(pngs[0]).convert("L"), dtype=np.uint8)
        print(f"page {args.map} density map ({a.shape[1]}x{a.shape[0]}px)")
        for line in density_map(a < 235):
            print("|" + line)
        return 0

    pngs = render(pdf, args.dpi, first, last)
    info = _words(pdf, first, last)
    rows = []
    for i, png in enumerate(pngs, start=first):
        met = audit(png, args.dpi)
        met.update(typography(pdf, info[i]))
        met["page"] = i
        rows.append(met)

    if args.summary:
        for key in ("margin_left", "margin_right", "margin_top", "margin_bottom",
                    "fill", "left_edge_mode", "mean_chars", "pitch",
                    "size_min", "size_max", "columns", "max_gap", "ink_ratio"):
            vals = [r[key] for r in rows if key in r and r[key] is not None]
            if not vals:
                continue
            if key == "left_edge_mode":
                pts = Counter(v[0][0] for v in vals)
                top = pts.most_common(4)
                print(f"{key:16} most common x: {top}")
                continue
            nums = [v for v in vals if isinstance(v, (int, float))]
            if not nums:
                continue
            lo, hi = min(nums), max(nums)
            print(f"{key:16} min {lo:>9} max {hi:>9} spread {round(hi - lo, 3):>8}")
        return 0

    for r in rows:
        if r.get("blank"):
            print(f"p{r['page']:>3} BLANK")
            continue
        gaps = r.get("gaps", [])
        big = [g for g in gaps if g > 60]
        print(
            f"p{r['page']:>3} "
            f"margins L{r['margin_left']:.3f} R{r['margin_right']:.3f} "
            f"T{r['margin_top']:.3f} B{r['margin_bottom']:.3f} | "
            f"fill {r['fill']:.0%} bands {r.get('n_bands', 0):>3} "
            f"cols {r.get('columns', 0)} | "
            f"chars {r.get('mean_chars', 0):>5} "
            f"({r.get('min_chars', 0)}-{r.get('max_chars', 0)}) "
            f"pitch {r.get('pitch', 0):>5} spread {r.get('pitch_spread', 0):>5} | "
            f"size {r.get('size_min', 0):>4}-{r.get('size_max', 0):<4} "
            f"left {r.get('left_edge_mode', [(0, 0)])[0][0]:>6} "
            f"(spread {r.get('left_edge_spread', 0):>5}) | "
            f"ink {r['ink_ratio']:.3f}"
            + (f" GAPS {big}" if big else "")
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
