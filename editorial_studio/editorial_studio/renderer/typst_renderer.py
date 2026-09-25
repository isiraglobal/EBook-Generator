from __future__ import annotations
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any

from editorial_studio.core.models import (
    Asset,
    DesignTokens,
    EditorialPlan,
    Manuscript,
    PagePlan,
    PagePurpose,
    LayoutFamily,
    ContentType,
    SemanticRole,
)
from editorial_studio.core.config import load_config

# ── Editorial palette ───────────────────────────────────────────────────────
# Warm paper / ink / brass / terracotta. Brand profiles may override any of
# these through ``DesignTokens.colors["palette"]``.
DEFAULT_PALETTE: dict[str, str] = {
    "paper": "#F7F3EC",
    "ink": "#1A1815",
    "brass": "#B08D57",
    "terracotta": "#A0523D",
    "slate": "#6B6560",
    "rule": "#D9CFBF",
    "cream": "#EFE8DB",
    "cream_deep": "#E4D9C6",
    "green": "#5C7A5C",
    "warn_bg": "#F6ECE6",
    "panel_bg": "#F3EDE3",
    "panel_bg_2": "#F6F1E7",
    "ink_on_dark": "#F7F3EC",
    "dark_note": "#C8BCA8",
}

# Typst falls back down the list, so a missing family degrades to a sibling
# rather than silently substituting a default sans.
FONT_FALLBACKS: dict[str, list[str]] = {
    "source serif 4": ["PT Serif", "Charter", "Georgia"],
    "source sans 3": ["PT Sans", "Avenir Next", "Helvetica Neue", "Arial"],
    "source code pro": ["PT Mono", "DejaVu Sans Mono", "Andale Mono"],
    "pt serif": ["PT Serif", "Charter", "Georgia"],
    "pt sans": ["PT Sans", "Avenir Next", "Helvetica Neue", "Arial"],
    "pt mono": ["PT Mono", "DejaVu Sans Mono", "Andale Mono"],
    "eb garamond": ["EB Garamond", "PT Serif", "Charter"],
    "inter": ["Inter", "PT Sans", "Avenir Next", "Arial"],
    "ibm plex serif": ["IBM Plex Serif", "PT Serif", "Charter"],
    "ibm plex sans": ["IBM Plex Sans", "PT Sans", "Avenir Next", "Arial"],
    "ibm plex mono": ["IBM Plex Mono", "PT Mono", "DejaVu Sans Mono"],
}

# Approximate metrics for the flow packer. Good enough to keep pages between
# roughly 60% and 95% full without a full measurement pass.
CHARS_PER_LINE = 92
# Lines of page height a block spends on chrome — the kicker, rule, card insets
# and spacing around its text. The first six are measured from rendered output
# by scripts/measure_components.py, which times each component between two
# marker rules; the rest are estimated from the same components' geometry and
# never appear in this manuscript. Guessed chrome silently over- and
# under-filled pages, which is what left near-blank spill sheets in the
# chapter bodies.
# Chrome is measured, not guessed: `typst compile --root / scripts/probe_components.typ
# /tmp/probe.pdf && python3 scripts/measure_components.py /tmp/probe.pdf` renders
# one of each component fenced by marker rules and reports the box height that
# is not accounted for by its own text. Re-run it after changing any card, callout
# or heading style. The values below are that probe's output; the ones it does not
# measure are scaled from the nearest measured neighbour.
BLOCK_CHROME_LINES: dict[str, float] = {
    "heading": 1.7,        # measured
    "paragraph": 0.4,      # measured
    "case_study": 2.7,     # measured
    "exercise": 2.5,       # measured
    "worked_example": 2.5, # measured
    "callout": 2.0,        # measured
    "warning": 2.0,        # callout in a different palette
    "list": 1.2,
    "list_item": 0.8,
    "checklist": 1.6,
    "definition": 2.4,
    "table": 5.0,
    "code": 4.0,
    "image_instruction": 12.0,
    "quotation": 4.0,
    "reference": 0.4,
    "process_diagram": 8.0,
    "footnote": 1.0,
}
# One ruled response line inside a generic exercise card, in page lines. This is
# the probe's measurement of `exercise-card` in helpers.typ, and the test suite
# guards it against drifting.
EXERCISE_LINE_LINES = 0.48

# One ruled response line on a workbook spread. The workbook family uses
# `answer-area` in design_system.typ, which draws a 13pt gap and a 0.55pt rule
# per line: (13 + 0.55) / 15.22pt = 0.89 of a baseline. It is nearly twice the
# card's line because the spread is writing space, not a form field. Sizing the
# spread with the card's figure fitted two exercises' worth of writing space
# onto a page that holds one.
ANSWER_AREA_LINE_LINES = 0.89

# A workbook spread's own furniture, in page lines: the head block, the accent
# rule and its gaps, and per task a number column, a kicker, a title and a brass
# marker. Measured against the rendered spread at 10.5pt on a 15.22pt baseline.
WORKBOOK_CHROME_LINES = 6.0
# Fraction of the physical page the flow planner will fill. See
# TypstRenderer._page_capacity_lines.
PAGE_FILL_HEADROOM = 0.94

# (main-column width fraction, headroom fraction) for each composed page family.
#
# The width factor is the share of the text measure the family's main column
# really gets, because wrapping the same paragraph into a 69%-wide column costs
# roughly 1.45x the lines. The headroom factor is the height the family's own
# furniture spends on the page: title block, frame, corner brackets, caption,
# input table, result panel, answer rules.
#
# Every entry is <= 1.0 in both factors, so a page planned under this rule can
# never ask for more lines than the physical page holds. Measured against the
# rendered book by scripts/qa_pdf.py and scripts/inspect_pdf.py.
# Space between two consecutive blocks, as a fraction of the body leading.
# The theme sets par_space_ratio 0.7, so each boundary after the first block on
# a page costs 0.7 * body size / body pitch ~= 0.48 of a line. A seven-block page
# carries six of them: three lines the per-block model did not know about, which
# is the size of the orphan that spilled.
BLOCK_SPACING_LINES = 0.5

# Leading factors the page families apply to a block's own text, as a multiple
# of the body leading that the line model counts at. Measured against the
# rendered book: the case-study scenario runs at 1.34, the pull-quote and
# diagram bodies at 1.32, and the opener preambles at 1.35-1.4.
BLOCK_LEADING: dict[str, float] = {
    "pull_quote": 1.32,
    "diagram": 1.32,
}

FAMILY_GEOMETRY: dict[str, tuple[float, float]] = {
    "reading": (1.00, 0.94),
    "reading-two-col": (0.49, 0.90),
    "image-led": (1.00, 0.70),
    # 132mm measure inside a 40mm/46mm margin page, and the top margin alone
    # costs five lines.
    "minimal-editorial": (0.85, 0.78),
    # 108mm main column of a 156mm measure.
    "asymmetric-grid": (0.70, 0.90),
    # 56mm main column: the tightest main measure in the book.
    "text-visual-split": (0.62, 0.80),
    # A full inset frame with a header band, corner brackets and a figure.
    "framed-feature": (0.87, 0.66),
    "full-width-feature": (1.00, 0.82),
    # 1.34 leading on the scenario plus a tinted takeaway panel below it.
    "case-study-editorial": (1.00, 0.70),
    "worked-example-page": (1.00, 0.82),
    "workbook-exercise": (1.00, 0.94),
    "checklist-page": (0.88, 0.86),
    "pull-quote-page": (1.00, 0.30),
    "diagram-page": (1.00, 0.58),
    # Landscape: a 247mm measure, but the title, rule and caption overhead is
    # proportionally smaller.
    "data-table-page": (1.00, 0.62),
    "recap-plan-page": (1.00, 0.90),
    "reference-page": (1.00, 0.90),
}

# The chapter openers. Each is a distinct composition of the same atoms, chosen
# by chapter position so no two consecutive openers arrange alike.
OPENER_FAMILIES = ("opener-split", "opener-stacked", "opener-vertical", "opener-centered")

# Families whose geometry is a promise that a figure is there, so the renderer
# draws one for them when the manuscript supplies no artwork. Excluded:
# `text-visual-split`, whose 38% region is a third of an A4 measure -- too narrow
# for a drawn figure's labels, so a split page only ever carries artwork the
# manuscript supplied at a size its author chose.
FIGURE_FAMILIES = ("diagram-page", "full-width-feature")

# A drawn figure wider than 2:1 is a landscape page's worth of information.
# Typst's A4 measure renders a 960x300 process strip at roughly 6pt labels in
# portrait, which is below the size the labels were drawn to be read at.
# Families that compose for a landscape sheet. A wide table and a full-bleed
# feature both want the extra 87mm of measure; a page that is portrait will not
# hold either of them at a readable size.
LANDSCAPE_FIGURE_FAMILIES = ("full-width-feature", "data-table-page")

# Chapters that open on ink. Three of twelve is a rhythm; all twelve would be a
# gimmick, and none would be a decision. Position-based, so it is deterministic.
DARK_OPENER_CHAPTERS = (1, 6, 11)

# The uppercase kicker a family prints above its own title. A family without
# one falls back to its own default in the template.
FAMILY_LABELS: dict[str, str] = {
    "minimal-editorial": "Field note",
    "framed-feature": "Framework",
    "full-width-feature": "Overview",
    "diagram-page": "Sequence",
    "data-table-page": "Reference table",
    "pull-quote-page": "In practice",
    "checklist-page": "Checklist",
}

