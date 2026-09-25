from __future__ import annotations
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from editorial_studio.core.models import (
    Asset,
    BrandProfile,
    ContentBlock,
    ContentType,
    DesignTokens,
    EditorialPlan,
    LayoutFamily,
    Manuscript,
    PagePlan,
    PagePurpose,
    SemanticRole,
)
from editorial_studio.content.intelligence import ContentAnalysis, ContentIntelligenceEngine
from editorial_studio.design_system.profiles import BuiltinBrandProfile, get_builtin_profile


@dataclass
class PublicationBrief:
    subject: str
    audience: str
    purpose: str
    tone: str
    complexity: str
    learning_objectives: list[str]
    visual_language: str
    recommended_page_size: str
    recommended_template: str
    color_theme: str
    typography_direction: str


class EditorialArtDirector:
    def __init__(self, llm_provider: str = "local"):
        self.llm_provider = llm_provider
        self.intelligence = ContentIntelligenceEngine()

    def create_publication_plan(
        self,
        manuscript: Manuscript,
        brand_profile: BrandProfile | BuiltinBrandProfile | None = None,
        user_instructions: str = "",
    ) -> EditorialPlan:
        # Analyze manuscript
        analysis = self.intelligence.analyze(manuscript)
        manuscript = self.intelligence.enrich_blocks(manuscript)

        # Generate publication brief
        brief = self._generate_brief(manuscript, analysis, user_instructions)

        # Select/adapt design system
        design_tokens = self._select_design_tokens(brand_profile, brief, analysis)

        # Create page plans
        page_plans = self._create_page_plans(manuscript, analysis, brief, design_tokens)

        # Create asset briefs
        asset_briefs = self._create_asset_briefs(manuscript, analysis, page_plans, design_tokens)

        # Build structure map
        structure_map = self._build_structure_map(manuscript, page_plans)

        plan = EditorialPlan(
            id=f"ep_{uuid.uuid4().hex[:12]}",
            manuscript_id=manuscript.id,
            brand_profile_id=getattr(brand_profile, "id", "default"),
            design_tokens=design_tokens,
            publication_brief=brief.__dict__,
            page_plans=page_plans,
            asset_briefs=asset_briefs,
            structure_map=structure_map,
            pagination_strategy="adaptive",
        )

        return plan

    def _generate_brief(
        self,
        manuscript: Manuscript,
        analysis: ContentAnalysis,
        user_instructions: str,
    ) -> PublicationBrief:
        domain = "general"
        if analysis.has_code:
            domain = "technical"
        elif analysis.has_exercises:
            domain = "educational"
        elif analysis.has_citations:
            domain = "academic"

        return PublicationBrief(
            subject=manuscript.title,
            audience=self._infer_audience(analysis, domain),
            purpose=self._infer_purpose(analysis, domain),
            tone=self._infer_tone(domain),
            complexity=analysis.reading_level,
            learning_objectives=self._extract_learning_objectives(manuscript) if analysis.has_exercises else [],
            visual_language=self._infer_visual_language(analysis, domain),
            recommended_page_size=analysis.recommended_page_size if hasattr(analysis, 'recommended_page_size') else "A4",
            recommended_template=analysis.recommended_layout if hasattr(analysis, 'recommended_layout') else "book",
            color_theme=self._select_color_theme(domain),
            typography_direction=self._select_typography_direction(domain),
        )

    def _infer_audience(self, analysis: ContentAnalysis, domain: str) -> str:
        if domain == "educational":
            return "Learners, students, professionals seeking skill development"
        elif domain == "technical":
            return "Developers, engineers, technical professionals"
        elif domain == "academic":
            return "Researchers, academics, graduate students"
        else:
            return "General professional audience"

    def _infer_purpose(self, analysis: ContentAnalysis, domain: str) -> str:
        if domain == "educational":
            return "Teach concepts and skills through structured lessons and practice"
        elif domain == "technical":
            return "Document technical implementation, APIs, and best practices"
        elif domain == "academic":
            return "Present research findings and scholarly analysis"
        else:
            return "Inform and guide readers through comprehensive content"

    def _infer_tone(self, domain: str) -> str:
        tones = {
            "educational": "encouraging, clear, structured",
            "technical": "precise, authoritative, practical",
            "academic": "formal, objective, rigorous",
            "general": "professional, accessible, engaging",
        }
        return tones.get(domain, tones["general"])

    def _infer_visual_language(self, analysis: ContentAnalysis, domain: str) -> str:
        if domain == "educational":
            return "clean, diagrammatic, workbook-friendly"
        elif domain == "technical":
            return "structured, code-friendly, reference-oriented"
        elif domain == "academic":
            return "scholarly, citation-ready, figure-heavy"
        elif analysis.has_images:
            return "editorial, image-led, magazine-style"
        else:
            return "typographic, reading-focused"

    def _select_color_theme(self, domain: str) -> str:
        themes = {
            "educational": "teal",
            "technical": "ibm-blue",
            "academic": "monochrome",
            "general": "navy",
        }
        return themes.get(domain, "navy")

    def _select_typography_direction(self, domain: str) -> str:
        directions = {
            "educational": "readable serif + clear sans",
            "technical": "technical serif + monospace-friendly sans",
            "academic": "classic serif + structured sans",
            "general": "editorial serif + elegant sans",
        }
        return directions.get(domain, "editorial serif + elegant sans")

    def _extract_learning_objectives(self, manuscript: Manuscript) -> list[str]:
        objectives = []
        for block in manuscript.content_blocks:
            if block.content_type == ContentType.HEADING and "objective" in block.content.lower():
                objectives.append(block.content)
            elif block.semantic_role == SemanticRole.EXERCISE:
                objectives.append(f"Practice: {block.content[:100]}")
        return objectives[:10]

    def _select_design_tokens(
        self,
        brand_profile: BrandProfile | BuiltinBrandProfile | None,
        brief: PublicationBrief,
        analysis: ContentAnalysis,
    ) -> DesignTokens:
        if brand_profile:
            tokens = brand_profile.design_tokens
        else:
            # Use builtin profile based on brief
            builtin = get_builtin_profile(brief.recommended_template) or get_builtin_profile("institutional")
            tokens = builtin.design_tokens

        # Adapt tokens based on brief
        adapted = DesignTokens(
            brand_name=tokens.brand_name,
            page_width_mm=tokens.page_width_mm,
            page_height_mm=tokens.page_height_mm,
            margin_top_mm=tokens.margin_top_mm,
            margin_bottom_mm=tokens.margin_bottom_mm,
            margin_inner_mm=tokens.margin_inner_mm,
            margin_outer_mm=tokens.margin_outer_mm,
            columns=tokens.columns,
            column_gutter_mm=tokens.column_gutter_mm,
            body_font_family=tokens.body_font_family,
            heading_font_family=tokens.heading_font_family,
            mono_font_family=tokens.mono_font_family,
            body_font_size_pt=tokens.body_font_size_pt,
            heading_font_sizes=dict(tokens.heading_font_sizes),
            line_height_em=tokens.line_height_em,
            paragraph_spacing_em=tokens.paragraph_spacing_em,
            first_line_indent_em=tokens.first_line_indent_em,
            colors=dict(tokens.colors),
            heading_weights=dict(tokens.heading_weights),
            numbered_headings=tokens.numbered_headings,
            show_toc=tokens.show_toc,
            show_header_footer=tokens.show_header_footer,
            header_rule=tokens.header_rule,
            page_num_position=tokens.page_num_position,
            chapter_break=tokens.chapter_break,
            indent_style=tokens.indent_style,
            hyphenate=tokens.hyphenate,
            justify=tokens.justify,
            image_treatment=tokens.image_treatment,
            illustration_style=tokens.illustration_style,
        )

        # Apply color theme
        adapted.colors = self._apply_color_theme(adapted.colors, brief.color_theme)

        # Adjust for page size
        if brief.recommended_page_size == "A5":
            adapted.page_width_mm = 148.0
            adapted.page_height_mm = 210.0

        return adapted

    def _apply_color_theme(self, colors: dict[str, str], theme: str) -> dict[str, str]:
        themes = {
            "navy": {"accent": "#1d3557", "accent_light": "#2a4a7c"},
            "ibm-blue": {"accent": "#0f62fe", "accent_light": "#3d8bff"},
            "teal": {"accent": "#0d9488", "accent_light": "#14b8a6"},
            "monochrome": {"accent": "#1a1a1a", "accent_light": "#333333"},
            "violet": {"accent": "#7c3aed", "accent_light": "#a855f7"},
            "emerald": {"accent": "#059669", "accent_light": "#10b981"},
            "amber": {"accent": "#d97706", "accent_light": "#f59e0b"},
            "crimson": {"accent": "#dc2626", "accent_light": "#ef4444"},
            "slate": {"accent": "#475569", "accent_light": "#64748b"},
            "classic": {"accent": "#8b0000", "accent_light": "#a52a2a"},
        }
        theme_colors = themes.get(theme, themes["navy"])
        result = dict(colors)
        result.update(theme_colors)
        return result

    def _create_page_plans(
        self,
        manuscript: Manuscript,
        analysis: ContentAnalysis,
        brief: PublicationBrief,
        design_tokens: DesignTokens,
    ) -> list[PagePlan]:
        plans: list[PagePlan] = []
        page_num = 1
        plans.append(self._make_cover_page(page_num, manuscript, design_tokens))
        page_num += 1
        plans.append(self._make_title_page(page_num, manuscript, design_tokens))
        page_num += 1

        front_blocks = [block for block in manuscript.content_blocks if block.matter == "front"]
        copyright_blocks = [
            block
            for block in front_blocks
            if block.metadata.get("kind") == "copyright_and_disclaimer"
            or "copyright" in block.content.lower()
        ]
        if copyright_blocks:
            plans.append(self._make_flow_page(
                page_num,
                copyright_blocks,
                design_tokens,
                PagePurpose.COPYRIGHT,
                LayoutFamily.TITLE,
            ))
            page_num += 1

        if design_tokens.show_toc and analysis.chapters > 1:
            plans.append(self._make_toc_page(page_num, manuscript, design_tokens))
            page_num += 1

        reserved_ids = {block.id for block in copyright_blocks}
        remaining_front = [
            block
            for block in front_blocks
            if block.id not in reserved_ids
            and block.semantic_role not in {
                SemanticRole.TITLE,
                SemanticRole.SUBTITLE,
                SemanticRole.AUTHOR,
                SemanticRole.COVER,
                SemanticRole.TOC,
            }
        ]
        front_plans, page_num = self._paginate_blocks(
            remaining_front,
            page_num,
            design_tokens,
            brief,
            PagePurpose.PREFACE,
            LayoutFamily.READING,
            target_words=420,
        )
        plans.extend(front_plans)

        chapter_blocks: dict[int, list[ContentBlock]] = {}
        for block in manuscript.content_blocks:
            if block.matter == "body" and block.chapter > 0:
                chapter_blocks.setdefault(block.chapter, []).append(block)

        for chapter_num in sorted(chapter_blocks):
            chapter_plans, page_num = self._plan_chapter(
                chapter_num,
                chapter_blocks[chapter_num],
                page_num,
                design_tokens,
                brief,
                analysis,
            )
            plans.extend(chapter_plans)

        back_groups = self._group_back_matter(
            [block for block in manuscript.content_blocks if block.matter == "back"]
        )
        for label, group in back_groups:
            role = group[0].semantic_role
            if role == SemanticRole.GLOSSARY:
                purpose = PagePurpose.GLOSSARY
                layout = LayoutFamily.GLOSSARY
            elif role == SemanticRole.APPENDIX:
                purpose = PagePurpose.APPENDIX
                layout = LayoutFamily.APPENDIX
            elif role in {SemanticRole.REFERENCE, SemanticRole.BIBLIOGRAPHY}:
                purpose = PagePurpose.REFERENCES
                layout = LayoutFamily.REFERENCES
            else:
                purpose = PagePurpose.SUMMARY
                layout = LayoutFamily.CLOSING
            group_plans, page_num = self._paginate_blocks(
                group,
                page_num,
                design_tokens,
                brief,
                purpose,
                layout,
                target_words=520,
                notes=label,
            )
            plans.extend(group_plans)

        plans.append(self._make_back_cover_page(page_num, design_tokens))
        return plans

    def _plan_chapter(
        self,
        chapter_num: int,
        blocks: list[ContentBlock],
        start_page: int,
        design_tokens: DesignTokens,
        brief: PublicationBrief,
        analysis: ContentAnalysis,
    ) -> tuple[list[PagePlan], int]:
        chapter_title = f"Chapter {chapter_num}"
        chapter_heading = next(
            (block for block in blocks if block.semantic_role == SemanticRole.CHAPTER),
            None,
        )
        if chapter_heading:
            chapter_title = chapter_heading.content
        opener = self._make_chapter_opener(
            start_page,
            chapter_title,
            chapter_num,
            design_tokens,
            chapter_heading.id if chapter_heading else None,
        )
        content_blocks = [block for block in blocks if block.id != (chapter_heading.id if chapter_heading else "")]
        content_plans, next_page = self._paginate_blocks(
            content_blocks,
            start_page + 1,
            design_tokens,
            brief,
            PagePurpose.CONTENT,
            None,
        )
        return [opener, *content_plans], next_page

    def _paginate_blocks(
        self,
        blocks: list[ContentBlock],
        start_page: int,
        design_tokens: DesignTokens,
        brief: PublicationBrief,
        purpose: PagePurpose,
        layout_family: LayoutFamily | None,
        target_words: int | None = None,
        notes: str = "",
    ) -> tuple[list[PagePlan], int]:
        if not blocks:
            return [], start_page
        budget = target_words or self._estimate_words_per_page(design_tokens, brief.visual_language)
        plans: list[PagePlan] = []
        current: list[ContentBlock] = []
        current_words = 0
        page_num = start_page
        for block in blocks:
            block_words = max(1, len(block.content.split()))
            if current and current_words + block_words > budget:
                page = (
                    self._make_flow_page(page_num, current, design_tokens, purpose, layout_family)
                    if layout_family is not None
                    else self._make_content_page(page_num, current, design_tokens, brief)
                )
                if notes:
                    page.notes = notes
                plans.append(page)
                page_num += 1
                current = []
                current_words = 0
            current.append(block)
            current_words += block_words
        if current:
            page = (
                self._make_flow_page(page_num, current, design_tokens, purpose, layout_family)
                if layout_family is not None
                else self._make_content_page(page_num, current, design_tokens, brief)
            )
            if notes:
                page.notes = notes
            plans.append(page)
            page_num += 1
        return plans, page_num

    def _group_back_matter(self, blocks: list[ContentBlock]) -> list[tuple[str, list[ContentBlock]]]:
        groups: list[tuple[str, list[ContentBlock]]] = []
        current: list[ContentBlock] = []
        for block in blocks:
            if block.content_type == ContentType.HEADING and block.level == 1 and current:
                groups.append((current[0].content, current))
                current = []
            current.append(block)
        if current:
            groups.append((current[0].content, current))
        return groups

    def _make_flow_page(
        self,
        page_num: int,
        blocks: list[ContentBlock],
        tokens: DesignTokens,
        purpose: PagePurpose,
        layout_family: LayoutFamily,
    ) -> PagePlan:
        return PagePlan(
            id=f"pp_{uuid.uuid4().hex[:12]}",
            page_number=page_num,
            purpose=purpose,
            layout_family=layout_family,
            content_block_ids=[block.id for block in blocks],
            page_width_mm=tokens.page_width_mm,
            page_height_mm=tokens.page_height_mm,
            margins={
                "top_mm": tokens.margin_top_mm,
                "bottom_mm": tokens.margin_bottom_mm,
                "left_mm": tokens.margin_inner_mm,
                "right_mm": tokens.margin_outer_mm,
            },
            density_target=0.78,
        )

    def _estimate_words_per_page(self, tokens: DesignTokens, visual_language: str) -> int:
        base = 350
        if tokens.body_font_size_pt > 11:
            base -= 50
        if tokens.line_height_em > 1.5:
            base -= 30
        if "image" in visual_language:
            base -= 80
        if tokens.columns == 2:
            base = int(base * 1.8)
        return base

    def _make_cover_page(self, page_num: int, manuscript: Manuscript, tokens: DesignTokens) -> PagePlan:
        return PagePlan(
            id=f"pp_{uuid.uuid4().hex[:12]}",
            page_number=page_num,
            purpose=PagePurpose.COVER,
            layout_family=LayoutFamily.COVER,
            page_width_mm=tokens.page_width_mm,
            page_height_mm=tokens.page_height_mm,
            margins={
                "top_mm": tokens.margin_top_mm,
                "bottom_mm": tokens.margin_bottom_mm,
                "left_mm": tokens.margin_inner_mm,
                "right_mm": tokens.margin_outer_mm,
            },
            typography={"title_size": "36pt", "subtitle_size": "18pt", "author_size": "14pt"},
            density_target=0.3,
            notes="Full-cover design with title, subtitle, author, brand mark",
        )

    def _make_title_page(self, page_num: int, manuscript: Manuscript, tokens: DesignTokens) -> PagePlan:
        title_block_ids = [
            block.id
            for block in manuscript.content_blocks
            if block.semantic_role in {SemanticRole.TITLE, SemanticRole.SUBTITLE, SemanticRole.AUTHOR}
        ]
        return PagePlan(
            id=f"pp_{uuid.uuid4().hex[:12]}",
            page_number=page_num,
            purpose=PagePurpose.TITLE_PAGE,
            layout_family=LayoutFamily.TITLE,
            content_block_ids=title_block_ids,
            page_width_mm=tokens.page_width_mm,
            page_height_mm=tokens.page_height_mm,
            margins={
                "top_mm": tokens.margin_top_mm,
                "bottom_mm": tokens.margin_bottom_mm,
                "left_mm": tokens.margin_inner_mm,
                "right_mm": tokens.margin_outer_mm,
            },
            typography={"title_size": "28pt", "author_size": "13pt"},
            density_target=0.25,
        )

    def _make_copyright_page(self, page_num: int, manuscript: Manuscript, tokens: DesignTokens) -> PagePlan:
        return PagePlan(
            id=f"pp_{uuid.uuid4().hex[:12]}",
            page_number=page_num,
            purpose=PagePurpose.COPYRIGHT,
            layout_family=LayoutFamily.TITLE,  # Similar layout to title page
            page_width_mm=tokens.page_width_mm,
            page_height_mm=tokens.page_height_mm,
            margins={
                "top_mm": tokens.margin_top_mm,
                "bottom_mm": tokens.margin_bottom_mm,
                "left_mm": tokens.margin_inner_mm,
                "right_mm": tokens.margin_outer_mm,
            },
            density_target=0.2,
        )

    def _make_toc_page(self, page_num: int, manuscript: Manuscript, tokens: DesignTokens) -> PagePlan:
        return PagePlan(
            id=f"pp_{uuid.uuid4().hex[:12]}",
            page_number=page_num,
            purpose=PagePurpose.TOC,
            layout_family=LayoutFamily.TOC,
            page_width_mm=tokens.page_width_mm,
            page_height_mm=tokens.page_height_mm,
            margins={
                "top_mm": tokens.margin_top_mm,
                "bottom_mm": tokens.margin_bottom_mm,
                "left_mm": tokens.margin_inner_mm,
                "right_mm": tokens.margin_outer_mm,
            },
            density_target=0.6,
        )

    def _make_chapter_opener(
        self, page_num: int, title: str, chapter_num: int, tokens: DesignTokens,
        heading_block_id: str | None = None
    ) -> PagePlan:
        block_ids = [heading_block_id] if heading_block_id else []
        return PagePlan(
            id=f"pp_{uuid.uuid4().hex[:12]}",
            page_number=page_num,
            purpose=PagePurpose.CHAPTER_OPENER,
            layout_family=LayoutFamily.CHAPTER_OPENER,
            content_block_ids=block_ids,
            page_width_mm=tokens.page_width_mm,
            page_height_mm=tokens.page_height_mm,
            margins={
                "top_mm": tokens.margin_top_mm,
                "bottom_mm": tokens.margin_bottom_mm,
                "left_mm": tokens.margin_inner_mm,
                "right_mm": tokens.margin_outer_mm,
            },
            typography={"chapter_label": "CHAPTER", "chapter_number": str(chapter_num), "title_size": "24pt"},
            density_target=0.35,
            notes=f"Chapter opener for: {title}",
        )

    def _make_content_page(
        self, page_num: int, blocks: list[ContentBlock], tokens: DesignTokens, brief: PublicationBrief
    ) -> PagePlan:
        # Determine layout family based on content
        has_images = any(b.content_type == ContentType.IMAGE_INSTRUCTION for b in blocks)
        has_tables = any(b.content_type == ContentType.TABLE for b in blocks)
        has_code = any(b.content_type == ContentType.CODE for b in blocks)
        has_exercises = any(b.content_type == ContentType.EXERCISE for b in blocks)
        has_worked_examples = any(b.content_type == ContentType.WORKED_EXAMPLE for b in blocks)
        has_case_studies = any(b.content_type == ContentType.CASE_STUDY for b in blocks)

        if has_tables:
            layout = LayoutFamily.COMPARISON_TABLE
        elif has_code:
            layout = LayoutFamily.READING
        elif has_worked_examples:
            layout = LayoutFamily.WORKED_EXAMPLE
        elif has_case_studies:
            layout = LayoutFamily.CASE_STUDY
        elif has_exercises:
            layout = LayoutFamily.EXERCISE
        elif has_images:
            layout = LayoutFamily.IMAGE_LED
        else:
            layout = LayoutFamily.READING

        block_ids = [b.id for b in blocks]

        return PagePlan(
            id=f"pp_{uuid.uuid4().hex[:12]}",
            page_number=page_num,
            purpose=PagePurpose.CONTENT,
            layout_family=layout,
            content_block_ids=block_ids,
            page_width_mm=tokens.page_width_mm,
            page_height_mm=tokens.page_height_mm,
            margins={
                "top_mm": tokens.margin_top_mm,
                "bottom_mm": tokens.margin_bottom_mm,
                "left_mm": tokens.margin_inner_mm,
                "right_mm": tokens.margin_outer_mm,
            },
            density_target=0.85,
        )

    def _make_recap_page(self, page_num: int, chapter_num: int, tokens: DesignTokens,
                          recap_block_ids: list[str] | None = None) -> PagePlan:
        return PagePlan(
            id=f"pp_{uuid.uuid4().hex[:12]}",
            page_number=page_num,
            purpose=PagePurpose.RECAP,
            layout_family=LayoutFamily.RECAP,
            content_block_ids=recap_block_ids or [],
            page_width_mm=tokens.page_width_mm,
            page_height_mm=tokens.page_height_mm,
            margins={
                "top_mm": tokens.margin_top_mm,
                "bottom_mm": tokens.margin_bottom_mm,
                "left_mm": tokens.margin_inner_mm,
                "right_mm": tokens.margin_outer_mm,
            },
            density_target=0.7,
        )

    def _make_references_page(self, page_num: int, tokens: DesignTokens,
                               ref_block_ids: list[str] | None = None) -> PagePlan:
        return PagePlan(
            id=f"pp_{uuid.uuid4().hex[:12]}",
            page_number=page_num,
            purpose=PagePurpose.REFERENCES,
            layout_family=LayoutFamily.REFERENCES,
            content_block_ids=ref_block_ids or [],
            page_width_mm=tokens.page_width_mm,
            page_height_mm=tokens.page_height_mm,
            margins={
                "top_mm": tokens.margin_top_mm,
                "bottom_mm": tokens.margin_bottom_mm,
                "left_mm": tokens.margin_inner_mm,
                "right_mm": tokens.margin_outer_mm,
            },
            density_target=0.8,
        )

    def _make_glossary_page(self, page_num: int, tokens: DesignTokens,
                             glossary_block_ids: list[str] | None = None) -> PagePlan:
        return PagePlan(
            id=f"pp_{uuid.uuid4().hex[:12]}",
            page_number=page_num,
            purpose=PagePurpose.GLOSSARY,
            layout_family=LayoutFamily.GLOSSARY,
            content_block_ids=glossary_block_ids or [],
            page_width_mm=tokens.page_width_mm,
            page_height_mm=tokens.page_height_mm,
            margins={
                "top_mm": tokens.margin_top_mm,
                "bottom_mm": tokens.margin_bottom_mm,
                "left_mm": tokens.margin_inner_mm,
                "right_mm": tokens.margin_outer_mm,
            },
            density_target=0.8,
        )

    def _make_about_author_page(self, page_num: int, tokens: DesignTokens,
                                 author_block_ids: list[str] | None = None) -> PagePlan:
        return PagePlan(
            id=f"pp_{uuid.uuid4().hex[:12]}",
            page_number=page_num,
            purpose=PagePurpose.BACK_COVER,  # Using back cover purpose for about author
            layout_family=LayoutFamily.CLOSING,
            content_block_ids=author_block_ids or [],
            page_width_mm=tokens.page_width_mm,
            page_height_mm=tokens.page_height_mm,
            margins={
                "top_mm": tokens.margin_top_mm,
                "bottom_mm": tokens.margin_bottom_mm,
                "left_mm": tokens.margin_inner_mm,
                "right_mm": tokens.margin_outer_mm,
            },
            density_target=0.3,
        )

    def _make_back_cover_page(self, page_num: int, tokens: DesignTokens) -> PagePlan:
        return PagePlan(
            id=f"pp_{uuid.uuid4().hex[:12]}",
            page_number=page_num,
            purpose=PagePurpose.BACK_COVER,
            layout_family=LayoutFamily.COVER,
            page_width_mm=tokens.page_width_mm,
            page_height_mm=tokens.page_height_mm,
            margins={
                "top_mm": tokens.margin_top_mm,
                "bottom_mm": tokens.margin_bottom_mm,
                "left_mm": tokens.margin_inner_mm,
                "right_mm": tokens.margin_outer_mm,
            },
            density_target=0.2,
        )

    def _create_asset_briefs(
        self,
        manuscript: Manuscript,
        analysis: ContentAnalysis,
        page_plans: list[PagePlan],
        design_tokens: DesignTokens,
    ) -> list[dict[str, Any]]:
        briefs: list[dict[str, Any]] = []

        # Extract image instructions
        for block in manuscript.content_blocks:
            if block.content_type == ContentType.IMAGE_INSTRUCTION:
                briefs.append({
                    "id": f"ab_{uuid.uuid4().hex[:8]}",
                    "type": "illustration",
                    "purpose": block.metadata.get("alt_text", "Illustration"),
                    "description": block.content,
                    "style": design_tokens.illustration_style,
                    "aspect_ratio": 4/3,
                    "placement": "inline",
                    "source_block_id": block.id,
                })

        # Add diagram briefs for technical content
        if analysis.has_code:
            for i, block in enumerate(manuscript.content_blocks):
                if block.content_type == ContentType.CODE and i > 0:
                    prev = manuscript.content_blocks[i-1]
                    if "diagram" in prev.content.lower() or "architecture" in prev.content.lower():
                        briefs.append({
                            "id": f"ab_{uuid.uuid4().hex[:8]}",
                            "type": "diagram",
                            "purpose": "Technical diagram",
                            "description": f"Diagram illustrating: {prev.content[:200]}",
                            "style": "technical",
                            "aspect_ratio": 16/9,
                            "placement": "inline",
                            "source_block_id": block.id,
                        })

        return briefs

    def _build_structure_map(
        self, manuscript: Manuscript, page_plans: list[PagePlan]
    ) -> dict[str, Any]:
        chapter_pages: dict[int, list[int]] = {}
        for plan in page_plans:
            if plan.purpose == PagePurpose.CHAPTER_OPENER:
                # Find which chapter this belongs to
                for block_id in plan.content_block_ids:
                    block = next((b for b in manuscript.content_blocks if b.id == block_id), None)
                    if block and block.chapter > 0:
                        if block.chapter not in chapter_pages:
                            chapter_pages[block.chapter] = []
                        chapter_pages[block.chapter].append(plan.page_number)

        return {
            "total_pages": len(page_plans),
            "chapters": {ch: {"pages": pages, "page_count": len(pages)} for ch, pages in chapter_pages.items()},
            "front_matter_pages": [p.page_number for p in page_plans if p.purpose in {
                PagePurpose.COVER,
                PagePurpose.TITLE_PAGE,
                PagePurpose.COPYRIGHT,
                PagePurpose.TOC,
                PagePurpose.FOREWORD,
                PagePurpose.PREFACE,
                PagePurpose.INTRODUCTION,
            }],
            "back_matter_pages": [p.page_number for p in page_plans if p.purpose in {
                PagePurpose.GLOSSARY,
                PagePurpose.REFERENCES,
                PagePurpose.APPENDIX,
                PagePurpose.SUMMARY,
                PagePurpose.BACK_COVER,
            }],
        }

    def validate_plan(self, plan: EditorialPlan, manuscript: Manuscript | None = None) -> list[str]:
        issues = []

        # Check all content blocks are assigned
        assigned_blocks = set()
        for page in plan.page_plans:
            assigned_blocks.update(page.content_block_ids)

        if manuscript:
            # Check all body blocks are assigned
            body_block_ids = {b.id for b in manuscript.content_blocks if b.matter == "body"}
            missing = body_block_ids - assigned_blocks
            if missing:
                issues.append(f"Missing {len(missing)} body blocks from page plans: {sorted(missing)[:10]}")
            
            # Check front matter blocks
            front_block_ids = {b.id for b in manuscript.content_blocks if b.matter == "front"}
            front_missing = front_block_ids - assigned_blocks
            if front_missing:
                issues.append(f"Missing {len(front_missing)} front matter blocks from page plans")
            
            # Check back matter blocks
            back_block_ids = {b.id for b in manuscript.content_blocks if b.matter == "back"}
            back_missing = back_block_ids - assigned_blocks
            if back_missing:
                issues.append(f"Missing {len(back_missing)} back matter blocks from page plans")
            
            # Check for duplicate block IDs in page plans
            all_assigned = []
            for page in plan.page_plans:
                all_assigned.extend(page.content_block_ids)
            if len(all_assigned) != len(set(all_assigned)):
                issues.append("Duplicate block IDs found across page plans")

        # Check for reasonable page count
        if len(plan.page_plans) > 500:
            issues.append("Excessive page count")

        # Check cover exists
        has_cover = any(p.purpose == PagePurpose.COVER for p in plan.page_plans)
        if not has_cover:
            issues.append("Missing cover page")

        # Check TOC exists if chapters > 1
        if manuscript and manuscript.content_blocks:
            chapters = max((b.chapter for b in manuscript.content_blocks if b.chapter > 0), default=0)
            if chapters > 1:
                has_toc = any(p.purpose == PagePurpose.TOC for p in plan.page_plans)
                if not has_toc:
                    issues.append("Missing TOC for multi-chapter manuscript")

        return issues