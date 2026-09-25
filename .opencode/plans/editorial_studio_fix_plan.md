# Editorial Studio Fix Plan: From 5-Page Failure to Production-Ready Ebook Pipeline

## Executive Summary

The Editorial Studio pipeline is architecturally broken: the planner creates 54 detailed page plans, but the renderer ignores them completely, dumping all chapter content into 13 giant sections and letting Typst auto-paginate. The result is a 27-page PDF with "Chapter 0" in the TOC, missing layout families, and no content coverage validation.

**Root Cause**: Complete disconnect between planner (page plans with `content_block_ids`) and renderer (ignores page plans, concatenates all blocks per chapter).

---

## Phase 1: Fix Manuscript Generator - Content Structure

### 1.1 Add `matter` Field to ContentBlock
**File**: `editorial_studio/editorial_studio/core/models.py`

Add `matter: str = "body"` field to `ContentBlock` dataclass with values: `"front"`, `"body"`, `"back"`.

### 1.2 Update ManuscriptGenerator
**File**: `editorial_studio/editorial_studio/content/generator.py`

Changes:
- Front matter blocks: `matter="front"`, `chapter=0` (or omit chapter)
- Body chapters: `matter="body"`, `chapter=1..N`
- Back matter blocks: `matter="back"`, `chapter=0` (or omit chapter)
- Add validation method `_validate_manuscript()`:
  - Minimum 300 words per chapter (configurable)
  - No placeholder strings ("Lorem ipsum", "TODO", "placeholder")
  - Each chapter has at least 3 content blocks (heading + 2 paragraphs)
  - All required sections present (intro, sections, summary, exercises)
  - No duplicate content IDs
  - Return validation result with specific errors

### 1.3 Update ManuscriptIngester
**File**: `editorial_studio/editorial_studio/content/ingestion.py`

- Detect front matter (title page, preface, TOC markers) -> `matter="front"`
- Detect back matter (glossary, references, index, about author) -> `matter="back"`
- Everything else -> `matter="body"`

---

## Phase 2: Fix Editorial Planner - Page Planning

### 2.1 Skip Chapter 0 in Page Plans
**File**: `editorial_studio/editorial_studio/art_director/planner.py`

In `_create_page_plans()`:
- Filter blocks: `body_blocks = [b for b in manuscript.content_blocks if b.matter == "body"]`
- Group only body blocks by chapter
- Front matter handled by dedicated template pages (cover, title, copyright, TOC)
- Back matter handled by dedicated template pages (glossary, references, back cover)

### 2.2 Ensure All Body Blocks Assigned
**File**: `editorial_studio/editorial_studio/art_director/planner.py`

In `_plan_chapter()`:
- Every content block (except headings) must be assigned to a page plan
- Track assigned block IDs, verify coverage at end
- Raise validation error if any body block unassigned

### 2.3 Fix Content Block IDs in Page Plans
**File**: `editorial_studio/editorial_studio/art_director/planner.py`

- `_make_content_page()`: include ALL block IDs for that page's content
- `_make_chapter_opener()`: include chapter heading block ID
- `_make_recap_page()`: include exercise/summary block IDs
- Verify no duplicate block IDs across pages

### 2.4 Validate Plan Coverage
**File**: `editorial_studio/editorial_studio/art_director/planner.py`

Enhance `validate_plan()`:
- Cross-reference all manuscript body blocks against page plan `content_block_ids`
- Report missing blocks as validation errors
- Check page count reasonable for word count

---

## Phase 3: Fix Typst Renderer - Hybrid Pagination

### 3.1 New Rendering Architecture
**File**: `editorial_studio/editorial_studio/renderer/typst_renderer.py`

**Core Concept**: Hybrid pagination
- **Fixed pages** (intentional art-directed): cover, title, copyright, TOC, chapter openers, full-page images, back cover -> use page plans with explicit layout families
- **Flow pages** (body content): let Typst auto-paginate with proper semantic structure, but inject layout hints per section

**Implementation**:
1. Split manuscript blocks into `front_matter`, `body_chapters`, `back_matter`
2. For fixed pages: generate explicit Typst pages using layout_library functions
3. For flow content: build sections with proper block-level serialization, let Typst paginate
4. Pass page plan metadata (layout_family, design_tokens) as section attributes for layout hints

### 3.2 Map Layout Families to layout_library.typ Functions
**File**: `editorial_studio/editorial_studio/renderer/typst_renderer.py`