# The topic vocabulary every composed page draws on.
#
# No page family may hardcode a subject noun. A manual about land, a course on
# machine learning and a report on municipal finance all use the same sixteen
# geometries; only the words change. A project supplies `domain_terms` in its
# publication brief and everything downstream — captions, labels, figure
# titles, axis captions, action lines — is built from them. Absent that, the
# neutral defaults below apply, which is why a manuscript with no brief at all
# still produces a coherent book.
DOMAIN_DEFAULT_TERMS: dict[str, str] = {
    "unit": "item",                # the thing the subject is made of
    "unit_plural": "items",
    "collection": "library",      # where those things are found
    "artifact": "record",         # the document that describes one
    "artifact_plural": "records",
    "measure": "measure",         # the quantity that is tracked
    "measure_plural": "measures",
    "actor": "practitioner",      # the person acting
    "stake": "stake",             # what is at risk
    "context": "context",         # the situation being worked through
    "unit_of_work": "task",       # a single piece of work
    "unit_of_work_plural": "tasks",
    # A sentence for a page with no artwork of its own. Composed rather than
    # hardcoded, because it is the one piece of prose the system writes itself.
    "figure_note": (
        "Read the boundaries of the problem before the item itself. Structure, "
        "access and dependency decide what any item can be used for, and they "
        "are recorded before the price is."
    ),
}

# Brief keys a project may use to declare its topic. `subject` and `audience`
# already exist on PublicationBrief, so a project only has to add the nouns.
DOMAIN_BRIEF_KEYS: dict[str, str] = {
    "domain_unit": "unit",
    "domain_unit_plural": "unit_plural",
    "domain_collection": "collection",
    "domain_artifact": "artifact",
    "domain_artifact_plural": "artifact_plural",
    "domain_measure": "measure",
    "domain_measure_plural": "measure_plural",
    "domain_actor": "actor",
    "domain_stake": "stake",
    "domain_context": "context",
    "domain_unit_of_work": "unit_of_work",
    "domain_unit_of_work_plural": "unit_of_work_plural",
    "domain_figure_note": "figure_note",
}



# A font's em box (ascent plus descent) as a multiple of its size. Typst's
# `par.leading` only accepts a length, and adds it to the em box rather than
# making up the whole baseline distance -- so `leading: 1.45em` produced a
# 22.6pt pitch on 10.5pt type, and 1.45 as a float is rejected outright. A theme
# that wants a total leading of N must pass N minus this. Measured by
# scripts/measure_components.py, which prints the table.
EM_BOX_RATIO: dict[str, float] = {
    "PT Serif": 0.70,
    "PT Sans": 0.70,
    "PT Mono": 0.70,
}
# The em box of a face with no measured entry.
DEFAULT_EM_BOX_RATIO = 0.70


# Labels the source manuscript writes into the text of a block. They name the
# block for the pipeline, not for the reader, and the callout kicker already
# says what the block is.
_BLOCK_LABEL = re.compile(
    r"^\s*(learning\s+objectives?|objectives?|key\s+takeaways?|summary|"
    r"important|note|warning|remember)\s*:\s*",
    re.IGNORECASE,
)


def _strip_label(text: str) -> str:
    return _BLOCK_LABEL.sub("", str(text).strip()).strip()


# Blocks that read as one unit and are never split across a page break.
# A worked example is one paragraph made of sentences; the family wants them
# split so it can lay out a stem, a numbered procedure and a closing note.
_EXAMPLE_SPLIT = re.compile(r"(?<=[.!?])\s+")

# Roles that a manuscript may tag on blocks which nevertheless carry a chapter
# number. Back matter is the common case: a source that ends with "Glossary",
# "References" and "About the Author" headings tags them with the last chapter's
# number, so chapter flow collected them and the last workbook page opened with
# the back-matter headings as an exercise title.
_NON_CHAPTER_ROLES = frozenset({
    SemanticRole.GLOSSARY,
    SemanticRole.REFERENCE,
    SemanticRole.BIBLIOGRAPHY,
    SemanticRole.INDEX,
    SemanticRole.APPENDIX,
    SemanticRole.BACK_MATTER,
    SemanticRole.FRONT_MATTER,
    SemanticRole.AUTHOR,
    SemanticRole.ABSTRACT,
})

# A trailing prose block whose whole content is a section label. A source that
# ends with "Glossary / References / About the Author" writes the last of those
# as an ordinary paragraph, so chapter flow was setting it as body text in the
# middle of the final workbook spread.
_BACK_MATTER_LABELS = frozenset({
    "glossary", "references", "bibliography", "index", "appendix",
    "about the author", "about the editor", "notes", "further reading",
})

_UNSPLITTABLE = frozenset({ContentType.EXERCISE, ContentType.WORKED_EXAMPLE})


