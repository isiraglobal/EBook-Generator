from __future__ import annotations
import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import json


class ContentType(enum.Enum):
    PARAGRAPH = "paragraph"
    HEADING = "heading"
    LIST = "list"
    LIST_ITEM = "list_item"
    DEFINITION = "definition"
    QUOTATION = "quotation"
    TABLE = "table"
    MATH = "math"
    EXERCISE = "exercise"
    QUIZ = "quiz"
    WORKED_EXAMPLE = "worked_example"
    CASE_STUDY = "case_study"
    WARNING = "warning"
    REFERENCE = "reference"
    CODE = "code"
    IMAGE_INSTRUCTION = "image_instruction"
    CALLOUT = "callout"
    FOOTNOTE = "footnote"
    CITATION = "citation"
    HYPERLINK = "hyperlink"
    PAGE_BREAK = "page_break"
    SECTION_BREAK = "section_break"
    UNKNOWN = "unknown"


class SemanticRole(enum.Enum):
    TITLE = "title"
    SUBTITLE = "subtitle"
    AUTHOR = "author"
    ABSTRACT = "abstract"
    CHAPTER = "chapter"
    SECTION = "section"
    SUBSECTION = "subsection"
    BODY = "body"
    CAPTION = "caption"
    FOOTNOTE = "footnote"
    SIDEBAR = "sidebar"
    PULL_QUOTE = "pull_quote"
    CALL_OUT = "call_out"
    FIGURE = "figure"
    TABLE = "table"
    CODE = "code"
    EQUATION = "equation"
    EXERCISE = "exercise"
    SOLUTION = "solution"
    EXAMPLE = "example"
    WARNING = "warning"
    NOTE = "note"
    TIP = "tip"
    REFERENCE = "reference"
    BIBLIOGRAPHY = "bibliography"
    APPENDIX = "appendix"
    GLOSSARY = "glossary"
    INDEX = "index"
    COVER = "cover"
    TOC = "toc"
    FRONT_MATTER = "front_matter"
    BACK_MATTER = "back_matter"
    UNKNOWN = "unknown"


class PagePurpose(enum.Enum):
    COVER = "cover"
    TITLE_PAGE = "title_page"
    COPYRIGHT = "copyright"
    DEDICATION = "dedication"
    TOC = "toc"
    FOREWORD = "foreword"
    PREFACE = "preface"
    INTRODUCTION = "introduction"
    CHAPTER_OPENER = "chapter_opener"
    PART_OPENER = "part_opener"
    CONTENT = "content"
    IMAGE_LED = "image_led"
    DIAGRAM = "diagram"
    TABLE_PAGE = "table_page"
    EXERCISE = "exercise"
    WORKED_EXAMPLE = "worked_example"
    CASE_STUDY = "case_study"
    SUMMARY = "summary"
    RECAP = "recap"
    GLOSSARY = "glossary"
    REFERENCES = "references"
    APPENDIX = "appendix"
    BACK_COVER = "back_cover"
    BLANK = "blank"
    UNKNOWN = "unknown"


class LayoutFamily(enum.Enum):
    COVER = "cover"
    TITLE = "title"
    TOC = "toc"
    CHAPTER_OPENER = "chapter_opener"
    PART_OPENER = "part_opener"
    READING = "reading"
    READING_TWO_COL = "reading_two_col"
    IMAGE_LED = "image_led"
    IMAGE_FULL = "image_full"
    ASYMMETRICAL = "asymmetrical"
    DEFINITION_SIDEBAR = "definition_sidebar"
    PULL_QUOTE = "pull_quote"
    CHECKLIST = "checklist"
    PROCESS_DIAGRAM = "process_diagram"
    COMPARISON_TABLE = "comparison_table"
    CASE_STUDY = "case_study"
    EXERCISE = "exercise"
    WORKED_EXAMPLE = "worked_example"
    RECAP = "recap"
    GLOSSARY = "glossary"
    REFERENCES = "references"
    APPENDIX = "appendix"
    CLOSING = "closing"


class JobStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QASeverity(enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ContentBlock:
    id: str
    content: str
    content_type: ContentType
    semantic_role: SemanticRole
    chapter: int = 0
    section: int = 0
    subsection: int = 0
    order: int = 0
    level: int = 0
    source_ref: str = ""
    source_file: str = ""
    source_line: int = 0
    citations: list[str] = field(default_factory=list)
    hyperlinks: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    editorial_constraints: dict[str, Any] = field(default_factory=dict)
    user_instructions: str = ""
    is_generated: bool = False
    traceability: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    matter: str = "body"

    def __post_init__(self):
        if not self.id:
            self.id = f"cb_{uuid.uuid4().hex[:12]}"


@dataclass
class Manuscript:
    id: str
    title: str
    author: str = ""
    description: str = ""
    source_format: str = ""
    source_files: list[str] = field(default_factory=list)
    content_blocks: list[ContentBlock] = field(default_factory=list)
    structure: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.id:
            self.id = f"ms_{uuid.uuid4().hex[:12]}"

    def get_blocks_by_chapter(self, chapter: int) -> list[ContentBlock]:
        return [b for b in self.content_blocks if b.chapter == chapter]

    def get_blocks_by_type(self, content_type: ContentType) -> list[ContentBlock]:
        return [b for b in self.content_blocks if b.content_type == content_type]

    def total_word_count(self) -> int:
        return sum(len(b.content.split()) for b in self.content_blocks)


@dataclass
class DesignTokens:
    brand_name: str = ""
    page_width_mm: float = 210.0
    page_height_mm: float = 297.0
    margin_top_mm: float = 25.0
    margin_bottom_mm: float = 25.0
    margin_inner_mm: float = 25.0
    margin_outer_mm: float = 25.0
    columns: int = 1
    column_gutter_mm: float = 5.0
    body_font_family: str = "PT Serif"
    heading_font_family: str = "PT Sans"
    mono_font_family: str = "PT Mono"
    body_font_size_pt: float = 10.5
    heading_font_sizes: dict[int, float] = field(default_factory=lambda: {1: 18.0, 2: 13.0, 3: 11.0})
    line_height_em: float = 1.4
    paragraph_spacing_em: float = 0.75
    first_line_indent_em: float = 1.5
    colors: dict[str, str] = field(default_factory=lambda: {
        "accent": "#1d3557",
        "heading": "#1a1a1a",
        "body": "#1a1a1a",
        "muted": "#64748b",
        "background": "#ffffff",
        "sidebar_bg": "#f8f9fa",
        "table_header": "#f1f1f1",
        "table_row_alt": "#fafafa",
    })
    heading_weights: dict[int, str] = field(default_factory=lambda: {1: "bold", 2: "semibold", 3: "semibold"})
    numbered_headings: bool = True
    show_toc: bool = True
    show_header_footer: bool = True
    header_rule: bool = True
    page_num_position: str = "bottom-center"
    chapter_break: bool = False
    indent_style: str = "indent"
    hyphenate: bool = True
    justify: bool = True
    image_treatment: str = "editorial"
    illustration_style: str = "clean"


@dataclass
class BrandProfile:
    id: str
    name: str
    description: str = ""
    logo_path: str = ""
    design_tokens: DesignTokens = field(default_factory=DesignTokens)
    cover_conventions: dict[str, Any] = field(default_factory=dict)
    section_opener_conventions: dict[str, Any] = field(default_factory=dict)
    running_header_template: str = ""
    running_footer_template: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.id:
            self.id = f"bp_{uuid.uuid4().hex[:12]}"


@dataclass
class VisualReference:
    id: str
    source_url: str = ""
    source_title: str = ""
    local_path: str = ""
    screenshot_path: str = ""
    retrieval_status: str = "pending"
    license_info: str = ""
    provenance: dict[str, Any] = field(default_factory=dict)
    analysis: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    design_principles: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.id:
            self.id = f"vr_{uuid.uuid4().hex[:12]}"


@dataclass
class Asset:
    id: str
    asset_type: str
    local_path: str
    original_source: str = ""
    generation_provider: str = ""
    prompt: str = ""
    generation_metadata: dict[str, Any] = field(default_factory=dict)
    source_url: str = ""
    license: str = ""
    provenance: dict[str, Any] = field(default_factory=dict)
    width_px: int = 0
    height_px: int = 0
    dpi: int = 300
    intended_page_id: str = ""
    placement: dict[str, Any] = field(default_factory=dict)
    crop_settings: dict[str, Any] = field(default_factory=dict)
    focal_point: tuple[float, float] = (0.5, 0.5)
    aspect_ratio: float = 1.0
    caption: str = ""
    alt_text: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.id:
            self.id = f"ast_{uuid.uuid4().hex[:12]}"


@dataclass
class PagePlan:
    id: str
    page_number: int
    purpose: PagePurpose
    layout_family: LayoutFamily
    content_block_ids: list[str] = field(default_factory=list)
    page_width_mm: float = 210.0
    page_height_mm: float = 297.0
    safe_area: dict[str, float] = field(default_factory=dict)
    margins: dict[str, float] = field(default_factory=dict)
    grid: dict[str, Any] = field(default_factory=dict)
    regions: dict[str, Any] = field(default_factory=dict)
    typography: dict[str, Any] = field(default_factory=dict)
    image_briefs: list[dict[str, Any]] = field(default_factory=list)
    components: list[dict[str, Any]] = field(default_factory=list)
    header_footer: dict[str, Any] = field(default_factory=dict)
    accessibility: dict[str, Any] = field(default_factory=dict)
    validation_criteria: dict[str, Any] = field(default_factory=dict)
    density_target: float = 0.85
    notes: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"pp_{uuid.uuid4().hex[:12]}"
        if not self.safe_area:
            self.safe_area = {
                "top_mm": self.margins.get("top_mm", 25.0),
                "bottom_mm": self.margins.get("bottom_mm", 25.0),
                "left_mm": self.margins.get("left_mm", 25.0),
                "right_mm": self.margins.get("right_mm", 25.0),
            }


@dataclass
class EditorialPlan:
    id: str
    manuscript_id: str
    brand_profile_id: str
    design_tokens: DesignTokens
    publication_brief: dict[str, Any] = field(default_factory=dict)
    page_plans: list[PagePlan] = field(default_factory=list)
    asset_briefs: list[dict[str, Any]] = field(default_factory=list)
    structure_map: dict[str, Any] = field(default_factory=dict)
    pagination_strategy: str = "auto"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.id:
            self.id = f"ep_{uuid.uuid4().hex[:12]}"


@dataclass
class QAIssue:
    id: str
    page_id: str
    page_number: int
    severity: QASeverity
    category: str
    message: str
    location: dict[str, Any] = field(default_factory=dict)
    suggested_fix: str = ""
    auto_fixable: bool = False
    fix_applied: bool = False
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.id:
            self.id = f"qa_{uuid.uuid4().hex[:12]}"


@dataclass
class QAReport:
    id: str
    publication_id: str
    render_job_id: str
    total_pages: int
    issues: list[QAIssue] = field(default_factory=list)
    passed: bool = False
    score: float = 0.0
    summary: str = ""
    page_images: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.id:
            self.id = f"qar_{uuid.uuid4().hex[:12]}"

    def hard_failures(self) -> list[QAIssue]:
        return [i for i in self.issues if i.severity in (QASeverity.ERROR, QASeverity.CRITICAL)]

    def warnings(self) -> list[QAIssue]:
        return [i for i in self.issues if i.severity == QASeverity.WARNING]


@dataclass
class RenderJob:
    id: str
    project_id: str
    editorial_plan_id: str
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    current_step: str = ""
    output_pdf_path: str = ""
    page_images: list[str] = field(default_factory=list)
    qa_report_id: str = ""
    error_message: str = ""
    logs: list[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0

    def __post_init__(self):
        if not self.id:
            self.id = f"rj_{uuid.uuid4().hex[:12]}"


@dataclass
class Project:
    id: str
    name: str
    description: str = ""
    manuscript_id: str = ""
    brand_profile_id: str = ""
    editorial_plan_id: str = ""
    render_job_id: str = ""
    output_pdf_path: str = ""
    source_bundle_path: str = ""
    version: int = 1
    status: str = "draft"
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.id:
            self.id = f"prj_{uuid.uuid4().hex[:12]}"