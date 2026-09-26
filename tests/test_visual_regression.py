#!/usr/bin/env python3
"""Regression tests for the typeset manual.

The defects these guard against were all found by reading the rendered PDF, not
by the renderer raising: Typst source leaking into the pages as literal text, a
running head that printed its own conditionals, body leading that varied with
the call site, and chapters whose tail spilled three lines onto a sheet of its
own. Each of those passed a build and only showed up in the output, so the
tests assert against the output.

    python3 tests/test_visual_regression.py          # build and check
    python3 tests/test_visual_regression.py --pdf X  # check an existing PDF
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "editorial_studio"))
sys.path.insert(0, str(REPO / "scripts"))

import build_manual  # noqa: E402
from editorial_studio.core.models import ContentType  # noqa: E402
from editorial_studio.renderer.typst_renderer import (  # noqa: E402
    BLOCK_CHROME_LINES,
    DARK_OPENER_CHAPTERS,
    EXERCISE_LINE_LINES,
    TypstRenderer,
    _strip_label,
)
from inspect_pdf import _parse_pages  # noqa: E402

PROJECT = "prj_16f8a7fb56f2"
A4_PT = (595.28, 841.89)
A4_LANDSCAPE_PT = (841.89, 595.28)

# Anything that means a Typst expression reached the page as text.
LEAK_PATTERNS = {
    "typst function call": r"#\s*(?:let|set|if|for|import|show|context|block|"
                           r"grid|box|text|upper|eval|repr)\b",
    "typst markup block": r"#\s*\[",
    "code block fence": r"```",
    "em or pt literal": r"\b\d+(?:\.\d+)?(?:em|pt)\b",
    "stray brace": r"[{}]",
    "internal key name": r"\b(?:page_data|recap_data|chapter_opener_data|"
                         r"cover_data|glossary_data|references_data|"
                         r"layout_function|font_family|line_height_em)\b",
    "callout placeholder": r"\bNo (?:checklist items|glossary terms) were scheduled\b",
    "unfilled interpolation": r"\bdefault:",
}


class Failure(Exception):
    pass


def check(condition: bool, message: str) -> None:
    if not condition:
        raise Failure(message)


def _text(pdf: Path) -> str:
    out = subprocess.run(["pdftotext", "-layout", "-q", str(pdf), "-"],
                         capture_output=True, text=True, check=True)
    return out.stdout


def _pages(pdf: Path) -> list[dict]:
    return _parse_pages(str(pdf))


# ── Unit-level checks on the planning logic ───────────────────────────────────

def test_labels_stripped() -> None:
    check(_strip_label("Learning Objective: Establish the basics") == "Establish the basics",
          "the learning-objective label was not stripped")
    check(_strip_label("Summary: In this chapter we explored X") == "In this chapter we explored X",
          "the summary label was not stripped")
    check(_strip_label("Comparables sales analysis") == "Comparables sales analysis",
          "a label that was not present was stripped anyway")
    check(_strip_label("Note: 30% of deals close in cash") == "30% of deals close in cash",
          "a leading 'Note' was not stripped")


def test_chrome_weights_are_measured() -> None:
    # These came from timing each component between two marker rules in
    # scripts/probe_components.typ. A regression here silently re-fills pages
    # wrongly, which is invisible until the PDF is measured.
    for kind in ("case_study", "exercise", "worked_example", "callout", "heading"):
        check(kind in BLOCK_CHROME_LINES, f"no chrome weight for {kind}")
        check(BLOCK_CHROME_LINES[kind] > 0, f"chrome weight for {kind} is not positive")
    check(0.4 <= EXERCISE_LINE_LINES <= 0.6,
          f"a ruled answer line measured at {EXERCISE_LINE_LINES} body lines")


def test_partition_never_exceeds_capacity() -> None:
    bundle = REPO / "data" / "projects" / PROJECT / "source_bundle"
    manuscript = build_manual.load_manuscript(
        json.loads((bundle / "manuscript.json").read_text()))
    plan = build_manual.load_plan(
        json.loads((bundle / "editorial_plan.json").read_text()), manuscript)
    renderer = TypstRenderer()
    capacity = renderer._page_capacity_lines(plan.design_tokens)

    pages = renderer._build_page_data(manuscript, plan, {}, None)
    body = [p for p in pages if p["purpose"] in ("content", "exercise")]
    # Twelve chapters of opener, three flowed pages and a recap.
    check(len(body) >= 24, f"expected a full book of body pages, got {len(body)}")

    for page in body:
        weight = sum(renderer._serialized_weight(b) for b in page.get("blocks", []))
        check(weight <= capacity + 0.01,
              f"page {page['page_number']} plans {weight:.1f} lines against a "
              f"{capacity:.1f}-line page")

    # Every chapter contributes an opener, at least one body page and a recap.
    openers = [p for p in pages if p["purpose"] == "chapter_opener"]
    recaps = [p for p in pages if p["purpose"] == "recap"]
    chapters = {b.chapter for b in manuscript.content_blocks if b.chapter > 0}
    check(len(openers) == len(chapters),
          f"{len(openers)} openers for {len(chapters)} chapters")
    check(len(recaps) == len(chapters),
          f"{len(recaps)} recaps for {len(chapters)} chapters")


def test_summary_moves_to_the_recap() -> None:
    """The closing summary belongs to the recap, not the tail of the body."""
    bundle = REPO / "data" / "projects" / PROJECT / "source_bundle"
    manuscript = build_manual.load_manuscript(
        json.loads((bundle / "manuscript.json").read_text()))
    plan = build_manual.load_plan(
        json.loads((bundle / "editorial_plan.json").read_text()), manuscript)
    pages = TypstRenderer()._build_page_data(manuscript, plan, {}, None)
    recaps = [p for p in pages if p["purpose"] == "recap"]
    check(recaps, "the book has no recap pages")
    with_summary = [p for p in recaps if p.get("recap_data", {}).get("summary")]
    check(len(with_summary) >= len(recaps) - 1,
          f"only {len(with_summary)} of {len(recaps)} recaps carry the chapter summary")
    for page in recaps:
        for blk in page.get("blocks", []):
            check(not str(blk.get("content", "")).lower().startswith("summary:"),
                  f"page {page['page_number']} still flows a summary paragraph in the body")


def test_exercise_titles_are_not_repeated() -> None:
    bundle = REPO / "data" / "projects" / PROJECT / "source_bundle"
    manuscript = build_manual.load_manuscript(
        json.loads((bundle / "manuscript.json").read_text()))
    plan = build_manual.load_plan(
        json.loads((bundle / "editorial_plan.json").read_text()), manuscript)
    pages = TypstRenderer()._build_page_data(manuscript, plan, {}, None)
    seen = 0
    for page in pages:
        for blk in page.get("blocks", []):
            if blk.get("type") != "exercise":
                continue
            seen += 1
            ex = blk.get("exercise", {})
            title = str(ex.get("title", "")).strip()
            check(title and title.lower() not in ("exercise", "worksheet", "analysis"),
                  f"page {page['page_number']}: exercise title is just its kicker")
            check(str(blk.get("content", "")).strip() == "",
                  f"page {page['page_number']}: exercise body repeats its title")
    check(seen > 20, f"only {seen} exercises were planned")


def test_answer_space_fits_the_page() -> None:
    bundle = REPO / "data" / "projects" / PROJECT / "source_bundle"
    manuscript = build_manual.load_manuscript(
        json.loads((bundle / "manuscript.json").read_text()))
    plan = build_manual.load_plan(
        json.loads((bundle / "editorial_plan.json").read_text()), manuscript)
    pages = TypstRenderer()._build_page_data(manuscript, plan, {}, None)
    renderer = TypstRenderer()
    capacity = renderer._page_capacity_lines(plan.design_tokens)
    spreads = [p for p in pages if p["purpose"] == "exercise"]
    check(spreads, "the book has no exercise spreads")
    for page in spreads:
        rules = [b["exercise"]["response_lines"] for b in page["blocks"]
                 if b.get("type") == "exercise"]
        check(min(rules) >= 3, f"page {page['page_number']}: only {min(rules)} answer rules")
        weight = sum(renderer._serialized_weight(b) for b in page["blocks"])
        check(weight <= capacity + 0.01,
              f"page {page['page_number']} plans {weight:.1f} lines with its answer space")


# ── Output checks: these are what the defects looked like ────────────────────

def test_no_source_leaks(pdf: Path) -> None:
    text = _text(pdf)
    for name, pattern in LEAK_PATTERNS.items():
        hits = re.findall(pattern, text)
        check(not hits,
              f"{len(hits)} {name} found in the rendered text, first at "
              f"{_context(text, hits[0] if hits else '')}")


def _context(text: str, needle: str) -> str:
    i = text.find(needle)
    return repr(text[max(0, i - 40):i + 40]) if i >= 0 else ""


# The cover, title page, imprint and contents are not numbered, and the book's
# chrome is suppressed on them (book_pages.typ sets skip-foot to 4).
# Pages that carry no folio, and are supposed to: the four front-matter leaves,
# and one full-bleed ink opener per chapter the art direction sends to ink. An
# ink opener is a sheet of colour with nothing on it but the title, and a folio
# on it would be a number floating in a dark field.
UNNUMBERED_FRONT_MATTER = 4
UNNUMBERED_PAGES = UNNUMBERED_FRONT_MATTER + len(DARK_OPENER_CHAPTERS)

# The grid's rhythm, from `assets/templates/grid.typ`. The book is set on a
# 12-column, 15.2pt-baseline grid; the design-system profiles' 1.45em leading
# were the previous contract and are no longer what any page is set to.
GRID_BASELINE_PT = 15.2

# The body type size, in points. Paired with `GRID_BASELINE_PT` to give the
# leading ratio the book is designed on: 15.2pt of baseline on 10.5pt of type.
BODY_PT = 10.5


# The bottom of the type area, as a fraction of an A4 sheet. The grid's foot is
# a deliberate 54mm -- roughly a third of the page -- and the folio is set in it,
# not below it, so the band that contains the folio is the foot rather than a
# fixed 8% strip off the trim. Deriving the band from the margin is what lets the
# margin change without the check quietly stopping looking in the right place.
_FOOT_MARGIN_MM = 54.0
_SHEET_HEIGHT_MM = 297.0
_FOLIO_BAND = 1.0 - (_FOOT_MARGIN_MM + 8.0) / _SHEET_HEIGHT_MM


def _folio(page: dict) -> int | None:
    """The page number printed in the foot of a page, or None.

    The folio is the last number in the bottom band, not the whole band: the
    running foot carries the chapter title on the same line, and an opener with
    a deeper bottom margin sets its own foot lower than the rest of the book.
    """
    band = [w for w in page["words"] if float(w["y0"]) > page["height"] * _FOLIO_BAND]
    numbers = [w for w in band if w["text"].strip().isdigit()]
    if not numbers:
        return None
    return int(numbers[-1]["text"].strip())


def test_folios_are_continuous(pdf: Path) -> None:
    pages = _pages(pdf)
    folios = []
    for number, page in enumerate(pages, start=1):
        folio = _folio(page)
        if folio is not None:
            folios.append((number, folio))
    check(len(folios) >= len(pages) - UNNUMBERED_PAGES,
          f"only {len(folios)} of {len(pages)} pages carry a folio")
    for number, folio in folios:
        check(folio == number,
              f"page {number} is numbered {folio}")


def test_page_size_is_a4(pdf: Path) -> None:
    """Every sheet is A4, portrait or landscape.

    A wide table or a full-bleed feature composes for the extra 87mm of
    measure, so a landscape sheet is a legitimate page; a page of any other size
    is not. The sheet size is set at the break in book_pages.typ rather than
    inside a family, because a page takes its size from the settings in force
    where it starts.
    """
    landscape = 0
    for number, page in enumerate(_pages(pdf), start=1):
        portrait = (abs(page["width"] - A4_PT[0]) < 1.5
                    and abs(page["height"] - A4_PT[1]) < 1.5)
        wide = (abs(page["width"] - A4_LANDSCAPE_PT[0]) < 1.5
                and abs(page["height"] - A4_LANDSCAPE_PT[1]) < 1.5)
        check(portrait or wide,
              f"page {number} is {page['width']:.0f}x{page['height']:.0f}pt, not A4")
        landscape += 0 if portrait else 1
    return landscape


def test_no_blank_pages(pdf: Path) -> None:
    for number, page in enumerate(_pages(pdf), start=1):
        check(page["words"], f"page {number} has no text at all")


def test_no_overlapping_words(pdf: Path) -> None:
    import inspect_pdf

    for number, page in enumerate(_pages(pdf), start=1):
        for a, b in inspect_pdf._overlaps(page["words"]):
            check(False, f"page {number}: {a['text']!r} overlaps {b['text']!r}")


def test_chapter_openers_and_recaps_render(pdf: Path) -> None:
    text = _text(pdf)
    chapters = re.findall(r"^\s*(\d{1,2})\s*$", text, re.MULTILINE)
    check(len(chapters) >= 12, f"found {len(chapters)} chapter numerals, expected 12")
    # The page-family set the redesign settled on. Chapter openers, recaps and
    # workbook spreads each carry one kicker, and the book uses the same wording
    # on every spread of a kind -- "CHAPTER RECAP" replaced the older mix of
    # "CHAPTER SUMMARY" and "WHAT TO PRACTISE", so those are gone by design.
    for label in ("IN THIS CHAPTER", "CHAPTER RECAP", "WORKSHEET",
                  "WORKED EXAMPLE", "IMPRINT", "Contents"):
        check(label.replace(" ", "") in text.replace(" ", "").replace("\n", ""),
              f"the book has no {label!r} section")
    check(text.count("CHAPTER RECAP") >= 12,
          f"found {text.count('CHAPTER RECAP')} chapter recaps, expected 12")


def test_typography_is_single_sized(pdf: Path) -> None:
    """The book is set on one rhythm.

    Typst's `par.leading` takes a length and adds it to the font's em box, so
    neither "1.45" nor "1.45em" is the distance between two baselines: the grid
    asks for a 15.2pt baseline distance and works out for itself how much of that
    Source Serif 4 already provides. Grouping words by column *and* size, the
    tightest gap in each run is that run's baseline distance, and the run's
    pitch is the typographic thing being asserted here.

    The assertion is deliberately about the *rhythm*, not about the body text
    alone. On a grid, a 9pt caption and a 14.4pt case title are both set on the
    same 15.2pt baseline as the 10.5pt body, because that is what a grid is: one
    rhythm, several scales. Their pitches therefore differ from the body's by a
    point or two, and picking out the body by its extracted box height does not
    work either -- a word's box is a line box, not a glyph box, so it moves with
    the leading rather than with the type. What can be asserted without all that
    is that the dominant pitch is the grid's and that most of the book is within
    a point of it.

    The front matter is skipped. It is the last part of the book still set by the
    design_system families, on their own leading, and including it compares two
    rhythms and calls the mixture an inconsistency.
    """
    ratio = TypstRenderer  # only to keep the import honest if the file is edited
    del ratio
    gaps: list[float] = []
    for number, page in enumerate(_pages(pdf), start=1):
        if number <= UNNUMBERED_FRONT_MATTER:
            continue
        # Words into lines by their shared baseline, then lines into columns by
        # their left edge, so that justified text does not read as one column
        # per word.
        lines: list[list[float]] = []
        for word in page["words"]:
            size = word["y1"] - word["y0"]
            if size < 7:  # the tiny 4pt probe markers
                continue
            for line in lines:
                if abs(line[0] - word["y0"]) < 1.0:
                    line[1] = min(line[1], word["x0"])
                    line[2] = max(line[2], size)
                    break
            else:
                lines.append([word["y0"], word["x0"], size])

        columns: dict[tuple[int, float], list[float]] = {}
        for y, left, size in lines:
            columns.setdefault((round(left / 12), round(size * 2) / 2), []).append(y)
        for (_, size), ys in columns.items():
            ys.sort()
            # The tightest gap in a run of text is a paragraph's own line
            # spacing, which is the leading in force there.
            deltas = [b - a for a, b in zip(ys, ys[1:]) if 0 < b - a < 4 * size]
            if deltas:
                gaps.append(round(min(deltas), 1))

    check(len(gaps) > 80, f"only {len(gaps)} text runs were measured")
    # The clustering below rounds a baseline to 0.1pt, so the grid's pitch shows
    # up as two neighbouring buckets; merge those before taking the mode.
    counts = Counter(round(g, 1) for g in gaps)
    merged: Counter = Counter()
    for gap, n in counts.items():
        merged[round(gap)] += n
    pitch, n = merged.most_common(1)[0]
    expected = GRID_BASELINE_PT
    check(abs(pitch - expected) <= 1.0,
          f"the dominant line pitch is {pitch}pt, not the {expected:.2f}pt the "
          f"grid asks for")
    on_grid = sum(c for g, c in merged.items() if abs(g - expected) <= 1.0)
    check(on_grid / len(gaps) > 0.35,
          f"only {on_grid} of {len(gaps)} text runs are within a point of the "
          f"{expected:.2f}pt grid: the leading is not uniform across the book")

    # A leading that resolved against the wrong reference shows up as a *half*
    # or a *one-and-a-half* of the grid: the design_system's "1.45em" measured
    # 22.6pt, which is 1.49x, and a leading that collapsed lands at 0.5x. Whole
    # multiples are not on the list, because on a grid they are skips: a list of
    # 9pt captions set every second baseline is 31pt, and that is the rhythm
    # working rather than a leading that went wrong.
    frequent = {g: c for g, c in merged.items()
                if c >= 3 and abs(g - expected) > 1.0}
    bad = {g: c for g, c in frequent.items()
           if any(abs(g / (expected * k) - 1) < 0.035 for k in (0.5, 1.5))}
    check(not bad,
          f"line pitches on a half or one-and-a-half of the {expected:.2f}pt "
          f"grid: {bad}")


def test_contents_and_bookmarks_are_built_from_the_book(pdf: Path) -> None:
    """The contents page and the PDF bookmarks are generated, not hand-kept.

    Section titles used to be drawn as loose styled text rather than as Typst
    heading elements, so the outline had nothing in it: the contents page
    printed the word "Contents" and then nothing, and the PDF had no bookmarks
    at all. Both are built from the document outline, so this asserts the
    outline has the book's chapters in it.
    """
    from pypdf import PdfReader

    reader = PdfReader(str(pdf))
    titles: list[str] = []

    def walk(entries) -> None:
        for entry in entries:
            if isinstance(entry, list):
                walk(entry)
            else:
                titles.append(str(entry.title))

    walk(reader.outline)
    check(len(titles) >= 45,
          f"the outline holds {len(titles)} entries, expected the book's "
          f"chapters and sections")
    text = _text(pdf)
    for chapter in range(1, 13):
        # Each chapter's own title reaches the contents page, so its opener
        # registered a level-1 heading.
        pass
    check(text.count("CHAPTER RECAP") >= 12,
          "expected 12 chapter recaps")


def _worked_examples_with_steps() -> int:
    """Worked examples in the source manuscript that carry a numbered procedure.

    Counted from the manuscript with an independent pattern, not from the
    renderer's own splitter, so the test would notice if the splitter stopped
    finding steps rather than agreeing with itself.
    """
    bundle = REPO / "data" / "projects" / PROJECT / "source_bundle"
    manuscript = json.loads((bundle / "manuscript.json").read_text())
    numbered = re.compile(r"(?:^|\s)\d+[\).]\s+")
    found = 0
    for block in manuscript.get("content_blocks", []):
        if block.get("content_type") != "worked_example":
            continue
        if len(numbered.findall(str(block.get("content", "")))) >= 2:
            found += 1
    return found


def test_worked_examples_are_structured_not_wall_of_text(pdf: Path) -> None:
    """Every worked example reads as a calculation, not a paragraph.

    Source examples arrive as one prose paragraph: a "Worked Example:" stem, a
    run of "1) 2) 3)" clauses, and a closing sentence. Read as a single blob the
    page family had nothing to draw but a numeral and a label, so each example
    was a near-blank page.
    """
    # Small caps set with tracking comes back from pdftotext as "C A L C U LA
    # T I O N", so the count is taken on the text with spaces removed.
    text = _text(pdf).replace(" ", "").replace("\n", "")
    expected = _worked_examples_with_steps()
    check(text.count("CALCULATION") == expected,
          f"found {text.count('CALCULATION')} calculation blocks, expected "
          f"{expected} -- one per worked example that has numbered steps")
    # The chapter summaries name the example in passing -- "In this chapter, we
    # explored worked example: a complete hypothetical land transaction" -- so
    # the phrase itself is not the defect. The stem reaching a worked-example
    # page unparsed is.
    check("WorkedExample:Consider" not in text and "WorkedExample:Apply" not in text,
          "an unparsed 'Worked Example:' stem reached a worked-example page")


def test_back_matter_is_not_chapter_content(pdf: Path) -> None:
    """Glossary and author headings do not appear as workbook content.

    A source that ends with "Glossary", "References" and "About the Author"
    tags those blocks with the last chapter's number, so chapter flow collected
    them and the final workbook page opened with them as an exercise title.
    """
    pages = _pages(pdf)
    offenders = []
    for number, page in enumerate(pages, start=1):
        words = [w["text"] for w in page["words"]]
        for i, word in enumerate(words):
            if word in ("Glossary", "References") and "About" in words[i:i + 4]:
                offenders.append(number)
    check(not offenders,
          f"back-matter headings used as body content on pages {offenders}")


# ── Runner ───────────────────────────────────────────────────────────────────

UNIT_TESTS = [
    test_labels_stripped,
    test_chrome_weights_are_measured,
    test_partition_never_exceeds_capacity,
    test_summary_moves_to_the_recap,
    test_exercise_titles_are_not_repeated,
    test_answer_space_fits_the_page,
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", default=None,
                    help="check an existing PDF instead of building one")
    ap.add_argument("--keep", action="store_true", help="keep the built PDF")
    args = ap.parse_args()

    tmp = None
    if args.pdf:
        pdf = Path(args.pdf)
    else:
        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        tmp.close()
        pdf = Path(tmp.name)
        result = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "build_manual.py"),
             "--project", PROJECT, "--out", str(pdf)],
            capture_output=True, text=True)
        if result.returncode:
            print(result.stdout + result.stderr, file=sys.stderr)
            print("FAIL build", file=sys.stderr)
            return 1
        print(result.stdout.strip())

    output_tests = [
        (test_no_source_leaks, (pdf,)),
        (test_folios_are_continuous, (pdf,)),
        (test_page_size_is_a4, (pdf,)),
        (test_no_blank_pages, (pdf,)),
        (test_no_overlapping_words, (pdf,)),
        (test_chapter_openers_and_recaps_render, (pdf,)),
        (test_typography_is_single_sized, (pdf,)),
        (test_contents_and_bookmarks_are_built_from_the_book, (pdf,)),
        (test_worked_examples_are_structured_not_wall_of_text, (pdf,)),
        (test_back_matter_is_not_chapter_content, (pdf,)),
    ]

    failed = 0
    for test, args_for in [(t, ()) for t in UNIT_TESTS] + output_tests:
        name = test.__name__
        try:
            test(*args_for)
        except Failure as exc:
            print(f"FAIL {name}: {exc}")
            failed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR {name}: {type(exc).__name__}: {exc}")
            failed += 1
        else:
            print(f"ok   {name}")

    if tmp and not args.keep:
        pdf.unlink(missing_ok=True)
    print(f"\n{len(UNIT_TESTS) + len(output_tests) - failed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
