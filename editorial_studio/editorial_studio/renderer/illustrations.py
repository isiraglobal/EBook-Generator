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


def risk_matrix_svg(
    axes: tuple[str, str],
    cells: list[tuple[str, str]],
    path: str | Path,
    width: int = 900,
    height: int = 620,
) -> str:
    """Probability/impact grid with the book's risks placed on it.

    `cells` is a list of (probability, impact) pairs in 0..1. Each labelled
    region gets a numeral so the figure stays readable at body size, and the
    shading steps through the palette rather than introducing new hues.
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    pad_l, pad_b, pad_t, pad_r = 118, 96, 54, 40
    cols = rows = 4
    cw = (width - pad_l - pad_r) / cols
    ch = (height - pad_t - pad_b) / rows

    # Low-to-high shading, warm and desaturated so labels stay the loudest thing.
    tints = ["#F6F1E7", "#EFE6D4", "#E5D3B8", "#D8BC94", "#C79E68"]
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" aria-label="Risk matrix">',
        f'<rect width="{width}" height="{height}" fill="{PAPER}"/>',
    ]
    for r in range(rows):
        for c in range(cols):
            level = min(4, (r + c) // 2)
            x = pad_l + c * cw
            y = pad_t + (rows - 1 - r) * ch
            out.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{cw:.1f}" height="{ch:.1f}" '
                f'fill="{tints[level]}" stroke="{RULE}" stroke-width="1"/>'
            )
    # Axis rules, heavier than the cell grid so the axes read as structure.
    out.append(f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{pad_t + rows * ch}" '
               f'stroke="{INK}" stroke-width="1.6"/>')
    out.append(f'<line x1="{pad_l}" y1="{pad_t + rows * ch}" x2="{pad_l + cols * cw}" '
               f'y2="{pad_t + rows * ch}" stroke="{INK}" stroke-width="1.6"/>')

    for i in range(cols):
        x = pad_l + (i + 0.5) * cw
        out.append(f'<text x="{x:.1f}" y="{pad_t + rows * ch + 26:.1f}" text-anchor="middle" '
                   f'font-family="PT Sans, Helvetica, Arial, sans-serif" font-size="13" '
                   f'fill="{SLATE}">{_esc(_truncate(axes[1], 14))} {i + 1}</text>')
    for i in range(rows):
        y = pad_t + (rows - 1 - i + 0.5) * ch
        out.append(f'<text x="{pad_l - 14:.1f}" y="{y + 5:.1f}" text-anchor="end" '
                   f'font-family="PT Sans, Helvetica, Arial, sans-serif" font-size="13" '
                   f'fill="{SLATE}">{i + 1}</text>')

    out.append(f'<text x="{pad_l - 96}" y="{pad_t + rows * ch / 2:.1f}" text-anchor="middle" '
               f'transform="rotate(-90 {pad_l - 96} {pad_t + rows * ch / 2:.1f})" '
               f'font-family="PT Sans, Helvetica, Arial, sans-serif" font-size="13" '
               f'font-weight="bold" fill="{INK}" letter-spacing="1.2">'
               f'{_esc(_truncate(axes[0], 28).upper())}</text>')
    out.append(f'<text x="{pad_l + cols * cw / 2:.1f}" y="{height - 22}" text-anchor="middle" '
               f'font-family="PT Sans, Helvetica, Arial, sans-serif" font-size="13" '
               f'font-weight="bold" fill="{INK}" letter-spacing="1.2">'
               f'{_esc(_truncate(axes[1], 28).upper())}</text>')

    for i, (p, im) in enumerate(cells):
        c = max(0, min(cols - 1, int(round(p * cols)) - 1 if p > 0 else 0))
        r = max(0, min(rows - 1, int(round(im * rows)) - 1 if im > 0 else 0))
        x = pad_l + (c + 0.5) * cw
        y = pad_t + (rows - 1 - r + 0.5) * ch
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="15" fill="{PAPER}" '
                   f'stroke="{TERRACOTTA}" stroke-width="2"/>')
        out.append(f'<text x="{x:.1f}" y="{y + 5:.1f}" text-anchor="middle" '
                   f'font-family="PT Mono, monospace" font-size="13" font-weight="bold" '
                   f'fill="{INK}">{i + 1:02d}</text>')
    out.append("</svg>")
    Path(path).write_text("\n".join(out), encoding="utf-8")
    return str(path)


def decision_tree_svg(
    question: str,
    branches: list[tuple[str, str]],
    path: str | Path,
    outcome_text: list[str] | None = None,
    width: int = 900,
    height: int = 560,
) -> str:
    """A yes/no gate with two outcomes, drawn as the book draws everything else.

    `branches` is (yes_label, no_label). The trunk carries the question and each
    panel states the action that follows, so the figure is a decision tool
    rather than an ornament. `outcome_text` is the action line per branch and is
    supplied by the caller: the generator knows nothing about the subject, so
    the same drawing serves a land manual, a course or an engineering report.
    """
    if outcome_text is None:
        outcome_text = [
            "Record the finding in the primary source, then price the constraint "
            "rather than the hope.",
            "Hold the decision open until the missing evidence is in hand.",
        ]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    trunk_w, gate_h = 300, 86
    top = 40
    trunk_x = (width - trunk_w) / 2

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" aria-label="Decision">',
        f'<rect width="{width}" height="{height}" fill="{PAPER}"/>',
        f'<rect x="{trunk_x:.1f}" y="{top}" width="{trunk_w}" height="{gate_h}" rx="4" '
        f'fill="none" stroke="{INK}" stroke-width="1.6"/>',
        f'<rect x="{trunk_x:.1f}" y="{top}" width="{trunk_w}" height="4" fill="{BRASS}"/>',
    ]
    words = _truncate(question, 90).split()
    line, lines = "", []
    for w in words:
        if len(line) + len(w) + 1 > 26:
            lines.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    lines.append(line)
    for i, ln in enumerate(lines[:3]):
        out.append(f'<text x="{width / 2:.1f}" y="{top + 34 + i * 20:.1f}" text-anchor="middle" '
                   f'font-family="PT Serif, Georgia, serif" font-size="17" fill="{INK}">'
                   f'{_esc(ln)}</text>')

    stem_bottom = top + gate_h
    mid_y = height / 2 + 20
    out.append(f'<line x1="{width / 2:.1f}" y1="{stem_bottom}" x2="{width / 2:.1f}" '
               f'y2="{mid_y - 12}" stroke="{INK}" stroke-width="1.6"/>')

    panel_w = (width - 120) / 2
    for i, lbl in enumerate(branches):
        px = 60 if i == 0 else width - 60 - panel_w
        out.append(f'<line x1="{width / 2:.1f}" y1="{mid_y - 12}" x2="{px + panel_w / 2:.1f}" '
                   f'y2="{mid_y - 12}" stroke="{INK}" stroke-width="1.6"/>')
        out.append(f'<line x1="{px + panel_w / 2:.1f}" y1="{mid_y - 12}" '
                   f'y2="{px + panel_w / 2:.1f}" y2="{mid_y:.1f}" stroke="{INK}" stroke-width="1.6"/>')
        tone = BRASS if i == 0 else TERRACOTTA
        out.append(f'<rect x="{px:.1f}" y="{mid_y:.1f}" width="{panel_w:.1f}" '
                   f'height="{height - mid_y - 60:.1f}" fill="none" stroke="{RULE}" '
                   f'stroke-width="1.2" rx="4"/>')
        out.append(f'<rect x="{px:.1f}" y="{mid_y:.1f}" width="{panel_w:.1f}" height="4" fill="{tone}"/>')
        out.append(f'<text x="{px + 18:.1f}" y="{mid_y + 34:.1f}" '
                   f'font-family="PT Sans, Helvetica, Arial, sans-serif" font-size="13" '
                   f'font-weight="bold" fill="{tone}" letter-spacing="1.6">'
                   f'{_esc(_truncate(lbl, 30).upper())}</text>')
        body = _truncate(outcome_text[i], 130)
        blines, cur = [], ""
        for w in body.split():
            if len(cur) + len(w) + 1 > 30:
                blines.append(cur)
                cur = w
            else:
                cur = f"{cur} {w}".strip()
        blines.append(cur)
        for j, ln in enumerate(blines[:5]):
            out.append(f'<text x="{px + 18:.1f}" y="{mid_y + 62 + j * 21:.1f}" '
                       f'font-family="PT Serif, Georgia, serif" font-size="15" fill="{INK}">'
                       f'{_esc(ln)}</text>')
    out.append("</svg>")
    Path(path).write_text("\n".join(out), encoding="utf-8")
    return str(path)
