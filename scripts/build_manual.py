#!/usr/bin/env python3
"""Fast local build harness for the Land Investor's Field Manual.

Loads the manuscript + editorial plan directly from a project's source bundle
and drives TypstRenderer without going through the full ingest/plan pipeline.

    python3 scripts/build_manual.py --project prj_16f8a7fb56f2 \
        --out output/land-field-manual-12ch.pdf
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "editorial_studio"))

from editorial_studio.core.models import (  # noqa: E402
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
from editorial_studio.renderer.typst_renderer import TypstRenderer  # noqa: E402

PROJECTS = REPO / "data" / "projects"


def _enum(enum_cls, value, fallback):
    try:
        return enum_cls(value)
    except ValueError:
        try:
            return enum_cls[str(value).upper()]
        except KeyError:
            return fallback


def load_manuscript(raw: dict) -> Manuscript:
    blocks = [
        ContentBlock(
            id=b["id"],
            content=b.get("content", ""),
            content_type=_enum(ContentType, b.get("content_type"), ContentType.PARAGRAPH),
            semantic_role=_enum(SemanticRole, b.get("semantic_role"), SemanticRole.BODY),
            chapter=b.get("chapter", 0),
            section=b.get("section", 0),
            subsection=b.get("subsection", 0),
            order=b.get("order", 0),
            level=b.get("level", 0),
            source_ref=b.get("source_ref", ""),
            metadata=b.get("metadata") or {},
            matter=b.get("matter", "body"),
        )
        for b in raw.get("content_blocks", [])
    ]
    return Manuscript(
        id=raw.get("id", "ms_local"),
        title=raw.get("title", "Untitled"),
        author=raw.get("author", ""),
        description=raw.get("description", ""),
        source_format=raw.get("source_format", ""),
        content_blocks=blocks,
        structure=raw.get("structure") or {},
        metadata=raw.get("metadata") or {},
    )


def load_plan(raw: dict, manuscript: Manuscript) -> EditorialPlan:
    tokens_raw = dict(raw.get("design_tokens") or {})
    heading_sizes = {
        int(k): float(v) for k, v in (tokens_raw.get("heading_font_sizes") or {}).items()
    }
    heading_weights = {int(k): v for k, v in (tokens_raw.get("heading_weights") or {}).items()}
    tokens = DesignTokens(
        brand_name=tokens_raw.get("brand_name", ""),
        page_width_mm=tokens_raw.get("page_width_mm", 210.0),
        page_height_mm=tokens_raw.get("page_height_mm", 297.0),
        margin_top_mm=tokens_raw.get("margin_top_mm", 25.0),
        margin_bottom_mm=tokens_raw.get("margin_bottom_mm", 25.0),
        margin_inner_mm=tokens_raw.get("margin_inner_mm", 25.0),
        margin_outer_mm=tokens_raw.get("margin_outer_mm", 25.0),
        columns=tokens_raw.get("columns", 1),
        column_gutter_mm=tokens_raw.get("column_gutter_mm", 5.0),
        body_font_family=tokens_raw.get("body_font_family", "Source Serif 4"),
        heading_font_family=tokens_raw.get("heading_font_family", "Source Sans 3"),
        mono_font_family=tokens_raw.get("mono_font_family", "Source Code Pro"),
        body_font_size_pt=tokens_raw.get("body_font_size_pt", 10.5),
        heading_font_sizes=heading_sizes,
        line_height_em=tokens_raw.get("line_height_em", 1.45),
        paragraph_spacing_em=tokens_raw.get("paragraph_spacing_em", 0.7),
        first_line_indent_em=tokens_raw.get("first_line_indent_em", 1.25),
        colors=tokens_raw.get("colors") or {},
        heading_weights=heading_weights,
        numbered_headings=tokens_raw.get("numbered_headings", True),
        show_toc=tokens_raw.get("show_toc", True),
        show_header_footer=tokens_raw.get("show_header_footer", True),
        header_rule=tokens_raw.get("header_rule", True),
        page_num_position=tokens_raw.get("page_num_position", "bottom-center"),
        chapter_break=tokens_raw.get("chapter_break", True),
        indent_style=tokens_raw.get("indent_style", "indent"),
        hyphenate=tokens_raw.get("hyphenate", True),
        justify=tokens_raw.get("justify", True),
        image_treatment=tokens_raw.get("image_treatment", "editorial"),
        illustration_style=tokens_raw.get("illustration_style", "clean"),
    )

    plans = []
    for p in raw.get("page_plans", []):
        plans.append(
            PagePlan(
                id=p.get("id", ""),
                page_number=p.get("page_number", 1),
                purpose=_enum(PagePurpose, p.get("purpose"), PagePurpose.CONTENT),
                layout_family=_enum(LayoutFamily, p.get("layout_family"), LayoutFamily.READING),
                content_block_ids=p.get("content_block_ids") or [],
                page_width_mm=p.get("page_width_mm", 210.0),
                page_height_mm=p.get("page_height_mm", 297.0),
                safe_area=p.get("safe_area") or {},
                margins=p.get("margins") or {},
                typography=p.get("typography") or {},
                image_briefs=p.get("image_briefs") or [],
                components=p.get("components") or [],
                density_target=p.get("density_target", 0.8),
                notes=p.get("notes", ""),
            )
        )

    return EditorialPlan(
        id=raw.get("id", "ep_local"),
        manuscript_id=manuscript.id,
        brand_profile_id=raw.get("brand_profile_id", ""),
        design_tokens=tokens,
        publication_brief=raw.get("publication_brief") or {},
        page_plans=plans,
        asset_briefs=raw.get("asset_briefs") or [],
        structure_map=raw.get("structure_map") or {},
        pagination_strategy=raw.get("pagination_strategy", "auto"),
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default="prj_16f8a7fb56f2")
    ap.add_argument("--out", default=str(REPO / "output" / "land-field-manual-12ch.pdf"))
    ap.add_argument("--bundle", default=None, help="explicit path to source_bundle dir")
    ap.add_argument("--dump-plan", default=None,
                    help="write the computed page plan as JSON, with the "
                         "estimated line weight of every planned page")
    args = ap.parse_args()

    bundle = Path(args.bundle) if args.bundle else PROJECTS / args.project / "source_bundle"
    ms_raw = json.loads((bundle / "manuscript.json").read_text())
    plan_raw = json.loads((bundle / "editorial_plan.json").read_text())

    manuscript = load_manuscript(ms_raw)
    plan = load_plan(plan_raw, manuscript)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    renderer = TypstRenderer()
    if args.dump_plan:
        pages = renderer._build_page_data(manuscript, plan, {}, None)[0]
        capacity = renderer._page_capacity_lines(plan.design_tokens)
        dump = {
            "capacity_lines": capacity,
            "pages": [
                {
                    "page": p["page_number"],
                    "layout": p["layout_family"],
                    "purpose": p["purpose"],
                    "blocks": len(p.get("blocks", [])),
                    "estimated_lines": round(
                        sum(renderer._serialized_weight(b) for b in p.get("blocks", [])), 2),
                }
                for p in pages
            ],
        }
        Path(args.dump_plan).write_text(json.dumps(dump, indent=2))
        print(f"dumped {len(pages)} planned pages to {args.dump_plan}")

    result = renderer.render_pdf(manuscript, plan, [], str(out))
    if not result.get("success"):
        print(result.get("error", "unknown render failure"), file=sys.stderr)
        return 1
    print(f"wrote {out} ({out.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
