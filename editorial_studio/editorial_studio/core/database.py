from __future__ import annotations
import enum
import json
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Generator, Optional

from editorial_studio.core.models import (
    Asset,
    BrandProfile,
    ContentBlock,
    ContentType,
    DesignTokens,
    EditorialPlan,
    Manuscript,
    PagePlan,
    PagePurpose,
    Project,
    QAIssue,
    QAReport,
    QASeverity,
    RenderJob,
    SemanticRole,
    LayoutFamily,
    VisualReference,
    JobStatus,
)


def _json_default(value: Any) -> Any:
    if isinstance(value, enum.Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    if isinstance(value, (datetime, Path)):
        return value.isoformat() if isinstance(value, datetime) else str(value)
    if isinstance(value, (set, tuple)):
        return list(value)
    return str(value)


def _json_dumps(value: Any) -> str:
    return json.dumps(value, default=_json_default)


class Database:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                self.db_path, check_same_thread=False, timeout=30.0
            )
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA foreign_keys = ON")
            self._local.conn.execute("PRAGMA journal_mode = WAL")
        return self._local.conn

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def _init_schema(self):
        with self.transaction() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    manuscript_id TEXT,
                    brand_profile_id TEXT,
                    editorial_plan_id TEXT,
                    render_job_id TEXT,
                    output_pdf_path TEXT,
                    source_bundle_path TEXT,
                    version INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'draft',
                    tags TEXT,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS manuscripts (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    author TEXT,
                    description TEXT,
                    source_format TEXT,
                    source_files TEXT,
                    content_blocks TEXT NOT NULL,
                    structure TEXT,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS brand_profiles (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    logo_path TEXT,
                    design_tokens TEXT NOT NULL,
                    cover_conventions TEXT,
                    section_opener_conventions TEXT,
                    running_header_template TEXT,
                    running_footer_template TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS visual_references (
                    id TEXT PRIMARY KEY,
                    source_url TEXT,
                    source_title TEXT,
                    local_path TEXT,
                    screenshot_path TEXT,
                    retrieval_status TEXT DEFAULT 'pending',
                    license_info TEXT,
                    provenance TEXT,
                    analysis TEXT,
                    tags TEXT,
                    design_principles TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS assets (
                    id TEXT PRIMARY KEY,
                    asset_type TEXT NOT NULL,
                    local_path TEXT NOT NULL,
                    original_source TEXT,
                    generation_provider TEXT,
                    prompt TEXT,
                    generation_metadata TEXT,
                    source_url TEXT,
                    license TEXT,
                    provenance TEXT,
                    width_px INTEGER DEFAULT 0,
                    height_px INTEGER DEFAULT 0,
                    dpi INTEGER DEFAULT 300,
                    intended_page_id TEXT,
                    placement TEXT,
                    crop_settings TEXT,
                    focal_point_x REAL DEFAULT 0.5,
                    focal_point_y REAL DEFAULT 0.5,
                    aspect_ratio REAL DEFAULT 1.0,
                    caption TEXT,
                    alt_text TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS editorial_plans (
                    id TEXT PRIMARY KEY,
                    manuscript_id TEXT NOT NULL,
                    brand_profile_id TEXT NOT NULL,
                    design_tokens TEXT NOT NULL,
                    publication_brief TEXT,
                    page_plans TEXT NOT NULL,
                    asset_briefs TEXT,
                    structure_map TEXT,
                    pagination_strategy TEXT DEFAULT 'auto',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (manuscript_id) REFERENCES manuscripts(id),
                    FOREIGN KEY (brand_profile_id) REFERENCES brand_profiles(id)
                );

                CREATE TABLE IF NOT EXISTS render_jobs (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    editorial_plan_id TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    progress REAL DEFAULT 0.0,
                    current_step TEXT,
                    output_pdf_path TEXT,
                    page_images TEXT,
                    qa_report_id TEXT,
                    error_message TEXT,
                    logs TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    retry_count INTEGER DEFAULT 0,
                    FOREIGN KEY (project_id) REFERENCES projects(id),
                    FOREIGN KEY (editorial_plan_id) REFERENCES editorial_plans(id)
                );

                CREATE TABLE IF NOT EXISTS qa_reports (
                    id TEXT PRIMARY KEY,
                    publication_id TEXT NOT NULL,
                    render_job_id TEXT NOT NULL,
                    total_pages INTEGER DEFAULT 0,
                    issues TEXT NOT NULL,
                    passed BOOLEAN DEFAULT 0,
                    score REAL DEFAULT 0.0,
                    summary TEXT,
                    page_images TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
                CREATE INDEX IF NOT EXISTS idx_render_jobs_project ON render_jobs(project_id);
                CREATE INDEX IF NOT EXISTS idx_editorial_plans_manuscript ON editorial_plans(manuscript_id);
                CREATE INDEX IF NOT EXISTS idx_assets_page ON assets(intended_page_id);
            """)

    # Project operations
    def create_project(self, project: Project) -> Project:
        with self.transaction() as conn:
            conn.execute(
                """INSERT INTO projects VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    project.id,
                    project.name,
                    project.description,
                    project.manuscript_id,
                    project.brand_profile_id,
                    project.editorial_plan_id,
                    project.render_job_id,
                    project.output_pdf_path,
                    project.source_bundle_path,
                    project.version,
                    project.status,
                    _json_dumps(project.tags),
                    _json_dumps(project.metadata),
                    project.created_at.isoformat(),
                    project.updated_at.isoformat(),
                ),
            )
        return project

    def get_project(self, project_id: str) -> Optional[Project]:
        with self.transaction() as conn:
            row = conn.execute(
                "SELECT * FROM projects WHERE id = ?", (project_id,)
            ).fetchone()
        if row:
            return self._row_to_project(row)
        return None

    def update_project(self, project: Project) -> Project:
        project.updated_at = datetime.now()
        with self.transaction() as conn:
            conn.execute(
                """UPDATE projects SET name=?, description=?, manuscript_id=?, brand_profile_id=?,
                   editorial_plan_id=?, render_job_id=?, output_pdf_path=?, source_bundle_path=?,
                   version=?, status=?, tags=?, metadata=?, updated_at=? WHERE id=?""",
                (
                    project.name,
                    project.description,
                    project.manuscript_id,
                    project.brand_profile_id,
                    project.editorial_plan_id,
                    project.render_job_id,
                    project.output_pdf_path,
                    project.source_bundle_path,
                    project.version,
                    project.status,
                    _json_dumps(project.tags),
                    _json_dumps(project.metadata),
                    project.updated_at.isoformat(),
                    project.id,
                ),
            )
        return project

    def list_projects(self, status: Optional[str] = None) -> list[Project]:
        with self.transaction() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM projects WHERE status = ? ORDER BY updated_at DESC",
                    (status,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM projects ORDER BY updated_at DESC"
                ).fetchall()
        return [self._row_to_project(row) for row in rows]

    def _row_to_project(self, row: sqlite3.Row) -> Project:
        return Project(
            id=row["id"],
            name=row["name"],
            description=row["description"] or "",
            manuscript_id=row["manuscript_id"] or "",
            brand_profile_id=row["brand_profile_id"] or "",
            editorial_plan_id=row["editorial_plan_id"] or "",
            render_job_id=row["render_job_id"] or "",
            output_pdf_path=row["output_pdf_path"] or "",
            source_bundle_path=row["source_bundle_path"] or "",
            version=row["version"],
            status=row["status"],
            tags=json.loads(row["tags"] or "[]"),
            metadata=json.loads(row["metadata"] or "{}"),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    # Manuscript operations
    def create_manuscript(self, manuscript: Manuscript) -> Manuscript:
        with self.transaction() as conn:
            conn.execute(
                """INSERT INTO manuscripts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    manuscript.id,
                    manuscript.title,
                    manuscript.author,
                    manuscript.description,
                    manuscript.source_format,
                    _json_dumps(manuscript.source_files),
                    _json_dumps([self._block_to_dict(b) for b in manuscript.content_blocks]),
                    _json_dumps(manuscript.structure),
                    _json_dumps(manuscript.metadata),
                    manuscript.created_at.isoformat(),
                    manuscript.updated_at.isoformat(),
                ),
            )
        return manuscript

    def get_manuscript(self, manuscript_id: str) -> Optional[Manuscript]:
        with self.transaction() as conn:
            row = conn.execute(
                "SELECT * FROM manuscripts WHERE id = ?", (manuscript_id,)
            ).fetchone()
        if row:
            return self._row_to_manuscript(row)
        return None

    def update_manuscript(self, manuscript: Manuscript) -> Manuscript:
        manuscript.updated_at = datetime.now()
        with self.transaction() as conn:
            conn.execute(
                """UPDATE manuscripts SET title=?, author=?, description=?, source_format=?,
                   source_files=?, content_blocks=?, structure=?, metadata=?, updated_at=?
                   WHERE id=?""",
                (
                    manuscript.title,
                    manuscript.author,
                    manuscript.description,
                    manuscript.source_format,
                    _json_dumps(manuscript.source_files),
                    _json_dumps([self._block_to_dict(b) for b in manuscript.content_blocks]),
                    _json_dumps(manuscript.structure),
                    _json_dumps(manuscript.metadata),
                    manuscript.updated_at.isoformat(),
                    manuscript.id,
                ),
            )
        return manuscript

    def _block_to_dict(self, block: ContentBlock) -> dict:
        return {
            "matter": block.matter,
            "id": block.id,
            "content": block.content,
            "content_type": block.content_type.value,
            "semantic_role": block.semantic_role.value,
            "chapter": block.chapter,
            "section": block.section,
            "subsection": block.subsection,
            "order": block.order,
            "level": block.level,
            "source_ref": block.source_ref,
            "source_file": block.source_file,
            "source_line": block.source_line,
            "citations": block.citations,
            "hyperlinks": block.hyperlinks,
            "references": block.references,
            "editorial_constraints": block.editorial_constraints,
            "user_instructions": block.user_instructions,
            "is_generated": block.is_generated,
            "traceability": block.traceability,
            "metadata": block.metadata,
        }

    def _dict_to_block(self, data: dict) -> ContentBlock:
        return ContentBlock(
            matter=data.get("matter", "body"),
            id=data["id"],
            content=data["content"],
            content_type=ContentType(data["content_type"]),
            semantic_role=SemanticRole(data["semantic_role"]),
            chapter=data.get("chapter", 0),
            section=data.get("section", 0),
            subsection=data.get("subsection", 0),
            order=data.get("order", 0),
            level=data.get("level", 0),
            source_ref=data.get("source_ref", ""),
            source_file=data.get("source_file", ""),
            source_line=data.get("source_line", 0),
            citations=data.get("citations", []),
            hyperlinks=data.get("hyperlinks", []),
            references=data.get("references", []),
            editorial_constraints=data.get("editorial_constraints", {}),
            user_instructions=data.get("user_instructions", ""),
            is_generated=data.get("is_generated", False),
            traceability=data.get("traceability", {}),
            metadata=data.get("metadata", {}),
        )

    def _row_to_manuscript(self, row: sqlite3.Row) -> Manuscript:
        blocks_data = json.loads(row["content_blocks"])
        return Manuscript(
            id=row["id"],
            title=row["title"],
            author=row["author"] or "",
            description=row["description"] or "",
            source_format=row["source_format"] or "",
            source_files=json.loads(row["source_files"] or "[]"),
            content_blocks=[self._dict_to_block(b) for b in blocks_data],
            structure=json.loads(row["structure"] or "{}"),
            metadata=json.loads(row["metadata"] or "{}"),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    # Brand Profile operations
    def create_brand_profile(self, profile: BrandProfile) -> BrandProfile:
        with self.transaction() as conn:
            conn.execute(
                """INSERT INTO brand_profiles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    profile.id,
                    profile.name,
                    profile.description,
                    profile.logo_path,
                    _json_dumps(self._tokens_to_dict(profile.design_tokens)),
                    _json_dumps(profile.cover_conventions),
                    _json_dumps(profile.section_opener_conventions),
                    profile.running_header_template,
                    profile.running_footer_template,
                    profile.created_at.isoformat(),
                    profile.updated_at.isoformat(),
                ),
            )
        return profile

    def upsert_brand_profile(self, profile: BrandProfile) -> BrandProfile:
        profile.updated_at = datetime.now()
        with self.transaction() as conn:
            conn.execute(
                """INSERT INTO brand_profiles
                   (id, name, description, logo_path, design_tokens, cover_conventions,
                    section_opener_conventions, running_header_template, running_footer_template,
                    created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET
                     name=excluded.name,
                     description=excluded.description,
                     logo_path=excluded.logo_path,
                     design_tokens=excluded.design_tokens,
                     cover_conventions=excluded.cover_conventions,
                     section_opener_conventions=excluded.section_opener_conventions,
                     running_header_template=excluded.running_header_template,
                     running_footer_template=excluded.running_footer_template,
                     updated_at=excluded.updated_at""",
                (
                    profile.id,
                    profile.name,
                    profile.description,
                    profile.logo_path,
                    _json_dumps(self._tokens_to_dict(profile.design_tokens)),
                    _json_dumps(profile.cover_conventions),
                    _json_dumps(profile.section_opener_conventions),
                    profile.running_header_template,
                    profile.running_footer_template,
                    profile.created_at.isoformat(),
                    profile.updated_at.isoformat(),
                ),
            )
        return profile

    def get_brand_profile(self, profile_id: str) -> Optional[BrandProfile]:
        with self.transaction() as conn:
            row = conn.execute(
                "SELECT * FROM brand_profiles WHERE id = ?", (profile_id,)
            ).fetchone()
        if row:
            return self._row_to_brand_profile(row)
        return None

    def list_brand_profiles(self) -> list[BrandProfile]:
        with self.transaction() as conn:
            rows = conn.execute(
                "SELECT * FROM brand_profiles ORDER BY name"
            ).fetchall()
        return [self._row_to_brand_profile(row) for row in rows]

    def _tokens_to_dict(self, tokens: DesignTokens) -> dict:
        return {
            "brand_name": tokens.brand_name,
            "page_width_mm": tokens.page_width_mm,
            "page_height_mm": tokens.page_height_mm,
            "margin_top_mm": tokens.margin_top_mm,
            "margin_bottom_mm": tokens.margin_bottom_mm,
            "margin_inner_mm": tokens.margin_inner_mm,
            "margin_outer_mm": tokens.margin_outer_mm,
            "columns": tokens.columns,
            "column_gutter_mm": tokens.column_gutter_mm,
            "body_font_family": tokens.body_font_family,
            "heading_font_family": tokens.heading_font_family,
            "mono_font_family": tokens.mono_font_family,
            "body_font_size_pt": tokens.body_font_size_pt,
            "heading_font_sizes": tokens.heading_font_sizes,
            "line_height_em": tokens.line_height_em,
            "paragraph_spacing_em": tokens.paragraph_spacing_em,
            "first_line_indent_em": tokens.first_line_indent_em,
            "colors": tokens.colors,
            "heading_weights": tokens.heading_weights,
            "numbered_headings": tokens.numbered_headings,
            "show_toc": tokens.show_toc,
            "show_header_footer": tokens.show_header_footer,
            "header_rule": tokens.header_rule,
            "page_num_position": tokens.page_num_position,
            "chapter_break": tokens.chapter_break,
            "indent_style": tokens.indent_style,
            "hyphenate": tokens.hyphenate,
            "justify": tokens.justify,
            "image_treatment": tokens.image_treatment,
            "illustration_style": tokens.illustration_style,
        }

    def _dict_to_tokens(self, data: dict) -> DesignTokens:
        return DesignTokens(
            brand_name=data.get("brand_name", ""),
            page_width_mm=data.get("page_width_mm", 210.0),
            page_height_mm=data.get("page_height_mm", 297.0),
            margin_top_mm=data.get("margin_top_mm", 25.0),
            margin_bottom_mm=data.get("margin_bottom_mm", 25.0),
            margin_inner_mm=data.get("margin_inner_mm", 25.0),
            margin_outer_mm=data.get("margin_outer_mm", 25.0),
            columns=data.get("columns", 1),
            column_gutter_mm=data.get("column_gutter_mm", 5.0),
            body_font_family=data.get("body_font_family", "Source Serif 4"),
            heading_font_family=data.get("heading_font_family", "Source Sans 3"),
            mono_font_family=data.get("mono_font_family", "Source Code Pro"),
            body_font_size_pt=data.get("body_font_size_pt", 10.5),
            heading_font_sizes=data.get("heading_font_sizes", {1: 18.0, 2: 13.0, 3: 11.0}),
            line_height_em=data.get("line_height_em", 1.4),
            paragraph_spacing_em=data.get("paragraph_spacing_em", 0.75),
            first_line_indent_em=data.get("first_line_indent_em", 1.5),
            colors=data.get("colors", {}),
            heading_weights=data.get("heading_weights", {1: "bold", 2: "semibold", 3: "semibold"}),
            numbered_headings=data.get("numbered_headings", True),
            show_toc=data.get("show_toc", True),
            show_header_footer=data.get("show_header_footer", True),
            header_rule=data.get("header_rule", True),
            page_num_position=data.get("page_num_position", "bottom-center"),
            chapter_break=data.get("chapter_break", False),
            indent_style=data.get("indent_style", "indent"),
            hyphenate=data.get("hyphenate", True),
            justify=data.get("justify", True),
            image_treatment=data.get("image_treatment", "editorial"),
            illustration_style=data.get("illustration_style", "clean"),
        )

    def _row_to_brand_profile(self, row: sqlite3.Row) -> BrandProfile:
        return BrandProfile(
            id=row["id"],
            name=row["name"],
            description=row["description"] or "",
            logo_path=row["logo_path"] or "",
            design_tokens=self._dict_to_tokens(json.loads(row["design_tokens"])),
            cover_conventions=json.loads(row["cover_conventions"] or "{}"),
            section_opener_conventions=json.loads(row["section_opener_conventions"] or "{}"),
            running_header_template=row["running_header_template"] or "",
            running_footer_template=row["running_footer_template"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    # Visual Reference operations
    def create_visual_reference(self, ref: VisualReference) -> VisualReference:
        with self.transaction() as conn:
            conn.execute(
                """INSERT INTO visual_references VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    ref.id,
                    ref.source_url,
                    ref.source_title,
                    ref.local_path,
                    ref.screenshot_path,
                    ref.retrieval_status,
                    ref.license_info,
                    _json_dumps(ref.provenance),
                    _json_dumps(ref.analysis),
                    _json_dumps(ref.tags),
                    _json_dumps(ref.design_principles),
                    ref.created_at.isoformat(),
                ),
            )
        return ref

    def get_visual_reference(self, ref_id: str) -> Optional[VisualReference]:
        with self.transaction() as conn:
            row = conn.execute(
                "SELECT * FROM visual_references WHERE id = ?", (ref_id,)
            ).fetchone()
        if row:
            return self._row_to_visual_reference(row)
        return None

    def list_visual_references(self, tags: Optional[list[str]] = None) -> list[VisualReference]:
        with self.transaction() as conn:
            if tags:
                placeholders = ",".join("?" * len(tags))
                rows = conn.execute(
                    f"SELECT * FROM visual_references WHERE tags LIKE ? ORDER BY created_at DESC",
                    (f"%{tags[0]}%",),  # Simplified for now
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM visual_references ORDER BY created_at DESC"
                ).fetchall()
        return [self._row_to_visual_reference(row) for row in rows]

    def _row_to_visual_reference(self, row: sqlite3.Row) -> VisualReference:
        return VisualReference(
            id=row["id"],
            source_url=row["source_url"] or "",
            source_title=row["source_title"] or "",
            local_path=row["local_path"] or "",
            screenshot_path=row["screenshot_path"] or "",
            retrieval_status=row["retrieval_status"],
            license_info=row["license_info"] or "",
            provenance=json.loads(row["provenance"] or "{}"),
            analysis=json.loads(row["analysis"] or "{}"),
            tags=json.loads(row["tags"] or "[]"),
            design_principles=json.loads(row["design_principles"] or "[]"),
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    # Asset operations
    def create_asset(self, asset: Asset) -> Asset:
        with self.transaction() as conn:
            conn.execute(
                """INSERT INTO assets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    asset.id,
                    asset.asset_type,
                    asset.local_path,
                    asset.original_source,
                    asset.generation_provider,
                    asset.prompt,
                    _json_dumps(asset.generation_metadata),
                    asset.source_url,
                    asset.license,
                    _json_dumps(asset.provenance),
                    asset.width_px,
                    asset.height_px,
                    asset.dpi,
                    asset.intended_page_id,
                    _json_dumps(asset.placement),
                    _json_dumps(asset.crop_settings),
                    asset.focal_point[0],
                    asset.focal_point[1],
                    asset.aspect_ratio,
                    asset.caption,
                    asset.alt_text,
                    asset.created_at.isoformat(),
                ),
            )
        return asset

    def get_asset(self, asset_id: str) -> Optional[Asset]:
        with self.transaction() as conn:
            row = conn.execute(
                "SELECT * FROM assets WHERE id = ?", (asset_id,)
            ).fetchone()
        if row:
            return self._row_to_asset(row)
        return None

    def get_assets_for_page(self, page_id: str) -> list[Asset]:
        with self.transaction() as conn:
            rows = conn.execute(
                "SELECT * FROM assets WHERE intended_page_id = ?", (page_id,)
            ).fetchall()
        return [self._row_to_asset(row) for row in rows]

    def _row_to_asset(self, row: sqlite3.Row) -> Asset:
        return Asset(
            id=row["id"],
            asset_type=row["asset_type"],
            local_path=row["local_path"],
            original_source=row["original_source"] or "",
            generation_provider=row["generation_provider"] or "",
            prompt=row["prompt"] or "",
            generation_metadata=json.loads(row["generation_metadata"] or "{}"),
            source_url=row["source_url"] or "",
            license=row["license"] or "",
            provenance=json.loads(row["provenance"] or "{}"),
            width_px=row["width_px"],
            height_px=row["height_px"],
            dpi=row["dpi"],
            intended_page_id=row["intended_page_id"] or "",
            placement=json.loads(row["placement"] or "{}"),
            crop_settings=json.loads(row["crop_settings"] or "{}"),
            focal_point=(row["focal_point_x"], row["focal_point_y"]),
            aspect_ratio=row["aspect_ratio"],
            caption=row["caption"] or "",
            alt_text=row["alt_text"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    # Editorial Plan operations
    def create_editorial_plan(self, plan: EditorialPlan) -> EditorialPlan:
        with self.transaction() as conn:
            conn.execute(
                """INSERT INTO editorial_plans VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    plan.id,
                    plan.manuscript_id,
                    plan.brand_profile_id,
                    _json_dumps(self._tokens_to_dict(plan.design_tokens)),
                    _json_dumps(plan.publication_brief),
                    _json_dumps([self._page_plan_to_dict(p) for p in plan.page_plans]),
                    _json_dumps(plan.asset_briefs),
                    _json_dumps(plan.structure_map),
                    plan.pagination_strategy,
                    plan.created_at.isoformat(),
                    plan.updated_at.isoformat(),
                ),
            )
        return plan

    def get_editorial_plan(self, plan_id: str) -> Optional[EditorialPlan]:
        with self.transaction() as conn:
            row = conn.execute(
                "SELECT * FROM editorial_plans WHERE id = ?", (plan_id,)
            ).fetchone()
        if row:
            return self._row_to_editorial_plan(row)
        return None

    def update_editorial_plan(self, plan: EditorialPlan) -> EditorialPlan:
        plan.updated_at = datetime.now()
        with self.transaction() as conn:
            conn.execute(
                """UPDATE editorial_plans SET brand_profile_id=?, design_tokens=?, publication_brief=?, page_plans=?, asset_briefs=?,
                   structure_map=?, pagination_strategy=?, updated_at=? WHERE id=?""",
                (
                    plan.brand_profile_id,
                    _json_dumps(self._tokens_to_dict(plan.design_tokens)),
                    _json_dumps(plan.publication_brief),
                    _json_dumps([self._page_plan_to_dict(p) for p in plan.page_plans]),
                    _json_dumps(plan.asset_briefs),
                    _json_dumps(plan.structure_map),
                    plan.pagination_strategy,
                    plan.updated_at.isoformat(),
                    plan.id,
                ),
            )
        return plan

    def _page_plan_to_dict(self, page: PagePlan) -> dict:
        return {
            "id": page.id,
            "page_number": page.page_number,
            "purpose": page.purpose.value,
            "layout_family": page.layout_family.value,
            "content_block_ids": page.content_block_ids,
            "page_width_mm": page.page_width_mm,
            "page_height_mm": page.page_height_mm,
            "safe_area": page.safe_area,
            "margins": page.margins,
            "grid": page.grid,
            "regions": page.regions,
            "typography": page.typography,
            "image_briefs": page.image_briefs,
            "components": page.components,
            "header_footer": page.header_footer,
            "accessibility": page.accessibility,
            "validation_criteria": page.validation_criteria,
            "density_target": page.density_target,
            "notes": page.notes,
        }

    def _dict_to_page_plan(self, data: dict) -> PagePlan:
        return PagePlan(
            id=data["id"],
            page_number=data["page_number"],
            purpose=PagePurpose(data["purpose"]),
            layout_family=LayoutFamily(data["layout_family"]),
            content_block_ids=data.get("content_block_ids", []),
            page_width_mm=data.get("page_width_mm", 210.0),
            page_height_mm=data.get("page_height_mm", 297.0),
            safe_area=data.get("safe_area", {}),
            margins=data.get("margins", {}),
            grid=data.get("grid", {}),
            regions=data.get("regions", {}),
            typography=data.get("typography", {}),
            image_briefs=data.get("image_briefs", []),
            components=data.get("components", []),
            header_footer=data.get("header_footer", {}),
            accessibility=data.get("accessibility", {}),
            validation_criteria=data.get("validation_criteria", {}),
            density_target=data.get("density_target", 0.85),
            notes=data.get("notes", ""),
        )

    def _row_to_editorial_plan(self, row: sqlite3.Row) -> EditorialPlan:
        return EditorialPlan(
            id=row["id"],
            manuscript_id=row["manuscript_id"],
            brand_profile_id=row["brand_profile_id"],
            design_tokens=self._dict_to_tokens(json.loads(row["design_tokens"])),
            publication_brief=json.loads(row["publication_brief"] or "{}"),
            page_plans=[self._dict_to_page_plan(p) for p in json.loads(row["page_plans"] or "[]")],
            asset_briefs=json.loads(row["asset_briefs"] or "[]"),
            structure_map=json.loads(row["structure_map"] or "{}"),
            pagination_strategy=row["pagination_strategy"] or "auto",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    # Render Job operations
    def create_render_job(self, job: RenderJob) -> RenderJob:
        with self.transaction() as conn:
            conn.execute(
                """INSERT INTO render_jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    job.id,
                    job.project_id,
                    job.editorial_plan_id,
                    job.status.value,
                    job.progress,
                    job.current_step,
                    job.output_pdf_path,
                    _json_dumps(job.page_images),
                    job.qa_report_id,
                    job.error_message,
                    _json_dumps(job.logs),
                    job.started_at.isoformat() if job.started_at else None,
                    job.completed_at.isoformat() if job.completed_at else None,
                    job.retry_count,
                ),
            )
        return job

    def get_render_job(self, job_id: str) -> Optional[RenderJob]:
        with self.transaction() as conn:
            row = conn.execute(
                "SELECT * FROM render_jobs WHERE id = ?", (job_id,)
            ).fetchone()
        if row:
            return self._row_to_render_job(row)
        return None

    def update_render_job(self, job: RenderJob) -> RenderJob:
        with self.transaction() as conn:
            conn.execute(
                """UPDATE render_jobs SET status=?, progress=?, current_step=?, output_pdf_path=?,
                   page_images=?, qa_report_id=?, error_message=?, logs=?, started_at=?, completed_at=?, retry_count=?
                   WHERE id=?""",
                (
                    job.status.value,
                    job.progress,
                    job.current_step,
                    job.output_pdf_path,
                    _json_dumps(job.page_images),
                    job.qa_report_id,
                    job.error_message,
                    _json_dumps(job.logs),
                    job.started_at.isoformat() if job.started_at else None,
                    job.completed_at.isoformat() if job.completed_at else None,
                    job.retry_count,
                    job.id,
                ),
            )
        return job

    def _row_to_render_job(self, row: sqlite3.Row) -> RenderJob:
        return RenderJob(
            id=row["id"],
            project_id=row["project_id"],
            editorial_plan_id=row["editorial_plan_id"],
            status=JobStatus(row["status"]),
            progress=row["progress"],
            current_step=row["current_step"] or "",
            output_pdf_path=row["output_pdf_path"] or "",
            page_images=json.loads(row["page_images"] or "[]"),
            qa_report_id=row["qa_report_id"] or "",
            error_message=row["error_message"] or "",
            logs=json.loads(row["logs"] or "[]"),
            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            retry_count=row["retry_count"],
        )

    # QA Report operations
    def create_qa_report(self, report: QAReport) -> QAReport:
        with self.transaction() as conn:
            conn.execute(
                """INSERT INTO qa_reports VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    report.id,
                    report.publication_id,
                    report.render_job_id,
                    report.total_pages,
                    _json_dumps([self._issue_to_dict(i) for i in report.issues]),
                    report.passed,
                    report.score,
                    report.summary,
                    _json_dumps(report.page_images),
                    report.created_at.isoformat(),
                ),
            )
        return report

    def get_qa_report(self, report_id: str) -> Optional[QAReport]:
        with self.transaction() as conn:
            row = conn.execute(
                "SELECT * FROM qa_reports WHERE id = ?", (report_id,)
            ).fetchone()
        if row:
            return self._row_to_qa_report(row)
        return None

    def _issue_to_dict(self, issue: QAIssue) -> dict:
        return {
            "id": issue.id,
            "page_id": issue.page_id,
            "page_number": issue.page_number,
            "severity": issue.severity.value,
            "category": issue.category,
            "message": issue.message,
            "location": issue.location,
            "suggested_fix": issue.suggested_fix,
            "auto_fixable": issue.auto_fixable,
            "fix_applied": issue.fix_applied,
            "created_at": issue.created_at.isoformat(),
        }

    def _dict_to_issue(self, data: dict) -> QAIssue:
        return QAIssue(
            id=data["id"],
            page_id=data["page_id"],
            page_number=data["page_number"],
            severity=QASeverity(data["severity"]),
            category=data["category"],
            message=data["message"],
            location=data.get("location", {}),
            suggested_fix=data.get("suggested_fix", ""),
            auto_fixable=data.get("auto_fixable", False),
            fix_applied=data.get("fix_applied", False),
            created_at=datetime.fromisoformat(data["created_at"]),
        )

    def _row_to_qa_report(self, row: sqlite3.Row) -> QAReport:
        return QAReport(
            id=row["id"],
            publication_id=row["publication_id"],
            render_job_id=row["render_job_id"],
            total_pages=row["total_pages"],
            issues=[self._dict_to_issue(i) for i in json.loads(row["issues"] or "[]")],
            passed=bool(row["passed"]),
            score=row["score"],
            summary=row["summary"] or "",
            page_images=json.loads(row["page_images"] or "[]"),
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def close(self):
        if hasattr(self._local, "conn") and self._local.conn:
            self._local.conn.close()
            self._local.conn = None


_db_instance: Optional[Database] = None


def get_database(config_path: str = "config.yaml") -> Database:
    global _db_instance
    if _db_instance is None:
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)
        db_path = config["storage"]["database_path"]
        _db_instance = Database(db_path)
    return _db_instance