Create mapping:
```python
LAYOUT_FUNCTION_MAP = {
    LayoutFamily.COVER: "layout-cover",
    LayoutFamily.TITLE: "layout-title-page",
    LayoutFamily.TOC: "layout-toc",
    LayoutFamily.CHAPTER_OPENER: "layout-chapter-opener",
    LayoutFamily.READING: "layout-reading",
    LayoutFamily.IMAGE_LED: "layout-image-led",
    LayoutFamily.CASE_STUDY: "layout-case-study",
    LayoutFamily.WORKED_EXAMPLE: "layout-worked-example",
    LayoutFamily.CHECKLIST: "layout-checklist",
    LayoutFamily.PROCESS_DIAGRAM: "layout-process-diagram",
    LayoutFamily.COMPARISON_TABLE: "layout-reading",  # tables rendered inline
    LayoutFamily.EXERCISE: "layout-exercise",
    LayoutFamily.RECAP: "layout-recap",
    LayoutFamily.GLOSSARY: "layout-reading",
    LayoutFamily.REFERENCES: "layout-reading",
    LayoutFamily.APPENDIX: "layout-reading",
    LayoutFamily.CLOSING: "layout-reading",
}
```

### 3.3 Serialize Blocks Individually (Not Concatenated)
**File**: `editorial_studio/editorial_studio/renderer/typst_renderer.py`

Rewrite `_build_sections()` -> new method `_build_flow_sections()`:
- Each block becomes a structured dict with type, content, metadata
- Don't concatenate paragraphs - keep as array of blocks
- Pass to Typst as `sections[i].blocks = [...]`

### 3.4 Render All Block Types
**File**: `editorial_studio/editorial_studio/renderer/typst_renderer.py` + `book.typ`

Implement serialization for:
- `HEADING` (levels 1-3) -> Typst headings
- `PARAGRAPH` -> body text
- `LIST` / `LIST_ITEM` -> Typst lists
- `DEFINITION` -> sidebar/boxed definition
- `TABLE` -> `render-table` helper
- `CODE` -> `render-code` helper
- `IMAGE_INSTRUCTION` -> figure with caption
- `EXERCISE` -> exercise block with response area
- `WORKED_EXAMPLE` -> worked example layout
- `CALLOUT` / `WARNING` / `NOTE` / `TIP` -> `callout-box` helper
- `QUOTATION` / `PULL_QUOTE` -> pull quote styling
- `CASE_STUDY` -> case study layout
- `FOOTNOTE` -> Typst footnote
- `CITATION` -> bibliography reference

### 3.5 Pass Design Tokens Per Section
**File**: `editorial_studio/editorial_studio/renderer/typst_renderer.py`

Each section gets:
- `layout_family` (from page plan or inferred)
- `design_tokens` (for typography, colors, spacing)
- `page_geometry` (margins, columns)

---

## Phase 4: Fix Templates - Layout Library Integration

### 4.1 Update book.typ Template
**File**: `editorial_studio/editorial_studio/assets/templates/book.typ`

Changes:
- Import `layout_library.typ`
- Remove "Chapter 0" handling - front matter never reaches body sections
- Add `#let layout-functions = (cover: layout-cover, ...)` from layout_library
- Add dispatch logic: `#layout-functions.at(section.layout_family, layout-reading)(doc, p, section)`

### 4.2 Fix Front Matter in Templates
**File**: `editorial_studio/editorial_studio/assets/templates/book.typ`

- Cover page: use `layout-cover` with doc.title, doc.author
- Title page: use `layout-title-page`
- Copyright page: use `layout-copyright` (new)
- TOC: use `layout-toc`
- These are FIXED pages - not part of flow sections

### 4.3 Ensure Layout Library Functions Accept Correct Parameters
**File**: `editorial_studio/editorial_studio/assets/templates/layout_library.typ`

Verify each function signature matches what renderer passes:
- `layout-cover(doc, p)`
- `layout-title-page(doc, p)`
- `layout-toc(doc, p)`
- `layout-chapter-opener(doc, p, chapter_num, chapter_title, epigraph, learning_objectives)`
- `layout-reading(doc, p, content_blocks)`
- `layout-image-led(doc, p, image_data, content_blocks)`
- `layout-case-study(doc, p, case_data)`
- `layout-worked-example(doc, p, example_data)`
- `layout-checklist(doc, p, checklist_data)`
- `layout-process-diagram(doc, p, diagram_data)`
- `layout-exercise(doc, p, exercise)`
- `layout-recap(doc, p, recap_data)`

### 4.4 Add Helpers for Missing Block Types
**File**: `editorial_studio/editorial_studio/assets/templates/helpers.typ`

Add helpers for:
- `render-definition(term, definition)`
- `render-pull-quote(text, author)`
- `render-footnote(text)`
- `render-citation(ref)`
- `render-sidebar(content)`

---

## Phase 5: Fix QA Engine - Validation Gates

### 5.1 Pre-Render Validation
**File**: `editorial_studio/editorial_studio/qa/engine.py`

