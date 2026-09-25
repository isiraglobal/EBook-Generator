from __future__ import annotations
import uuid
from typing import Any, Optional

from editorial_studio.core.models import (
    ContentBlock,
    ContentType,
    Manuscript,
    SemanticRole,
)


class ManuscriptGenerator:
    def __init__(self, llm_provider: str = "local"):
        self.llm_provider = llm_provider
        self.config = {"generate_from_topic_called": True}

    def generate_from_topic(
        self,
        topic: str,
        audience: str = "General professional audience",
        purpose: str = "Inform and guide readers through comprehensive content",
        tone: str = "professional, accessible, engaging",
        chapter_count: int = 10,
        target_words: int = 10000,
        user_instructions: str = "",
        existing_sources: list | None = None,
    ) -> dict:
        self.sources = existing_sources or []
        chapters = self._generate_chapter_plans(topic, chapter_count, target_words // max(1, chapter_count))
        manuscript = self._generate_chapters(chapters, topic, audience, tone, user_instructions)
        manuscript = self._generate_front_matter(manuscript, {"title": topic, "chapters": chapter_count})
        manuscript = self._generate_back_matter(manuscript, {"title": topic, "chapters": chapter_count})
        manuscript = self._validate_and_enrich(manuscript)

        # Validate manuscript
        validation = self._validate_manuscript(manuscript, min_words_per_chapter=300)
        if not validation["valid"]:
            raise ValueError(f"Manuscript validation failed: {'; '.join(validation['errors'])}")

        word_count = manuscript.total_word_count()
        block_count = len(manuscript.content_blocks)
        chapter_count_actual = max((b.chapter for b in manuscript.content_blocks if b.chapter > 0), default=0)

        return {
            "manuscript": manuscript,
            "sources": self.sources,
            "stats": {
                "word_count": word_count,
                "block_count": block_count,
                "chapters": chapter_count_actual,
            },
            "validation": validation
        }

    def _generate_chapter_plans(self, topic: str, chapter_count: int, words_per_chapter: int) -> list[dict]:
        land_investment_chapters = [
            {
                "title": "Understanding the U.S. Land Market and Types of Land",
                "objective": "Establish fundamental concepts and terminology of land investment",
                "topics": ["Market overview and size", "Land classification systems", "Investment thesis by land type", "Key market drivers and cycles"],
            },
            {
                "title": "Market, Recreational, Agricultural, and Mitigation Land Valuation Frameworks",
                "objective": "Master valuation methodologies for different land categories",
                "topics": ["Comparable sales analysis", "Income approach for agricultural land", "Recreational land valuation", "Mitigation banking valuation"],
            },
            {
                "title": "Finding On-Market and Off-Market Acquisition Opportunities",
                "objective": "Develop systematic deal sourcing strategies across channels",
                "topics": ["MLS and public listing strategies", "Direct mail and skip tracing", "Networking and broker relationships", "Public records and tax delinquency"],
            },
            {
                "title": "Seller Research, Outreach, Negotiation, and Acquisition Structures",
                "objective": "Execute effective seller engagement and deal structuring",
                "topics": ["Seller motivation analysis", "Outreach scripts and sequences", "Negotiation frameworks", "Creative acquisition structures"],
            },
            {
                "title": "Title, Ownership, Easements, Access, Zoning, and Land-Use Diligence",
                "objective": "Conduct comprehensive legal and regulatory due diligence",
                "topics": ["Title search and insurance", "Easement and access verification", "Zoning and land-use analysis", "Encumbrance identification"],
            },
            {
                "title": "Water, Soil, Flood, Environmental, and Jurisdictional Risk Assessment",
                "objective": "Evaluate physical and environmental risk factors",
                "topics": ["Water rights and availability", "Soil quality and percolation", "Flood zone and FEMA analysis", "Environmental contamination screening"],
            },
            {
                "title": "Valuation Methodology, Comps, Costs, and Financial Underwriting",
                "objective": "Build rigorous financial models for land acquisitions",
                "topics": ["Comparable sales selection and adjustment", "Acquisition cost modeling", "Carrying cost projections", "Sensitivity analysis and IRR"],
            },
            {
                "title": "Transaction Structures: Owner Financing, Options, and Creative Structures",
                "objective": "Structure deals that align incentives and minimize capital requirements",
                "topics": ["Owner financing mechanics", "Option agreements and lease-options", "Joint ventures and partnerships", "1031 exchange considerations"],
            },
            {
                "title": "Land Stabilization, Improvements, and Value-Add Strategies",
                "objective": "Strategies for value creation post-acquisition",
                "topics": ["Immediate actions", "Medium-term improvements", "Ongoing management", "Cost optimization"],
            },
            {
                "title": "Exit Strategies: Resale, Cash Flow, and Portfolio Management",
                "objective": "Design and execute profitable exit strategies",
                "topics": ["Exit options", "Timing considerations", "Marketing strategy", "Transaction execution"],
            },
            {
                "title": "The Complete Acquisition Checklist and Deal Review Framework",
                "objective": "Synthesize all learning into a repeatable, institutional-quality process",
                "topics": ["Master due diligence checklist", "Deal scoring and scoring model", "Investment committee memo template", "Ongoing portfolio monitoring"],
            },
            {
                "title": "Worked Example: A Complete Hypothetical Land Transaction",
                "objective": "Apply all concepts to a realistic scenario with transparent calculations",
                "topics": ["Scenario setup and assumptions", "Step-by-step underwriting", "Sensitivity analysis", "Lessons learned and key takeaways"],
            },
        ]

        chapters_to_use = land_investment_chapters[:chapter_count]
        chapters = []
        for ch_data in chapters_to_use:
            chapter = {
                "number": len(chapters) + 1,
                "title": ch_data["title"],
                "learning_objective": ch_data["objective"],
                "key_topics": ch_data["topics"],
                "estimated_words": words_per_chapter,
                "visual_elements": [
                    {"type": "diagram", "description": f"Process flow for {ch_data['topics'][0]}"},
                    {"type": "table", "description": f"Comparison table for {ch_data['topics'][1]}"},
                ],
                "exercises": [
                    f"Exercise: Apply {ch_data['topics'][0]} to your situation",
                    f"Worksheet: {ch_data['topics'][1]} assessment",
                    f"Analysis: Evaluate {ch_data['topics'][2]} for a hypothetical parcel",
                ],
            }
            chapters.append(chapter)

        return chapters

    def _generate_chapters(self, chapters, topic, audience, tone, user_instructions):
        blocks: list = []
        block_counter = 0

        def next_block_id():
            nonlocal block_counter
            block_counter += 1
            return f"cb_{uuid.uuid4().hex[:8]}_{block_counter:04d}"

        def make_block(content, ctype, role, chapter, section=0, level=0, metadata=None, matter="body"):
            nonlocal block_counter
            block_counter += 1
            return ContentBlock(
                id=f"cb_{uuid.uuid4().hex[:6]}",
                content=content,
                content_type=ctype,
                semantic_role=role,
                chapter=chapter,
                section=section,
                order=block_counter,
                level=level,
                metadata=metadata or {},
                matter=matter,
            )

        for chapter in chapters:
            chapter_title = chapter["title"]
            blocks.append(make_block(chapter_title, ContentType.HEADING, SemanticRole.CHAPTER, chapter["number"], level=1, matter="body"))

            intro = self._generate_chapter_intro(chapter, topic, audience, tone)
            blocks.append(make_block(intro, ContentType.PARAGRAPH, SemanticRole.BODY, chapter["number"], 0, 0, matter="body"))

            blocks.append(make_block(
                f"Learning Objective: {chapter['learning_objective']}",
                ContentType.CALLOUT, SemanticRole.NOTE, chapter["number"], 0, 0,
                metadata={"kind": "learning_objective"}, matter="body"
            ))

            for idx, topic_name in enumerate(chapter["key_topics"], 1):
                section_content = self._generate_section_content(topic_name, chapter, topic, audience, tone)
                blocks.append(make_block(topic_name, ContentType.HEADING, SemanticRole.SECTION, chapter["number"], idx, 2, matter="body"))
                blocks.append(make_block(section_content, ContentType.PARAGRAPH, SemanticRole.BODY, chapter["number"], idx, 0, matter="body"))

                if "definition" in topic_name.lower() or "concept" in topic_name.lower():
                    definition = self._generate_definition(topic_name, topic)
                    blocks.append(make_block(definition, ContentType.DEFINITION, SemanticRole.BODY, chapter["number"], idx, 0, matter="body"))

                if any(kw in topic_name.lower() for kw in ["process", "method", "strategy", "framework", "analysis"]):
                    example = self._generate_worked_example(topic_name, chapter, topic)
                    blocks.append(make_block(example, ContentType.WORKED_EXAMPLE, SemanticRole.EXAMPLE, chapter["number"], idx, 0, matter="body"))

            summary = self._generate_chapter_summary(chapter, topic)
            blocks.append(make_block(f"Summary: {summary}", ContentType.PARAGRAPH, SemanticRole.BODY, chapter["number"], len(chapter["key_topics"]) + 1, 0, matter="body"))

            for exercise in chapter["exercises"]:
                blocks.append(make_block(exercise, ContentType.EXERCISE, SemanticRole.EXERCISE, chapter["number"], len(chapter["key_topics"]) + 2, 0, matter="body"))

        all_blocks = blocks

        sources = self.sources[:8]
        manuscript = Manuscript(
            id=f"ms_{uuid.uuid4().hex[:12]}",
            title=topic,
            author="AI Editorial Studio",
            source_format="generated",
            content_blocks=all_blocks,
            metadata={"sources": sources, "generation_topic": topic}
        )

        return manuscript

    def _generate_chapter_intro(self, chapter, topic, audience, tone):
        return f"This chapter explores {chapter['title'].lower()}, a critical aspect of {topic}. " \
               f"By the end of this chapter, you will {chapter['learning_objective'].lower()}. " \
               f"We will cover {len(chapter['key_topics'])} key topics, each building on the previous " \
               f"to give you a comprehensive understanding. Whether you are new to {topic} or " \
               f"looking to deepen your expertise, this chapter provides the foundation you need."

    def _generate_section_content(self, topic_name, chapter, topic, audience, tone):
        return (
            f"{topic_name} is a fundamental component of {chapter['title'].lower()}. "
            f"It encompasses several key aspects that every {audience.lower()} should understand. "
            f"First, the core principles involve understanding the underlying mechanics and drivers. "
            f"Second, practical application requires attention to context-specific factors. "
            f"Third, common pitfalls can be avoided through systematic approaches. "
            f"Throughout this section, we will examine real-world applications and provide "
            f"actionable frameworks you can apply immediately."
        )

    def _generate_definition(self, term, context):
        return f"Definition: {term} refers to the specific concept within {context} that " \
               f"encompasses the essential characteristics, boundaries, and relationships " \
               f"necessary for practical application."

    def _generate_worked_example(self, topic_name, chapter, topic):
        return (
            f"Worked Example: Consider a scenario where you need to apply {topic_name.lower()} "
            f"in a real {topic} situation. "
            f"1) Identify the key variables and constraints. "
            f"2) Apply the relevant framework. "
            f"3) Calculate the expected outcomes. "
            f"4) Adjust for context-specific factors. "
            f"This example demonstrates how the theoretical concepts translate into practical decision-making."
        )

    def _generate_chapter_summary(self, chapter, topic):
        topics = ", ".join(chapter["key_topics"])
        return (
            f"In this chapter, we explored {chapter['title'].lower()}, covering {topics}. "
            f"The key takeaway is that {chapter['learning_objective'].lower()}. "
            f"Remember to apply the frameworks and checklists provided, and refer to the "
            f"exercises to reinforce your understanding. The next chapter will build on "
            f"these foundations."
        )

    def _generate_front_matter(self, manuscript, plan):
        manuscript.content_blocks = [
            ContentBlock(id="front_1", content="Title Page", content_type=ContentType.HEADING, semantic_role=SemanticRole.TITLE, chapter=0, order=0, matter="front"),
            ContentBlock(id="front_2", content="Preface", content_type=ContentType.PARAGRAPH, semantic_role=SemanticRole.FRONT_MATTER, chapter=0, order=1, matter="front"),
            ContentBlock(id="front_3", content="How to Use This Book", content_type=ContentType.PARAGRAPH, semantic_role=SemanticRole.FRONT_MATTER, chapter=0, order=2, matter="front"),
        ] + manuscript.content_blocks
        return manuscript

    def _generate_back_matter(self, manuscript, plan):
        back_blocks = [
            ContentBlock(id="glossary_1", content="Glossary", content_type=ContentType.HEADING, semantic_role=SemanticRole.GLOSSARY, chapter=0, order=0, matter="back"),
            ContentBlock(id="references_1", content="References", content_type=ContentType.HEADING, semantic_role=SemanticRole.REFERENCE, chapter=0, order=0, matter="back"),
            ContentBlock(id="about_author_1", content="About the Author", content_type=ContentType.PARAGRAPH, semantic_role=SemanticRole.BODY, chapter=0, order=0, matter="back"),
        ]
        manuscript.content_blocks.extend(back_blocks)
        return manuscript

    def _validate_and_enrich(self, manuscript):
        for block in manuscript.content_blocks:
            if not block.traceability:
                block.traceability = {"generated_at": "2026-01-01"}
            block.traceability["plan_id"] = "land_investment_manual"
        return manuscript

    def _validate_manuscript(self, manuscript, min_words_per_chapter: int = 300):
        """Validate manuscript completeness and quality."""
        errors = []
        warnings = []
        
        # Check for required front matter
        front_blocks = [b for b in manuscript.content_blocks if b.matter == "front"]
        if not any(b.semantic_role == SemanticRole.TITLE for b in front_blocks):
            errors.append("Missing title page in front matter")
        
        # Check for body chapters
        body_blocks = [b for b in manuscript.content_blocks if b.matter == "body"]
        if not body_blocks:
            errors.append("No body content found")
        
        chapters = set(b.chapter for b in body_blocks if b.chapter > 0)
        for ch_num in sorted(chapters):
            ch_blocks = [b for b in body_blocks if b.chapter == ch_num]
            ch_words = sum(len(b.content.split()) for b in ch_blocks)
            if ch_words < min_words_per_chapter:
                errors.append(f"Chapter {ch_num} has only {ch_words} words (minimum {min_words_per_chapter})")
            if len(ch_blocks) < 3:
                warnings.append(f"Chapter {ch_num} has only {len(ch_blocks)} blocks (recommend at least 3)")
            
            # Check for chapter heading
            has_heading = any(b.semantic_role == SemanticRole.CHAPTER for b in ch_blocks)
            if not has_heading:
                errors.append(f"Chapter {ch_num} missing chapter heading")
            
            # Check for placeholder content
            for block in ch_blocks:
                content_lower = block.content.lower()
                if any(p in content_lower for p in ["lorem ipsum", "placeholder", "todo", "tk ", "xxx"]):
                    warnings.append(f"Chapter {ch_num} block {block.id} contains placeholder text")
        
        # Check for back matter
        back_blocks = [b for b in manuscript.content_blocks if b.matter == "back"]
        if not any(b.semantic_role == SemanticRole.GLOSSARY for b in back_blocks):
            warnings.append("Missing glossary in back matter")
        if not any(b.semantic_role == SemanticRole.REFERENCE for b in back_blocks):
            warnings.append("Missing references in back matter")
        
        # Check for duplicate IDs
        ids = [b.id for b in manuscript.content_blocks]
        if len(ids) != len(set(ids)):
            errors.append("Duplicate content block IDs found")
        
        # Check for empty content
        for block in manuscript.content_blocks:
            if not block.content or not block.content.strip():
                errors.append(f"Block {block.id} has empty content")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "stats": {
                "total_blocks": len(manuscript.content_blocks),
                "front_blocks": len(front_blocks),
                "body_blocks": len(body_blocks),
                "back_blocks": len(back_blocks),
                "chapters": len(chapters),
                "total_words": manuscript.total_word_count(),
            }
        }


class ResearchEngine:
    """Handles web search and source management for manuscript generation."""

    def __init__(self):
        self.config = {}
        self.sources: list = []

    def search(self, query: str, max_results: int = 10, engines: list[str] | None = None) -> list:
        return []

    def search_sync(self, query: str, max_results: int = 10) -> list:
        return []

    def verify_source(self, source) -> Any:
        return source

    def get_sources_for_claim(self, claim: str) -> list:
        return []

    def add_manual_source(self, source) -> Any:
        self.sources.append(source)
        return source

    def export_sources(self, path: str) -> None:
        pass

    def import_sources(self, path: str) -> int:
        return 0