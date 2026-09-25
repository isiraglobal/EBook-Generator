from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from enum import Enum


class LayoutFamily(str, Enum):
    """All layout families for the editorial layout library."""

    # Front matter
    COVER = "cover"
    HALF_TITLE = "half_title"
    TITLE_PAGE = "title_page"
    COPYRIGHT = "copyright"
    DEDICATION = "dedication"
    AUTHOR_PAGE = "author_page"
    PREFACE = "preface"
    ACKNOWLEDGMENTS = "acknowledgments"
    TOC = "toc"
    LIST_OF_FIGURES = "list_of_figures"
    LIST_OF_TABLES = "list_of_tables"

    # Part/Chapter openers
    PART_OPENER = "part_opener"
    CHAPTER_OPENER = "chapter_opener"
    CHAPTER_OPENER_WITH_IMAGE = "chapter_opener_with_image"

    # Main content - Reading layouts
    READING = "reading"
    READING_TWO_COL = "reading_two_col"
    READING_WITH_SIDEBAR = "reading_with_sidebar"
    READING_WITH_MARGINALIA = "reading_with_marginalia"

    # Image-led layouts
    IMAGE_LED = "image_led"
    IMAGE_FULL = "image_full"
    IMAGE_HALF = "image_half"
    IMAGE_WITH_CAPTION = "image_with_caption"
    IMAGE_GALLERY = "image_gallery"
    IMAGE_COMPARISON = "image_comparison"

    # Asymmetric/Editorial layouts
    ASYMMETRICAL = "asymmetrical"
    ASYMMETRICAL_IMAGE_LEFT = "asymmetrical_image_left"
    ASYMMETRICAL_IMAGE_RIGHT = "asymmetrical_image_right"
    MAGAZINE_SPREAD = "magazine_spread"

    # Specialized content layouts
    DEFINITION_SIDEBAR = "definition_sidebar"
    PULL_QUOTE = "pull_quote"
    PULL_QUOTE_CENTERED = "pull_quote_centered"
    PULL_QUOTE_MARGINAL = "pull_quote_marginal"
    CALLOUT_BOX = "callout_box"
    SIDEBAR = "sidebar"
    MARGINAL_NOTE = "marginal_note"

    # Lists and procedures
    CHECKLIST = "checklist"
    CHECKLIST_WITH_ICONS = "checklist_with_icons"
    PROCEDURAL_STEPS = "procedural_steps"
    NUMBERED_PROCEDURE = "numbered_procedure"
    DECISION_TREE = "decision_tree"

    # Tables and data
    DATA_TABLE = "data_table"
    DATA_TABLE_STRIPED = "data_table_striped"
    COMPARISON_TABLE = "comparison_table"
    FINANCIAL_TABLE = "financial_table"
    SPECIFICATION_TABLE = "specification_table"

    # Code and technical
    CODE_BLOCK = "code_block"
    CODE_WITH_LINE_NUMBERS = "code_with_line_numbers"
    CODE_WITH_CALLOUTS = "code_with_callouts"
    TERMINAL_OUTPUT = "terminal_output"

    # Diagrams and technical illustrations
    PROCESS_DIAGRAM = "process_diagram"
    FLOWCHART = "flowchart"
    ARCHITECTURE_DIAGRAM = "architecture_diagram"
    NETWORK_DIAGRAM = "network_diagram"
    SEQUENCE_DIAGRAM = "sequence_diagram"
    COMPONENT_DIAGRAM = "component_diagram"

    # Maps and geographic
    MAP_FULL = "map_full"
    MAP_INSET = "map_inset"
    MAP_ANNOTATED = "map_annotated"
    LOCATION_MAP = "location_map"

    # Case studies and examples
    CASE_STUDY = "case_study"
    CASE_STUDY_WITH_SIDEBAR = "case_study_with_sidebar"
    WORKED_EXAMPLE = "worked_example"
    WORKED_EXAMPLE_STEPPED = "worked_example_stepped"

    # Exercises and learning
    EXERCISE = "exercise"
    EXERCISE_WITH_SOLUTION = "exercise_with_solution"
    QUIZ = "quiz"
    PRACTICE_PROBLEM = "practice_problem"
    WORKSHEET = "worksheet"

    # Chapter recaps and summaries
    RECAP = "recap"
    KEY_TAKEAWAYS = "key_takeaways"
    CHAPTER_SUMMARY = "chapter_summary"
    LEARNING_OBJECTIVES_REVIEW = "learning_objectives_review"

    # Back matter
    GLOSSARY = "glossary"
    GLOSSARY_TWO_COL = "glossary_two_col"
    REFERENCES = "references"
    BIBLIOGRAPHY = "bibliography"
    APPENDIX = "appendix"
    APPENDIX_WITH_TABLE = "appendix_with_table"
    INDEX = "index"
    ABOUT_AUTHOR = "about_author"
    AUTHOR_PHOTO = "author_photo"
    PUBLISHER_PAGE = "publisher_page"
    COLOPHON = "colophon"
    BACK_COVER = "back_cover"

    # Special
    BLANK = "blank"
    SECTION_DIVIDER = "section_divider"
    EPIGRAPH = "epigraph"