class TypstRenderer:
    def __init__(self, config: dict | None = None):
        self.config = config or load_config().data
        self.typst_path = self.config.get("rendering", {}).get("typst_path", "typst")
        package_root = Path(__file__).parent.parent
        self.fonts_dir = package_root / self.config.get("rendering", {}).get("fonts_dir", "assets/fonts")
        self.templates_dir = package_root / self.config.get("rendering", {}).get("templates_dir", "assets/templates")
        self.default_dpi = self.config.get("rendering", {}).get("default_dpi", 300)
        self.preview_dpi = self.config.get("rendering", {}).get("preview_dpi", 144)

        # Layout family to layout_library function mapping.
        # Keys must match the layout-functions dictionary in layout_library.typ.
        # NOTE: values are bare keys, not "layout-*" identifiers.
        self.layout_function_map = {
            LayoutFamily.COVER: "cover",
            LayoutFamily.TITLE: "title-page",
            LayoutFamily.TOC: "toc",
            LayoutFamily.CHAPTER_OPENER: "chapter-opener",
            LayoutFamily.READING: "reading",
            LayoutFamily.READING_TWO_COL: "reading-two-col",
            LayoutFamily.IMAGE_LED: "image-led",
            LayoutFamily.IMAGE_FULL: "image-led",
            LayoutFamily.ASYMMETRICAL: "reading",
            LayoutFamily.DEFINITION_SIDEBAR: "reading",
            LayoutFamily.PULL_QUOTE: "reading",
            LayoutFamily.CHECKLIST: "checklist",
            LayoutFamily.PROCESS_DIAGRAM: "process-diagram",
            LayoutFamily.COMPARISON_TABLE: "reading",
            LayoutFamily.CASE_STUDY: "case-study",
            LayoutFamily.EXERCISE: "exercise",
            LayoutFamily.WORKED_EXAMPLE: "worked-example",
            LayoutFamily.RECAP: "recap",
            LayoutFamily.GLOSSARY: "glossary",
            LayoutFamily.REFERENCES: "references",
            LayoutFamily.APPENDIX: "reading",
            LayoutFamily.CLOSING: "reading",
            LayoutFamily.PART_OPENER: "chapter-opener",
        }

        # Page purpose wins over layout family for front and back matter: the
        # plan reuses the `title`/`cover` families for pages that must render
        # as an imprint page or a back cover.
        self.purpose_layout_map = {
            PagePurpose.COVER: "cover",
            PagePurpose.TITLE_PAGE: "title-page",
            PagePurpose.COPYRIGHT: "copyright",
            PagePurpose.DEDICATION: "reading",
            PagePurpose.TOC: "toc",
            PagePurpose.GLOSSARY: "glossary",
            PagePurpose.REFERENCES: "references",
            PagePurpose.BACK_COVER: "back-cover",
            PagePurpose.BLANK: "reading",
        }


    def render_pdf(self, manuscript: Manuscript, plan: EditorialPlan, assets: list[Asset],
                   output_path: str, strict_layout: bool = False,
                   watermark: dict[str, Any] | None = None) -> dict[str, Any]:
        work_dir = Path(tempfile.mkdtemp(prefix=f"editorial_render_{uuid.uuid4().hex[:8]}_"))
        output_path_abs = Path(output_path).resolve()
        try:
            assets_dir = work_dir / "assets"
            assets_dir.mkdir(parents=True, exist_ok=True)

            asset_map = {}
            for asset in assets:
                src = Path(asset.local_path)
                if src.exists():
                    dst = assets_dir / src.name
                    shutil.copy2(src, dst)
                    asset_map[asset.id] = f"assets/{src.name}"

            # Handle watermark image if provided
            watermark_data = {}
            if watermark and watermark.get("enabled", False):
                watermark_path = watermark.get("image_path") or watermark.get("text")
                if watermark_path:
                    src = Path(watermark_path)
                    if src.exists():
                        dst = assets_dir / src.name
                        shutil.copy2(src, dst)
                        watermark_data = {
                            "enabled": True,
                            "image_path": f"assets/{src.name}",
                            "text": watermark.get("text", ""),
                            "position": watermark.get("position", "center"),
                            "scale": watermark.get("scale", 1.0),
                            "rotation": watermark.get("rotation", 0),
                            "opacity": watermark.get("opacity", 0.15),
                            "color": watermark.get("color", "#000000"),
                            "pages": watermark.get("pages", "all"),
                            "layer": watermark.get("layer", "under"),
                        }

            # Build page-by-page data structure from editorial plan
            page_data = self._build_page_data(manuscript, plan, asset_map, assets_dir)

            content_data = {
                "title": manuscript.title,
                "subtitle": manuscript.description,
                "author": manuscript.author,
                "publisher": plan.design_tokens.brand_name,
                "language": "en",
                "preset": self._tokens_to_preset(plan.design_tokens, plan),
                # The topic vocabulary, at document level so a family can read
                # a noun without every page having to repeat it.
                "domain": self._domain_terms(plan),
                "pages": page_data,
                "watermark": watermark_data,
            }

            content_json_path = assets_dir / "content.json"
            content_json_path.write_text(json.dumps(content_data, ensure_ascii=False, indent=2))

            # Use the page-based template for proper per-page rendering
            template_path = self.templates_dir / "book_pages.typ"

            main_typ = work_dir / "main.typ"
            shutil.copy2(template_path, main_typ)

            for helper in self.templates_dir.glob("helpers.typ"):
                shutil.copy2(helper, work_dir / helper.name)

            # The layout library and the two modules it composes with. A
            # family that lives in its own file is still part of the book, so
            # it has to travel to the render work directory like the rest.
            for companion in ("layout_library.typ", "design_system.typ",
                              "page_families.typ"):
                src = self.templates_dir / companion
                if src.exists():
                    shutil.copy2(src, work_dir / companion)

            cmd = [
                self.typst_path, "compile",
                "--font-path", str(self.fonts_dir),
                str(main_typ), str(output_path_abs)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(work_dir), timeout=300)

            if result.returncode != 0:
                return {"success": False, "error": result.stderr, "output_path": ""}

            if not output_path_abs.exists():
                return {"success": False, "error": "PDF not generated", "output_path": ""}

            return {"success": True, "error": "", "output_path": str(output_path_abs)}

        finally:
            # Set EBOOK_KEEP_TYPST=1 to keep the work directory. Page families
            # are chosen in Python but paginated by Typst, and weak page breaks
            # mean the two page counts differ; the generated content.json and
            # main.typ are the only way to see what a given PDF page was asked
            # to typeset when a page does not come out as planned.
            if os.environ.get("EBOOK_KEEP_TYPST") != "1":
                shutil.rmtree(work_dir, ignore_errors=True)
            else:
                print(f"kept typst work dir: {work_dir}")

    def render_preview(self, manuscript: Manuscript, plan: EditorialPlan, assets: list[Asset],
                       output_dir: str, pages: str = "1-3", dpi: int | None = None) -> dict[str, Any]:
        dpi = dpi or self.preview_dpi
        work_dir = Path(tempfile.mkdtemp(prefix=f"editorial_preview_{uuid.uuid4().hex[:8]}_"))
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        try:
            assets_dir = work_dir / "assets"
            assets_dir.mkdir(parents=True, exist_ok=True)

            asset_map = {}
            for asset in assets:
                src = Path(asset.local_path)
                if src.exists():
                    dst = assets_dir / src.name
                    shutil.copy2(src, dst)
                    asset_map[asset.id] = f"assets/{src.name}"

            page_data = self._build_page_data(manuscript, plan, asset_map, assets_dir)

            content_data = {
                "title": manuscript.title,
                "subtitle": manuscript.description,
                "author": manuscript.author,
                "publisher": plan.design_tokens.brand_name,
                "language": "en",
                "preset": self._tokens_to_preset(plan.design_tokens, plan),
                "pages": page_data,
            }

            content_json_path = assets_dir / "content.json"
            content_json_path.write_text(json.dumps(content_data, ensure_ascii=False, indent=2))

            template_path = self.templates_dir / "book_pages.typ"
            if not template_path.exists():
                template_path = self.templates_dir / "book.typ"

            main_typ = work_dir / "main.typ"
            shutil.copy2(template_path, main_typ)

            for helper in self.templates_dir.glob("helpers.typ"):
                shutil.copy2(helper, work_dir / helper.name)

            # The layout library and the two modules it composes with. A
            # family that lives in its own file is still part of the book, so
            # it has to travel to the render work directory like the rest.
            for companion in ("layout_library.typ", "design_system.typ",
                              "page_families.typ"):
                src = self.templates_dir / companion
                if src.exists():
                    shutil.copy2(src, work_dir / companion)

            preview_pattern = work_dir / "preview_{0p}.png"
            cmd = [
                self.typst_path, "compile",
                "--font-path", str(self.fonts_dir),
                "--format", "png",
                "--ppi", str(dpi),
                "--pages", pages,
                str(main_typ), str(preview_pattern)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(work_dir), timeout=300)

            if result.returncode != 0:
                return {"success": False, "error": result.stderr, "preview_paths": []}

            png_files = sorted(work_dir.glob("preview_*.png"))
            if not png_files:
                single = work_dir / "preview.png"
                if single.exists():
                    png_files = [single]

            copied_paths = []
            for i, png in enumerate(png_files):
                dst = output_path / f"preview_{i+1:02d}.png"
                shutil.copy2(png, dst)
                copied_paths.append(str(dst))

            return {"success": True, "error": "", "preview_paths": copied_paths, "page_count": len(copied_paths)}

        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    def _mapping_value(self, mapping: dict, key, default):
        if key in mapping:
            return mapping[key]
        string_key = str(key)
        if string_key in mapping:
            return mapping[string_key]
        return default

    def _resolve_font(self, family: str) -> list[str]:
        """Return a Typst font stack: requested family first, then siblings."""
        name = str(family or "").strip()
        if not name:
            return ["PT Serif"]
        stack = FONT_FALLBACKS.get(name.lower(), [name])
        for extra in ("PT Serif", "PT Sans", "PT Mono"):
            if extra not in stack:
                stack.append(extra)
        return stack

    def _resolve_palette(self, tokens: DesignTokens) -> dict[str, str]:
        """Semantic editorial palette, with brand overrides layered on top.

        Precedence, lowest to highest: shared editorial defaults, the profile's
        ``colors["palette"]``, the profile's dedicated accent keys, then legacy
        flat token names for roles the palette never claimed.
        """
        palette = dict(DEFAULT_PALETTE)
        raw = tokens.colors.get("palette")
        explicit: set[str] = set()
        if isinstance(raw, dict):
            explicit = {k for k, v in raw.items() if isinstance(v, str)}
            palette.update({k: raw[k] for k in explicit})

        accents = (("accent_brass", "brass"), ("accent_secondary", "terracotta"))
        for src, dst in accents:
            value = tokens.colors.get(src)
            if isinstance(value, str) and value.strip():
                palette[dst] = value
                explicit.discard(dst)

        legacy = {
            "background": "paper",
            "body": "ink",
            "heading": "ink",
            "muted": "slate",
            "rule": "rule",
            "table_header": "cream_deep",
        }
        for src, dst in legacy.items():
            value = tokens.colors.get(src)
            if isinstance(value, str) and value.strip() and dst not in explicit:
                palette[dst] = value

        return palette

    def _tokens_to_preset(self, tokens: DesignTokens, plan: "EditorialPlan | None" = None) -> dict[str, Any]:
        return {
            "body_font": self._resolve_font(tokens.body_font_family),
            "heading_font": self._resolve_font(tokens.heading_font_family),
            "mono_font": self._resolve_font(tokens.mono_font_family),
            "palette": self._resolve_palette(tokens),
            "link_color": tokens.colors.get("accent", "#B08D57"),
            "text_size": f"{tokens.body_font_size_pt}pt",
            "leading_ratio": float(tokens.line_height_em),
            "leading_extra_ratio": max(
                0.0,
                float(tokens.line_height_em) - self._em_box_ratio(tokens.body_font_family),
            ),
            "par_space_ratio": float(tokens.paragraph_spacing_em),
            "justify": tokens.justify,
            "hyphenate": tokens.hyphenate,
            "paper": "a4" if tokens.page_width_mm >= 210 else "a5",
            "margin_left": f"{tokens.margin_inner_mm}mm",
            "margin_right": f"{tokens.margin_outer_mm}mm",
            "margin_top": f"{tokens.margin_top_mm}mm",
            "margin_bottom": f"{tokens.margin_bottom_mm}mm",
            "margin_inner": f"{tokens.margin_inner_mm}mm",
            "margin_outer": f"{tokens.margin_outer_mm}mm",
            "accent_color": tokens.colors.get("accent", "#B08D57"),
            "heading_color": tokens.colors.get("heading", "#1A1815"),
            "body_color": tokens.colors.get("body", "#1A1815"),
            "muted_color": tokens.colors.get("muted", "#6B6560"),
            "sidebar_bg": tokens.colors.get("sidebar_bg", "#EFE8DB"),
            "table_header": tokens.colors.get("table_header", "#E4D9C6"),
            "table_row_alt": tokens.colors.get("table_row_alt", "#FBF8F2"),
            "page_width": f"{tokens.page_width_mm}mm",
            "page_height": f"{tokens.page_height_mm}mm",
            "h1_size": f"{self._mapping_value(tokens.heading_font_sizes, 1, 22)}pt",
            "h2_size": f"{self._mapping_value(tokens.heading_font_sizes, 2, 14)}pt",
            "h3_size": f"{self._mapping_value(tokens.heading_font_sizes, 3, 11.5)}pt",
            "h1_weight": self._mapping_value(tokens.heading_weights, 1, "bold"),
            "h2_weight": self._mapping_value(tokens.heading_weights, 2, "semibold"),
            "h3_weight": self._mapping_value(tokens.heading_weights, 3, "semibold"),
            "numbered_headings": tokens.numbered_headings,
            "show_toc": tokens.show_toc,
            "show_header_footer": tokens.show_header_footer,
            "header_rule": tokens.header_rule,
            "page_num_position": tokens.page_num_position,
            "indent": f"{tokens.first_line_indent_em}em",
            "chapter_break": tokens.chapter_break,
            "kicker": self._kicker(plan) if plan is not None else str(tokens.brand_name or "FIELD MANUAL").upper(),
            "page_contract": {
                "columns": tokens.columns,
                "section_breaks": tokens.chapter_break,
                "final_page_policy": "partial_ok" if tokens.chapter_break else "min_fill",
                "min_final_fill": 0.5,
                "underfill_tolerance_lines": 3.0,
            },
        }

    # ── Vertical flow packing ────────────────────────────────────────────────
    def _kicker(self, plan: EditorialPlan) -> str:
        """Short line-mark for the cover, running head and colophon."""
        brief = plan.publication_brief or {}
        for key in ("kicker", "imprint", "series"):
            value = str(brief.get(key, "")).strip()
            if value:
                return value.upper()
        genre = str(brief.get("recommended_template", "")).strip().lower()
        if genre in ("book", "technical", "report"):
            return "FIELD MANUAL"
        return str(plan.design_tokens.brand_name or "FIELD MANUAL").upper()

    def _em_box_ratio(self, family: str) -> float:
        """Em box of the face that will actually be used, as a size ratio."""
        for face in self._resolve_font(family):
            if face in EM_BOX_RATIO:
                return EM_BOX_RATIO[face]
        return DEFAULT_EM_BOX_RATIO

    def _page_capacity_lines(self, tokens: DesignTokens) -> float:
        """Body lines a page holds, with headroom for weight estimation error.

        Block weights are measured, not exact, so planning a page to the very
        last line spills one line onto a sheet of its own. Sweeping this factor
        against the rendered book, 0.92 was the tightest value that produced no
        spill pages while keeping the shortest page above a third full.
        """
        usable_mm = tokens.page_height_mm - tokens.margin_top_mm - tokens.margin_bottom_mm
        point_size = tokens.body_font_size_pt
        leading_mm = point_size * tokens.line_height_em * 25.4 / 72
        return max(10.0, usable_mm / leading_mm) * PAGE_FILL_HEADROOM

    def _group_weight(self, blocks: list) -> float:
        """Line weight of a page's blocks, including the space between them."""
        if not blocks:
            return 0.0
        return sum(self._block_weight(b) for b in blocks) + \
            BLOCK_SPACING_LINES * (len(blocks) - 1)

    @staticmethod
    def _block_weight(block, exercise_lines: int = 5) -> float:
        kind = block.content_type.value
        words = max(1, len(str(block.content).split()))
        text_lines = words / (CHARS_PER_LINE / 6.0)  # ~15 words per line
        weight = text_lines + BLOCK_CHROME_LINES.get(kind, 1.5)
        if kind == "exercise":
            weight += exercise_lines * EXERCISE_LINE_LINES
        if kind == "image_instruction":
            weight = max(weight, 14.0)
        leading = BLOCK_LEADING.get(kind)
        if leading:
            # Several families set their lead paragraph at 1.3-1.45x the body
            # leading. Counting those lines at the body leading understates a
            # case study by a third, which is how a page planned at three
            # quarters of its height came to fill the sheet and spill a two-line
            # tail. Weight the text at the leading it will actually be set in.
            weight += text_lines * (leading - 1.0)
        return weight

    def _serialized_weight(self, blk: dict[str, Any]) -> float:
        """Line weight of an already-serialized block, for plan diagnostics."""
        kind = str(blk.get("type", "paragraph"))
        body = str(blk.get("content", ""))
        if not body.strip():
            body = str(blk.get(kind, {}).get("title", ""))
        text_lines = max(1, len(body.split())) / (CHARS_PER_LINE / 6.0)
        weight = text_lines + BLOCK_CHROME_LINES.get(kind, 1.5)
        if kind == "exercise":
            weight += int(blk.get("exercise", {}).get("response_lines", 5)) * EXERCISE_LINE_LINES
        return weight

    @staticmethod
    def _exercise_title(block) -> str:
        """The text an exercise's card header will occupy, before serialization.

        Mirrors the subject split in `_serialize_block` so the planner charges
        for the same words the template will draw.
        """
        content = str(block.content or "").strip()
        label, _, subject = content.partition(":")
        if not subject.strip() or len(label) > 20:
            label, subject = "Exercise", content
        return str(block.metadata.get("title", subject)).strip() or label

    _STEP_RE = re.compile(r"(?:^|\s)(\d+)[\).]\s+")

    def _worked_example(self, block) -> dict:
        """A worked example as structure, from metadata or from the block text.

        Source examples arrive as one prose paragraph: a "Worked Example:" stem,
        then a run of "1) 2) 3)" steps, then a closing sentence on what the
        example shows. Read as a single blob the page family had nothing to draw
        but a number and a label, so each example was a near-blank page. The
        stem becomes the problem, the numbered clauses become the calculation
        steps, and the closing sentence becomes the verification note.
        """
        meta = block.metadata
        text = str(block.content or "").strip()
        parts = [p for p in _EXAMPLE_SPLIT.split(text) if p and p.strip()]
        problem = str(meta.get("problem", "")).strip()
        steps = list(meta.get("steps", []) or [])
        answer = str(meta.get("answer", "")).strip()
        verification = str(meta.get("verification", "")).strip()

        if not problem and parts:
            # Drop the "Worked Example:" label; the family prints its own kicker.
            first = re.sub(r"^worked\s+example\s*[:\-]\s*", "", parts[0], flags=re.I)
            problem = first.strip()
        numbered = [p for p in parts[1:] if self._STEP_RE.match(p)]
        if not steps:
            steps = [
                self._STEP_RE.sub("", p, count=1).strip()
                for p in numbered
            ]
        if not answer and parts:
            tail = [p for p in parts[1:] if p not in numbered]
            if tail:
                answer = " ".join(tail).strip()
        if not verification and steps and not answer:
            verification = answer
            answer = ""
        # A heading-only example ("Lessons learned and key takeaways") carries no
        # example at all. Its title is the subject, not the problem, so nothing is
        # promoted into the problem slot and the page stays sparse by design.
        if not problem and not steps and not answer:
            problem = ""
        return {
            "title": str(meta.get("title", "")).strip(),
            "problem": problem,
            "given": list(meta.get("given", []) or []),
            "steps": steps,
            "answer": answer,
            "verification": verification,
        }

    def _fit_answer_space(self, group: list, capacity: float) -> None:
        """Size an exercise spread's ruled answer space to the page it shares.

        A fixed five rules left three exercises floating in the top third of
        their page. Giving each exercise an equal share of the remaining height
        makes the spread read as working space rather than as a short page.
        """
        exercises = [b for b in group if b.content_type == ContentType.EXERCISE]
        if not exercises:
            return
        others = self._group_weight([b for b in group
                                    if b.content_type != ContentType.EXERCISE])
        # The workbook family draws its own furniture -- a running head, an
        # accent rule, a numbered task header and a brass marker per task -- so
        # the space left for rules is the physical page less all of that, not
        # the flow capacity less the block's share of it.
        fixed = others + WORKBOOK_CHROME_LINES + sum(
            len(str(b.content).split()) / (CHARS_PER_LINE / 6.0)
            + len(self._exercise_title(b).split()) / (CHARS_PER_LINE / 6.0)
            for b in exercises
        )
        spare = (capacity - fixed) / len(exercises)
        rules = int(spare / ANSWER_AREA_LINE_LINES)
        rules = max(3, min(18, rules))
        for b in exercises:
            b.metadata["response_lines"] = rules

    def _lead_candidates(self, blocks: list) -> list[str]:
        """Families that could carry a page led by this content, best first.

        A page's family is decided by the block that *leads* it, not by a count
        over the whole page. Counting made every page containing a case study
        come out the same way, and a page whose family is only known once it is
        full cannot be packed to that family's budget at all.
        """
        if not blocks:
            return ["reading"]
        lead = blocks[0]
        kind = lead.content_type.value
        counts: dict[str, int] = {}
        for b in blocks:
            counts[b.content_type.value] = counts.get(b.content_type.value, 0) + 1

        def score(*families: str) -> int:
            return sum(counts.get(f, 0) for f in families)

        # A page that opens on one of these is that thing, full stop.
        if kind == "exercise":
            return ["workbook-exercise"]
        if kind == "worked_example" or counts.get("worked_example"):
            # A worked example is a page's climax whatever its position, the way
            # an exercise is. As a mere nomination it lost to the rotation and
            # was set as a plain card, so the numbered procedure lost its
            # heading, its inputs and its result panel. The family flows the
            # page's other blocks underneath.
            return ["worked-example-page"]
        if kind == "table":
            return ["data-table-page"]
        if kind in ("quotation", "pull_quote"):
            return ["pull-quote-page", "minimal-editorial"]
        if kind in ("process_diagram", "checklist") or (
                kind in ("list", "list_item") and score("list", "list_item") >= 3):
            return ["diagram-page", "checklist-page", "full-width-feature", "reading"]

        # Everything else is prose, and prose has several honest compositions.
        out: list[str] = []
        if kind == "case_study":
            # Four case studies in a row must not read as four of the same
            # page, so a case-led page rotates through real geometries.
            out += ["case-study-editorial", "text-visual-split", "full-width-feature",
                    "framed-feature", "asymmetric-grid"]
        if kind == "heading":
            # A heading wants a display title, and a sidebar or a frame gives
            # the section's own reference material somewhere reserved to live.
            out += ["asymmetric-grid", "full-width-feature", "framed-feature"]
            out += ["text-visual-split", "reading", "minimal-editorial"]
        else:
            out += ["reading", "minimal-editorial", "full-width-feature"]
            out += ["framed-feature", "text-visual-split", "asymmetric-grid"]

        seen: set[str] = set()
        return [f for f in out if not (f in seen or seen.add(f))]

    def _page_layout_for(self, blocks: list, rotation: int = 0,
                         capacity: float | None = None) -> str:
        """Pick a page design family for a page's content.

        Where the lead block allows several families, the rotation index
        decides, which is what guarantees that two adjacent pages of similar
        material still compose differently. Families the page would overrun are
        skipped, so the choice never costs vertical space it has not got.
        """
        candidates = self._lead_candidates(blocks)
        if len(candidates) == 1:
            return candidates[0]
        if capacity is None:
            return candidates[rotation % len(candidates)]
        weight = self._group_weight(blocks)
        affordable = [f for f in candidates
                      if weight <= self._family_budget(f, capacity) + 0.01]
        if not affordable:
            return "reading"
        return affordable[rotation % len(affordable)]

    def _family_budget(self, family: str, capacity: float) -> float:
        """Line weight a family can hold before its fixed regions overflow.

        Two factors. `width` is the fraction of the text measure the family's
        main column actually gets, because the same paragraph wrapped into a
        69%-wide column costs roughly 1.45x the lines. `headroom` is the space
        the family's own furniture consumes: a title block, a frame, a caption,
        an input table, a result panel.

        Block weights are always counted in full-measure lines, so a narrow
        column has to *raise* the line budget by the same factor it costs in
        leading -- `headroom / width`, not `width * headroom`. The product form
        shrank the budget of exactly the families that typeset narrow, which
        pushed them into accepting text they could not hold: a case study led by
        a figure was planned at 65% of a page and then spilled two lines.
        """
        spec = FAMILY_GEOMETRY.get(family)
        if spec is None:
            return capacity
        width, headroom = spec
        return capacity * headroom / width

    def _opener_for(self, chapter: int) -> tuple[str, int]:
        """Chapter opener family and variant, by chapter position.

        Three chapters in the book open on ink; the rest cycle through four
        light compositions. Both rules are position-based so the sequence is
        reproducible and no two adjacent openers share an arrangement.
        """
        if chapter in DARK_OPENER_CHAPTERS:
            return "dark-feature-opener", (DARK_OPENER_CHAPTERS.index(chapter)) % 2
        return OPENER_FAMILIES[(chapter - 1) % len(OPENER_FAMILIES)], (chapter - 1) % 4

    def _count_so_far(self, pages: list[dict[str, Any]], family: str) -> int:
        """How many pages already use a family, for its running index."""
        return sum(1 for p in pages if p.get("layout_function") == family)

    def _page_heading(self, blocks: list) -> str:
        """The heading that names a page, for a generated figure's seed."""
        for b in blocks:
            if b.content_type == ContentType.HEADING:
                return str(b.content).strip()
        for b in blocks:
            if b.content_type in (ContentType.CASE_STUDY, ContentType.WORKED_EXAMPLE):
                return str(b.metadata.get("title", "") or b.content).strip()[:60]
        return ""

    def _domain_terms(self, plan: EditorialPlan) -> dict[str, str]:
        """The topic vocabulary this book is written in.

        Read from `domain_*` keys in the publication brief, defaulted to the
        neutral set. Every family and every generated figure takes its nouns
        from here, which is what lets the same design system typeset a manual,
        a course, a report or a workbook without editing a template.
        """
        brief = plan.publication_brief or {}
        terms = dict(DOMAIN_DEFAULT_TERMS)
        for brief_key, term_key in DOMAIN_BRIEF_KEYS.items():
            value = str(brief.get(brief_key, "") or "").strip()
            if value:
                terms[term_key] = value
        # The one sentence the system writes itself is composed from the nouns
        # above, so it stays true to the subject instead of describing a
        # different one.
        unit = terms["unit"]
        terms["figure_note"] = (
            f"Read the boundaries of the problem before the {unit} itself. "
            f"Structure, access and dependency decide what any {unit} can be "
            f"used for, and they belong in the record before the decision is."
        )
        return terms



    def _partition(self, blocks: list, capacity: float) -> list[tuple[list, str]]:
        """Split ordered blocks into pages, each with the family it will use.

        The family is fixed when the page's first block lands and the page then
        fills to *that* family's budget. Doing it the other way round — filling
        to the physical page and deciding the look afterwards — is what made a
        69%-column page overflow a 100%-column plan, and it is also why every
        page came out looking the same.

        Exercises and worked examples are atomic: a run of them stays together,
        because splitting one across a break strands its ruled answer space.
        """
        if not blocks:
            return []

        items: list[list] = []
        for block in blocks:
            unsplittable = block.content_type in _UNSPLITTABLE
            # A workbook spread carries a small, bounded number of tasks, each
            # with its own ruled response area. Three tasks and three sets of
            # rules did not fit a page and produced a title over clipped cards,
            # so a run of exercises is capped at two per page.
            groupable = unsplittable and block.content_type in _UNSPLITTABLE
            if (groupable and items and items[-1]
                    and items[-1][0].content_type == block.content_type
                    and block.content_type != ContentType.EXERCISE):
                items[-1].append(block)
            elif (groupable and items and items[-1]
                    and items[-1][0].content_type == ContentType.EXERCISE
                    and sum(1 for b in items[-1]
                            if b.content_type == ContentType.EXERCISE) < 2):
                items[-1].append(block)
            else:
                items.append([block])

        pages: list[tuple[list, str]] = []
        current: list = []
        used = 0.0
        family = ""
        rotation = 0

        def start(item: list) -> None:
            nonlocal current, used, family, rotation
            current = list(item)
            used = self._group_weight(current)
            family = self._page_layout_for(current, rotation, capacity)

        for item in items:
            if not current:
                start(item)
                continue
            weight = self._group_weight(item)
            # A card is atomic: the renderer cannot know where inside one a
            # break would fall, and a page that ends a few lines short of a
            # card leaves a gap the size of the card. So an atomic block starts
            # a page rather than stranding the one before it -- except when the
            # page holds nothing but the heading that introduces it, which is
            # the one case where joining is strictly better.
            atomic = any(b.content_type in _UNSPLITTABLE for b in item)
            introduces = len(current) == 1 and current[0].content_type == ContentType.HEADING
            joins_heading = (atomic and introduces
                             and used + weight <= self._family_budget(family, capacity))
            if not joins_heading and (
                    atomic or used + weight > self._family_budget(family, capacity)):
                pages.append((current, family))
                rotation += 1
                start(item)
            else:
                current.extend(item)
                used += weight
        if current:
            pages.append((current, family))

        # A heading is a promise about what follows. Ending a page on one prints
        # the section title as the last line on the sheet and sends the section
        # itself to the next page, which is what produced a page whose entire
        # content was the words "Key market drivers and cycles". The heading
        # moves forward to open the page that holds its section.
        for i in range(len(pages) - 1):
            group, family = pages[i]
            while (len(group) > 1
                   and group[-1].content_type == ContentType.HEADING):
                moved = group.pop()
                nxt_blocks, nxt_family = pages[i + 1]
                nxt_blocks.insert(0, moved)
                pages[i + 1] = (nxt_blocks, nxt_family)
                pages[i] = (group, family)
                group, family = pages[i]

        # A page can end up heavier than the family it was opened with, because
        # the last block added is never split. Walk blocks back to the page
        # before until the page fits what it will actually be typeset as.
        index = 0
        while index < len(pages):
            group, family = pages[index]
            weight = self._group_weight(group)
            if (weight <= self._family_budget(family, capacity) + 0.01
                    or len(group) <= 1 or index == 0):
                index += 1
                continue
            moved = group.pop(0)
            prev, prev_family = pages[index - 1]
            # `group.pop(0)` yields one block, not a group, so it is appended
            # rather than extended.
            prev.append(moved)
            pages[index - 1] = (prev, prev_family)
            pages[index] = (group, family)
            index += 1

        # Greedy packing can leave a light last page. Walk trailing items back
        # from the page before it while both stay within bounds.
        if len(pages) > 1:
            last_blocks, last_family = pages[-1]
            last = self._group_weight(last_blocks)
            while last < capacity * 0.5 and len(pages[-2][0]) > 1:
                prev_blocks, prev_family = pages[-2]
                moved = prev_blocks.pop()
                cost = self._block_weight(moved)
                prev = self._group_weight(prev_blocks)
                if (last + cost > self._family_budget(last_family, capacity)
                        or prev - cost < capacity * 0.55):
                    prev_blocks.append(moved)
                    break
                last_blocks.insert(0, moved)
                last += cost
            pages[-1] = (last_blocks, last_family)

        # The two rearrangement passes above move blocks between pages, so a
        # page's lead block is not necessarily the one its family was chosen
        # for: a worked example shifted onto a paragraph-led page kept the
        # reading family and lost its calculation region. The family is
        # re-decided here, from each page's final contents, and the rotation
        # index is the page's position so the sequence stays deterministic.
        for i, (group, _) in enumerate(pages):
            pages[i] = (group, self._page_layout_for(group, i, capacity))

        # Never leave a heading alone at the top of a page: give it the block
        # that follows it, borrowing the previous page's tail if needed.
        for i, (group, family) in enumerate(pages):
            if i and len(group) == 1 and group[0].content_type == ContentType.HEADING:
                if i + 1 < len(pages):
                    nxt = pages[i + 1][0]
                    nxt.insert(0, group.pop())
                else:
                    prev = pages[i - 1][0]
                    prev.append(group.pop())
                pages[i] = (group, family)
        return [(g, f) for g, f in pages if g]

    def _chapter_practice(self, chapter_blocks: list) -> list[dict[str, str]]:
        """The exercises a chapter sets, as kind plus subject.

        The chapter closing page needs content the summary does not already
        carry. An earlier version filled it with a line lifted from each
        section's case study, but every case study in this manuscript opens
        with the same sentence, so the page read as repeated filler.
        """
        out: list[dict[str, str]] = []
        for block in chapter_blocks:
            if block.content_type != ContentType.EXERCISE:
                continue
            label, _, subject = str(block.content).strip().partition(":")
            if not subject.strip() or len(label) > 20:
                label, subject = "Exercise", str(block.content).strip()
            out.append({"kind": label, "subject": subject})
        return out[:6]

    def _make_page(self, number: int, purpose: PagePurpose, layout_function: str,
                   blocks: list, page_plan=None, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        tokens = None
        page: dict[str, Any] = {
            "page_number": number,
            "purpose": purpose.value,
            "layout_family": layout_function,
            "layout_function": layout_function,
            # Carried on every page so a family can name the subject without
            # reaching for the document payload.
            "domain": {},
            "width_mm": 210.0,
            "height_mm": 297.0,
            "margins": {"top_mm": 25.0, "bottom_mm": 24.0, "left_mm": 26.0, "right_mm": 22.0},
            "density_target": 0.8,
            "blocks": [],
        }
        if page_plan is not None:
            page["width_mm"] = page_plan.page_width_mm
            page["height_mm"] = page_plan.page_height_mm
            page["margins"] = dict(page_plan.margins or page["margins"])
            page["density_target"] = page_plan.density_target
            page["page_plan_id"] = page_plan.id
        if extra:
            page.update(extra)
        return page

    def _build_page_data(self, manuscript: Manuscript, plan: EditorialPlan,
                         asset_map: dict[str, str], asset_dir: Path | None = None) -> list[dict[str, Any]]:
        """Build the page sequence for the book.

        The editorial plan expresses intent (which chapter, which layout family,
        which density) but its one-block-per-page decomposition leaves the book
        mostly empty. This method treats the plan as the spine — front matter
        order, chapter boundaries, recap placement — and flows each chapter's
        blocks into filled pages using a measured packing pass.
        """
        tokens = plan.design_tokens
        asset_map = dict(asset_map)
        blocks_by_id = {b.id: b for b in manuscript.content_blocks}
        capacity = self._page_capacity_lines(tokens)
        domain = self._domain_terms(plan)
        pages: list[dict[str, Any]] = []
        n = 0

        def next_number() -> int:
            nonlocal n
            n += 1
            return n

        def push(page: dict[str, Any], block_list: list) -> None:
            page["domain"] = domain
            if block_list:
                page["blocks"] = [self._serialize_block(b, asset_map) for b in block_list]
            pages.append(page)

        # ── Front matter, in the order the plan declares it ───────────────────
        front_order = [PagePurpose.COVER, PagePurpose.TITLE_PAGE, PagePurpose.COPYRIGHT, PagePurpose.TOC]
        by_purpose: dict[PagePurpose, PagePlan] = {}
        for pp in sorted(plan.page_plans, key=lambda p: p.page_number):
            if pp.purpose in front_order and pp.purpose not in by_purpose:
                by_purpose[pp.purpose] = pp

        for purpose in front_order:
            pp = by_purpose.get(purpose)
            if pp is None:
                continue
            layout = self.purpose_layout_map.get(purpose, "reading")
            page = self._make_page(next_number(), purpose, layout, [], pp)
            if purpose == PagePurpose.COVER:
                page["cover_data"] = self._build_cover_data(manuscript, tokens)
            elif purpose == PagePurpose.TITLE_PAGE:
                page["title_data"] = self._build_title_data(manuscript, tokens)
            elif purpose == PagePurpose.COPYRIGHT:
                page["blocks"] = [
                    {"type": "paragraph", "content": para, "level": 0, "metadata": {}}
                    for para in self._build_imprint(manuscript, plan)
                ]
            elif purpose == PagePurpose.TOC:
                page["toc_data"] = self._build_toc_data(manuscript, tokens)
            push(page, [])

        # ── Chapters ─────────────────────────────────────────────────────────
        chapter_titles = {
            b.chapter: str(b.content).strip()
            for b in manuscript.content_blocks
            if b.semantic_role == SemanticRole.CHAPTER
        }
        chapter_nums = sorted({b.chapter for b in manuscript.content_blocks if b.chapter > 0})
        opener_by_chapter = {
            pp.typography.get("chapter_number", ""): pp
            for pp in plan.page_plans
            if pp.purpose == PagePurpose.CHAPTER_OPENER and pp.typography
        }

        for chapter in chapter_nums:
            title = chapter_titles.get(chapter) or f"Chapter {chapter}"
            chapter_blocks = sorted(
                (b for b in manuscript.content_blocks
                 if b.chapter == chapter
                 and b.semantic_role != SemanticRole.CHAPTER
                 and b.semantic_role not in _NON_CHAPTER_ROLES),
                key=lambda b: (b.order, b.id),
            )
            # A trailing label paragraph is a back-matter section title the
            # source wrote as prose, not a sentence. It is kept only when
            # something follows it that reads as its content.
            while chapter_blocks:
                tail = chapter_blocks[-1]
                text = str(tail.content).strip().lower().rstrip(":")
                if (tail.content_type == ContentType.PARAGRAPH
                        and text in _BACK_MATTER_LABELS):
                    chapter_blocks.pop()
                    continue
                break
            if not chapter_blocks:
                continue

            objectives = [
                _strip_label(str(b.content))
                for b in chapter_blocks
                if b.content_type == ContentType.CALLOUT
                and str(b.metadata.get("kind", "")).lower() in ("learning_objective", "objective")
            ]
            section_titles = [
                str(b.content).strip()
                for b in chapter_blocks
                if b.content_type == ContentType.HEADING
            ]
            if not objectives:
                objectives = [f"Work through the sections on {t.lower()}." for t in section_titles[:3]]

            opener_layout, opener_variant = self._opener_for(chapter)
            opener = self._make_page(
                next_number(), PagePurpose.CHAPTER_OPENER, opener_layout, [],
                opener_by_chapter.get(str(chapter)),
                {
                    "layout_variant": opener_variant,
                    "family_label": f"Chapter {chapter}",
                    "chapter_opener_data": {
                        "chapter_number": str(chapter),
                        "chapter_title": title,
                        "epigraph": "",
                        "learning_objectives": objectives[:3],
                        "section_titles": section_titles,
                    }
                },
            )
            if asset_dir is not None and section_titles:
                figure = self._chapter_illustration(
                    chapter, title, section_titles, asset_dir, domain)
                if figure:
                    opener["illustration"] = figure
                    opener["blocks"] = [{
                        "type": "image_instruction",
                        "content": figure["caption"],
                        "level": 0,
                        "metadata": {"asset_id": figure["id"]},
                        "image": figure,
                    }]
            push(opener, [])

            # Flow the chapter body. Greedy packing leaves a nearly empty tail
            # page whenever a chapter overruns its page budget, so the blocks
            # are partitioned into an even number of roughly equal pages
            # instead. Order is preserved, and a heading never opens a page
            # without the section it introduces.
            # The closing summary belongs to the recap spread, not the body
            # flow, where it stranded three lines on a page of its own. Most
            # chapters state it in a paragraph; the worked-example chapter
            # states it in the final worked example, so the label is looked for
            # in any block type.
            summary = ""
            body_blocks: list = []
            for b in chapter_blocks:
                text = str(b.content).strip()
                if (not summary and text.lower().startswith("summary:")
                        and b.content_type in (ContentType.PARAGRAPH,
                                               ContentType.WORKED_EXAMPLE)):
                    summary = text
                    continue
                body_blocks.append(b)
            chapter_blocks = body_blocks

            flow = self._partition(chapter_blocks, capacity)

            # A running page counter drives the alternation rules: the visual
            # region of a split page, and which chapters get the ink opener.
            illustration_side = "right"
            # Rotation is per chapter, so the family sequence restarts with each
            # chapter instead of running monotonically through the book.
            rotation = chapter - 1
            for group, layout in flow:
                rotation += 1
                if layout == "text-visual-split":
                    illustration_side = "left" if illustration_side == "right" else "right"
                page = self._make_page(
                    next_number(),
                    PagePurpose.EXERCISE if layout == "workbook-exercise" else PagePurpose.CONTENT,
                    layout, [],
                )
                page["layout_variant"] = n % 4
                page["illustration_side"] = illustration_side
                if layout == "workbook-exercise":
                    page["exercise_index"] = self._count_so_far(pages, "workbook-exercise") + 1
                if layout == "worked-example-page":
                    page["example_index"] = self._count_so_far(pages, "worked-example-page") + 1
                if layout == "diagram-page":
                    page["figure_index"] = self._count_so_far(pages, "diagram-page") + 1
                page["family_label"] = FAMILY_LABELS.get(layout, "")
                if layout in LANDSCAPE_FIGURE_FAMILIES:
                    # Published with the orientation, because a page takes its
                    # size from the settings in force where it starts and the
                    # plan is what decides the sheet.
                    page["orientation"] = "landscape"
                    page["width_mm"] = 297.0
                    page["height_mm"] = 210.0
                # A visual family with nothing to show needs a figure drawn for
                # it. The manuscript supplies no artwork, and the family's whole
                # geometry is a promise that something is there.
                if asset_dir is not None and layout in FIGURE_FAMILIES:
                    head = self._page_heading(group)
                    figure = self._page_figure(
                        page["page_number"], layout, head, section_titles, asset_dir, domain)
                    if figure:
                        page["illustration"] = figure
                        page["figure_caption"] = figure["caption"]
                        if layout in LANDSCAPE_FIGURE_FAMILIES:
                            page["orientation"] = "landscape"
                self._fit_answer_space(group, capacity)
                if layout == "workbook-exercise":
                    fitted = [b for b in group if b.content_type == ContentType.EXERCISE]
                    if fitted:
                        page["answer_rules"] = int(
                            fitted[0].metadata.get("response_lines", 10))
                push(page, group)

            recap_points = section_titles[:6] or [
                str(b.content).strip()[:180] for b in chapter_blocks
                if b.content_type in (ContentType.PARAGRAPH, ContentType.CASE_STUDY)
            ][:3]
            recap = self._make_page(next_number(), PagePurpose.RECAP, "recap-plan-page", [])
            recap["layout_variant"] = chapter % 4
            recap["family_label"] = f"Chapter {chapter} recap"
            recap["recap_data"] = {
                "title": f"Chapter {chapter}: what to carry forward",
                "summary": _strip_label(summary),
                "points": section_titles,
                # The exercises this chapter set, so the closing page says what
                # the reader was asked to do rather than repeating the section
                # list the summary already enumerates.
                "practice": self._chapter_practice(chapter_blocks),
            }
            push(recap, [])

        # ── Back matter ──────────────────────────────────────────────────────
        glossary_entries = [
            {"term": str(b.metadata.get("term", "")).strip() or self._term_from(b),
             "definition": str(b.content).strip()}
            for b in manuscript.content_blocks
            if b.content_type == ContentType.DEFINITION
        ]
        if glossary_entries:
            page = self._make_page(next_number(), PagePurpose.GLOSSARY, "reference-page", [])
            page["glossary_data"] = {"entries": glossary_entries}
            push(page, [])

        # References are whatever the manuscript marks as one: a block of
        # content_type REFERENCE, or a block whose semantic role is REFERENCE.
        # A source that ends with a bare "References" heading carries the
        # heading and nothing under it, so it is used as the section title and
        # no empty page is emitted for it.
        reference_blocks = [
            b for b in manuscript.content_blocks
            if b.content_type == ContentType.REFERENCE
            or b.semantic_role == SemanticRole.REFERENCE
        ]
        reference_entries = [
            str(b.content).strip() for b in reference_blocks
            if b.content_type != ContentType.HEADING and str(b.content).strip()
        ]
        reference_title = next(
            (str(b.content).strip() for b in reference_blocks
             if b.content_type == ContentType.HEADING and str(b.content).strip()),
            "",
        )
        if reference_entries:
            page = self._make_page(next_number(), PagePurpose.REFERENCES, "reference-page", [])
            page["references_data"] = {"entries": reference_entries,
                                       "title": reference_title}
            push(page, [])

        back = self._make_page(next_number(), PagePurpose.BACK_COVER, "back-cover", [])
        back["back_cover_data"] = self._build_back_cover_data(manuscript, tokens)
        push(back, [])

        return pages

    def _term_from(self, block) -> str:
        """Derive a glossary term from a definition block that omits one."""
        head = str(block.content).strip().split(".")[0]
        words = [w for w in head.replace(":", " ").split() if w][:6]
        return " ".join(words) if words else "Term"

    def _chapter_illustration(self, chapter: int, title: str, sections: list[str],
                              asset_dir: Path, domain: dict[str, str]) -> dict[str, Any] | None:
        """Generate the chapter's opening plate as a real, deterministic SVG.

        The plate is a schematic, not decoration: a bounded field divided into
        the chapter's own sections and keyed with their headings. The caption
        names the book's subject vocabulary, so it reads correctly whatever the
        manuscript is about.
        """
        from editorial_studio.renderer.illustrations import parcel_map_svg

        name = f"chapter_{chapter:02d}_plate.svg"
        target = asset_dir / name
        try:
            parcel_map_svg(title, sections[:4], target)
        except Exception:  # artwork must never break a build
            return None
        unit = domain.get("unit", "item")
        unit_plural = domain.get("unit_plural", unit + "s")
        return {
            "id": f"plate_ch{chapter:02d}",
            "path": f"assets/{name}",
            "caption": f"Chapter {chapter} — orientation plate. The field is divided into the "
                       f"chapter's own sections; each band is a {unit} of the {unit_plural} "
                       f"the chapter works through.",
            "alt": title,
            "width": "100%",
            "aspect": 960 / 520,
            "generated": True,
        }

    def _page_figure(self, page_number: int, family: str, head: str, sections: list[str],
                     asset_dir: Path, domain: dict[str, str]) -> dict[str, Any] | None:
        """Generate the diagram a figure-led page family needs.

        The manuscript carries no artwork of its own, and a design system whose
        visual families never get a figure is four families short of its
        promise. So the renderer draws one: a matrix, a decision gate or a
        process strip, chosen by the family that asked for it, seeded from the
        page's own heading so the same page always draws the same figure.

        Nothing here knows the subject. The captions and axis labels come from
        the domain vocabulary, so the same three drawings serve any book.
        """
        from editorial_studio.renderer.illustrations import (
            decision_tree_svg,
            risk_matrix_svg,
            step_diagram_svg,
        )

        unit = domain.get("unit", "item")
        measure = domain.get("measure", "measure")
        stake = domain.get("stake", "risk")
        collection = domain.get("collection", "record set")
        artifact = domain.get("artifact", "record")
        name = f"page_{page_number:03d}_{family.replace('-', '_')}.svg"
        target = asset_dir / name
        try:
            if family == "text-visual-split":
                risk_matrix_svg(
                    (f"Likelihood of {stake}", f"Consequence for the {unit}"),
                    [(0.72, 0.78), (0.30, 0.62), (0.55, 0.24), (0.18, 0.80),
                     (0.84, 0.40), (0.42, 0.52)],
                    target,
                )
                caption = (f"How {stake} accumulates against a single {unit}. Each numbered "
                           f"point is one {measure} worth recording before the decision is "
                           f"made; the shading is ordinal, not statistical.")
                aspect = 900 / 620
            elif family == "diagram-page":
                steps = [s for s in sections if str(s).strip()][:6] or [head]
                step_diagram_svg([str(s) for s in steps], target)
                caption = (f"The working sequence for this section. Each step narrows the "
                           f"{collection} to what still needs a decision, and none of them "
                           f"can be skipped without accepting a known {stake}.")
                aspect = 960 / 300
            else:
                labels = [s for s in sections if str(s).strip()][:2] or [head]
                decision_tree_svg(
                    f"Is the evidence for this {unit} sufficient to proceed?",
                    [("Yes — proceed", "No — hold")],
                    target,
                    outcome_text=[
                        f"Confirm the finding against the primary {artifact}, "
                        f"then price the constraint rather than the hope.",
                        f"Hold the decision open, and name the {measure} that would settle it.",
                    ],
                )
                caption = (f"A decision gate for the {unit} work in this section. The question "
                           f"is the same in both directions; only the evidence required to pass "
                           f"it changes.")
                aspect = 900 / 560
        except Exception:  # artwork must never break a build
            return None
        return {
            "id": f"fig_p{page_number:03d}_{family}",
            "path": f"assets/{name}",
            "caption": caption,
            "alt": head or unit,
            "width": "100%",
            "aspect": aspect,
            "generated": True,
        }


    def _build_imprint(self, manuscript: Manuscript, plan: EditorialPlan) -> list[str]:
        year = 2026
        publisher = plan.design_tokens.brand_name or "Editorial Studio"
        return [
            f"Copyright © {year} {publisher}.",
            "This publication was generated from a local manuscript workflow and is provided for "
            "educational purposes. It is not legal, tax, accounting, engineering, environmental, "
            "forestry, permitting, or investment advice. Every worked example and case study is "
            "composite and illustrative; nothing described here is a real case, client, or "
            "transaction.",
            "Verify all figures, records, and authorities against their original sources before "
            "relying on them, and read the material against the rules that actually govern your "
            "jurisdiction, organisation, or subject.",
            # Name the faces the PDF actually embeds. Typst substitutes the
            # requested families when they are not installed, so quoting the
            # design intent here produced a colophon that contradicted the
            # type on the page.
            "First edition.",
        ]


    def _build_sections(self, manuscript: Manuscript, plan: EditorialPlan,
                        asset_map: dict[str, str]) -> list[dict[str, Any]]:
        """Build sections data for the original book.typ template."""
        sections = []
        
        # Create a lookup for blocks by ID
        block_by_id = {b.id: b for b in manuscript.content_blocks}
        
        # Group blocks by chapter
        chapter_blocks: dict[int, list] = {}
        for block in manuscript.content_blocks:
            if block.matter == "body" and block.chapter > 0:
                if block.chapter not in chapter_blocks:
                    chapter_blocks[block.chapter] = []
                chapter_blocks[block.chapter].append(block)
        
        # Process each chapter
        for ch_num in sorted(chapter_blocks.keys()):
            blocks = chapter_blocks[ch_num]
            if not blocks:
                continue
            
            chapter_title = f"Chapter {ch_num}"
            for block in blocks:
                if block.semantic_role == "chapter":
                    chapter_title = block.content
                    break
            
            section_content = []
            section_images = []
            section_tables = []
            section_code = []
            section_callouts = []
            
            for block in blocks:
                if block.content_type.value == "heading" and block.level > 1:
                    if section_content:
                        sections.append(self._make_section(
                            f"{chapter_title} - Section {len(sections) + 1}",
                            "\n\n".join(section_content), 2,
                            section_images, section_tables, section_code, section_callouts
                        ))
                        section_content = []
                        section_images = []
                        section_tables = []
                        section_code = []
                        section_callouts = []
                elif block.content_type.value == "paragraph":
                    section_content.append(block.content)
                elif block.content_type.value == "image_instruction":
                    asset_id = block.metadata.get("asset_id")
                    if asset_id and asset_id in asset_map:
                        section_images.append({
                            "path": asset_map[asset_id],
                            "caption": block.metadata.get("alt_text", ""),
                            "width": "85%",
                            "position": "auto",
                            "aspect": 0.75,
                        })
                elif block.content_type.value == "table":
                    section_tables.append({
                        "headers": ["Column 1", "Column 2"],
                        "rows": [["Data 1", "Data 2"]],
                        "caption": "",
                    })
                elif block.content_type.value == "code":
                    section_code.append({
                        "code": block.content,
                        "language": block.metadata.get("language", ""),
                        "caption": "",
                    })
                elif block.content_type.value in ("warning", "callout"):
                    section_callouts.append({
                        "text": block.content,
                        "kind": "warning" if block.content_type.value == "warning" else "info",
                    })
            
            if section_content or section_images or section_tables or section_code or section_callouts:
                sections.append(self._make_section(
                    chapter_title,
                    "\n\n".join(section_content) if section_content else "",
                    1,
                    section_images, section_tables, section_code, section_callouts
                ))
        
        return sections

    def _make_section(self, title: str, content: str, level: int,
                      images: list, tables: list, code_blocks: list, callouts: list) -> dict:
        return {
            "id": f"s_{uuid.uuid4().hex[:6]}",
            "title": title,
            "content": content,
            "level": level,
            "numbered": True,
            "images": images,
            "galleries": [],
            "tables": tables,
            "code_blocks": code_blocks,
            "callouts": callouts,
        }

    def _serialize_block(self, block, asset_map: dict[str, str]) -> dict[str, Any]:
        """Serialize a content block to a dictionary for Typst."""
        serialized = {
            "id": block.id,
            "matter": block.matter,
            "type": block.content_type.value,
            "role": block.semantic_role.value,
            "chapter": block.chapter,
            "section": block.section,
            "level": block.level,
            "content": block.content,
            "metadata": block.metadata,
        }

        if block.content_type in (ContentType.LIST, ContentType.LIST_ITEM):
            serialized["list"] = {
                "items": block.metadata.get("items", [block.content]),
            }
        elif block.content_type == ContentType.IMAGE_INSTRUCTION:
            asset_id = block.metadata.get("asset_id")
            if asset_id and asset_id in asset_map:
                serialized["image"] = {
                    "path": asset_map[asset_id],
                    "caption": block.metadata.get("caption") or block.metadata.get("alt_text", ""),
                    "alt": block.metadata.get("alt_text", ""),
                    "width": block.metadata.get("width", "85%"),
                    "position": block.metadata.get("position", "auto"),
                    "aspect": block.metadata.get("aspect", 0.75),
                }
        elif block.content_type == ContentType.TABLE:
            serialized["table"] = {
                "headers": block.metadata.get("headers", ["Column 1", "Column 2"]),
                "rows": block.metadata.get("rows", [["Data 1", "Data 2"]]),
                "caption": block.metadata.get("caption", ""),
            }
        elif block.content_type == ContentType.CODE:
            serialized["code"] = {
                "code": block.content,
                "language": block.metadata.get("language", ""),
                "caption": block.metadata.get("caption", ""),
            }
        elif block.content_type == ContentType.EXERCISE:
            # Source exercises read "Worksheet: Land classification assessment".
            # The label belongs in the card kicker, not repeated above the
            # title, which is what a bare "Exercise" default produced.
            label, _, subject = str(block.content).strip().partition(":")
            if not subject.strip() or len(label) > 20:
                label, subject = "Exercise", str(block.content).strip()
            meta = block.metadata
            title = str(meta.get("title", subject)).strip()
            # The card already sets the subject as its title; repeating the full
            # prompt underneath printed the same sentence twice.
            prompt = subject if subject.strip().lower() != title.strip().lower() else ""
            serialized["exercise"] = {
                "kicker": str(meta.get("kicker", label)).strip() or "Exercise",
                "title": title,
                "instructions": meta.get("instructions", ""),
                "question": prompt,
                "hints": meta.get("hints", []),
                "response_type": meta.get("response_type", "lines"),
                "response_lines": meta.get("response_lines", 5),
            }
            serialized["content"] = prompt
        elif block.content_type == ContentType.WORKED_EXAMPLE:
            ex = self._worked_example(block)
            if not ex["steps"]:
                # A source tags its section summaries as worked examples: "This
                # chapter explores ...", "<Section> is a fundamental component
                # of ...". There is no calculation in them, so a worked-example
                # page could only draw a numeral and a label and then stand
                # empty. Without steps it is prose, and it is set as prose.
                text = str(block.content or "").strip()
                if text.lower().startswith("worked example:"):
                    text = re.sub(r"^worked\s+example\s*:\s*", "", text,
                                  flags=re.IGNORECASE)
                serialized["type"] = "paragraph"
                serialized["content"] = text
            else:
                serialized["worked_example"] = ex
        elif block.content_type == ContentType.CASE_STUDY:
            serialized["case_study"] = {
                "title": block.metadata.get("title", ""),
                "context": block.metadata.get("context", ""),
            }
        elif block.content_type == ContentType.REFERENCE:
            serialized["reference"] = {
                "text": block.content,
                "url": block.metadata.get("url", ""),
            }
        elif block.content_type == ContentType.DEFINITION:
            serialized["definition"] = {
                "term": block.metadata.get("term", ""),
                "definition": block.content,
            }
        elif block.content_type in (ContentType.WARNING, ContentType.CALLOUT):
            # The kicker comes from the block's declared kind so a learning
            # objective is not filed under a generic "Note".
            kind = str(block.metadata.get("kind", "")).strip().lower()
            if not kind:
                kind = "warning" if block.content_type == ContentType.WARNING else "info"
            serialized["callout"] = {
                "text": _strip_label(block.content),
                "kind": kind,
            }
        elif block.content_type == ContentType.QUOTATION:
            serialized["pull_quote"] = {
                "text": block.content,
                "author": block.metadata.get("author", ""),
            }
        elif block.content_type == ContentType.FOOTNOTE:
            serialized["footnote"] = block.content

        return serialized

    def _build_cover_data(self, manuscript: Manuscript, tokens: DesignTokens) -> dict[str, Any]:
        return {
            "title": manuscript.title,
            "subtitle": manuscript.description or "",
            "author": manuscript.author,
            "publisher": tokens.brand_name or "Editorial Studio",
            "background_color": self._resolve_palette(tokens)["paper"],
        }

    def _build_back_cover_data(self, manuscript: Manuscript, tokens: DesignTokens) -> dict[str, Any]:
        palette = self._resolve_palette(tokens)
        return {
            "background_color": palette["ink"],
            "accent_color": palette["brass"],
            # The back cover sells the manuscript's own scope. Taking it from
            # the description is what keeps a generated book from carrying a
            # subject the manuscript never mentioned.
            "text": (manuscript.description or "").strip()
                    or "A working manual for the decisions this subject actually requires.",
        }


    def _build_title_data(self, manuscript: Manuscript, tokens: DesignTokens) -> dict[str, Any]:
        return {
            "title": manuscript.title,
            "subtitle": manuscript.description or "",
            "author": manuscript.author,
            "publisher": tokens.brand_name if hasattr(tokens, 'brand_name') else "",
            "publisher_location": "",
        }

    def _build_toc_data(self, manuscript: Manuscript, tokens: DesignTokens) -> dict[str, Any]:
        """Chapter index. Typst's `outline` supplies live page numbers; this is
        the editorial fallback used when outline is unavailable."""
        return {
            "sections": [
                {"title": str(b.content).strip(), "page": 1}
                for b in manuscript.content_blocks
                if b.semantic_role == SemanticRole.CHAPTER and b.matter == "body" and b.chapter > 0
            ]
        }


    def _select_template(self, plan: EditorialPlan) -> str:
        brief = plan.publication_brief
        recommended = brief.get("recommended_layout", "book")

        template_map = {
            "book": "book",
            "technical": "technical",
            "report": "report",
            "journal": "journal",
            "portfolio": "portfolio",
            "letter": "letter",
            "academic": "academic_ru",
            "resume": "resume",
        }
        return template_map.get(recommended, "book")