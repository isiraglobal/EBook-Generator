"""Engine guarantees that must hold for every publication, whatever its subject.

These tests are deliberately about the engine, not about any one book. A
publication's subject changes; the promise that every content block is either
typeset or reported does not.
"""

from __future__ import annotations

import importlib.util
import inspect
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "editorial_studio"))

from editorial_studio.renderer.accounting import ContentAccount, account_content  # noqa: E402


PROJECT = "prj_16f8a7fb56f2"


def _build_manual_module():
    spec = importlib.util.spec_from_file_location(
        "build_manual", REPO / "scripts" / "build_manual.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _field_manual():
    """The existing manuscript, used as one test case among any number."""
    bm = _build_manual_module()
    project = REPO / "data" / "projects" / PROJECT
    manuscript = bm.load_manuscript(
        json.loads((project / "source_bundle" / "manuscript.json").read_text())
    )
    plan = bm.load_plan(json.loads((project / "editorial_plan.json").read_text()), manuscript)
    return bm, manuscript, plan


# ── Content accounting ───────────────────────────────────────────────────────


def test_accounting_reports_a_block_that_reaches_no_page() -> None:
    """A block in the manuscript but in no page must be reported, not dropped.

    The account is only worth anything if it fails when it should. This builds
    the failure deliberately rather than trusting the happy path.
    """
    class Block:
        def __init__(self, bid, kind="paragraph", role="body"):
            self.id = bid
            self.content = f"content for {bid}"
            self.content_type = kind
            self.semantic_role = role
            self.chapter = 1
            self.matter = "body"

    class Manuscript:
        content_blocks = [Block("kept"), Block("lost")]

    pages = [{"page_number": 1, "blocks": [{"id": "kept", "type": "paragraph"}]}]
    account = account_content(Manuscript(), pages)

    assert account.rendered and account.rendered[0].block_id == "kept"
    assert [d.block_id for d in account.unaccounted] == ["lost"], (
        "a block that reached no page must be reported as unaccounted"
    )
    assert account.complete is False
    assert "unaccounted" in account.summary()


def test_accounting_distinguishes_rendered_from_consumed() -> None:
    """A block used as a section title is consumed, and says where it went."""
    class Block:
        def __init__(self, bid, kind, role):
            self.id = bid
            self.content = f"content {bid}"
            self.content_type = kind
            self.semantic_role = role
            self.chapter = 0
            self.matter = "body"

    class Manuscript:
        content_blocks = [Block("h", "heading", "reference")]

    account = account_content(Manuscript(), [], claims={"h": "references section title"})
    assert account.complete
    assert account.consumed[0].reason == "references section title"


def test_field_manual_loses_no_content() -> None:
    """The real manuscript must account for every block it contains."""
    bm, manuscript, plan = _field_manual()
    pages, claims = bm.TypstRenderer()._build_page_data(manuscript, plan, {}, None)
    account = account_content(manuscript, pages, claims=claims)

    assert account.complete, (
        "content was dropped from the field manual:\n"
        + "\n".join(
            f"  {d.block_id} {d.content_type}/{d.semantic_role} ch{d.chapter}: {d.preview}"
            for d in account.unaccounted
        )
    )
    # And the accounting must actually be looking at a real book.
    assert len(manuscript.content_blocks) > 150, "the test manuscript looks truncated"
    assert len(account.rendered) > 150


# ── Topic independence ───────────────────────────────────────────────────────

#: Vocabulary that only makes sense for the one subject the engine was built
#: against. Its presence in product code means the engine has a subject.
SUBJECT_VOCABULARY = re.compile(
    r"\b(parcel|acreage|farmland|raw land|recreational land|land investor|"
    r"land valuation|land now|landnow|title commitment|deed|easement|"
    r"underwriting worksheet|deal scorecard|1031 exchange)\b",
    re.IGNORECASE,
)

#: Modules that exist to hold one test publication's material. They are data,
#: not engine, so they are exempt: the manuscript is a test case, and the
#: engine must be able to be tested against something.
TEST_FIXTURE_MODULES = {
    "land_chapters_01_04",
    "land_chapters_05_08",
    "land_chapters_09_12",
    "field_manual_content",
}


def _product_modules() -> list[Path]:
    package = REPO / "editorial_studio" / "editorial_studio"
    modules = []
    for path in package.rglob("*.py"):
        if path.stem in TEST_FIXTURE_MODULES or path.stem.startswith("test_"):
            continue
        modules.append(path)
    return modules


def test_product_code_carries_no_subject_vocabulary() -> None:
    """No engine module may be written about one publication's subject.

    Comments and docstrings count. A template or a generator that names parcels
    cannot typeset a pharmacology monograph; it will only typeset land.
    """
    offences: list[str] = []
    for path in _product_modules():
        for number, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            match = SUBJECT_VOCABULARY.search(line)
            if match:
                offences.append(
                    f"{path.relative_to(REPO)}:{number}: {match.group(0)} -- {line.strip()[:90]}"
                )
    assert not offences, (
        "subject vocabulary found in product code:\n" + "\n".join(offences)
    )


def test_engine_does_not_infer_a_subject_from_a_topic() -> None:
    """No module may switch behaviour by matching a subject's keywords.

    Inferring "this request is about land" from the words in it is how a
    universal engine quietly becomes a single-niche one.
    """
    offenders: list[str] = []
    for path in _product_modules():
        source = path.read_text(encoding="utf-8", errors="replace")
        for match in re.finditer(r"def\s+_is_\w+_request\s*\(", source):
            offenders.append(f"{path.relative_to(REPO)}: {match.group(0)}")
    assert not offenders, (
        "subject is still inferred by keyword matching:\n" + "\n".join(offenders)
    )


def test_content_package_does_not_export_a_subject_specific_generator() -> None:
    """The public content API must not offer topic-fixed prose generation.

    Content is the user's agent's work. The package may offer intake, analysis,
    research and assembly; it may not offer to invent a manual about land.
    """
    init = REPO / "editorial_studio" / "editorial_studio" / "content" / "__init__.py"
    source = init.read_text(encoding="utf-8")
    assert "ManuscriptGenerator" not in source, (
        "content/__init__.py still exports the subject-specific generator"
    )


def test_accounting_module_has_no_subject_vocabulary() -> None:
    """The accounting facility must read the same for any publication."""
    source = (REPO / "editorial_studio" / "editorial_studio" / "renderer"
              / "accounting.py").read_text(encoding="utf-8")
    assert not SUBJECT_VOCABULARY.search(source)


# ── Public surface ───────────────────────────────────────────────────────────


def test_renderer_reports_a_content_account() -> None:
    """A render result must carry its account, or the check cannot be run."""
    bm, manuscript, plan = _field_manual()
    result = bm.TypstRenderer().render_pdf(
        manuscript, plan, [], str(Path("/tmp/est_account_check.pdf"))
    )
    assert result["success"], result.get("error")
    account = result.get("content_account")
    assert account, "render_pdf returned no content_account"
    assert account["counts"]["total"] == len(manuscript.content_blocks)
    assert account["complete"], account["summary"]


def test_account_content_signature_is_backwards_compatible() -> None:
    """Existing callers that pass only a manuscript and pages still work."""
    sig = inspect.signature(account_content)
    params = list(sig.parameters)
    assert params[:3] == ["manuscript", "page_data", "structural_roles"]
    assert sig.parameters["claims"].default is None
