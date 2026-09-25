#!/usr/bin/env python3
"""Measure the true height of each typst component and emit the constants.

The flow planner in typst_renderer.py estimates how much page height a block
consumes as its text length plus a per-kind "chrome" allowance for the kicker,
rule, card insets and spacing. Those allowances were guessed, and guessing them
either over- or under-filled pages, which is what left chapters ending in
three-line spill sheets. This renders one of each component fenced by marker
rules (scripts/probe_components.typ) and reports the measured chrome, so
BLOCK_CHROME_LINES comes from real geometry.

    typst compile --root / scripts/probe_components.typ /tmp/probe.pdf
    python3 scripts/measure_components.py /tmp/probe.pdf

It also reports each font's natural line height, the figure
NATURAL_LEADING_RATIO in typst_renderer.py carries.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# Probe page geometry, matching the manuscript's text block.
BODY_PITCH = 10.5 * 1.45  # body_font_size_pt * line_height_em
CASES = ["paragraph", "case_study", "worked_example",
         "exercise-0-rules", "exercise-5-rules", "callout", "heading"]

WORD = re.compile(
    r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>'
)
LINE = re.compile(r"<line ")


def _pitch(pdf: Path) -> float:
    out = subprocess.run(["pdftotext", "-bbox-layout", "-q", str(pdf), "-"],
                         capture_output=True, text=True, check=True).stdout
    lines = re.findall(r'<line xMin="([\d.]+)" yMin="([\d.]+)"', out)
    ys = [float(y) for _, y in lines]
    return (ys[2] - ys[1]) if len(ys) > 2 else 0.0


def _em_boxes() -> dict[str, float]:
    """A face's em box as a size ratio: what `par.leading` adds to."""
    table: dict[str, float] = {}
    for face in ("PT Serif", "PT Sans", "PT Mono"):
        src = (
            '#set page(width:210mm,height:80mm,margin:15mm)\n'
            f'#set text(size: 10.5pt, font: "{face}")\n'
            "#set par(leading: 0pt)\n"
            "#for i in range(6) [alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi ]\n"
        )
        probe = Path("/tmp/_em_box.typ")
        probe.write_text(src)
        subprocess.run(["typst", "compile", str(probe), "/tmp/_em_box.pdf"],
                       capture_output=True)
        out = subprocess.run(
            ["pdftotext", "-bbox-layout", "-q", "/tmp/_em_box.pdf", "-"],
            capture_output=True, text=True).stdout
        ys = [float(y) for _, y in re.findall(r'<line xMin="([\d.]+)" yMin="([\d.]+)"', out)]
        if len(ys) > 2:
            table[face] = round((ys[2] - ys[1]) / 10.5, 3)
    return table


def main() -> int:
    pdf = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/probe.pdf")
    out = subprocess.run(["pdftotext", "-bbox-layout", "-q", str(pdf), "-"],
                         capture_output=True, text=True, check=True).stdout
    pages = out.split("<page ")[1:]

    print("em box ratios (EM_BOX_RATIO):")
    for face, ratio in _em_boxes().items():
        print(f"    {face!r}: {ratio},")
    print()
    print(f"body pitch {BODY_PITCH:.3f}pt")
    print(f"{'component':<18}{'box pt':>9}{'box lines':>11}{'text':>7}{'chrome':>8}")
    measured: dict[str, float] = {}
    for name, page in zip(CASES, pages):
        words = WORD.findall(page)
        top = [w for w in words if "TOPMARKER" in w[4]]
        end = [w for w in words if "ENDMARKER" in w[4]]
        if not (top and end):
            continue
        box = float(end[0][1]) - float(top[0][1])
        # One line of text per rendered line that is not a marker. Rules are
        # graphics and produce no line, so they stay in the box.
        text_lines = max(0, len(LINE.findall(page)) - 2)
        measured[name] = box / BODY_PITCH
        print(f"{name:<18}{box:>9.1f}{box / BODY_PITCH:>11.2f}"
              f"{text_lines:>7}{box / BODY_PITCH - text_lines:>8.2f}")

    if "exercise-0-rules" in measured and "exercise-5-rules" in measured:
        per_rule = (measured["exercise-5-rules"] - measured["exercise-0-rules"]) / 5
        print(f"\none ruled answer line = {per_rule:.2f} body lines "
              f"(EXERCISE_LINE_LINES)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
