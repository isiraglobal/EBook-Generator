# EBook-Generator — typeset books and manuals from structured manuscripts

**Turn a JSON manuscript into a print-ready, A4 PDF with live contents, bookmarks,
running heads, folios, illustrations and workbook spreads — laid out by a measured
page planner, not by guesswork.**

`EBook-Generator` is an open-source book and manual typesetter. You hand it a
manuscript: an ordered list of content blocks with chapter and section numbers.
It gives you back a designed PDF — cover, title page, imprint, contents, chapter
openers, body pages, case studies, worked examples, exercises with ruled answer
space, chapter recaps, references, glossary and back cover.

It is built for anyone producing a long document that has to look professionally
typeset: self-published books, field manuals, course workbooks, technical
handbooks, internal reports. Nothing in it is specific to any one subject.

- **Manuscript to PDF, end to end.** One command, no browser, no headless Chrome.
- **Measured layout.** Page fill is computed from calibrated constants, not
  estimated by eye, so pages do not spill two lines onto a sheet of their own.
- **19 page families.** Openers, magazine grids, case studies, data tables in
  landscape, workbooks, pull quotes, diagrams, references — selected per page from
  the content, with the family frozen at the page boundary.
- **Built-in visual QA.** Rasterises the output and reports fill, overlap,
  geometry and placeholder issues with zero critical defects as the target.
- **Regression-tested against the PDF.** Thirteen tests that read the rendered
  output, because these defects never raise an exception — they only show up on
  the page.

---

## Table of contents

