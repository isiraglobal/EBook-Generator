from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from editorial_studio.core.models import BrandProfile, DesignTokens

# Shared editorial palette: warm paper, ink, brass, terracotta. Brand profiles
# inherit it and override individual roles as needed. The renderer reads this
# from ``DesignTokens.colors["palette"]`` and falls back to the same values, so
# the Typst component library and the Python design system stay in step.
EDITORIAL_PALETTE: dict[str, str] = {
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


@dataclass
class BuiltinBrandProfile:
    id: str
    name: str
    description: str
    design_tokens: DesignTokens
    cover_conventions: dict[str, Any] = field(default_factory=dict)
    section_opener_conventions: dict[str, Any] = field(default_factory=dict)


def create_landnow_profile() -> BuiltinBrandProfile:
    return BuiltinBrandProfile(
        id="builtin_landnow",
        name="LandNow Institutional",
        description="Premium institutional editorial direction for land investment publications",
        design_tokens=DesignTokens(
            brand_name="LandNow",
            page_width_mm=210.0,
            page_height_mm=297.0,
            margin_top_mm=25.0,
            margin_bottom_mm=30.0,
            margin_inner_mm=28.0,
            margin_outer_mm=22.0,
            columns=1,
            column_gutter_mm=5.0,
            body_font_family="PT Serif",
            heading_font_family="PT Sans",
            mono_font_family="PT Mono",
            body_font_size_pt=10.5,
            heading_font_sizes={1: 22.0, 2: 15.0, 3: 12.0},
            line_height_em=1.5,
            paragraph_spacing_em=0.75,
            first_line_indent_em=1.5,
            colors={
                "palette": dict(EDITORIAL_PALETTE),
                "accent": "#0f172a",
                "accent_light": "#1e293b",
                "accent_brass": "#c4a35a",
                "heading": "#0f172a",
                "body": "#1e293b",
                "muted": "#64748b",
                "background": "#fefefe",
                "sidebar_bg": "#f8fafc",
                "table_header": "#e2e8f0",
                "table_row_alt": "#f1f5f9",
                "rule": "#c4a35a",
                "page_number": "#94a3b8",
            },
            heading_weights={1: "bold", 2: "semibold", 3: "medium"},
            numbered_headings=True,
            show_toc=True,
            show_header_footer=True,
            header_rule=True,
            page_num_position="bottom-center",
            chapter_break=True,
            indent_style="indent",
            hyphenate=True,
            justify=True,
            image_treatment="editorial",
            illustration_style="geographic",
        ),
        cover_conventions={
            "layout": "institutional",
            "background": "deep_navy",
            "accent_line": "brass",
            "title_style": "display_serif",
            "subtitle_style": "elegant_sans",
            "ornament": "compass_rose",
        },
        section_opener_conventions={
            "layout": "full_width_title",
            "accent_rule": "brass",
            "spacing": "generous",
            "drop_cap": False,
        },
    )


def create_institutional_financial_profile() -> BuiltinBrandProfile:
    return BuiltinBrandProfile(
        id="builtin_institutional",
        name="Institutional Financial",
        description="Conservative, authoritative design for financial reports and analysis",
        design_tokens=DesignTokens(
            brand_name="Institutional",
            page_width_mm=210.0,
            page_height_mm=297.0,
            margin_top_mm=25.0,
            margin_bottom_mm=25.0,
            margin_inner_mm=28.0,
            margin_outer_mm=22.0,
            columns=1,
            column_gutter_mm=5.0,
            body_font_family="PT Serif",
            heading_font_family="PT Sans",
            mono_font_family="PT Mono",
            body_font_size_pt=10.5,
            heading_font_sizes={1: 18.0, 2: 14.0, 3: 11.0},
            line_height_em=1.45,
            paragraph_spacing_em=0.7,
            first_line_indent_em=1.25,
            colors={
                "palette": dict(EDITORIAL_PALETTE),
                "accent": "#1d3557",
                "heading": "#1d3557",
                "body": "#1a1a1a",
                "muted": "#64748b",
                "background": "#ffffff",
                "sidebar_bg": "#f8f9fa",
                "table_header": "#e9ecef",
                "table_row_alt": "#f8f9fa",
            },
            heading_weights={1: "bold", 2: "semibold", 3: "semibold"},
            numbered_headings=True,
            show_toc=True,
            show_header_footer=True,
            header_rule=True,
            page_num_position="bottom-center",
            chapter_break=True,
        ),
        cover_conventions={"layout": "formal", "background": "navy", "accent": "gold"},
        section_opener_conventions={"layout": "centered", "rule": "gold"},
    )


def create_educational_course_profile() -> BuiltinBrandProfile:
    return BuiltinBrandProfile(
        id="builtin_educational",
        name="Educational Course",
        description="Clear, accessible design for courses, workbooks, and learning materials",
        design_tokens=DesignTokens(
            brand_name="Education",
            page_width_mm=210.0,
            page_height_mm=297.0,
            margin_top_mm=25.0,
            margin_bottom_mm=25.0,
            margin_inner_mm=25.0,
            margin_outer_mm=25.0,
            columns=1,
            column_gutter_mm=6.0,
            body_font_family="PT Serif",
            heading_font_family="PT Sans",
            mono_font_family="PT Mono",
            body_font_size_pt=11.0,
            heading_font_sizes={1: 20.0, 2: 15.0, 3: 12.0},
            line_height_em=1.55,
            paragraph_spacing_em=1.0,
            first_line_indent_em=0,
            colors={
                "palette": dict(EDITORIAL_PALETTE),
                "accent": "#0d9488",
                "heading": "#111827",
                "body": "#1f2937",
                "muted": "#6b7280",
                "background": "#ffffff",
                "sidebar_bg": "#f0fdfa",
                "table_header": "#ccfbf1",
                "table_row_alt": "#f0fdfa",
            },
            heading_weights={1: "bold", 2: "bold", 3: "semibold"},
            numbered_headings=True,
            show_toc=True,
            show_header_footer=True,
            header_rule=False,
            page_num_position="bottom-center",
            chapter_break=True,
            indent_style="space",
            justify=False,
        ),
        cover_conventions={"layout": "clean", "accent": "teal", "icon": "book"},
        section_opener_conventions={"layout": "spacious", "learning_objectives": True},
    )


def create_scientific_technical_profile() -> BuiltinBrandProfile:
    return BuiltinBrandProfile(
        id="builtin_scientific",
        name="Scientific Technical",
        description="Precision-oriented design for technical guides, documentation, and research",
        design_tokens=DesignTokens(
            brand_name="Technical",
            page_width_mm=210.0,
            page_height_mm=297.0,
            margin_top_mm=25.0,
            margin_bottom_mm=25.0,
            margin_inner_mm=25.0,
            margin_outer_mm=25.0,
            columns=1,
            column_gutter_mm=5.0,
            body_font_family="PT Serif",
            heading_font_family="PT Sans",
            mono_font_family="PT Mono",
            body_font_size_pt=10.0,
            heading_font_sizes={1: 20.0, 2: 14.0, 3: 11.0},
            line_height_em=1.5,
            paragraph_spacing_em=0.8,
            first_line_indent_em=0,
            colors={
                "palette": dict(EDITORIAL_PALETTE),
                "accent": "#0f62fe",
                "heading": "#161616",
                "body": "#161616",
                "muted": "#6f6f6f",
                "background": "#ffffff",
                "sidebar_bg": "#edf5ff",
                "table_header": "#d6e4f0",
                "table_row_alt": "#f2f7fc",
            },
            heading_weights={1: "bold", 2: "semibold", 3: "semibold"},
            numbered_headings=True,
            show_toc=True,
            show_header_footer=True,
            header_rule=True,
            page_num_position="top-right",
            chapter_break=False,
            indent_style="space",
            justify=False,
        ),
        cover_conventions={"layout": "technical", "accent": "ibm_blue", "geometry": True},
        section_opener_conventions={"layout": "structured", "numbered": True},
    )


def create_nature_travel_profile() -> BuiltinBrandProfile:
    return BuiltinBrandProfile(
        id="builtin_nature",
        name="Nature Travel",
        description="Visual-forward design for nature, travel, and feature publications",
        design_tokens=DesignTokens(
            brand_name="Nature",
            page_width_mm=210.0,
            page_height_mm=297.0,
            margin_top_mm=20.0,
            margin_bottom_mm=20.0,
            margin_inner_mm=25.0,
            margin_outer_mm=25.0,
            columns=1,
            column_gutter_mm=6.0,
            body_font_family="PT Serif",
            heading_font_family="PT Sans",
            mono_font_family="PT Mono",
            body_font_size_pt=11.0,
            heading_font_sizes={1: 24.0, 2: 16.0, 3: 12.0},
            line_height_em=1.6,
            paragraph_spacing_em=1.0,
            first_line_indent_em=1.5,
            colors={
                "palette": dict(EDITORIAL_PALETTE),
                "accent": "#7c3aed",
                "heading": "#1e1a14",
                "body": "#1e1a14",
                "muted": "#a89878",
                "background": "#fafaf9",
                "sidebar_bg": "#f5f3ff",
                "table_header": "#ede9fe",
                "table_row_alt": "#fafafa",
            },
            heading_weights={1: "bold", 2: "semibold", 3: "semibold"},
            numbered_headings=False,
            show_toc=False,
            show_header_footer=True,
            header_rule=False,
            page_num_position="bottom-center",
            chapter_break=True,
        ),
        cover_conventions={"layout": "image_hero", "full_bleed": True, "minimal_text": True},
        section_opener_conventions={"layout": "image_led", "full_width": True},
    )


def create_minimalist_manual_profile() -> BuiltinBrandProfile:
    return BuiltinBrandProfile(
        id="builtin_minimalist",
        name="Minimalist Manual",
        description="Clean, functional design for professional manuals and documentation",
        design_tokens=DesignTokens(
            brand_name="Minimalist",
            page_width_mm=210.0,
            page_height_mm=297.0,
            margin_top_mm=30.0,
            margin_bottom_mm=30.0,
            margin_inner_mm=30.0,
            margin_outer_mm=30.0,
            columns=1,
            column_gutter_mm=8.0,
            body_font_family="PT Sans",
            heading_font_family="PT Sans",
            mono_font_family="PT Mono",
            body_font_size_pt=10.0,
            heading_font_sizes={1: 18.0, 2: 13.0, 3: 11.0},
            line_height_em=1.6,
            paragraph_spacing_em=1.0,
            first_line_indent_em=0,
            colors={
                "palette": dict(EDITORIAL_PALETTE),
                "accent": "#475569",
                "heading": "#1e293b",
                "body": "#334155",
                "muted": "#94a3b8",
                "background": "#ffffff",
                "sidebar_bg": "#f8fafc",
                "table_header": "#e2e8f0",
                "table_row_alt": "#f1f5f9",
            },
            heading_weights={1: "600", 2: "500", 3: "500"},
            numbered_headings=False,
            show_toc=True,
            show_header_footer=False,
            header_rule=False,
            page_num_position="bottom-center",
            chapter_break=True,
            indent_style="space",
            justify=False,
        ),
        cover_conventions={"layout": "typographic", "minimal": True},
        section_opener_conventions={"layout": "clean", "generous_whitespace": True},
    )


BUILTIN_PROFILES = {
    "landnow": create_landnow_profile(),
    "institutional": create_institutional_financial_profile(),
    "educational": create_educational_course_profile(),
    "scientific": create_scientific_technical_profile(),
    "nature": create_nature_travel_profile(),
    "minimalist": create_minimalist_manual_profile(),
}


def get_builtin_profile(profile_id: str) -> BuiltinBrandProfile | None:
    return BUILTIN_PROFILES.get(profile_id)


def list_builtin_profiles() -> list[BuiltinBrandProfile]:
    return list(BUILTIN_PROFILES.values())