"""Content-block accounting: what the manuscript asked for, and what came out.

A publication is built by moving content blocks into pages. Every stage of that
move is a place a block can be lost: a filter that drops a type, a family that
renders only the first block of a kind, a partitioner that overflows, a
back-matter rule that swallows a heading. The failure is silent by nature -- the
PDF builds, the page count looks plausible, and the text is simply gone.

This module makes the move auditable. It takes the manuscript and the page data
the renderer actually produced, and reports every block the manuscript
contained, with a disposition for each:

``rendered``
    The block reached a page and was serialized for typesetting.
``consumed``
    The block was deliberately used somewhere other than the page body -- as a
    chapter opener's title, a recap's summary, a reference entry. The reason
    says where it went.
``unaccounted``
    The block is in the manuscript and in no page. This is a defect. It is
    reported, never swallowed, and it carries enough context for an agent to
    decide whether to re-place the block or correct the source.

The distinction between ``consumed`` and ``unaccounted`` is the whole point. A
consumer must say what it did with a block; a silent drop is indistinguishable
from a bug and is treated as one.

Nothing here knows what a publication is about.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


#: Roles whose blocks are headings that name a structure rather than read as
#: body copy. A chapter heading is the opener's title, not a paragraph.
STRUCTURAL_ROLES = frozenset({"chapter", "title", "subtitle", "author"})


@dataclass
class BlockDisposition:
    """What happened to one manuscript block."""

    block_id: str
    content_type: str
    semantic_role: str
    chapter: int
    matter: str
    disposition: str
    reason: str = ""
    page: int | None = None
    preview: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "block_id": self.block_id,
            "content_type": self.content_type,
            "semantic_role": self.semantic_role,
            "chapter": self.chapter,
            "matter": self.matter,
            "disposition": self.disposition,
            "reason": self.reason,
            "page": self.page,
            "preview": self.preview,
        }


@dataclass
class ContentAccount:
    """The audit of one manuscript through one render."""

    dispositions: list[BlockDisposition] = field(default_factory=list)

    def _add(self, block: Any, disposition: str, reason: str = "",
             page: int | None = None) -> None:
        content = str(getattr(block, "content", "") or "")
        self.dispositions.append(
            BlockDisposition(
                block_id=str(getattr(block, "id", "")),
                content_type=_value(getattr(block, "content_type", "")),
                semantic_role=_value(getattr(block, "semantic_role", "")),
                chapter=int(getattr(block, "chapter", 0) or 0),
                matter=str(getattr(block, "matter", "body") or "body"),
                disposition=disposition,
                reason=reason,
                page=page,
                preview=" ".join(content.split())[:120],
            )
        )

    def by(self, disposition: str) -> list[BlockDisposition]:
        return [d for d in self.dispositions if d.disposition == disposition]

    @property
    def rendered(self) -> list[BlockDisposition]:
        return self.by("rendered")

    @property
    def consumed(self) -> list[BlockDisposition]:
        return self.by("consumed")

    @property
    def unaccounted(self) -> list[BlockDisposition]:
        return self.by("unaccounted")

    @property
    def complete(self) -> bool:
        """True when no block was lost.

        A publication is only allowed to call itself finished when this holds.
        """
        return not self.unaccounted

    def summary(self) -> str:
        return (
            f"{len(self.rendered)} rendered, {len(self.consumed)} consumed, "
            f"{len(self.unaccounted)} unaccounted of {len(self.dispositions)} blocks"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "complete": self.complete,
            "counts": {
                "total": len(self.dispositions),
                "rendered": len(self.rendered),
                "consumed": len(self.consumed),
                "unaccounted": len(self.unaccounted),
            },
            "summary": self.summary(),
            "unaccounted": [d.to_dict() for d in self.unaccounted],
            "consumed": [d.to_dict() for d in self.consumed],
            "dispositions": [d.to_dict() for d in self.dispositions],
        }


def _value(raw: Any) -> str:
    """Enum or plain string to a plain string."""
    return str(getattr(raw, "value", raw))


def _iter_page_blocks(page_data: Iterable[dict[str, Any]]):
    """Yield ``(page_number, block_dict)`` for every serialized page block.

    Only blocks carrying a source ``id`` are considered. A page may also hold
    content the renderer synthesized -- a cover's title, a contents entry, a
    generated figure -- and those have no manuscript block behind them, so they
    are not part of the accounting.
    """
    for page in page_data or []:
        number = page.get("page_number") or page.get("number")
        for block in page.get("blocks") or []:
            if isinstance(block, dict) and block.get("id"):
                yield number, block


def account_content(manuscript: Any,
                    page_data: Iterable[dict[str, Any]],
                    structural_roles: Iterable[str] = STRUCTURAL_ROLES,
                    claims: dict[str, str] | None = None) -> ContentAccount:
    """Account every block of ``manuscript`` against the pages actually built.

    ``page_data`` is the list the renderer handed to Typst, not a re-derivation
    of what it should have produced. That distinction is deliberate: the audit
    has to see the same pages the typesetter saw, or it cannot catch a family
    that discarded a block after planning.

    ``claims`` maps a block id to a reason supplied by the renderer for a block
    it used somewhere other than the page body -- as a section page's title, for
    instance. A claim is trusted but recorded, so the reason appears in the
    report rather than disappearing with the block.
    """
    structural = {str(r).lower() for r in structural_roles}
    account = ContentAccount()
    claims = claims or {}

    placed: dict[str, int | None] = {}
    for number, block in _iter_page_blocks(page_data):
        block_id = str(block.get("id"))
        if block_id not in placed:
            placed[block_id] = number

    for block in getattr(manuscript, "content_blocks", []) or []:
        block_id = str(getattr(block, "id", ""))
        if block_id in placed:
            account._add(block, "rendered", page=placed[block_id])
            continue
        reason = claims.get(block_id) or _consumption_reason(block, structural)
        if reason:
            account._add(block, "consumed", reason=reason)
        else:
            account._add(
                block,
                "unaccounted",
                reason="in the manuscript but in no built page",
            )
    return account


def _consumption_reason(block: Any, structural: Iterable[str]) -> str:
    """Why a block that is not in the page body is not a loss, or ``""``.

    Only roles and matters with a deliberate, structural destination qualify. A
    block is not excused for being inconvenient: an excuse has to name a place
    the content was used.
    """
    structural = set(structural)
    role = _value(getattr(block, "semantic_role", "")).lower()
    matter = str(getattr(block, "matter", "body") or "body").lower()
    content_type = _value(getattr(block, "content_type", "")).lower()
    text = " ".join(str(getattr(block, "content", "") or "").split())

    if role in structural:
        return f"structural heading carried by the {role} opener or title page"
    if matter == "front":
        return ("front matter expressed by the cover, title, imprint and "
                "contents pages rather than as a body block")
    if matter == "back":
        if content_type == "reference" or role in ("reference", "bibliography"):
            return "reference entry collected by the references section"
        if role in ("glossary", "appendix", "index"):
            return f"{role} entry collected by the back-matter section"
        return "back matter expressed by its own section page"
    if content_type == "page_break":
        return "pagination instruction, not printable content"
    if content_type == "section_break":
        return "pagination instruction, not printable content"
    if text.lower().startswith("summary:"):
        return "chapter summary carried by the chapter recap"
    return ""
