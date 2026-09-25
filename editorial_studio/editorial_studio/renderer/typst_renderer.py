from __future__ import annotations
import json
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


class TypstRenderer:
    def __init__(self, config: dict | None = None):
        self.config = config or load_config().data
        self.typst_path = self.config.get("rendering", {}).get("typst_path", "typst")
        package_root = Path(__file__).parent.parent
        self.fonts_dir = package_root / self.config.get("rendering", {}).get("fonts_dir", "assets/fonts")
        self.templates_dir = package_root / self.config.get("rendering", {}).get("templates_dir", "assets/templates")
        self.default_dpi = self.config.get("rendering", {}).get("default_dpi", 300)
        self.preview_dpi = self.config.get("rendering", {}).get("preview_dpi", 144)

        # Layout family to layout_library function mapping
        # Keys must match the layout-functions dictionary in layout_library.typ
        self.layout_function_map = {
            LayoutFamily.COVER: "cover",
            LayoutFamily.TITLE: "title-page",
            LayoutFamily.TOC: "toc",
            LayoutFamily.CHAPTER_OPENER: "chapter-opener",
            LayoutFamily.READING: "reading",
            LayoutFamily.IMAGE_LED: "image-led",
            LayoutFamily.CASE_STUDY: "case-study",
            LayoutFamily.WORKED_EXAMPLE: "worked-example",
            LayoutFamily.CHECKLIST: "checklist",
            LayoutFamily.PROCESS_DIAGRAM: "process-diagram",
            LayoutFamily.COMPARISON_TABLE: "reading",
            LayoutFamily.EXERCISE: "exercise",
            LayoutFamily.RECAP: "recap",
            LayoutFamily.GLOSSARY: "reading",
            LayoutFamily.REFERENCES: "reading",
            LayoutFamily.APPENDIX: "reading",
            LayoutFamily.CLOSING: "reading",
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
            page_data = self._build_page_data(manuscript, plan, asset_map)

            content_data = {
                "title": manuscript.title,
                "subtitle": manuscript.description,
                "author": manuscript.author,
                "publisher": plan.design_tokens.brand_name,
                "language": "en",
                "preset": self._tokens_to_preset(plan.design_tokens),
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

            page_data = self._build_page_data(manuscript, plan, asset_map)

            content_data = {
                "title": manuscript.title,
                "subtitle": manuscript.description,
                "author": manuscript.author,
                "publisher": plan.design_tokens.brand_name,
                "language": "en",
                "preset": self._tokens_to_preset(plan.design_tokens),
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

    def _tokens_to_preset(self, tokens: DesignTokens) -> dict[str, Any]:
        return {
            "body_font": tokens.body_font_family,
            "heading_font": tokens.heading_font_family,
            "mono_font": tokens.mono_font_family,
            "text_size": f"{tokens.body_font_size_pt}pt",
            "leading": f"{tokens.line_height_em}em",
            "justify": tokens.justify,
            "hyphenate": tokens.hyphenate,
            "paper": "a4" if tokens.page_width_mm >= 210 else "a5",
            "margin_left": f"{tokens.margin_inner_mm}mm",
            "margin_right": f"{tokens.margin_outer_mm}mm",
            "margin_top": f"{tokens.margin_top_mm}mm",
            "margin_bottom": f"{tokens.margin_bottom_mm}mm",
            "margin_inner": f"{tokens.margin_inner_mm}mm",
            "margin_outer": f"{tokens.margin_outer_mm}mm",
            "accent_color": tokens.colors.get("accent", "#1d3557"),
            "heading_color": tokens.colors.get("heading", "#1a1a1a"),
            "body_color": tokens.colors.get("body", "#1a1a1a"),
            "muted_color": tokens.colors.get("muted", "#64748b"),
            "sidebar_bg": tokens.colors.get("sidebar_bg", "#f8f9fa"),
            "table_header": tokens.colors.get("table_header", "#f1f1f1"),
            "table_row_alt": tokens.colors.get("table_row_alt", "#fafafa"),
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
            "page_contract": {
                "columns": tokens.columns,
                "section_breaks": tokens.chapter_break,
                "final_page_policy": "partial_ok" if tokens.chapter_break else "min_fill",
                "min_final_fill": 0.5,
                "underfill_tolerance_lines": 3.0,
            },
        }

    def _build_page_data(self, manuscript: Manuscript, plan: EditorialPlan,
                         asset_map: dict[str, str]) -> list[dict[str, Any]]:
        """Build page-by-page data from editorial plan."""
        pages = []

        # Create a lookup for blocks by ID
        block_by_id = {b.id: b for b in manuscript.content_blocks}

        for page_plan in plan.page_plans:
            page = {
                "page_number": page_plan.page_number,
                "purpose": page_plan.purpose.value,
                "layout_family": page_plan.layout_family.value,
                "layout_function": self.layout_function_map.get(page_plan.layout_family, "layout-reading"),
                "width_mm": page_plan.page_width_mm,
                "height_mm": page_plan.page_height_mm,
                "margins": page_plan.margins,
                "density_target": page_plan.density_target,
                "blocks": [],
            }

            page_blocks: list = []
            for block_id in page_plan.content_block_ids:
                block = block_by_id.get(block_id)
                if block:
                    page_blocks.append(block)
                    page["blocks"].append(self._serialize_block(block, asset_map))

            # Add page-specific data based on purpose
            if page_plan.purpose == PagePurpose.COVER:
                page["cover_data"] = self._build_cover_data(manuscript, plan.design_tokens)
            elif page_plan.purpose == PagePurpose.TITLE_PAGE:
                page["title_data"] = self._build_title_data(manuscript, plan.design_tokens)
            elif page_plan.purpose == PagePurpose.TOC:
                page["toc_data"] = self._build_toc_data(manuscript, plan.design_tokens)
            elif page_plan.purpose == PagePurpose.CHAPTER_OPENER:
                chapter_num = page_plan.typography.get("chapter_number", "1") if page_plan.typography else "1"
                chapter_title = page_plan.notes.removeprefix("Chapter opener for: ") if page_plan.notes else f"Chapter {chapter_num}"
                chapter_number = int(chapter_num) if str(chapter_num).isdigit() else 0
                objectives = [
                    block.content
                    for block in manuscript.content_blocks
                    if block.matter == "body"
                    and block.chapter == chapter_number
                    and block.content_type == ContentType.CALLOUT
                ][:3]
                page["chapter_opener_data"] = {
                    "chapter_number": chapter_num,
                    "chapter_title": chapter_title,
                    "epigraph": "",
                    "learning_objectives": objectives,
                }
            elif page_plan.purpose == PagePurpose.GLOSSARY:
                page["glossary_data"] = {
                    "entries": [
                        {"term": block.metadata.get("term", ""), "definition": block.content}
                        for block in page_blocks
                        if block.content_type == ContentType.DEFINITION
                    ]
                }
            elif page_plan.purpose == PagePurpose.REFERENCES:
                page["references_data"] = {"entries": [block.content for block in page_blocks]}
            elif page_plan.purpose == PagePurpose.BACK_COVER:
                page["back_cover_data"] = {
                    "background_color": plan.design_tokens.colors.get("accent", "#1d3557"),
                    "text": "A practical field manual for disciplined land investment decisions.",
                }

            pages.append(page)

        return pages

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
                    "caption": block.metadata.get("alt_text", ""),
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
            serialized["exercise"] = {
                "title": block.metadata.get("title", "Exercise"),
                "instructions": block.metadata.get("instructions", ""),
                "question": block.content,
                "hints": block.metadata.get("hints", []),
                "response_type": block.metadata.get("response_type", "lines"),
                "response_lines": block.metadata.get("response_lines", 5),
            }
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
            serialized["callout"] = {
                "text": block.content,
                "kind": "warning" if block.content_type == ContentType.WARNING else "info",
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
            "publisher": tokens.brand_name,
            "background_color": tokens.colors.get("background", "#f4f0e6"),
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
        return {
            "sections": [
                {"title": b.content, "page": 1}  # Will be filled by Typst outline
                for b in manuscript.content_blocks
                if b.semantic_role == SemanticRole.CHAPTER and b.matter == "body"
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