- [Why this exists](#why-this-exists)
- [Requirements](#requirements)
- [Install](#install)
- [Quickstart](#quickstart)
- [Command reference](#command-reference)
- [Input format](#input-format)
- [Output](#output)
- [How the layout planner works](#how-the-layout-planner-works)
- [Page families](#page-families)
- [Visual QA](#visual-qa)
- [Tests](#tests)
- [Repository layout](#repository-layout)
- [Extending it](#extending-it)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Why this exists

Word processors and HTML-to-PDF pipelines typeset **flow**, not **pages**. They
are good at the first and bad at the second: a chapter ends three lines into a
new sheet, a table is split across a page turn, an exercise's writing space is
squeezed to nothing, and the contents page is a hand-typed list that is wrong by
the second revision.

A book is a sequence of *pages*. Every page has a shape, and the shape is chosen
from what the page has to hold. This generator treats the page as the unit:

1. A planner reads the manuscript and splits it into pages.
2. Each page is assigned a **family** — a layout that suits its content — and the
   family is **frozen** at the page boundary, so the rest of the page composes
   inside one shape instead of being re-typed per paragraph.
3. The planner's line weights come from **measured** component heights, not
   intuition, so a page it says will fit actually fits.
4. Typst sets the result, and a QA pass rasterises it and measures what came out.

The output of step 4 is compared against the plan. Where they disagree, the
constants are re-measured rather than the threshold loosened.

## Requirements

| Tool | Version | Needed for | Install |
| --- | --- | --- | --- |
| [Typst](https://typst.app) | 0.13+ (developed on 0.15.1) | typesetting | `brew install typst` |
| Python | 3.10+ (developed on 3.13) | planner, renderer, QA | — |
| Poppler | any | `qa_pdf.py` and the tests | `brew install poppler` |
| Pillow, NumPy, pypdf, PyYAML | any | QA, inspection, config | `pip install -r requirements-render.txt` |

The typefaces (PT Serif, PT Sans, PT Mono) are resolved from your system font
paths. If they are missing, Typst substitutes and the layout still builds, but
line breaking and measure will differ from the measured geometry.

## Install

```bash
git clone <your-fork-or-clone-url> ebook-generator
cd ebook-generator

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-render.txt
```

The render path is deliberately light. The full `editorial_studio` distribution
(FastAPI service, MCP server, web UI, ingestion and AI pipelines) is installed
only if you want it:

```bash
pip install -e editorial_studio       # optional: the complete application
editorial-studio --help
```

## Quickstart

Build the bundled 12-chapter example:

```bash
python3 scripts/build_manual.py
# wrote output/land-field-manual-12ch.pdf
```

Check it:

```bash
python3 scripts/qa_pdf.py output/land-field-manual-12ch.pdf
# pages: 85  mean vertical fill: 71%
# critical: 0  warnings: 0
```

Run the regression tests against a fresh build:

```bash
python3 tests/test_visual_regression.py
# 16 passed, 0 failed
```

Build your own manuscript:

```bash
python3 scripts/build_manual.py \
    --bundle path/to/my_project/source_bundle \
    --out output/my-book.pdf
```

`--bundle` points at a directory holding `manuscript.json` and
`editorial_plan.json`. Nothing else is required.

## Command reference

### `scripts/build_manual.py` — render

```
python3 scripts/build_manual.py [--project ID] [--out PATH] [--bundle DIR] [--dump-plan PATH]
```

| Flag | Default | Meaning |
| --- | --- | --- |
| `--project` | `prj_16f8a7fb56f2` | Project id under `data/projects/`. |
| `--bundle` | *(none)* | Explicit source bundle directory. Overrides `--project`. |
| `--out` | `output/land-field-manual-12ch.pdf` | Output PDF path. |
| `--dump-plan` | *(none)* | Write the computed page plan as JSON, with each page's family, purpose and estimated line weight. |

Set `EBOOK_KEEP_TYPST=1` to keep the Typst work directory instead of deleting it
after the build. Page families are chosen in Python but paginated by Typst, and
weak page breaks mean the two page counts differ; the retained
`assets/content.json` and `main.typ` are the only way to see what a given PDF page
was actually asked to typeset.

### `scripts/qa_pdf.py` — measure the output

```
python3 scripts/qa_pdf.py BOOK.pdf
```

Rasterises every page and reports fill ratio, blank pages, word overlap, content
bleed and placeholder text. Exits non-zero on critical issues.

### `scripts/inspect_pdf.py` — structure and geometry

```
python3 scripts/inspect_pdf.py BOOK.pdf [--plan plan.json] [--pages 1-20] [--no-ink]
```

Page-by-page word and line boxes, page sizes, fonts, bleed edges. Fill is
measured from the raster, so a ruled answer line counts as ink; `--no-ink`
falls back to the text boxes alone and cannot see a rule. Also used as a library
by the test suite (`_parse_pages`, `_overlaps`).

`--plan` takes the JSON from `--dump-plan` and labels each page with its
declared purpose. Note that plan page numbers and PDF page numbers can differ:
the plan does not know that the contents page runs to two sheets, because
Typst paginates it.

### `scripts/measure_components.py` — re-measure the constants

```
typst compile --root / scripts/probe_components.typ /tmp/probe.pdf
python3 scripts/measure_components.py /tmp/probe.pdf
```

Prints the measured chrome for every page component. **Run this after changing any
card, callout or heading style** and copy the output into `BLOCK_CHROME_LINES` in
`editorial_studio/editorial_studio/renderer/typst_renderer.py`. The planner is
only as accurate as these measurements.

## Input format

A source bundle is a directory of JSON. Two files matter:

```
source_bundle/
├── manuscript.json      # the content
└── editorial_plan.json  # design tokens and declared pages
```

`manuscript.json` is an ordered block list. Each block declares what it *is*; the
renderer decides how it looks.

```json
{
  "id": "ms_...",
  "title": "The Land Investor's Field Manual",
  "author": "...",
  "content_blocks": [
    {
      "id": "cb_0001",
      "content": "Chapter title",
      "content_type": "heading",
      "semantic_role": "title",
      "chapter": 1,
      "section": 0,
      "order": 1,
      "level": 0,
      "metadata": {}
    }
  ]
}
```

### Fields that drive layout

| Field | Effect |
| --- | --- |
| `content_type` | Chooses the component: `heading`, `paragraph`, `case_study`, `worked_example`, `exercise`, `callout`, `list`, `checklist`, `definition`, `table`, `quotation`, `reference`, `image_instruction`. |
| `chapter` | Groups blocks into a chapter: opener, body, recap. |
| `order` | Sequence within the chapter. |
| `level` | Heading depth; level 1 and 2 entries reach the contents page. |
| `semantic_role` | `glossary`, `reference`, `index`, `appendix` and `back_matter` are routed out of chapter flow into the back matter, even when they carry a chapter number. |
| `metadata` | Per-block detail: exercise `kicker` / `title` / `response_lines`, case-study `title` / `context`, table headers and rows, illustration `path` / `caption`. |

A worked example or case study may arrive as a single prose paragraph. The
renderer decomposes it into a problem statement, numbered calculation steps and a
closing verification note, so the page composes as a worked calculation rather
than a wall of text.

### Design tokens

`editorial_plan.json` carries the page size, margins, palette and type scale.
`EDITORIAL_PALETTE` in `editorial_studio/editorial_studio/design_system/profiles.py`
holds the editorial palettes. The default is a warm paper-and-ink scheme
(`#F7F3EC` paper, `#1A1815` ink, `#B08D57` brass, `#A0523D` terracotta).

## Output

A single A4 PDF containing, in order:

1. Cover
2. Title page
3. Imprint / copyright
4. Contents (chapters, then sections) — live, from the document outline
5. Per chapter: an opener, then body pages, then workbook spreads, then a recap
6. Glossary and references, if the manuscript has any
7. Back cover

Page size is A4 throughout. Seven of the example book's pages are landscape
(842×595) because they lead with a wide figure; the sheet size is a property of
the plan, not of the layout, and the two interleave freely.

Also present: running heads, folios on every numbered page, PDF bookmarks, and
deterministic SVG illustrations generated from the page's own content — so the
book needs no artwork and every rebuild is byte-stable.

## How the layout planner works

`typst_renderer.py` computes the book in one pass.

**Capacity.** The text block's height divided by the body baseline pitch, scaled
by `PAGE_FILL_HEADROOM` (0.94) to leave room for estimation error. On A4 with
10.5pt type at a 15.22pt pitch that is about 43 lines.

**Weight.** Every block is weighed in page lines: its text at
`CHARS_PER_LINE / 6` words per line, plus measured chrome for its component
(insets, kickers, rules, card padding), plus any ruled answer lines it carries,
plus 0.5 of a line for the space after it.

**Partition.** Blocks are grouped into pages greedily. Unsplittable blocks
(exercises, worked examples, cases) are atomic: they start a page rather than
stranding the one before them. A heading is never allowed to end a page — it
moves forward to open the page holding its section.

**Family.** The page's lead block nominates candidate families; the first one
whose budget the page's weight fits wins, with a rotation so two adjacent pages of
similar material still compose differently. The family is then fixed for the page.

**Budget.** `FAMILY_GEOMETRY[family] = (column_width, headroom)`, applied as
`capacity * headroom / width`. The division matters: weights are counted in
full-measure lines, so a narrower column must *raise* the line budget by the same
factor it costs in leading.

**Answer space.** For a workbook spread, the physical page less the spread's own
furniture and the exercises' own words is divided by the number of tasks and by
`ANSWER_AREA_LINE_LINES` (0.89 — a 13pt gap plus a 0.55pt rule at a 15.22pt
pitch), clamped to 3–18 rules per task.

If a rendered page disagrees with the plan, the constants move; the QA threshold
does not.

## Page families

Nineteen layouts, all in `editorial_studio/editorial_studio/assets/templates/page_families.typ`:

| | Family | Use |
| --- | --- | --- |
| A | `minimal-editorial` | Quiet text page with a wide margin field |
| B | `opener-split`, `opener-stacked`, `opener-vertical`, `opener-centered` | Four chapter-opening compositions |
| C | `dark-feature-opener` | Full-bleed ink opener with its own light footer |
| D | `asymmetric-grid` | Main column plus a wide sidebar band |
| E | `text-visual-split` | Narrow text column beside a figure |
| F | `framed-feature` | One concept in an inset frame with corner brackets |
| G | `full-width-feature` | Dominant wide element; landscape when the plan says so |
| H | `case-study-editorial` | Scenario, body, and a "what to carry forward" panel |
| I | `worked-example-page` | Numeral, problem, inputs, numbered calculation, result |
| J | `workbook-exercise` | Up to two tasks, each with its own ruled response area |
| K | `checklist-page` | Ticked action list |
| L | `pull-quote-page` | Large attributed quotation |
| M | `diagram-page` | Process diagram with numbered steps |
| N | `data-table-page` | Landscape reference table |
| O | `recap-plan-page` | Chapter closing page: summary, sections, practice |
| P | `reference-page` | Glossary or sources |

Page size is set at the break in `book_pages.typ`, not inside a family. A page
takes its size from the settings in force where it starts, and the break that
starts it belongs to the previous page's scope — so a family-level `set page` was
silently overridden. The plan publishes `width_mm` / `height_mm` per page and the
loop applies them, which is what makes a landscape table page actually landscape.

## Visual QA

```
$ $ python3 scripts/qa_pdf.py output/land-field-manual-12ch.pdf
pages: 85  mean vertical fill: 71%
critical: 0  warnings: 0
```

Checks performed:

- **Fill** — used depth of the text block, from the first inked body row to the
  last. Measured this way because a workbook page is a header and eighteen ruled
  writing lines, each one row of ink separated by a band of paper; measuring
  contiguous ink bands scored a full page of writing space as a title-only page.
- **Blank pages** and **word overlap** on both axes.
- **Geometry** — bleed past the trim, unexpected page sizes. A run can hold
  portrait and landscape sheets together, so the reported sizes are a set.
- **Placeholder text** — `nan`, `TODO`, unfilled interpolations.

Ink analysis runs at 144dpi with a cutoff at gray 235. Paper is about 243 and a
0.55pt rule anti-aliases to about 208, so a cutoff at 200 read every hairline in
the book as paper. Column-overlap detection keeps the stricter cutoff, because
light rules span the full measure and would otherwise look like two columns
colliding.

## Tests

```
python3 tests/test_visual_regression.py
python3 tests/test_visual_regression.py --pdf path/to/any.pdf
```

The suite builds the book and asserts against the rendered PDF:

| Test | Guards |
| --- | --- |
| `test_no_source_leaks` | Typst source never reaches the page as text |
| `test_labels_stripped` | Internal kicker labels are not printed twice |
| `test_page_size_is_a4` | Every sheet is A4, portrait or landscape |
| `test_folios_are_continuous` | Every numbered page carries its own number |
| `test_no_blank_pages` | No sheet is empty |
| `test_no_overlapping_words` | No two words are printed on top of one another |
| `test_chapter_openers_and_recaps_render` | Front matter and all 12 recaps present |
| `test_typography_is_single_sized` | Leading is a fixed multiple of the type size everywhere |
| `test_chrome_weights_are_measured` | Planner constants match the probe output |
| `test_partition_never_exceeds_capacity` | No planned page is over budget |
| `test_summary_moves_to_the_recap` | Chapter summaries are not duplicated in the body |
| `test_exercise_titles_are_not_repeated` | Exercise titles appear once |
| `test_answer_space_fits_the_page` | Ruled response space matches the available height |
| `test_contents_and_bookmarks_are_built_from_the_book` | The outline is built from real heading elements, so contents and bookmarks are never stale |
| `test_worked_examples_are_structured_not_wall_of_text` | Every worked example with numbered steps gets a calculation region |
| `test_back_matter_is_not_chapter_content` | Glossary and author headings do not appear as workbook content |

## Repository layout

```
ebook-generator/
├── scripts/
│   ├── build_manual.py          # render a manuscript to PDF
│   ├── qa_pdf.py                # measure the output
│   ├── inspect_pdf.py           # page structure and geometry
│   ├── measure_components.py    # re-measure the planner's constants
│   └── probe_components.typ     # the fixture that measurement renders
├── tests/
│   └── test_visual_regression.py
├── data/projects/<id>/source_bundle/
│   ├── manuscript.json
│   └── editorial_plan.json
├── output/                      # build artifacts, gitignored
└── editorial_studio/editorial_studio/
    ├── renderer/typst_renderer.py    # the planner and serialiser
    ├── core/models.py                # Manuscript, ContentBlock, ContentType, PagePurpose
    ├── design_system/profiles.py     # palettes
    └── assets/templates/
        ├── design_system.typ         # type scale, rules, panels, answer areas
        ├── page_families.typ         # the 19 page families
        ├── layout_library.typ        # dispatch and shared layout helpers
        ├── helpers.typ               # cards, lists, tables, running chrome
        └── book_pages.typ            # entry point, page geometry, show rules
```

Generated files are never committed. PDFs, page rasters, `__pycache__`, the dev
SQLite database and `output/` are all in `.gitignore`; a build is
`python3 scripts/build_manual.py` and nothing else.

## Extending it

**Add a page family.** Write `#let layout-my-family(pg, doc, th) = { ... }` in
`page_families.typ`, register the name in `layout_library.typ`'s
`layout-functions` map, add its geometry to `FAMILY_GEOMETRY` and its kicker to
`FAMILY_LABELS` in `typst_renderer.py`, and nominate it in
`_lead_candidates`. Re-measure the components it uses.

**Add a content type.** Add it to `ContentType`, handle it in
`_serialize_block` and in `render-block` in `helpers.typ`, and add its chrome
cost to `BLOCK_CHROME_LINES`.

**Change a card, callout or heading.** Re-run `measure_components.py` and update
`BLOCK_CHROME_LINES`. This is not optional bookkeeping: a wrong constant does not
raise, it just quietly re-fills every page that uses the component.

**Change a palette.** Edit `EDITORIAL_PALETTE` in
`design_system/profiles.py`; the type scale and leading live in
`design_system.typ`.

## Troubleshooting

**"typst: command not found"** — install Typst 0.13+ and make sure it is on
`PATH`. The renderer shells out to it; there is no pure-Python fallback.

**A page spills two lines onto a sheet of its own.** The planner under-estimated
that page. Check `FAMILY_GEOMETRY` for the family: is the column width right, and
is the headroom still true? If a component changed, re-run
`measure_components.py`. If the page is led by a family that draws its own
structure (a worked example's inputs grid, a summary's exercise list), that
structure is not in `BLOCK_CHROME_LINES` and should be charged there.

**A page is only 5% full and carries two lines.** The same problem in the other
direction: an over-estimate, or a block the page cannot hold. The partition
handles a stranded heading; a stranded *paragraph* means the budget is too low.

**Blank or half-page landscape.** Sheet size is set at the break in
`book_pages.typ`. If a family still sets `width`/`height`/`flipped`, remove them:
`flipped: true` means the dimensions you supply are portrait-first, so
`width: 297mm, height: 210mm, flipped: true` asks for a **portrait** sheet.

**A rule or hairline is not visible to QA.** It probably is not visible at all.
Ink analysis runs at 144dpi with a cutoff at 235; paper is about 243. If a rule
needs to survive a printer, give it real weight (0.5pt or more).

**Fonts substituted.** `typst fonts` lists what Typst can see. The design assumes
PT Serif / PT Sans / PT Mono; a substitution changes measure and breaks the
measured geometry.

## License

MIT. See `editorial_studio/pyproject.toml`.