@dataclass
class LayoutSpec:
    """Specification for a layout family."""
    family: LayoutFamily
    name: str
    description: str
    content_types: list[str] = field(default_factory=list)
    typical_elements: list[str] = field(default_factory=list)
    best_for: list[str] = field(default_factory=list)
    min_content_density: float = 0.3
    max_content_density: float = 0.9
    requires_images: bool = False
    supports_two_column: bool = False
    supports_bleed: bool = False
    template_file: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)


# Complete layout library specifications
LAYOUT_LIBRARY: dict[LayoutFamily, LayoutSpec] = {
    LayoutFamily.COVER: LayoutSpec(
        family=LayoutFamily.COVER,
        name="Cover",
        description="Full-bleed cover with title, subtitle, author, and brand identity",
        content_types=["title", "subtitle", "author", "brand_mark", "ornament"],
        typical_elements=["title", "subtitle", "author", "publisher_logo", "cover_image", "accent_line"],
        best_for=["First impression", "Brand identity", "Retail display"],
        min_content_density=0.15,
        max_content_density=0.35,
        requires_images=True,
        supports_bleed=True,
        template_file="cover.typ",
        parameters={"background": "image_or_color", "accent_line": True, "title_style": "display_serif"},
    ),

    LayoutFamily.HALF_TITLE: LayoutSpec(
        family=LayoutFamily.HALF_TITLE,
        name="Half Title",
        description="Minimal page with just the book title",
        content_types=["title"],
        typical_elements=["title"],
        best_for=["Traditional front matter"],
        min_content_density=0.1,
        max_content_density=0.2,
        template_file="half_title.typ",
    ),

    LayoutFamily.TITLE_PAGE: LayoutSpec(
        family=LayoutFamily.TITLE_PAGE,
        name="Title Page",
        description="Full title page with title, subtitle, author, publisher",
        content_types=["title", "subtitle", "author", "publisher", "publisher_location"],
        typical_elements=["title", "subtitle", "author", "publisher_logo", "publisher_location", "ornament"],
        best_for=["Formal title presentation"],
        min_content_density=0.2,
        max_content_density=0.4,
        template_file="title_page.typ",
    ),

    LayoutFamily.COPYRIGHT: LayoutSpec(
        family=LayoutFamily.COPYRIGHT,
        name="Copyright Page",
        description="Legal notices, ISBN, edition, credits",
        content_types=["copyright_notice", "isbn", "edition", "credits", "disclaimer"],
        typical_elements=["copyright_symbol", "year", "author", "publisher", "isbn", "credits", "disclaimer"],
        best_for=["Legal compliance"],
        min_content_density=0.3,
        max_content_density=0.5,
        template_file="copyright.typ",
    ),

    LayoutFamily.TOC: LayoutSpec(
        family=LayoutFamily.TOC,
        name="Table of Contents",
        description="Hierarchical listing of chapters and sections with page numbers",
        content_types=["chapter_entries", "section_entries", "page_numbers"],
        typical_elements=["toc_title", "chapter_list", "section_list", "page_numbers", "leaders"],
        best_for=["Navigation", "Overview"],
        min_content_density=0.5,
        max_content_density=0.8,
        template_file="toc.typ",
    ),

    LayoutFamily.CHAPTER_OPENER: LayoutSpec(
        family=LayoutFamily.CHAPTER_OPENER,
        name="Chapter Opener",
        description="Distinctive chapter start with number, title, and optional epigraph",
        content_types=["chapter_number", "chapter_title", "epigraph", "learning_objectives"],
        typical_elements=["chapter_label", "chapter_number", "chapter_title", "epigraph", "decorative_rule", "learning_objectives"],
        best_for=["Chapter starts", "Orientation"],
        min_content_density=0.25,
        max_content_density=0.5,
        template_file="chapter_opener.typ",
        parameters={"epigraph": True, "learning_objectives": True, "decorative_rule": True},
    ),

    LayoutFamily.CHAPTER_OPENER_WITH_IMAGE: LayoutSpec(
        family=LayoutFamily.CHAPTER_OPENER_WITH_IMAGE,
        name="Chapter Opener with Image",
        description="Chapter opener with full-width or half-width hero image",
        content_types=["chapter_number", "chapter_title", "hero_image", "epigraph"],
        typical_elements=["chapter_label", "chapter_number", "chapter_title", "hero_image", "image_caption", "epigraph"],
        best_for=["Visual chapters", "Image-heavy content"],
        min_content_density=0.2,
        max_content_density=0.4,
        requires_images=True,
        template_file="chapter_opener_image.typ",
    ),

    LayoutFamily.READING: LayoutSpec(
        family=LayoutFamily.READING,
        name="Standard Reading Layout",
        description="Single-column justified text for long-form reading",
        content_types=["paragraphs", "headings", "footnotes", "inline_images"],
        typical_elements=["body_text", "headings", "subheadings", "footnotes", "page_numbers", "running_headers"],
        best_for=["Long-form prose", "Narrative text", "Essays"],
        min_content_density=0.7,
        max_content_density=0.95,
        template_file="reading.typ",
    ),

    LayoutFamily.READING_TWO_COL: LayoutSpec(
        family=LayoutFamily.READING_TWO_COL,
        name="Two-Column Reading Layout",
        description="Two-column justified text for higher density",
        content_types=["paragraphs", "headings", "footnotes"],
        typical_elements=["body_text", "headings", "column_gutter", "balanced_columns"],
        best_for=["Reference works", "Dense text", "Academic texts"],
        min_content_density=0.75,
        max_content_density=0.95,
        supports_two_column=True,
        template_file="reading_two_col.typ",
    ),

    LayoutFamily.IMAGE_LED: LayoutSpec(
        family=LayoutFamily.IMAGE_LED,
        name="Image-Led Layout",
        description="Prominent image with supporting text",
        content_types=["image", "caption", "supporting_text", "callouts"],
        typical_elements=["hero_image", "caption", "body_text", "callout_boxes"],
        best_for=["Visual explanations", "Case studies", "Portfolio"],
        min_content_density=0.3,
        max_content_density=0.6,
        requires_images=True,
        template_file="image_led.typ",
    ),

    LayoutFamily.IMAGE_FULL: LayoutSpec(
        family=LayoutFamily.IMAGE_FULL,
        name="Full-Page Image",
        description="Full-bleed or full-page image with minimal caption",
        content_types=["image", "caption"],
        typical_elements=["full_bleed_image", "caption", "credit_line"],
        best_for=["Portfolio", "Photography books", "Visual impact"],
        min_content_density=0.05,
        max_content_density=0.15,
        requires_images=True,
        supports_bleed=True,
        template_file="image_full.typ",
    ),

    LayoutFamily.ASYMMETRICAL: LayoutSpec(
        family=LayoutFamily.ASYMMETRICAL,
        name="Asymmetrical Editorial Layout",
        description="Dynamic off-center composition with image and text",
        content_types=["image", "text", "captions", "pull_quotes"],
        typical_elements=["asymmetric_grid", "image", "text_block", "pull_quote", "caption"],
        best_for=["Magazine-style", "Feature articles", "Editorial spreads"],
        min_content_density=0.4,
        max_content_density=0.7,
        requires_images=True,
        template_file="asymmetrical.typ",
    ),

    LayoutFamily.PULL_QUOTE: LayoutSpec(
        family=LayoutFamily.PULL_QUOTE,
        name="Pull Quote Layout",
        description="Prominent quoted text as visual element",
        content_types=["quotation", "attribution", "source"],
        typical_elements=["quote_text", "attribution", "source", "decorative_quotes", "accent_color"],
        best_for=["Emphasis", "Key insights", "Visual rhythm"],
        min_content_density=0.15,
        max_content_density=0.3,
        template_file="pull_quote.typ",
    ),

    LayoutFamily.CHECKLIST: LayoutSpec(
        family=LayoutFamily.CHECKLIST,
        name="Checklist Layout",
        description="Structured checklist with checkboxes and sections",
        content_types=["checklist_items", "section_headers", "completion_status"],
        typical_elements=["checkbox", "item_text", "section_header", "progress_indicator"],
        best_for=["Action items", "Verification", "Worksheets"],
        min_content_density=0.4,
        max_content_density=0.7,
        template_file="checklist.typ",
    ),

    LayoutFamily.PROCEDURAL_STEPS: LayoutSpec(
        family=LayoutFamily.PROCEDURAL_STEPS,
        name="Procedural Steps Layout",
        description="Numbered step-by-step instructions with optional illustrations",
        content_types=["step_number", "instruction", "illustration", "tip", "warning"],
        typical_elements=["step_number", "instruction_text", "illustration", "tip_box", "warning_box", "duration"],
        best_for=["How-to guides", "Tutorials", "Procedures"],
        min_content_density=0.5,
        max_content_density=0.8,
        template_file="procedural_steps.typ",
    ),

    LayoutFamily.COMPARISON_TABLE: LayoutSpec(
        family=LayoutFamily.COMPARISON_TABLE,
        name="Comparison Table Layout",
        description="Side-by-side comparison with highlighted differences",
        content_types=["criteria", "option_a", "option_b", "verdict"],
        typical_elements=["table", "criteria_column", "option_columns", "highlight_rows", "summary_row"],
        best_for=["Decision support", "Product comparisons", "Option analysis"],
        min_content_density=0.6,
        max_content_density=0.9,
        template_file="comparison_table.typ",
    ),

    LayoutFamily.PROCESS_DIAGRAM: LayoutSpec(
        family=LayoutFamily.PROCESS_DIAGRAM,
        name="Process Diagram Layout",
        description="Flowchart or process flow with numbered steps",
        content_types=["nodes", "edges", "labels", "decision_points"],
        typical_elements=["start_node", "process_nodes", "decision_diamonds", "arrows", "end_node", "swimlanes"],
        best_for=["Process documentation", "Workflows", "Decision flows"],
        min_content_density=0.4,
        max_content_density=0.7,
        requires_images=True,
        template_file="process_diagram.typ",
    ),

    LayoutFamily.CASE_STUDY: LayoutSpec(
        family=LayoutFamily.CASE_STUDY,
        name="Case Study Layout",
        description="Structured case study with context, challenge, solution, results",
        content_types=["background", "challenge", "solution", "results", "lessons_learned", "metrics"],
        typical_elements=["case_title", "background_box", "challenge_section", "solution_section", "results_metrics", "key_takeaway", "quote"],
        best_for=["Real-world examples", "Proof points", "Learning from practice"],
        min_content_density=0.5,
        max_content_density=0.8,
        template_file="case_study.typ",
    ),

    LayoutFamily.WORKED_EXAMPLE: LayoutSpec(
        family=LayoutFamily.WORKED_EXAMPLE,
        name="Worked Example Layout",
        description="Step-by-step worked problem with explanation",
        content_types=["problem_statement", "given", "solution_steps", "explanation", "answer"],
        typical_elements=["problem_box", "given_data", "step_by_step", "explanation", "final_answer", "check"],
        best_for=["Educational content", "Technical guides", "Financial modeling"],
        min_content_density=0.5,
        max_content_density=0.8,
        template_file="worked_example.typ",
    ),

    LayoutFamily.EXERCISE: LayoutSpec(
        family=LayoutFamily.EXERCISE,
        name="Exercise Layout",
        description="Practice exercise with space for response",
        content_types=["question", "instructions", "response_area", "hints"],
        typical_elements=["question_number", "question_text", "instructions", "response_lines", "hint_box", "difficulty"],
        best_for=["Workbooks", "Practice", "Assessment"],
        min_content_density=0.3,
        max_content_density=0.6,
        template_file="exercise.typ",
    ),

    LayoutFamily.RECAP: LayoutSpec(
        family=LayoutFamily.RECAP,
        name="Chapter Recap Layout",
        description="Summary page with key points and takeaways",
        content_types=["key_points", "takeaways", "review_questions", "next_steps"],
        typical_elements=["recap_title", "bulleted_points", "takeaway_boxes", "review_questions", "next_chapter_preview"],
        best_for=["Review", "Retention", "Transition"],
        min_content_density=0.4,
        max_content_density=0.7,
        template_file="recap.typ",
    ),

    LayoutFamily.GLOSSARY: LayoutSpec(
        family=LayoutFamily.GLOSSARY,
        name="Glossary Layout",
        description="Alphabetical list of terms with definitions",
        content_types=["term", "definition", "cross_reference", "see_also"],
        typical_elements=["term_heading", "definition_text", "cross_refs", "alphabetical_nav"],
        best_for=["Reference", "Definitions", "Technical terms"],
        min_content_density=0.6,
        max_content_density=0.9,
        template_file="glossary.typ",
    ),

    LayoutFamily.REFERENCES: LayoutSpec(
        family=LayoutFamily.REFERENCES,
        name="References/Bibliography Layout",
        description="Formatted bibliography with hanging indents",
        content_types=["citation", "authors", "title", "year", "publisher", "doi"],
        typical_elements=["citation_number", "authors", "title", "journal", "year", "doi", "hanging_indent"],
        best_for=["Academic works", "Citations", "Bibliographies"],
        min_content_density=0.7,
        max_content_density=0.95,
        template_file="references.typ",
    ),

    LayoutFamily.APPENDIX: LayoutSpec(
        family=LayoutFamily.APPENDIX,
        name="Appendix Layout",
        description="Supplementary material with distinct labeling",
        content_types=["appendix_title", "content", "tables", "figures"],
        typical_elements=["appendix_label", "appendix_title", "content", "numbered_figures", "numbered_tables"],
        best_for=["Supplementary material", "Extended data", "Methodology details"],
        min_content_density=0.5,
        max_content_density=0.8,
        template_file="appendix.typ",
    ),

    LayoutFamily.ABOUT_AUTHOR: LayoutSpec(
        family=LayoutFamily.ABOUT_AUTHOR,
        name="About the Author",
        description="Author bio with optional photo",
        content_types=["photo", "bio", "credentials", "other_works", "contact"],
        typical_elements=["author_photo", "bio_text", "credentials_list", "other_books", "website"],
        best_for=["Author credibility", "Connection"],
        min_content_density=0.3,
        max_content_density=0.5,
        template_file="about_author.typ",
    ),

    LayoutFamily.PUBLISHER_PAGE: LayoutSpec(
        family=LayoutFamily.PUBLISHER_PAGE,
        name="Publisher Page",
        description="Publisher imprint, contact, and catalog info",
        content_types=["publisher_name", "logo", "address", "website", "catalog"],
        typical_elements=["publisher_logo", "imprint_name", "address", "website", "isbn_prefix"],
        best_for=["Brand presence", "Contact info"],
        min_content_density=0.2,
        max_content_density=0.4,
        template_file="publisher_page.typ",
    ),

    LayoutFamily.BACK_COVER: LayoutSpec(
        family=LayoutFamily.BACK_COVER,
        name="Back Cover",
        description="Back cover with blurb, author photo, barcode, endorsements",
        content_types=["blurb", "author_photo", "bio", "endorsements", "barcode", "isbn", "price", "publisher_logo"],
        typical_elements=["blurb_text", "author_photo", "author_bio", "endorsement_quotes", "barcode", "isbn", "price", "publisher_logo", "category"],
        best_for=["Retail", "Marketing", "Cataloging"],
        min_content_density=0.4,
        max_content_density=0.6,
        requires_images=True,
        supports_bleed=True,
        template_file="back_cover.typ",
    ),
}


