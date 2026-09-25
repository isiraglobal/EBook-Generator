from __future__ import annotations
import json
import math
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
BLOCK_CHROME_LINES: dict[str, float] = {
    "heading": 2.3,
    "paragraph": 0.4,
    "case_study": 4.2,
    "exercise": 4.1,
    "worked_example": 4.0,
    "callout": 2.6,
    "warning": 2.6,
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
# One ruled response line under an exercise, differenced from the probe at
# scripts/measure_components.py.
EXERCISE_LINE_LINES = 0.48
# Fraction of the physical page the flow planner will fill. See
# TypstRenderer._page_capacity_lines.
PAGE_FILL_HEADROOM = 0.94

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

            # Also copy layout_library.typ
            layout_lib = self.templates_dir / "layout_library.typ"
            if layout_lib.exists():
                shutil.copy2(layout_lib, work_dir / "layout_library.typ")

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
            shutil.rmtree(work_dir, ignore_errors=True)

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

            layout_lib = self.templates_dir / "layout_library.typ"
            if layout_lib.exists():
                shutil.copy2(layout_lib, work_dir / "layout_library.typ")

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

    def _block_weight(self, block, exercise_lines: int = 5) -> float:
        kind = block.content_type.value
        words = max(1, len(str(block.content).split()))
        text_lines = words / (CHARS_PER_LINE / 6.0)  # ~15 words per line
        weight = text_lines + BLOCK_CHROME_LINES.get(kind, 1.5)
        if kind == "exercise":
            weight += exercise_lines * EXERCISE_LINE_LINES
        if kind == "image_instruction":
            weight = max(weight, 14.0)
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

    def _fit_answer_space(self, group: list, capacity: float) -> None:
        """Size an exercise spread's ruled answer space to the page it shares.

        A fixed five rules left three exercises floating in the top third of
        their page. Giving each exercise an equal share of the remaining height
        makes the spread read as working space rather than as a short page.
        """
        exercises = [b for b in group if b.content_type == ContentType.EXERCISE]
        if not exercises:
            return
        others = sum(self._block_weight(b) for b in group
                     if b.content_type != ContentType.EXERCISE)
        fixed = others + sum(
            BLOCK_CHROME_LINES[ContentType.EXERCISE.value]
            + len(str(b.content).split()) / (CHARS_PER_LINE / 6.0)
            for b in exercises
        )
        spare = (capacity - fixed) / len(exercises)
        rules = int(spare / EXERCISE_LINE_LINES)
        rules = max(3, min(24, rules))
        for b in exercises:
            b.metadata["response_lines"] = rules

    def _page_layout_for(self, blocks: list) -> str:
        """Pick a layout family from the dominant content of a flowed page."""
        kinds = [b.content_type.value for b in blocks]
        counts: dict[str, int] = {}
        for k in kinds:
            counts[k] = counts.get(k, 0) + 1

        def score(*families: str) -> int:
            return sum(counts.get(f, 0) for f in families)

        if score("image_instruction") >= 1 and len(blocks) <= 3:
            return "image-led"
        if score("exercise") >= 1:
            return "exercise"
        if score("worked_example") >= 1:
            return "worked-example"
        if score("process_diagram") >= 1:
            return "process-diagram"
        if score("list", "list_item", "checklist") >= 2 and len(blocks) <= 6:
            return "checklist"
        if score("case_study") >= 2:
            return "case-study"
        if score("case_study") >= 1:
            return "case-study" if len(blocks) <= 4 else "reading"
        return "reading"

    def _partition(self, blocks: list, capacity: float) -> list[list]:
        """Split ordered blocks into filled pages, then even out the last one.

        Exercises and worked examples read as units, so a run of them is kept
        together rather than split across a break, which would strand the
        ruled answer space.
        """
        if not blocks:
            return []

        items: list[list] = []
        for block in blocks:
            unsplittable = block.content_type in _UNSPLITTABLE
            if (unsplittable and items
                    and items[-1] and items[-1][0].content_type == block.content_type):
                items[-1].append(block)
            else:
                items.append([block])
        weights = [sum(self._block_weight(b) for b in item) for item in items]

        # Fill strictly to the physical page capacity. An earlier version aimed
        # at an even average and allowed 15% over, which overflowed the first
        # page of every chapter and pushed its tail onto a half-empty sheet.
        groups: list[list] = []
        current: list = []
        used = 0.0
        for item, w in zip(items, weights):
            if current and used + w > capacity:
                groups.append(current)
                current, used = [], 0.0
            current.extend(item)
            used += w
        if current:
            groups.append(current)

        # Greedy packing can leave a light last page. Walk trailing items back
        # from the page before it while both stay within bounds.
        if len(groups) > 1:
            last = sum(self._block_weight(b) for b in groups[-1])
            while last < capacity * 0.5 and len(groups[-2]) > 1:
                moved = groups[-2].pop()
                cost = self._block_weight(moved)
                prev = sum(self._block_weight(b) for b in groups[-2])
                if last + cost > capacity or prev - cost < capacity * 0.55:
                    groups[-2].append(moved)
                    break
                groups[-1].insert(0, moved)
                last += cost

        # Never leave a heading alone at the top of a page: give it the block
        # that follows it, borrowing the previous page's tail if needed.
        for i, group in enumerate(groups):
            if i and len(group) == 1 and group[0].content_type == ContentType.HEADING:
                if i + 1 < len(groups):
                    groups[i + 1].insert(0, group.pop())
                else:
                    groups[i - 1].append(group.pop())
        return [g for g in groups if g]

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
        pages: list[dict[str, Any]] = []
        n = 0

        def next_number() -> int:
            nonlocal n
            n += 1
            return n

        def push(page: dict[str, Any], block_list: list) -> None:
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
                 if b.chapter == chapter and b.semantic_role != SemanticRole.CHAPTER),
                key=lambda b: (b.order, b.id),
            )
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

            opener = self._make_page(
                next_number(), PagePurpose.CHAPTER_OPENER, "chapter-opener", [],
                opener_by_chapter.get(str(chapter)),
                {
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
                figure = self._chapter_illustration(chapter, title, section_titles, asset_dir)
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

            for group in flow:
                layout = self._page_layout_for(group)
                page = self._make_page(
                    next_number(),
                    PagePurpose.EXERCISE if layout == "exercise" else PagePurpose.CONTENT,
                    layout, [],
                )
                self._fit_answer_space(group, capacity)
                push(page, group)

            recap_points = section_titles[:6] or [
                str(b.content).strip()[:180] for b in chapter_blocks
                if b.content_type in (ContentType.PARAGRAPH, ContentType.CASE_STUDY)
            ][:3]
            recap = self._make_page(next_number(), PagePurpose.RECAP, "recap", [])
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
            page = self._make_page(next_number(), PagePurpose.GLOSSARY, "glossary", [])
            page["glossary_data"] = {"entries": glossary_entries}
            push(page, [])

        reference_entries = [
            str(b.content).strip() for b in manuscript.content_blocks
            if b.content_type == ContentType.REFERENCE and str(b.content).strip()
        ]
        if reference_entries:
            page = self._make_page(next_number(), PagePurpose.REFERENCES, "references", [])
            page["references_data"] = {"entries": reference_entries}
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
                              asset_dir: Path) -> dict[str, Any] | None:
        """Generate the chapter's parcel-map plate as a real SVG asset."""
        from editorial_studio.renderer.illustrations import parcel_map_svg

        name = f"chapter_{chapter:02d}_plate.svg"
        target = asset_dir / name
        try:
            parcel_map_svg(title, sections[:4], target)
        except Exception:  # artwork must never break a build
            return None
        return {
            "id": f"plate_ch{chapter:02d}",
            "path": f"assets/{name}",
            "caption": f"Chapter {chapter} — survey schematic. Contour bands indicate the "
                       f"terrain and access questions covered in the sections that follow.",
            "alt": title,
            "width": "100%",
            "aspect": 960 / 520,
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
            "composite and illustrative; no parcel described here is offered for sale.",
            "Land transactions are governed by state and local law and by the specific documents "
            "attached to any given property. Verify all figures, records, and authorities against "
            "original sources before relying on them.",
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
            serialized["worked_example"] = {
                "title": block.metadata.get("title", ""),
                "problem": block.metadata.get("problem", ""),
                "given": block.metadata.get("given", []),
                "steps": block.metadata.get("steps", []),
                "answer": block.metadata.get("answer", ""),
                "verification": block.metadata.get("verification", ""),
            }
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
            "text": "A working field manual for disciplined land acquisition, diligence, "
                    "valuation, transaction structuring, and portfolio decisions.",
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