Add `validate_before_render(manuscript, plan)`:
- Manuscript completeness: min words/chapter, no placeholders, all chapters present
- Plan coverage: every body block ID appears in page plans
- Asset references: all image_instruction blocks have corresponding assets
- Font availability: required fonts installed

Return `ValidationResult(passed, errors, warnings)`

### 5.2 Post-Render Content Coverage Check
**File**: `editorial_studio/editorial_studio/qa/engine.py`

Add `validate_content_coverage(manuscript, pdf_path, plan)`:
- Extract text from each PDF page (pypdf)
- For each manuscript body block, search for its content in PDF text
- Fuzzy match (substring, 80% word overlap)
- Report: covered_blocks, missing_blocks, coverage_percentage
- Fail if coverage < 95%

### 5.3 Enhanced QA Report
**File**: `editorial_studio/editorial_studio/qa/engine.py`

Add to QAReport:
- `content_coverage: float`
- `missing_block_ids: list[str]`
- `extra_pdf_content: list[str]` (content in PDF not in manuscript)
- `layout_family_coverage: dict[str, int]` (pages per layout family)

### 5.4 Block Export on Coverage Failure
**File**: `editorial_studio/editorial_studio/export/publisher.py`

If QA coverage fails:
- Don't create export package
- Return detailed error with missing block IDs
- CLI/API returns failure with actionable message

---

## Phase 6: Regression Test Manuscript

### 6.1 Create Test Manuscript
**File**: `test_manuscript_full.json` (or markdown)

Content:
- 8+ chapters
- Chapter 1: Intro with definitions, worked example, exercise
- Chapter 2: Process diagram, checklist
- Chapter 3: Comparison table, case study
- Chapter 4: Image-led with caption
- Chapter 5: Code block, pull quote
- Chapter 6: Multiple sections, subsections
- Chapter 7: Footnotes, citations
- Chapter 8: Recap with review questions
- Front matter: title, preface, TOC
- Back matter: glossary, references, index, about author

### 6.2 Add Regression Tests
**File**: `editorial_studio/editorial_studio/tests/test_e2e.py`

Tests:
- `test_full_pipeline_coverage()`: all blocks in PDF
- `test_all_layout_families_render()`: each layout family appears
- `test_no_chapter_zero_in_toc()`: TOC doesn't show chapter 0
- `test_page_count_appropriate()`: pages approx words/350
- `test_margins_respected()`: margins match design tokens
- `test_tables_render()`: tables appear with headers/rows
- `test_exercises_render()`: exercises have response areas
- `test_images_render()`: images with captions
- `test_qa_blocks_export()`: export fails if coverage < 95%

---

## Phase 7: Generate Land Investor's Field Manual

### 7.1 Run Full Pipeline
```bash
python3 -m editorial_studio.cli.main end-to-end land_investor_manual.json \
  --title "The Land Investor's Field Manual" \
  --author "AI Editorial Studio" \
  --brand institutional \
  --output land_investor_final.pdf
```

### 7.2 Verify Output
- Page count: 40+ (12 chapters x ~3 pages + front/back matter)
- All 12 chapters in TOC with correct page numbers
- Multiple layout families: cover, title, toc, chapter_opener, reading, exercise, recap, references
- QA score > 80, coverage > 95%
- No "Chapter 0" in TOC
- Professional typography: justified, hyphenated, proper indents

### 7.3 Document Remaining Limitations
- Vision model QA requires API keys
- Image generation requires provider API keys
- Research engine returns mock data without API keys
- Some layout families need real assets (diagrams, images)

---

## File Modification Summary

| File | Changes |
|------|---------|
| `core/models.py` | Add `matter` field to ContentBlock |
| `content/generator.py` | Set matter field, add validation |
| `content/ingestion.py` | Detect matter type from markdown |
| `art_director/planner.py` | Skip chapter 0, ensure block assignment, validate coverage |
| `renderer/typst_renderer.py` | Hybrid pagination, layout mapping, block serialization |
| `assets/templates/book.typ` | Import layout_library, dispatch per section, fix front matter |
| `assets/templates/layout_library.typ` | Verify function signatures, add missing |
| `assets/templates/helpers.typ` | Add helpers for definition, pull_quote, footnote, citation |
| `qa/engine.py` | Pre-render validation, post-render coverage check |
| `export/publisher.py` | Block export on QA failure |
| `tests/test_e2e.py` | New regression test suite |
| `test_manuscript_full.json` | Comprehensive test manuscript |

---

## Success Criteria

1. Pipeline runs without "Chapter 0" in TOC
2. All 194 manuscript blocks appear in final PDF (>=95% coverage)
3. 8+ layout families visibly rendered in PDF
4. QA score > 80, no hard failures
5. Regression test passes with full test manuscript
6. Land Investor's Field Manual: 40+ pages, professional quality
7. Export package includes all artifacts
8. All existing tests still pass
