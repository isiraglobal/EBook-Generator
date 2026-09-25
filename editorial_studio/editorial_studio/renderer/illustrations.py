"""Deterministic, on-brand SVG illustrations for editorial figures.

The generator produces real artwork (parcel/topographic motifs derived from the
content it illustrates) instead of leaving empty placeholder boxes in the PDF.
Everything is seeded, so the same input always yields the same figure and the
layout stays visually stable between builds.
"""
from __future__ import annotations

import math
import re
from pathlib import Path

# Warm paper / ink / brass editorial system, mirroring helpers.typ.
PAPER = "#F7F3EC"
INK = "#1A1815"
BRASS = "#B08D57"
TERRACOTTA = "#A0523D"
SLATE = "#6B6560"
RULE = "#D9CFBF"


def _seed(text: str) -> int:
    h = 2166136261
    for ch in text.encode("utf-8"):
        h = ((h ^ ch) * 16777619) & 0xFFFFFFFF
    return h or 1


def _rng(seed: int):
    state = {"s": seed}

    def nxt() -> float:
        state["s"] = (1103515245 * state["s"] + 12345) & 0x7FFFFFFF
        return state["s"] / 0x7FFFFFFF

    return nxt


def _esc(s: str) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _truncate(s: str, n: int) -> str:
    s = re.sub(r"\s+", " ", str(s)).strip()
    if len(s) <= n:
        return s
    return s[: n - 1].rstrip() + "…"


def parcel_map_svg(
    title: str,
    labels: list[str],
    path: str | Path,
    width: int = 960,
    height: int = 520,
) -> str:
    """Topographic parcel motif: contour bands, a survey boundary, callouts."""
    seed = _seed(title + "|".join(labels))
    rnd = _rng(seed)
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    pad = 46
    w, h = width - pad * 2, height - pad * 2
    out: list[str] = []
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" aria-label="{_esc(_truncate(title, 120))}">'
    )
    out.append(f'<rect width="{width}" height="{height}" fill="{PAPER}"/>')

    # Contour bands: stacked sinusoids with drifting phase.
    bands = 9
    for b in range(bands):
        amp = 26 + b * 5 + rnd() * 8
        phase = rnd() * math.tau
        y0 = pad + h * (0.14 + 0.72 * b / (bands - 1))
        pts = []
        steps = 64
        for i in range(steps + 1):
            x = pad + w * i / steps
            t = i / steps
            y = y0 + amp * (
                0.55 * math.sin(t * math.tau * 1.4 + phase)
                + 0.30 * math.sin(t * math.tau * 2.7 + phase * 1.7)
            )
            pts.append(f"{x:.1f},{y:.1f}")
        out.append(
            f'<polyline points="{" ".join(pts)}" fill="none" stroke="{BRASS}" '
            f'stroke-width="{0.9 if b % 3 else 1.5}" stroke-opacity="{0.5 if b % 3 else 0.75}"/>'
        )

    # Survey boundary: a closed, slightly irregular quadrilateral.
    cx, cy = pad + w * 0.5, pad + h * 0.5
    span_x, span_y = w * 0.30, h * 0.30
    corners = []
    for k in range(4):
        a = math.tau * (k / 4) + 0.42
        jitter = 0.82 + rnd() * 0.3
        corners.append(
            (cx + math.cos(a) * span_x * jitter, cy + math.sin(a) * span_y * jitter)
        )
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in corners)
    out.append(f'<polygon points="{poly}" fill="{TERRACOTTA}" fill-opacity="0.07" '
               f'stroke="{TERRACOTTA}" stroke-width="1.6"/>')
    for x, y in corners:
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{PAPER}" '
                   f'stroke="{TERRACOTTA}" stroke-width="1.4"/>')

    # Bearing ticks along the top edge, like a plat sheet.
    for i in range(1, 8):
        x = pad + w * i / 8
        out.append(f'<line x1="{x:.1f}" y1="{pad - 12}" x2="{x:.1f}" y2="{pad - 2}" '
                   f'stroke="{SLATE}" stroke-width="0.8" stroke-opacity="0.55"/>')
    out.append(f'<line x1="{pad}" y1="{pad - 7}" x2="{pad + w}" y2="{pad - 7}" '
               f'stroke="{SLATE}" stroke-width="0.8" stroke-opacity="0.55"/>')

    # Scale bar.
    out.append(f'<g transform="translate({pad},{height - pad + 8})">')
    out.append(f'<line x1="0" y1="0" x2="120" y2="0" stroke="{INK}" stroke-width="1.6"/>')
    out.append(f'<line x1="0" y1="-5" x2="0" y2="5" stroke="{INK}" stroke-width="1.6"/>')
    out.append(f'<line x1="60" y1="-4" x2="60" y2="4" stroke="{INK}" stroke-width="1.2"/>')
    out.append(f'<line x1="120" y1="-5" x2="120" y2="5" stroke="{INK}" stroke-width="1.6"/>')
    out.append("</g>")

    # Section callouts, evenly spaced along the bottom.
    shown = [_truncate(x, 22) for x in labels if str(x).strip()][:4]
    if shown:
        n = len(shown)
        slot = w / n
        for i, label in enumerate(shown):
            x = pad + slot * (i + 0.5)
            y = height - pad - 4
            out.append(f'<line x1="{x:.1f}" y1="{y - 22}" x2="{x:.1f}" y2="{y - 6}" '
                       f'stroke="{BRASS}" stroke-width="1.1"/>')
            out.append(f'<circle cx="{x:.1f}" cy="{y - 22}" r="3.2" fill="{BRASS}"/>')
            out.append(
                f'<text x="{x:.1f}" y="{y + 4}" text-anchor="middle" font-family="PT Sans, Helvetica, Arial, sans-serif" '
                f'font-size="15" fill="{SLATE}">{_esc(label)}</text>'
            )

    out.append("</svg>")
    svg = "".join(out)
    Path(path).write_text(svg, encoding="utf-8")
    return str(path)


