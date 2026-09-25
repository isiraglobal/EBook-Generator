from __future__ import annotations

import math
import uuid
from datetime import datetime
from typing import Any

from editorial_studio.content.land_chapters_01_04 import LAND_CHAPTERS_01_04
from editorial_studio.content.land_chapters_05_08 import LAND_CHAPTERS_05_08
from editorial_studio.content.land_chapters_09_12 import LAND_CHAPTERS_09_12
from editorial_studio.core.models import ContentBlock, ContentType, Manuscript, SemanticRole


LAND_CHAPTERS = LAND_CHAPTERS_01_04 + LAND_CHAPTERS_05_08 + LAND_CHAPTERS_09_12


class ManuscriptGenerator:
    def __init__(self, llm_provider: str = "local"):
        self.llm_provider = llm_provider
        self.config = {"generate_from_topic_called": True}
        self.sources: list = []
        self.generated_at = datetime.now().isoformat()
        self.generation_id = f"gen_{uuid.uuid4().hex[:12]}"
        self.profile = "generic"
        self.block_counter = 0
        self.validation_warnings: list[str] = []
        self._current_user_instructions = ""

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
        self.generated_at = datetime.now().isoformat()
        self.generation_id = f"gen_{uuid.uuid4().hex[:12]}"
        self.block_counter = 0
        self.validation_warnings = []
        self._current_user_instructions = user_instructions.strip()
        self.profile = "land_investment" if self._is_land_investment_request(
            topic, purpose, user_instructions
        ) else "generic"

        requested_chapters = max(1, int(chapter_count))
        requested_words = max(0, int(target_words))
        body_blocks, chapter_plan = self._build_body(
            topic=topic,
            audience=audience,
            purpose=purpose,
            tone=tone,
            chapter_count=requested_chapters,
            target_words=requested_words,
            user_instructions=user_instructions,
        )
        front_blocks = self._build_front_matter(
            topic=topic,
            audience=audience,
            purpose=purpose,
            tone=tone,
            user_instructions=user_instructions,
        )
        back_blocks = self._build_back_matter(topic=topic)
        self._renumber(front_blocks + body_blocks + back_blocks)

        manuscript = Manuscript(
            id=f"ms_{uuid.uuid4().hex[:12]}",
            title=topic.strip() or "Untitled Publication",
            author="AI Editorial Studio",
            description=self._description_for(topic),
            source_format="generated",
            content_blocks=front_blocks + body_blocks + back_blocks,
            structure=self._structure_map(chapter_plan),
            metadata={
                "generation_id": self.generation_id,
                "generated_at": self.generated_at,
                "generator_profile": self.profile,
                "llm_provider": self.llm_provider,
                "generation_topic": topic,
                "audience": audience,
                "purpose": purpose,
                "tone": tone,
                "target_words": requested_words,
                "user_instructions": user_instructions,
                "source_count": len(self.sources),
                "chapter_plan": chapter_plan,
                "educational_notice": (
                    "Educational content only. Legal, tax, accounting, engineering, environmental, "
                    "forestry, permitting, and investment decisions require qualified local professionals."
                ),
            },
        )

        minimum_words = 1200 if self.profile == "land_investment" else 300
        validation = self._validate_manuscript(
            manuscript,
            min_words_per_chapter=minimum_words,
            target_words=requested_words,
        )
        if not validation["valid"]:
            raise ValueError(f"Manuscript validation failed: {'; '.join(validation['errors'])}")

        body_words = sum(
            len(block.content.split())
            for block in manuscript.content_blocks
            if block.matter == "body"
        )
        return {
            "manuscript": manuscript,
            "sources": self.sources,
            "stats": {
                "word_count": manuscript.total_word_count(),
                "body_word_count": body_words,
                "block_count": len(manuscript.content_blocks),
                "chapters": len({block.chapter for block in manuscript.content_blocks if block.chapter > 0}),
            },
            "validation": validation,
        }

    def _is_land_investment_request(self, *values: str) -> bool:
        text = " ".join(value for value in values if value).lower()
        terms = {
            "land investment",
            "land investor",
            "raw land",
            "acreage",
            "farmland",
            "recreational land",
            "rural land",
            "land acquisition",
            "land valuation",
            "land due diligence",
        }
        return any(term in text for term in terms)

    def _build_body(
        self,
        topic: str,
        audience: str,
        purpose: str,
        tone: str,
        chapter_count: int,
        target_words: int,
        user_instructions: str,
    ) -> tuple[list[ContentBlock], list[dict[str, Any]]]:
        if self.profile == "land_investment":
            selected = LAND_CHAPTERS[:chapter_count]
            if chapter_count > len(LAND_CHAPTERS):
                self.validation_warnings.append(
                    f"Requested {chapter_count} chapters; the land profile contains {len(LAND_CHAPTERS)}."
                )
            return self._build_land_body(topic, audience, selected, user_instructions), selected

        chapters = self._generic_chapter_plans(topic, chapter_count)
        return self._build_generic_body(
            topic,
            audience,
            purpose,
            tone,
            chapters,
            target_words,
            user_instructions,
        ), chapters

    def _build_land_body(
        self,
        topic: str,
        audience: str,
        chapters: list[dict[str, Any]],
        user_instructions: str,
    ) -> list[ContentBlock]:
        blocks: list[ContentBlock] = []
        for chapter in chapters:
            number = int(chapter["number"])
            section_titles = [section["title"] for section in chapter["sections"]]
            blocks.append(
                self._make_block(
                    chapter["title"],
                    ContentType.HEADING,
                    SemanticRole.CHAPTER,
                    chapter=number,
                    level=1,
                )
            )
            blocks.append(
                self._make_block(
                    self._land_chapter_introduction(chapter, topic, audience),
                    ContentType.PARAGRAPH,
                    SemanticRole.BODY,
                    chapter=number,
                )
            )
            blocks.append(
                self._make_block(
                    f"Learning objective: {chapter['objective']}",
                    ContentType.CALLOUT,
                    SemanticRole.NOTE,
                    chapter=number,
                    metadata={"kind": "learning_objective", "title": "Learning Objective"},
                )
            )
            for section_number, section in enumerate(chapter["sections"], 1):
                blocks.extend(
                    self._land_section_blocks(number, section_number, section, section_titles)
                )
            blocks.append(
                self._make_block(
                    self._land_chapter_summary(chapter),
                    ContentType.HEADING,
                    SemanticRole.SECTION,
                    chapter=number,
                    section=len(chapter["sections"]) + 1,
                    level=2,
                )
            )
            blocks.append(
                self._make_block(
                    self._land_chapter_review(chapter),
                    ContentType.PARAGRAPH,
                    SemanticRole.BODY,
                    chapter=number,
                    section=len(chapter["sections"]) + 1,
                )
            )
        return blocks

    def _land_section_blocks(
        self,
        chapter_number: int,
        section_number: int,
        section: dict[str, Any],
        section_titles: list[str],
    ) -> list[ContentBlock]:
        blocks: list[ContentBlock] = []
        blocks.append(
            self._make_block(
                section["title"],
                ContentType.HEADING,
                SemanticRole.SECTION,
                chapter=chapter_number,
                section=section_number,
                level=2,
            )
        )
        for paragraph in section["paragraphs"]:
            blocks.append(
                self._make_block(
                    paragraph,
                    ContentType.PARAGRAPH,
                    SemanticRole.BODY,
                    chapter=chapter_number,
                    section=section_number,
                )
            )

        definition = section["definition"]
        blocks.append(
            self._make_block(
                definition["definition"],
                ContentType.DEFINITION,
                SemanticRole.BODY,
                chapter=chapter_number,
                section=section_number,
                metadata={"term": definition["term"]},
            )
        )
        blocks.append(
            self._make_block(
                "\n".join(section["checklist"]),
                ContentType.LIST,
                SemanticRole.BODY,
                chapter=chapter_number,
                section=section_number,
                metadata={
                    "title": "Field Checklist",
                    "ordered": False,
                    "items": list(section["checklist"]),
                },
            )
        )
        table = section["table"]
        blocks.append(
            self._make_block(
                table["caption"],
                ContentType.TABLE,
                SemanticRole.TABLE,
                chapter=chapter_number,
                section=section_number,
                metadata={
                    "caption": table["caption"],
                    "headers": list(table["headers"]),
                    "rows": [list(row) for row in table["rows"]],
                },
            )
        )
        worked = section["worked_example"]
        given = worked.get("given", [])
        if not isinstance(given, list):
            given = [str(given)]
        worked_content = "\n".join(
            [
                worked["problem"],
                *given,
                *worked["steps"],
                worked["answer"],
                worked["verification"],
            ]
        ).strip()
        blocks.append(
            self._make_block(
                worked_content,
                ContentType.WORKED_EXAMPLE,
                SemanticRole.EXAMPLE,
                chapter=chapter_number,
                section=section_number,
                metadata={**worked, "solution": worked["answer"]},
            )
        )
        case_study = section["case_study"]
        case_content = "\n\n".join(
            [
                f"Situation: {case_study['situation']}",
                f"Analysis: {case_study['analysis']}",
                f"Decision: {case_study['decision']}",
                f"Lesson: {case_study['lesson']}",
            ]
        )
        blocks.append(
            self._make_block(
                case_content,
                ContentType.CASE_STUDY,
                SemanticRole.EXAMPLE,
                chapter=chapter_number,
                section=section_number,
                metadata=dict(case_study),
            )
        )
        image = section["image_instruction"]
        blocks.append(
            self._make_block(
                image["description"],
                ContentType.IMAGE_INSTRUCTION,
                SemanticRole.FIGURE,
                chapter=chapter_number,
                section=section_number,
                metadata={
                    "description": image["description"],
                    "alt_text": image["alt_text"],
                    "asset_available": False,
                },
            )
        )
        exercise = section["exercise"]
        blocks.append(
            self._make_block(
                exercise["question"],
                ContentType.EXERCISE,
                SemanticRole.EXERCISE,
                chapter=chapter_number,
                section=section_number,
                metadata={**exercise, "response_lines": self._exercise_lines(exercise)},
            )
        )
        return blocks

    def _exercise_lines(self, exercise: dict[str, Any]) -> list[str]:
        lines = exercise.get("response_lines", [])
        if isinstance(lines, list):
            return [str(line) for line in lines]
        return [str(lines)] if lines else ["Response:"]

    def _land_chapter_introduction(
        self, chapter: dict[str, Any], topic: str, audience: str
    ) -> str:
        return (
            f"{topic} is a rights-and-evidence business before it is an acreage business. This chapter "
            f"develops a repeatable approach to {chapter['objective'].lower()} The goal is not to "
            f"remove uncertainty; it is to identify the evidence that controls the decision, separate "
            f"facts from assumptions, and give {audience.lower()} a record that another reviewer can test. "
            f"The chapter moves from core principles to a field checklist, a transparent hypothetical "
            f"calculation, a case analysis, and a practice prompt. Each example is instructional rather "
            f"than a claim about a particular parcel, transaction, law, or market outcome."
        )

    def _land_chapter_summary(self, chapter: dict[str, Any]) -> str:
        return "Chapter Synthesis and Decision Checklist"

    def _land_chapter_review(self, chapter: dict[str, Any]) -> str:
        sections = ", ".join(section["title"] for section in chapter["sections"])
        return (
            f"The chapter connects {sections}. Before moving to the next chapter, restate the "
            f"investment objective, identify the two facts with the greatest value effect, name the "
            f"professional or document needed to verify each fact, and decide what evidence would cause "
            f"you to reprice, restructure, or stop. The objective to reinforce is: {chapter['objective']}"
        )

    def _generic_chapter_plans(self, topic: str, chapter_count: int) -> list[dict[str, Any]]:
        dimensions = [
            ("Foundations and Context", "Core concepts, scope, stakeholders, and decision boundaries"),
            ("Research and Evidence", "Evidence quality, source evaluation, assumptions, and limitations"),
            ("Analysis and Design", "Methods, tradeoffs, scenarios, and quantitative reasoning"),
            ("Execution and Review", "Implementation, controls, measurement, and continuous improvement"),
        ]
        plans: list[dict[str, Any]] = []
        for number in range(1, chapter_count + 1):
            plans.append(
                {
                    "number": number,
                    "title": f"{topic}: Dimension {number}",
                    "objective": f"Develop a defensible understanding of dimension {number} and apply it to a realistic decision.",
                    "dimensions": dimensions,
                }
            )
        return plans

    def _build_generic_body(
        self,
        topic: str,
        audience: str,
        purpose: str,
        tone: str,
        chapters: list[dict[str, Any]],
        target_words: int,
        user_instructions: str,
    ) -> list[ContentBlock]:
        words_per_section = max(
            160,
            target_words // max(1, len(chapters) * max(1, len(chapters[0]["dimensions"]))),
        )
        blocks: list[ContentBlock] = []
        for chapter in chapters:
            number = chapter["number"]
            blocks.append(
                self._make_block(
                    chapter["title"],
                    ContentType.HEADING,
                    SemanticRole.CHAPTER,
                    chapter=number,
                    level=1,
                )
            )
            blocks.append(
                self._make_block(
                    f"This chapter advances {purpose.lower()} for {audience.lower()} by focusing on "
                    f"{chapter['objective'].lower()} The emphasis is {tone}, with each concept tied to "
                    f"evidence, a decision, and a practical review step.",
                    ContentType.PARAGRAPH,
                    SemanticRole.BODY,
                    chapter=number,
                )
            )
            blocks.append(
                self._make_block(
                    f"Learning objective: {chapter['objective']}",
                    ContentType.CALLOUT,
                    SemanticRole.NOTE,
                    chapter=number,
                    metadata={"kind": "learning_objective", "title": "Learning Objective"},
                )
            )
            for section_number, (title, focus) in enumerate(chapter["dimensions"], 1):
                blocks.append(
                    self._make_block(
                        title,
                        ContentType.HEADING,
                        SemanticRole.SECTION,
                        chapter=number,
                        section=section_number,
                        level=2,
                    )
                )
                paragraphs = self._generic_paragraphs(
                    topic,
                    title,
                    focus,
                    section_number,
                    words_per_section,
                    user_instructions,
                )
                for paragraph in paragraphs:
                    blocks.append(
                        self._make_block(
                            paragraph,
                            ContentType.PARAGRAPH,
                            SemanticRole.BODY,
                            chapter=number,
                            section=section_number,
                        )
                    )
                blocks.append(
                    self._make_block(
                        f"{title} is the structured use of relevant evidence to improve a decision under explicit constraints.",
                        ContentType.DEFINITION,
                        SemanticRole.BODY,
                        chapter=number,
                        section=section_number,
                        metadata={"term": title},
                    )
                )
                blocks.append(
                    self._make_block(
                        "\n".join(
                            [
                                f"Define the decision connected to {title.lower()}.",
                                "Record the assumptions, owner, source, and date.",
                                "Test a base case and at least one adverse case.",
                                "Name the evidence that would reverse the conclusion.",
                                "Document the action, owner, and review date.",
                            ]
                        ),
                        ContentType.LIST,
                        SemanticRole.BODY,
                        chapter=number,
                        section=section_number,
                        metadata={
                            "title": f"{title} Checklist",
                            "ordered": True,
                            "items": [
                                f"Define the decision connected to {title.lower()}.",
                                "Record the assumptions, owner, source, and date.",
                                "Test a base case and at least one adverse case.",
                                "Name the evidence that would reverse the conclusion.",
                                "Document the action, owner, and review date.",
                            ],
                        },
                    )
                )
                blocks.append(
                    self._make_block(
                        f"Hypothetical {title}: the team states one objective, records three assumptions, "
                        f"compares two courses of action, records the result, and reviews the decision when "
                        f"new evidence arrives.",
                        ContentType.WORKED_EXAMPLE,
                        SemanticRole.EXAMPLE,
                        chapter=number,
                        section=section_number,
                        metadata={
                            "title": f"Hypothetical {title}",
                            "problem": f"Apply {focus.lower()} to a fictional decision.",
                            "given": ["A documented objective", "A fixed time and resource limit", "One adverse scenario"],
                            "steps": ["State the baseline.", "Test the adverse case.", "Record the decision rule."],
                            "answer": "Choose only the action that remains supportable under the documented evidence.",
                            "solution": "Choose only the action that remains supportable under the documented evidence.",
                            "verification": "Have a second reviewer reproduce the comparison from the same record.",
                        },
                    )
                )
                blocks.append(
                    self._make_block(
                        f"Apply {title.lower()} to a current situation, record what you know, what you infer, "
                        f"and what you still need to verify.",
                        ContentType.EXERCISE,
                        SemanticRole.EXERCISE,
                        chapter=number,
                        section=section_number,
                        metadata={
                            "title": f"Apply {title}",
                            "instructions": "Use a current or hypothetical situation relevant to your work.",
                            "question": f"How would {title.lower()} change the decision?",
                            "hints": ["Separate facts from assumptions.", "Include an adverse case."],
                            "response_type": "Decision note",
                            "response_lines": ["Situation:", "Evidence:", "Alternatives:", "Decision and review date:"],
                        },
                    )
                )
            blocks.append(
                self._make_block(
                    f"Review the evidence, alternatives, decision, owner, and unresolved questions before "
                    f"continuing to the next dimension of {topic}.",
                    ContentType.PARAGRAPH,
                    SemanticRole.BODY,
                    chapter=number,
                    section=len(chapter["dimensions"]) + 1,
                )
            )
        return blocks

    def _generic_paragraphs(
        self,
        topic: str,
        title: str,
        focus: str,
        section_number: int,
        target_words: int,
        user_instructions: str,
    ) -> list[str]:
        paragraph_count = max(2, min(6, math.ceil(target_words / 125)))
        instruction_clause = ""
        if user_instructions.strip():
            instruction_clause = f" The working brief also requires attention to this constraint: {user_instructions.strip()} "
        templates = [
            f"{title} matters because {topic} decisions are made through connected evidence rather than isolated observations. Begin with the decision owner, the time horizon, the resources available, and the outcome that would count as useful. This frame prevents a compelling detail from becoming the objective. {instruction_clause}The first task is to state what is known, what is assumed, and what can be tested before money or time is committed.",
            f"A practical treatment of {focus.lower()} compares the baseline with at least one credible alternative. Use consistent units, time periods, and definitions so the comparison changes because the underlying assumption changed, not because the presentation changed. Record uncertainty rather than disguising it as precision. A reviewer should be able to reproduce the result, identify the sensitive input, and explain why the selected case remains supportable.",
            f"Evidence quality has several dimensions: relevance, reliability, recency, completeness, and traceability. A recent claim can still be weak if it addresses the wrong question, while an older foundational source may remain useful when definitions are stable. Triangulate important conclusions with independent evidence and preserve source dates. When sources conflict, describe the conflict, test whether they define the subject differently, and avoid averaging incompatible measures into false precision.",
            f"Decision quality depends on explicit criteria. Set thresholds, constraints, and review triggers before reviewing the preferred answer. Distinguish reversible choices from commitments that are expensive to unwind. For {topic.lower()}, a small pilot, staged commitment, or additional verification may preserve optionality. The strongest plan states what will be done next, who owns it, what it costs, and what new evidence will cause the team to change course.",
            f"Implementation turns analysis into an operating system. Translate the decision into tasks, owners, dates, required inputs, and acceptance criteria. Track material changes rather than every trivial edit. Review both outputs and behavior: a technically correct recommendation can still fail if it cannot be implemented, funded, communicated, or monitored. Create an escalation path for assumptions that fail and a record of lessons for the next cycle.",
            f"Reflection completes the cycle. Compare the expected result with observed evidence, identify which assumptions mattered, and update the framework. Preserve useful uncertainty: not every question can be answered before action, but important unknowns can be bounded, assigned, and monitored. A mature {topic.lower()} practice makes uncertainty visible, updates decisions on a schedule, and preserves enough context that another person can continue the work without relying on memory.",
        ]
        return templates[:paragraph_count]

    def _build_front_matter(
        self,
        topic: str,
        audience: str,
        purpose: str,
        tone: str,
        user_instructions: str,
    ) -> list[ContentBlock]:
        blocks: list[ContentBlock] = []
        blocks.append(self._make_block(topic, ContentType.HEADING, SemanticRole.TITLE, matter="front", level=1))
        subtitle = self._subtitle_for(topic)
        blocks.append(self._make_block(subtitle, ContentType.PARAGRAPH, SemanticRole.SUBTITLE, matter="front"))
        blocks.append(self._make_block("AI Editorial Studio", ContentType.PARAGRAPH, SemanticRole.AUTHOR, matter="front"))
        blocks.append(
            self._make_block(
                f"Prepared for {audience}. {purpose} Reading level and tone: {tone}.",
                ContentType.PARAGRAPH,
                SemanticRole.ABSTRACT,
                matter="front",
            )
        )
        blocks.append(
            self._make_block(
                self._copyright_notice(),
                ContentType.PARAGRAPH,
                SemanticRole.FRONT_MATTER,
                matter="front",
                metadata={"kind": "copyright_and_disclaimer"},
            )
        )
        blocks.append(
            self._make_block(
                "Preface",
                ContentType.HEADING,
                SemanticRole.FRONT_MATTER,
                matter="front",
                level=1,
            )
        )
        for paragraph in self._preface_paragraphs(topic, audience, user_instructions):
            blocks.append(
                self._make_block(
                    paragraph,
                    ContentType.PARAGRAPH,
                    SemanticRole.FRONT_MATTER,
                    matter="front",
                )
            )
        blocks.append(
            self._make_block(
                "How to Use This Book",
                ContentType.HEADING,
                SemanticRole.FRONT_MATTER,
                matter="front",
                level=1,
            )
        )
        for paragraph in self._usage_paragraphs(topic):
            blocks.append(
                self._make_block(
                    paragraph,
                    ContentType.PARAGRAPH,
                    SemanticRole.FRONT_MATTER,
                    matter="front",
                )
            )
        blocks.append(
            self._make_block(
                "Suggested Learning Path",
                ContentType.HEADING,
                SemanticRole.FRONT_MATTER,
                matter="front",
                level=2,
            )
        )
        blocks.append(
            self._make_block(
                "\n".join(
                    [
                        "Read Chapters 1-2 to establish the market, land categories, and valuation basis.",
                        "Use Chapters 3-4 to source opportunities and test seller intent.",
                        "Apply Chapters 5-6 as legal and physical diligence gates before price is committed.",
                        "Build the financial case in Chapters 7-8, including downside and structure risk.",
                        "Use Chapters 9-10 to plan improvements and exits.",
                        "Apply Chapters 11-12 with the checklists, scorecard, and complete hypothetical transaction.",
                    ]
                ),
                ContentType.LIST,
                SemanticRole.FRONT_MATTER,
                matter="front",
                metadata={"title": "Suggested Learning Path", "ordered": True, "items": []},
            )
        )
        return blocks

    def _copyright_notice(self) -> str:
        return (
            f"Copyright © {datetime.now().year} AI Editorial Studio. This publication was generated "
            f"from a local manuscript workflow and is provided for educational purposes. It is not legal, "
            f"tax, accounting, engineering, environmental, forestry, permitting, brokerage, or investment "
            f"advice. Land rights, regulations, hazards, prices, and market conditions vary by location "
            f"and change over time. Verify current facts with the parcel, the relevant public records, and "
            f"qualified local professionals before relying on this material."
        )

    def _preface_paragraphs(self, topic: str, audience: str, user_instructions: str) -> list[str]:
        paragraphs = [
            (
                f"Land is easy to describe and difficult to know. Acreage, photographs, listing language, and "
                f"a county map can create a confident first impression without establishing what rights the "
                f"buyer would receive or what the land can support. {topic} therefore begins with a simple "
                f"rule: an attractive story is a lead for diligence, never a substitute for evidence. This "
                f"manual is designed to turn that rule into a repeatable process for {audience.lower()}."
            ),
            (
                "The chapters move in the same order used in serious acquisition work. Define the relevant "
                "market, classify the land, source opportunities, understand the seller, verify title and "
                "use, assess physical and environmental constraints, value the rights, choose a structure, "
                "underwrite the downside, plan improvements, and design an exit. The order prevents a common "
                "error: negotiating hard on price for a parcel whose access, water, title, or permitted use "
                "does not support the intended plan."
            ),
            (
                "Examples and cases are deliberately hypothetical. Their numbers are included to make methods "
                "visible, not to imply a typical price, return, timeline, legal result, or environmental "
                "outcome. Local rules and evidence can change every part of a land decision. The most important "
                "skill is not memorizing a number; it is recognizing which number belongs in the model, which "
                "belongs in a reserve, and which remains unknown."
            ),
            (
                "Use the checklists as gates, not as decoration. A field that remains unresolved should have "
                "an owner, a next evidence request, a cost, and a stop condition. When a document, visit, or "
                "professional opinion arrives, update the model rather than merely placing the item in a file. "
                "The resulting record should let another reviewer reproduce the recommendation and understand "
                "why the team accepted, adjusted, or rejected the opportunity."
            ),
        ]
        if user_instructions.strip():
            paragraphs.append(
                f"This edition also records the following user direction: {user_instructions.strip()} The "
                f"instruction is treated as a constraint on generation and review, not as a substitute for "
                f"local evidence."
            )
        return paragraphs

    def _usage_paragraphs(self, topic: str) -> list[str]:
        return [
            (
                f"Read {topic} sequentially for a foundation, or enter through the chapter matching the "
                f"decision in front of you. The field checklist after each major section is a compact review; "
                f"the longer appendix checklists are intended for transaction files. A worked example shows "
                f"how assumptions flow through a calculation, while the case study shows how evidence and "
                f"judgment should remain visibly separate."
            ),
            (
                "Keep the manuscript, maps, photographs, title materials, inspection notes, and model in one "
                "organized project record. Give every source a date and owner. Preserve the original file, "
                "record later versions, and explain material changes. A reliable file does not merely contain "
                "documents; it connects each document to a claim, condition, decision, or unresolved question."
            ),
            (
                "Use the model conservatively. Begin with the use the buyer can actually deliver, exclude "
                "unverified appreciation, carry holding and improvement costs, and test adverse assumptions. "
                "A deal can still fail after an attractive model. The purpose of the framework is to expose "
                "the conditions under which the decision changes while there is still time to act."
            ),
        ]

    def _build_back_matter(self, topic: str) -> list[ContentBlock]:
        blocks: list[ContentBlock] = []
        blocks.append(
            self._make_block("Glossary", ContentType.HEADING, SemanticRole.GLOSSARY, matter="back", level=1)
        )
        for term, definition in self._glossary_entries():
            blocks.append(
                self._make_block(
                    definition,
                    ContentType.DEFINITION,
                    SemanticRole.GLOSSARY,
                    matter="back",
                    metadata={"term": term},
                )
            )

        blocks.append(
            self._make_block(
                "Appendix A: Parcel File Request List",
                ContentType.HEADING,
                SemanticRole.APPENDIX,
                matter="back",
                level=1,
            )
        )
        blocks.append(
            self._make_block(
                "\n".join(
                    [
                        "Current deed, prior deeds, title commitment, exceptions, and lien information",
                        "Recorded plat, legal description, boundary survey, and access instruments",
                        "Parcel map, tax history, assessed classification, and special assessments",
                        "Zoning, subdivision, setback, overlay, and planning materials",
                        "Flood, wetland, soil, drainage, water, septic, and utility evidence",
                        "Leases, tenant communications, operating history, and improvement records",
                        "Comparable sales with source dates and a documented adjustment rationale",
                    ]
                ),
                ContentType.LIST,
                SemanticRole.APPENDIX,
                matter="back",
                metadata={"title": "Parcel File Request", "ordered": True, "items": []},
            )
        )

        blocks.append(
            self._make_block(
                "Appendix B: Underwriting Worksheet",
                ContentType.HEADING,
                SemanticRole.APPENDIX,
                matter="back",
                level=1,
            )
        )
        blocks.append(
            self._make_block(
                "Underwriting Worksheet",
                ContentType.TABLE,
                SemanticRole.TABLE,
                matter="back",
                metadata={
                    "caption": "Land underwriting categories",
                    "headers": ["Category", "Base Case", "Downside Case", "Evidence / Assumption"],
                    "rows": [
                        ["Purchase price and closing costs", "Enter amount", "Enter amount", "Contract and estimates"],
                        ["Required reserves", "Enter amount", "Enter amount", "Diligence scope and local quotes"],
                        ["Annual holding costs", "Enter annual amount", "Enter annual amount", "Taxes, insurance, maintenance, utilities"],
                        ["Improvement program", "Enter amount", "Enter amount", "Scope, schedule, contingency"],
                        ["Exit value", "Enter amount", "Enter amount", "Comparable evidence and scenario"],
                        ["Holding period", "Enter years", "Enter years", "Strategy and trigger review"],
                        ["Required return", "Enter rate", "Enter rate", "Investor policy and risk"],
                    ],
                },
            )
        )

        blocks.append(
            self._make_block(
                "Appendix C: Deal Scorecard",
                ContentType.HEADING,
                SemanticRole.APPENDIX,
                matter="back",
                level=1,
            )
        )
        blocks.append(
            self._make_block(
                "Deal Scorecard",
                ContentType.TABLE,
                SemanticRole.TABLE,
                matter="back",
                metadata={
                    "caption": "Scored acquisition review",
                    "headers": ["Criterion", "Weight", "Score", "Evidence Required"],
                    "rows": [
                        ["Market and demand", "20", "1-5", "Buyer evidence and relevant transactions"],
                        ["Title, access, and use", "25", "1-5", "Documents, survey, planning review"],
                        ["Physical and environmental risk", "20", "1-5", "Inspection, maps, professional evidence"],
                        ["Price and downside", "20", "1-5", "Comparable analysis and cash model"],
                        ["Execution and exit", "15", "1-5", "Contract, marketability, scenario plan"],
                    ],
                },
            )
        )

        blocks.append(
            self._make_block(
                "References and Primary Source Directory",
                ContentType.HEADING,
                SemanticRole.REFERENCE,
                matter="back",
                level=1,
            )
        )
        for reference in self._references():
            blocks.append(
                self._make_block(
                    reference,
                    ContentType.REFERENCE,
                    SemanticRole.REFERENCE,
                    matter="back",
                    metadata={"verified_current_edition": False},
                )
            )

        blocks.append(
            self._make_block(
                "About This Edition and AI Disclosure",
                ContentType.HEADING,
                SemanticRole.BACK_MATTER,
                matter="back",
                level=1,
            )
        )
        blocks.append(
            self._make_block(
                f"{topic} was assembled by AI Editorial Studio through a local, deterministic manuscript "
                f"workflow. The edition contains educational prose, hypothetical calculations, and source "
                f"directories rather than parcel-specific legal, engineering, environmental, tax, or "
                f"investment conclusions. A qualified reviewer should verify every material fact against "
                f"current primary records before a transaction decision.",
                ContentType.PARAGRAPH,
                SemanticRole.BACK_MATTER,
                matter="back",
            )
        )
        return blocks

    def _glossary_entries(self) -> list[tuple[str, str]]:
        return [
            ("Access", "A legally documented and practically usable route for reaching and servicing land."),
            ("Agricultural land", "Land used or classified for crop, pasture, nursery, forestry, or related production; local law and programs define the term precisely."),
            ("Appraisal", "A reasoned opinion of value prepared for a defined purpose, effective date, and intended user under applicable professional standards."),
            ("Assessment", "A governmental property value used for taxation or local purposes; it is not automatically a market value."),
            ("Comparable sale", "A transaction used as evidence of value because its property, rights, market, and date are sufficiently similar to the subject."),
            ("Contingency", "A defined condition in a contract that permits withdrawal, price adjustment, or another response if a specified event occurs."),
            ("Due diligence", "The organized process of verifying facts, rights, constraints, costs, and uncertainties relevant to a decision."),
            ("Easement", "A nonpossessory right to use a defined area for a defined purpose, subject to the instrument and governing law."),
            ("Encumbrance", "A claim, interest, restriction, lien, or other burden that may affect ownership, use, transfer, or financing."),
            ("Fee simple", "An ownership interest commonly described as ownership without a stated duration, subject to recorded rights and applicable law."),
            ("Fixture", "An improvement or item attached to land that may be treated as part of the real property under applicable law and facts."),
            ("Hypothetical case", "An instructional example used to demonstrate a method; it is not a representation of a real parcel or outcome."),
            ("Market value", "A value concept defined by a particular standard of valuation, intended user, effective date, and jurisdiction or professional context."),
            ("Net operating income", "Income remaining after operating expenses, with the treatment of taxes, capital expenditures, reserves, and financing stated explicitly."),
            ("Option", "A contractual right, not necessarily ownership, to decide whether to complete a purchase or another transaction under stated terms."),
            ("Plat", "A recorded map or plan showing a subdivision, parcel, right-of-way, easement, or other defined boundaries and features."),
            ("Purchase agreement", "The contract that states the parties, property, price, financing, diligence rights, representations, conditions, and remedies."),
            ("Rezoning", "A regulatory change of land-use classification or requirements through the applicable public process; it is not an automatic entitlement."),
            ("Title", "The legal evidence supporting ownership and the recorded interests that burden or define the estate."),
            ("Title commitment", "A preliminary statement issued under specified underwriting rules describing proposed coverage, exceptions, and requirements; it is not the insurance policy."),
            ("Valuation", "The analytical process of forming a reasoned opinion or range of value for a defined property, rights, purpose, and effective date."),
            ("Water right", "A legal or contractual interest in water use that depends on the applicable system, jurisdiction, priority rules, and documentation."),
            ("Zoning", "Public land-use and development rules that classify permitted uses and standards; zoning alone does not guarantee project approval."),
        ]

    def _references(self) -> list[str]:
        return [
            "U.S. Department of Agriculture, National Agricultural Statistics Service. Census of Agriculture and related county-level agricultural data publications. Verify the current edition and local geography.",
            "U.S. Department of Agriculture, Farm Service Agency. Public reference materials concerning conservation programs, wetland and easement programs, and agricultural records. Verify current program rules.",
            "U.S. Census Bureau. Census of Population and Housing and related geographic and demographic publications. Use the geography and date appropriate to the parcel.",
            "Federal Emergency Management Agency. Flood Map Service Center materials, flood-zone source information, and insurance guidance. Verify the effective map and local adoption status.",
            "U.S. Environmental Protection Agency. Envirofacts, Brownfields, wetlands, and environmental screening resources. Use state and local records for parcel-specific conclusions.",
            "U.S. Army Corps of Engineers. Public regulatory materials, nationwide permits, and water-resource information. Confirm current rules, regional practice, and site facts.",
            "U.S. Department of the Interior, Bureau of Land Management. Public survey, cadastral, and land-record materials relevant to federal and adjacent lands.",
            "Internal Revenue Service. Publication 544, Sales and Other Dispositions of Assets, and current instructions for Form 1031 and related exchanges. Consult a qualified tax adviser.",
            "State and local county recorder, assessor, planning, tax, health, road, water, and environmental offices. Their current public records and local interpretations are essential to parcel diligence.",
            "County and municipal codes, subdivision plats, zoning maps, floodplain regulations, assessment districts, road maintenance records, and meeting minutes where applicable.",
            "American Society of Appraisers. Current Uniform Standards of Professional Appraisal Practice and supporting technical standards. Use the edition and jurisdiction required for the assignment.",
            "Qualified local surveyors, title attorneys, engineers, environmental professionals, foresters, agricultural specialists, lenders, brokers, and other licensed or credentialed advisers.",
        ]

    def _subtitle_for(self, topic: str) -> str:
        if self.profile == "land_investment":
            return "A practical, diligence-first field manual for sourcing, evaluating, underwriting, and managing land"
        return f"A practical guide to understanding and applying {topic.lower()}"

    def _description_for(self, topic: str) -> str:
        if self.profile == "land_investment":
            return "An educational field manual for disciplined land acquisition, diligence, valuation, transaction structuring, and portfolio decisions."
        return f"An educational guide to {topic}."

    def _make_block(
        self,
        content: str,
        content_type: ContentType,
        semantic_role: SemanticRole,
        chapter: int = 0,
        section: int = 0,
        subsection: int = 0,
        level: int = 0,
        metadata: dict[str, Any] | None = None,
        matter: str = "body",
    ) -> ContentBlock:
        self.block_counter += 1
        return ContentBlock(
            id=f"cb_{uuid.uuid4().hex[:10]}_{self.block_counter:05d}",
            content=content.strip(),
            content_type=content_type,
            semantic_role=semantic_role,
            chapter=chapter,
            section=section,
            subsection=subsection,
            order=self.block_counter,
            level=level,
            user_instructions=self._current_user_instructions,
            is_generated=True,
            traceability={
                "generation_id": self.generation_id,
                "generated_at": self.generated_at,
                "profile": self.profile,
            },
            metadata=metadata or {},
            matter=matter,
        )

    def _renumber(self, blocks: list[ContentBlock]) -> None:
        for order, block in enumerate(blocks, 1):
            block.order = order

    def _structure_map(self, chapter_plan: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "profile": self.profile,
            "chapter_count": len(chapter_plan),
            "chapters": [
                {
                    "number": chapter["number"],
                    "title": chapter["title"],
                    "objective": chapter["objective"],
                    "section_count": len(chapter.get("sections", chapter.get("dimensions", []))),
                }
                for chapter in chapter_plan
            ],
        }

    def _validate_manuscript(
        self,
        manuscript: Manuscript,
        min_words_per_chapter: int = 300,
        target_words: int = 0,
    ) -> dict:
        errors: list[str] = []
        warnings = list(self.validation_warnings)
        front_blocks = [block for block in manuscript.content_blocks if block.matter == "front"]
        body_blocks = [block for block in manuscript.content_blocks if block.matter == "body"]
        back_blocks = [block for block in manuscript.content_blocks if block.matter == "back"]

        if not any(block.semantic_role == SemanticRole.TITLE for block in front_blocks):
            errors.append("Missing title in front matter")
        if not any(block.semantic_role == SemanticRole.FRONT_MATTER for block in front_blocks):
            errors.append("Missing substantive front matter")
        if not any(block.semantic_role == SemanticRole.GLOSSARY for block in back_blocks):
            errors.append("Missing glossary in back matter")
        if not any(block.semantic_role == SemanticRole.REFERENCE for block in back_blocks):
            errors.append("Missing references in back matter")
        if not any(block.semantic_role == SemanticRole.APPENDIX for block in back_blocks):
            warnings.append("No appendices in back matter")

        chapters = sorted({block.chapter for block in body_blocks if block.chapter > 0})
        if not chapters:
            errors.append("No body chapters found")
        if chapters and chapters != list(range(1, len(chapters) + 1)):
            errors.append("Chapter numbering is not continuous")

        for chapter_number in chapters:
            chapter_blocks = [block for block in body_blocks if block.chapter == chapter_number]
            chapter_words = sum(len(block.content.split()) for block in chapter_blocks)
            if chapter_words < min_words_per_chapter:
                errors.append(
                    f"Chapter {chapter_number} has {chapter_words} words; minimum is {min_words_per_chapter}"
                )
            if not any(block.semantic_role == SemanticRole.CHAPTER for block in chapter_blocks):
                errors.append(f"Chapter {chapter_number} missing chapter heading")
            if len(chapter_blocks) < 12:
                warnings.append(f"Chapter {chapter_number} has only {len(chapter_blocks)} content blocks")

        ids = [block.id for block in manuscript.content_blocks]
        if len(ids) != len(set(ids)):
            errors.append("Duplicate content block IDs found")
        orders = [block.order for block in manuscript.content_blocks]
        if orders != list(range(1, len(orders) + 1)):
            errors.append("Content block order is not globally sequential")
        invalid_matters = sorted({block.matter for block in manuscript.content_blocks} - {"front", "body", "back"})
        if invalid_matters:
            errors.append(f"Invalid matter values: {invalid_matters}")
        for block in manuscript.content_blocks:
            if not block.content.strip():
                errors.append(f"Block {block.id} has empty content")
                continue
            lowered = block.content.lower()
            if any(marker in lowered for marker in ("lorem ipsum", "placeholder", "todo", " tbd ", " xxx")):
                warnings.append(f"Block {block.id} contains placeholder-like text")
            if not block.is_generated:
                warnings.append(f"Block {block.id} is not marked as generated")

        actual_words = manuscript.total_word_count()
        if target_words and actual_words < target_words:
            warnings.append(
                f"Generated {actual_words} words, below the requested target of {target_words}"
            )
        if self.profile == "land_investment":
            glossary_entries = [
                block for block in back_blocks if block.content_type == ContentType.DEFINITION
            ]
            references = [
                block for block in back_blocks if block.content_type == ContentType.REFERENCE
            ]
            if len(glossary_entries) < 10:
                errors.append("Land profile requires at least 10 glossary definitions")
            if len(references) < 5:
                errors.append("Land profile requires at least 5 source-directory entries")
            body_types = {block.content_type for block in body_blocks}
            required_types = {
                ContentType.PARAGRAPH,
                ContentType.HEADING,
                ContentType.DEFINITION,
                ContentType.LIST,
                ContentType.TABLE,
                ContentType.WORKED_EXAMPLE,
                ContentType.CASE_STUDY,
                ContentType.EXERCISE,
            }
            missing_types = sorted(item.value for item in required_types - body_types)
            if missing_types:
                errors.append(f"Land profile is missing content types: {missing_types}")

        return {
            "valid": not errors,
            "errors": errors,
            "warnings": warnings,
            "stats": {
                "total_blocks": len(manuscript.content_blocks),
                "front_blocks": len(front_blocks),
                "body_blocks": len(body_blocks),
                "back_blocks": len(back_blocks),
                "chapters": len(chapters),
                "total_words": actual_words,
                "body_words": sum(len(block.content.split()) for block in body_blocks),
            },
        }


class ResearchEngine:
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
        return None

    def import_sources(self, path: str) -> int:
        return 0
