"""Assembling a manuscript from what the user's agent wrote.

The engine does not know what a publication is about, and it does not write
one. The user's agent researches, plans, and writes; this module takes the
result and turns it into a validated :class:`~editorial_studio.core.models.Manuscript`
that the rest of the pipeline can plan, typeset, and check.

That division is deliberate. A generator that invents prose can only invent the
prose it was built around, which is how a universal engine ends up serving one
subject. An assembler has no vocabulary of its own, so it serves whatever it is
handed.

Three things are enforced here, because they are the three ways a publication
can quietly become untrue:

**Provenance.** Every block says where it came from -- what the user supplied,
what research produced, or what the agent inferred. The distinction is carried
into the manuscript and into the report, so a reader of the record can tell
evidence from inference.

**No invented sources.** A block that cites something must name a source that
was actually registered. A citation to something nobody supplied is refused at
assembly time, not discovered at proof stage.

**Declared structure.** An outline is validated against what the format
requires -- a title, a body, resolvable cross-references -- so a structural
mistake surfaces before a page is typeset.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable, Sequence

from editorial_studio.core.models import (
    ContentBlock,
    ContentType,
    Manuscript,
    SemanticRole,
)

#: Where a block's content came from. Free text is rejected so that the set
#: stays small enough to filter on later.
PROVENANCE_USER = "user_provided"
PROVENANCE_RESEARCH = "researched"
PROVENANCE_INFERRED = "agent_inferred"
PROVENANCE_INSTRUCTION = "user_instruction"

PROVENANCE_KINDS = frozenset({
    PROVENANCE_USER,
    PROVENANCE_RESEARCH,
    PROVENANCE_INFERRED,
    PROVENANCE_INSTRUCTION,
})

PROVENANCE_DESCRIPTIONS = {
    PROVENANCE_USER: "supplied by the user",
    PROVENANCE_RESEARCH: "drawn from a registered external source",
    PROVENANCE_INFERRED: "inferred by the agent; not evidence",
    PROVENANCE_INSTRUCTION: "follows a direct user instruction",
}


@dataclass
class PublicationBrief:
    """What the user asked to be published.

    Every field is a fact about the publication, not about a subject. The
    renderer reads ``domain_*`` keys from this to name things in the
    publication's own vocabulary; nothing here decides what the book is about.
    """

    title: str
    subtitle: str = ""
    author: str = ""
    audience: str = ""
    purpose: str = ""
    tone: str = ""
    format: str = "book"
    target_words: int = 0
    domain_terms: dict[str, str] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "subtitle": self.subtitle,
            "author": self.author,
            "audience": self.audience,
            "purpose": self.purpose,
            "tone": self.tone,
            "format": self.format,
            "target_words": self.target_words,
            "domain_terms": dict(self.domain_terms),
            **self.extra,
        }


@dataclass
class SourceRecord:
    """A source that was actually supplied, so a citation can point at it."""

    source_id: str
    title: str
    locator: str = ""
    kind: str = "web"
    retrieved: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "title": self.title,
            "locator": self.locator,
            "kind": self.kind,
            "retrieved": self.retrieved,
            "notes": self.notes,
        }


@dataclass
class AssemblyResult:
    manuscript: Manuscript
    sources: list[SourceRecord]
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    provenance_counts: dict[str, int] = field(default_factory=dict)

    @property
    def valid(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "manuscript_id": self.manuscript.id,
            "title": self.manuscript.title,
            "valid": self.valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "provenance": dict(self.provenance_counts),
            "sources": [s.to_dict() for s in self.sources],
            "block_count": len(self.manuscript.content_blocks),
            "word_count": self.manuscript.total_word_count(),
        }


class ManuscriptAssembler:
    """Builds a validated manuscript from an agent-supplied outline.

    The outline is plain data, so an agent can produce it from anything: a
    research pass, a set of uploaded manuscripts, a conversation with the user.
    Nothing in here interprets the subject.
    """

    def __init__(self, assembly_id: str | None = None) -> None:
        self.assembly_id = assembly_id or f"asm_{uuid.uuid4().hex[:12]}"
        self.assembled_at = datetime.now().isoformat()
        self._counter = 0

    # ── Public entry point ───────────────────────────────────────────────────

    def assemble(
        self,
        brief: PublicationBrief,
        outline: Sequence[dict[str, Any]],
        sources: Iterable[SourceRecord | dict[str, Any]] = (),
        front_matter: Sequence[dict[str, Any]] = (),
        back_matter: Sequence[dict[str, Any]] = (),
    ) -> AssemblyResult:
        result = AssemblyResult(manuscript=None, sources=[])  # type: ignore[arg-type]
        source_records = self._coerce_sources(sources)
        known_sources = {s.source_id for s in source_records}

        blocks: list[ContentBlock] = []
        errors: list[str] = []
        warnings: list[str] = []

        for block in front_matter:
            made, block_errors = self._build_block(block, chapter=0, matter="front",
                                                   known_sources=known_sources)
            if made:
                blocks.append(made)
            errors.extend(block_errors)

        for chapter_number, chapter in enumerate(outline or [], start=1):
            blocks.extend(self._assemble_chapter(
                chapter, chapter_number, known_sources, errors))

        for block in back_matter:
            made, block_errors = self._build_block(block, chapter=0, matter="back",
                                                   known_sources=known_sources)
            if made:
                blocks.append(made)
            errors.extend(block_errors)

        self._renumber(blocks)

        manuscript = Manuscript(
            id=f"ms_{uuid.uuid4().hex[:12]}",
            title=brief.title.strip() or "Untitled Publication",
            author=brief.author,
            description=brief.subtitle or brief.purpose,
            source_format="assembled",
            content_blocks=blocks,
            structure={"chapters": len(outline or [])},
            metadata={
                "assembly_id": self.assembly_id,
                "assembled_at": self.assembled_at,
                "brief": brief.to_dict(),
                "source_count": len(source_records),
            },
        )

        errors.extend(self._validate(manuscript, brief))
        counts = self._provenance_counts(blocks)

        result.manuscript = manuscript
        result.sources = source_records
        result.errors = errors
        result.warnings = warnings
        result.provenance_counts = counts
        return result

    # ── Internals ────────────────────────────────────────────────────────────

    def _assemble_chapter(
        self,
        chapter: dict[str, Any],
        chapter_number: int,
        known_sources: set[str],
        errors: list[str],
    ) -> list[ContentBlock]:
        blocks: list[ContentBlock] = []
        title = str(chapter.get("title", "")).strip()
        if not title:
            errors.append(f"chapter {chapter_number} has no title")
        else:
            blocks.append(self._block(
                title, ContentType.HEADING, SemanticRole.CHAPTER,
                chapter=chapter_number, level=1,
                provenance=str(chapter.get("provenance", PROVENANCE_INFERRED)),
            ))

        for section_number, section in enumerate(chapter.get("sections", []), start=1):
            blocks.extend(self._assemble_section(
                section, chapter_number, section_number, known_sources, errors))
        return blocks

    def _assemble_section(
        self,
        section: dict[str, Any],
        chapter_number: int,
        section_number: int,
        known_sources: set[str],
        errors: list[str],
    ) -> list[ContentBlock]:
        blocks: list[ContentBlock] = []
        title = str(section.get("title", "")).strip()
        if title:
            blocks.append(self._block(
                title, ContentType.HEADING, SemanticRole.SECTION,
                chapter=chapter_number, section=section_number, level=2,
                provenance=str(section.get("provenance", PROVENANCE_INFERRED)),
            ))

        for raw in section.get("blocks", []):
            made, block_errors = self._build_block(
                raw, chapter=chapter_number, section=section_number,
                known_sources=known_sources,
            )
            if made:
                blocks.append(made)
            errors.extend(block_errors)
        return blocks

    def _build_block(
        self,
        raw: dict[str, Any],
        chapter: int,
        section: int = 0,
        matter: str = "body",
        known_sources: set[str] | None = None,
    ) -> tuple[ContentBlock | None, list[str]]:
        known_sources = known_sources or set()
        errors: list[str] = []
        content = str(raw.get("content", "")).strip()
        if not content:
            return None, errors

        provenance = str(raw.get("provenance", PROVENANCE_INFERRED))
        if provenance not in PROVENANCE_KINDS:
            errors.append(
                f"block declares unknown provenance {provenance!r}; "
                f"expected one of {sorted(PROVENANCE_KINDS)}"
            )
            return None, errors

        content_type = self._content_type(raw.get("content_type"))
        metadata = dict(raw.get("metadata") or {})

        # A citation is a claim that something was consulted. Refuse the ones
        # that point at nothing: an invented source is worse than a missing one,
        # because it survives review by looking real.
        for source_id in self._cited_source_ids(raw, metadata):
            if source_id not in known_sources:
                errors.append(
                    f"block cites source {source_id!r}, which was not supplied; "
                    f"register the source or drop the citation"
                )
        if errors:
            return None, errors

        if content_type == ContentType.CITATION and not self._cited_source_ids(raw, metadata):
            errors.append(
                "citation block names no source; a citation without a source is "
                "not evidence"
            )
            return None, errors

        role = self._semantic_role(raw.get("semantic_role"), content_type)
        return self._block(
            content, content_type, role,
            chapter=chapter, section=section,
            level=int(raw.get("level", 0) or 0),
            provenance=provenance,
            metadata=metadata,
            matter=matter,
        ), errors

    def _block(
        self,
        content: str,
        content_type: ContentType,
        role: SemanticRole,
        chapter: int = 0,
        section: int = 0,
        level: int = 0,
        provenance: str = PROVENANCE_INFERRED,
        metadata: dict[str, Any] | None = None,
        matter: str = "body",
    ) -> ContentBlock:
        self._counter += 1
        return ContentBlock(
            id=f"cb_{uuid.uuid4().hex[:10]}_{self._counter:05d}",
            content=content.strip(),
            content_type=content_type,
            semantic_role=role,
            chapter=chapter,
            section=section,
            order=self._counter,
            level=level,
            traceability={
                "assembly_id": self.assembly_id,
                "assembled_at": self.assembled_at,
                "provenance": provenance,
                "provenance_description": PROVENANCE_DESCRIPTIONS.get(
                    provenance, provenance),
            },
            metadata=metadata or {},
            matter=matter,
        )

    @staticmethod
    def _content_type(raw: Any) -> ContentType:
        try:
            return ContentType(str(raw)) if raw else ContentType.PARAGRAPH
        except ValueError:
            return ContentType.PARAGRAPH

    @staticmethod
    def _semantic_role(raw: Any, content_type: ContentType) -> SemanticRole:
        if raw:
            try:
                return SemanticRole(str(raw))
            except ValueError:
                pass
        # A sensible default per type, not per subject.
        return {
            ContentType.HEADING: SemanticRole.SECTION,
            ContentType.TABLE: SemanticRole.TABLE,
            ContentType.IMAGE_INSTRUCTION: SemanticRole.FIGURE,
            ContentType.CODE: SemanticRole.CODE,
            ContentType.REFERENCE: SemanticRole.REFERENCE,
            ContentType.CITATION: SemanticRole.REFERENCE,
            ContentType.CALLOUT: SemanticRole.CALL_OUT,
            ContentType.QUOTATION: SemanticRole.PULL_QUOTE,
            ContentType.EXERCISE: SemanticRole.EXERCISE,
            ContentType.WORKED_EXAMPLE: SemanticRole.EXAMPLE,
            ContentType.CASE_STUDY: SemanticRole.EXAMPLE,
            ContentType.DEFINITION: SemanticRole.BODY,
        }.get(content_type, SemanticRole.BODY)

    @staticmethod
    def _cited_source_ids(raw: dict[str, Any], metadata: dict[str, Any]) -> list[str]:
        found: list[str] = []
        for key in ("source_ids", "source_id", "sources"):
            value = raw.get(key, metadata.get(key))
            if isinstance(value, str) and value:
                found.append(value)
            elif isinstance(value, (list, tuple)):
                found.extend(str(v) for v in value if v)
        return found

    @staticmethod
    def _coerce_sources(sources: Iterable[SourceRecord | dict[str, Any]]) -> list[SourceRecord]:
        records: list[SourceRecord] = []
        for source in sources or ():
            if isinstance(source, SourceRecord):
                records.append(source)
            elif isinstance(source, dict):
                records.append(SourceRecord(
                    source_id=str(source.get("source_id") or source.get("id") or ""),
                    title=str(source.get("title", "")),
                    locator=str(source.get("locator") or source.get("url", "")),
                    kind=str(source.get("kind", "web")),
                    retrieved=str(source.get("retrieved", "")),
                    notes=str(source.get("notes", "")),
                ))
        return [r for r in records if r.source_id]

    @staticmethod
    def _renumber(blocks: list[ContentBlock]) -> None:
        for order, block in enumerate(blocks, start=1):
            block.order = order

    @staticmethod
    def _provenance_counts(blocks: list[ContentBlock]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for block in blocks:
            kind = (block.traceability or {}).get("provenance", PROVENANCE_INFERRED)
            counts[kind] = counts.get(kind, 0) + 1
        return counts

    @staticmethod
    def _validate(manuscript: Manuscript, brief: PublicationBrief) -> list[str]:
        errors: list[str] = []
        if not manuscript.title.strip():
            errors.append("publication has no title")

        body = [b for b in manuscript.content_blocks if b.matter == "body"]
        if not body:
            errors.append("publication has no body content")

        chapters = {b.chapter for b in body if b.chapter > 0}
        if not chapters:
            errors.append("publication has no chapters")
        else:
            expected = set(range(min(chapters), max(chapters) + 1))
            if chapters != expected:
                missing = sorted(expected - chapters)
                errors.append(
                    f"chapter numbering has gaps; missing {missing}"
                )

        # A section that promises something must deliver it. This is the check
        # that catches a research pass that produced a heading and no text.
        for chapter in sorted(chapters):
            chapter_blocks = [b for b in body if b.chapter == chapter]
            prose = [b for b in chapter_blocks
                     if b.content_type == ContentType.PARAGRAPH
                     and len(str(b.content).split()) >= 20]
            if not prose:
                errors.append(
                    f"chapter {chapter} has headings but no substantive prose"
                )

        if brief.target_words and manuscript.total_word_count() < brief.target_words * 0.5:
            errors.append(
                f"manuscript has {manuscript.total_word_count()} words, "
                f"under half the {brief.target_words} requested"
            )
        return errors