def step_diagram_svg(steps: list[str], path: str | Path, width: int = 960, height: int = 300) -> str:
    """Numbered process strip used for figure-led process spreads."""
    seed = _seed("|".join(steps))
    rnd = _rng(seed)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    n = max(1, len(steps))
    gap = 18
    box_w = (width - 2 * gap - (n - 1) * gap) / n
    top, box_h = 46, height - 46 - 44

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
           f'width="{width}" height="{height}" role="img" aria-label="Process">',
           f'<rect width="{width}" height="{height}" fill="{PAPER}"/>']
    for i, step in enumerate(steps):
        x = gap + i * (box_w + gap)
        out.append(f'<rect x="{x:.1f}" y="{top}" width="{box_w:.1f}" height="{box_h}" '
                   f'fill="none" stroke="{RULE}" stroke-width="1.2" rx="4"/>')
        out.append(f'<rect x="{x:.1f}" y="{top}" width="{box_w:.1f}" height="4" fill="{BRASS}"/>')
        out.append(f'<text x="{x + 14:.1f}" y="{top + 30}" font-family="PT Sans, Helvetica, Arial, sans-serif" '
                   f'font-size="14" font-weight="bold" fill="{TERRACOTTA}" letter-spacing="1.5">{i + 1:02d}</text>')
        words = _truncate(step, 64).split()
        line, lines = "", []
        for w_ in words:
            if len(line) + len(w_) + 1 > 26:
                lines.append(line)
                line = w_
            else:
                line = (line + " " + w_).strip()
        if line:
            lines.append(line)
        for j, line in enumerate(lines[:4]):
            out.append(f'<text x="{x + 14:.1f}" y="{top + 58 + j * 21}" '
                       f'font-family="PT Sans, Helvetica, Arial, sans-serif" font-size="15" '
                       f'fill="{INK}">{_esc(line)}</text>')
        if i < n - 1:
            ax = x + box_w + gap / 2
            out.append(f'<line x1="{ax - 7:.1f}" y1="{top + box_h / 2}" x2="{ax + 3:.1f}" y2="{top + box_h / 2}" '
                       f'stroke="{BRASS}" stroke-width="1.6"/>')
            out.append(f'<polygon points="{ax + 7:.1f},{top + box_h / 2} {ax - 1:.1f},{top + box_h / 2 - 5} '
                       f'{ax - 1:.1f},{top + box_h / 2 + 5}" fill="{BRASS}"/>')
    out.append(f'<line x1="0" y1="{height - 12}" x2="{width}" y2="{height - 12}" stroke="{RULE}" stroke-width="1"/>')
    out.append("</svg>")
    Path(path).write_text("".join(out), encoding="utf-8")
    return str(path)
