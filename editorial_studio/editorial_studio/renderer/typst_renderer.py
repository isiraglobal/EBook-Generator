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

    def render_pdf(self, manuscript: Manuscript, plan: EditorialPlan, assets: list[Asset],
                   output_path: str, strict_layout: bool = False) -> dict[str, Any]:
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

            content_data = {
                "title": manuscript.title,
                "author": manuscript.author,
                "language": "en",
                "preset": self._tokens_to_preset(plan.design_tokens),
                "sections": self._build_sections(manuscript, plan, asset_map),
            }

            content_json_path = assets_dir / "content.json"
            content_json_path.write_text(json.dumps(content_data, ensure_ascii=False, indent=2))

            template_name = self._select_template(plan)
            template_path = self.templates_dir / f"{template_name}.typ"
            if not template_path.exists():
                template_path = self.templates_dir / "book.typ"

            main_typ = work_dir / "main.typ"
            shutil.copy2(template_path, main_typ)

            for helper in self.templates_dir.glob("helpers.typ"):
                shutil.copy2(helper, work_dir / helper.name)

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

            content_data = {
                "title": manuscript.title,
                "author": manuscript.author,
                "language": "en",
                "preset": self._tokens_to_preset(plan.design_tokens),
                "sections": self._build_sections(manuscript, plan, asset_map),
            }

            content_json_path = assets_dir / "content.json"
            content_json_path.write_text(json.dumps(content_data, ensure_ascii=False, indent=2))

            template_name = self._select_template(plan)
            template_path = self.templates_dir / f"{template_name}.typ"
            if not template_path.exists():
                template_path = self.templates_dir / "book.typ"

            main_typ = work_dir / "main.typ"
            shutil.copy2(template_path, main_typ)

            for helper in self.templates_dir.glob("helpers.typ"):
                shutil.copy2(helper, work_dir / helper.name)

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
            "accent_color": tokens.colors.get("accent", "#1d3557"),
            "heading_color": tokens.colors.get("heading", "#1a1a1a"),
            "body_color": tokens.colors.get("body", "#1a1a1a"),
            "muted_color": tokens.colors.get("muted", "#64748b"),
            "h1_size": f"{tokens.heading_font_sizes.get(1, 18)}pt",
            "h2_size": f"{tokens.heading_font_sizes.get(2, 13)}pt",
            "h3_size": f"{tokens.heading_font_sizes.get(3, 11)}pt",
            "h1_weight": tokens.heading_weights.get(1, "bold"),
            "h2_weight": tokens.heading_weights.get(2, "semibold"),
            "h3_weight": tokens.heading_weights.get(3, "semibold"),
            "numbered_headings": tokens.numbered_headings,
            "show_toc": tokens.show_toc,
            "show_header_footer": tokens.show_header_footer,
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

    def _build_sections(self, manuscript: Manuscript, plan: EditorialPlan,
                        asset_map: dict[str, str]) -> list[dict[str, Any]]:
        sections = []
        current_chapter = -1
        current_section = -1

        chapter_blocks: dict[int, list[Any]] = {}
        for block in manuscript.content_blocks:
            if block.chapter not in chapter_blocks:
                chapter_blocks[block.chapter] = []
            chapter_blocks[block.chapter].append(block)

        for ch_num in sorted(chapter_blocks.keys()):
            blocks = chapter_blocks[ch_num]
            if not blocks:
                continue

            chapter_title = f"Chapter {ch_num}"
            for block in blocks:
                if block.semantic_role.value == "chapter":
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