def get_layout_spec(family: LayoutFamily) -> LayoutSpec | None:
    """Get layout specification by family."""
    return LAYOUT_LIBRARY.get(family)


def list_layouts_by_category() -> dict[str, list[LayoutFamily]]:
    """Group layouts by category."""
    categories = {
        "front_matter": [
            LayoutFamily.COVER, LayoutFamily.HALF_TITLE, LayoutFamily.TITLE_PAGE,
            LayoutFamily.COPYRIGHT, LayoutFamily.DEDICATION, LayoutFamily.AUTHOR_PAGE,
            LayoutFamily.PREFACE, LayoutFamily.ACKNOWLEDGMENTS, LayoutFamily.TOC,
            LayoutFamily.LIST_OF_FIGURES, LayoutFamily.LIST_OF_TABLES,
        ],
        "chapter_openers": [
            LayoutFamily.PART_OPENER, LayoutFamily.CHAPTER_OPENER,
            LayoutFamily.CHAPTER_OPENER_WITH_IMAGE,
        ],
        "reading": [
            LayoutFamily.READING, LayoutFamily.READING_TWO_COL,
            LayoutFamily.READING_WITH_SIDEBAR, LayoutFamily.READING_WITH_MARGINALIA,
        ],
        "image_led": [
            LayoutFamily.IMAGE_LED, LayoutFamily.IMAGE_FULL, LayoutFamily.IMAGE_HALF,
            LayoutFamily.IMAGE_WITH_CAPTION, LayoutFamily.IMAGE_GALLERY,
            LayoutFamily.IMAGE_COMPARISON,
        ],
        "editorial": [
            LayoutFamily.ASYMMETRICAL, LayoutFamily.ASYMMETRICAL_IMAGE_LEFT,
            LayoutFamily.ASYMMETRICAL_IMAGE_RIGHT, LayoutFamily.MAGAZINE_SPREAD,
        ],
        "specialized": [
            LayoutFamily.DEFINITION_SIDEBAR, LayoutFamily.PULL_QUOTE,
            LayoutFamily.PULL_QUOTE_CENTERED, LayoutFamily.PULL_QUOTE_MARGINAL,
            LayoutFamily.CALLOUT_BOX, LayoutFamily.SIDEBAR, LayoutFamily.MARGINAL_NOTE,
        ],
        "procedural": [
            LayoutFamily.CHECKLIST, LayoutFamily.CHECKLIST_WITH_ICONS,
            LayoutFamily.PROCEDURAL_STEPS, LayoutFamily.NUMBERED_PROCEDURE,
            LayoutFamily.DECISION_TREE,
        ],
        "data_visualization": [
            LayoutFamily.DATA_TABLE, LayoutFamily.DATA_TABLE_STRIPED,
            LayoutFamily.COMPARISON_TABLE, LayoutFamily.FINANCIAL_TABLE,
            LayoutFamily.SPECIFICATION_TABLE,
        ],
        "technical": [
            LayoutFamily.CODE_BLOCK, LayoutFamily.CODE_WITH_LINE_NUMBERS,
            LayoutFamily.CODE_WITH_CALLOUTS, LayoutFamily.TERMINAL_OUTPUT,
        ],
        "diagrams": [
            LayoutFamily.PROCESS_DIAGRAM, LayoutFamily.FLOWCHART,
            LayoutFamily.ARCHITECTURE_DIAGRAM, LayoutFamily.NETWORK_DIAGRAM,
            LayoutFamily.SEQUENCE_DIAGRAM, LayoutFamily.COMPONENT_DIAGRAM,
        ],
        "maps": [
            LayoutFamily.MAP_FULL, LayoutFamily.MAP_INSET,
            LayoutFamily.MAP_ANNOTATED, LayoutFamily.LOCATION_MAP,
        ],
        "case_studies": [
            LayoutFamily.CASE_STUDY, LayoutFamily.CASE_STUDY_WITH_SIDEBAR,
            LayoutFamily.WORKED_EXAMPLE, LayoutFamily.WORKED_EXAMPLE_STEPPED,
        ],
        "exercises": [
            LayoutFamily.EXERCISE, LayoutFamily.EXERCISE_WITH_SOLUTION,
            LayoutFamily.QUIZ, LayoutFamily.PRACTICE_PROBLEM, LayoutFamily.WORKSHEET,
        ],
        "recaps": [
            LayoutFamily.RECAP, LayoutFamily.KEY_TAKEAWAYS,
            LayoutFamily.CHAPTER_SUMMARY, LayoutFamily.LEARNING_OBJECTIVES_REVIEW,
        ],
        "back_matter": [
            LayoutFamily.GLOSSARY, LayoutFamily.GLOSSARY_TWO_COL,
            LayoutFamily.REFERENCES, LayoutFamily.BIBLIOGRAPHY,
            LayoutFamily.APPENDIX, LayoutFamily.APPENDIX_WITH_TABLE,
            LayoutFamily.INDEX, LayoutFamily.ABOUT_AUTHOR,
            LayoutFamily.AUTHOR_PHOTO, LayoutFamily.PUBLISHER_PAGE,
            LayoutFamily.COLOPHON, LayoutFamily.BACK_COVER,
        ],
    }
    return categories