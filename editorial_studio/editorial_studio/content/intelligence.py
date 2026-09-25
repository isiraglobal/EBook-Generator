from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Any
from collections import Counter

from editorial_studio.core.models import ContentBlock, ContentType, Manuscript, SemanticRole


@dataclass
class ContentAnalysis:
    total_blocks: int
    total_words: int
    chapters: int
    sections: int
    content_type_distribution: dict[str, int]
    semantic_role_distribution: dict[str, int]
    has_tables: bool
    has_code: bool
    has_images: bool
    has_math: bool
    has_exercises: bool
    has_citations: bool
    reading_level: str
    estimated_pages: int
    structure_summary: dict[str, Any]
    language: str = "en"


class ContentIntelligenceEngine:
    def __init__(self):
        self.technical_patterns = [
            r"\b(API|SDK|HTTP|REST|JSON|XML|SQL|CPU|GPU|RAM|SSD|UI|UX|CI|CD|DevOps|AWS|GCP|Azure)\b",
            r"\b(function|class|method|variable|parameter|algorithm|complexity|optimization)\b",
            r"\b(deploy|scale|monitor|debug|test|compile|runtime|dependency)\b",
        ]
        self.academic_patterns = [
            r"\b(research|study|analysis|hypothesis|theorem|proof|lemma|corollary)\b",
            r"\b(et al\.|ibid\.|cf\.|e\.g\.|i\.e\.)\b",
            r"\b(significant|correlation|causation|methodology|literature review)\b",
        ]
        self.educational_patterns = [
            r"\b(exercise|quiz|worksheet|practice|homework|assignment|lesson|module)\b",
            r"\b(learning objective|outcome|competency|skill|knowledge)\b",
            r"\b(step-by-step|walkthrough|tutorial|guide|example)\b",
        ]
        self.business_patterns = [
            r"\b(ROI|KPI|revenue|profit|margin|growth|strategy|market|customer)\b",
            r"\b(stakeholder|deliverable|milestone|roadmap|quarter|fiscal)\b",
            r"\b(budget|forecast|investment|risk|compliance|governance)\b",
        ]

    def analyze(self, manuscript: Manuscript) -> ContentAnalysis:
        blocks = manuscript.content_blocks
        total_words = sum(len(b.content.split()) for b in blocks)

        type_dist = Counter(b.content_type.value for b in blocks)
        role_dist = Counter(b.semantic_role.value for b in blocks)

        chapters = max((b.chapter for b in blocks), default=0)
        sections = max((b.section for b in blocks), default=0)

        has_tables = any(b.content_type == ContentType.TABLE for b in blocks)
        has_code = any(b.content_type == ContentType.CODE for b in blocks)
        has_images = any(b.content_type == ContentType.IMAGE_INSTRUCTION for b in blocks)
        has_math = any(b.content_type == ContentType.MATH for b in blocks)
        has_exercises = any(b.content_type == ContentType.EXERCISE for b in blocks)
        has_citations = any(b.citations for b in blocks)

        all_text = " ".join(b.content for b in blocks)
        reading_level = self._estimate_reading_level(all_text)
        domain = self._classify_domain(all_text)
        estimated_pages = self._estimate_pages(total_words, has_tables, has_code, has_images)

        structure = self._analyze_structure(blocks)

        return ContentAnalysis(
            total_blocks=len(blocks),
            total_words=total_words,
            chapters=chapters,
            sections=sections,
            content_type_distribution=dict(type_dist),
            semantic_role_distribution=dict(role_dist),
            has_tables=has_tables,
            has_code=has_code,
            has_images=has_images,
            has_math=has_math,
            has_exercises=has_exercises,
            has_citations=has_citations,
            reading_level=reading_level,
            estimated_pages=estimated_pages,
            structure_summary=structure,
            language="en",
        )

    def _estimate_reading_level(self, text: str) -> str:
        sentences = len(re.split(r"[.!?]+", text))
        words = len(text.split())
        if sentences == 0:
            return "unknown"
        avg_words_per_sentence = words / sentences
        if avg_words_per_sentence < 10:
            return "elementary"
        elif avg_words_per_sentence < 15:
            return "middle_school"
        elif avg_words_per_sentence < 20:
            return "high_school"
        elif avg_words_per_sentence < 25:
            return "college"
        else:
            return "graduate"

    def _classify_domain(self, text: str) -> str:
        text_lower = text.lower()
        scores = {
            "technical": sum(len(re.findall(p, text_lower)) for p in self.technical_patterns),
            "academic": sum(len(re.findall(p, text_lower)) for p in self.academic_patterns),
            "educational": sum(len(re.findall(p, text_lower)) for p in self.educational_patterns),
            "business": sum(len(re.findall(p, text_lower)) for p in self.business_patterns),
        }
        if not any(scores.values()):
            return "general"
        return max(scores, key=scores.get)

    def _estimate_pages(self, word_count: int, has_tables: bool, has_code: bool, has_images: bool) -> int:
        words_per_page = 350
        if has_tables:
            words_per_page = 280
        if has_code:
            words_per_page = 300
        if has_images:
            words_per_page = 320
        return max(1, word_count // words_per_page + 1)

    def _analyze_structure(self, blocks: list[ContentBlock]) -> dict[str, Any]:
        chapter_structure: dict[int, dict[str, Any]] = {}
        for block in blocks:
            if block.chapter not in chapter_structure:
                chapter_structure[block.chapter] = {
                    "title": "",
                    "sections": [],
                    "block_count": 0,
                    "word_count": 0,
                }
            ch = chapter_structure[block.chapter]
            ch["block_count"] += 1
            ch["word_count"] += len(block.content.split())
            if block.semantic_role == SemanticRole.CHAPTER and not ch["title"]:
                ch["title"] = block.content
            elif block.semantic_role == SemanticRole.SECTION:
                ch["sections"].append({
                    "title": block.content,
                    "subsection": block.subsection,
                })

        return {
            "chapters": chapter_structure,
            "total_chapters": len(chapter_structure),
            "avg_blocks_per_chapter": sum(c["block_count"] for c in chapter_structure.values()) / max(1, len(chapter_structure)),
        }

    def enrich_blocks(self, manuscript: Manuscript) -> Manuscript:
        for block in manuscript.content_blocks:
            if block.content_type == ContentType.PARAGRAPH:
                block = self._classify_paragraph(block)
            elif block.content_type == ContentType.HEADING:
                block = self._classify_heading(block)
            block.traceability["enriched"] = True
        return manuscript

    def _classify_paragraph(self, block: ContentBlock) -> ContentBlock:
        text = block.content.lower()
        if re.search(r"\b(exercise|practice|try this|activity)\b", text):
            block.content_type = ContentType.EXERCISE
            block.semantic_role = SemanticRole.EXERCISE
        elif re.search(r"\b(example|for instance|e\.g\.)\b", text) and len(text) > 100:
            block.content_type = ContentType.WORKED_EXAMPLE
            block.semantic_role = SemanticRole.EXAMPLE
        elif re.search(r"\b(case study|real.world|in practice)\b", text):
            block.content_type = ContentType.CASE_STUDY
            block.semantic_role = SemanticRole.EXAMPLE
        elif re.search(r"\b(warning|caution|important|note)\b", text):
            block.content_type = ContentType.WARNING
            block.semantic_role = SemanticRole.WARNING
        elif re.search(r"\b(definition|defined as|means|refers to)\b", text) and len(text) < 200:
            block.content_type = ContentType.DEFINITION
            block.semantic_role = SemanticRole.BODY
        return block

    def _classify_heading(self, block: ContentBlock) -> ContentBlock:
        text = block.content.lower()
        # Don't reclassify chapter headings (level 1)
        if block.level == 1:
            return block
        if "exercise" in text or "practice" in text:
            block.semantic_role = SemanticRole.EXERCISE
        elif "example" in text or "case study" in text:
            block.semantic_role = SemanticRole.EXAMPLE
        elif "summary" in text or "recap" in text or "conclusion" in text:
            block.semantic_role = SemanticRole.BODY
        elif "reference" in text or "bibliography" in text:
            block.semantic_role = SemanticRole.REFERENCE
        elif "appendix" in text:
            block.semantic_role = SemanticRole.APPENDIX
        elif "glossary" in text:
            block.semantic_role = SemanticRole.GLOSSARY
        return block

    def generate_publication_brief(self, analysis: ContentAnalysis) -> dict[str, Any]:
        domain = "general"
        if analysis.has_code:
            domain = "technical"
        elif analysis.has_exercises:
            domain = "educational"
        elif analysis.has_citations:
            domain = "academic"

        return {
            "subject_domain": domain,
            "content_complexity": analysis.reading_level,
            "primary_format": "course" if analysis.has_exercises else "guide" if analysis.has_code else "book",
            "visual_density": "high" if analysis.has_images else "medium" if analysis.has_tables else "low",
            "navigation_needs": "high" if analysis.chapters > 5 else "medium",
            "reference_requirements": analysis.has_citations,
            "interactive_elements": analysis.has_exercises,
            "recommended_page_size": "A4" if analysis.has_code or analysis.has_tables else "A5",
            "recommended_layout": "technical" if analysis.has_code else "journal" if analysis.has_images else "book",
        }