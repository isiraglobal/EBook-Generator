"""Apply the replacement content to a project's manuscript.json in place.

The manuscript's shape is preserved exactly: block ids, content types, chapter
and section numbers, order, and the key set of every block. Only the text of the
templated blocks changes, plus the ``metadata`` the case-study and
worked-example families read to build their panels.

Run:

    python3 scripts/apply_field_manual_content.py \\
        --project prj_16f8a7fb56f2
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "editorial_studio"))

# The field manual's own material is a test fixture, not part of the engine, so
# it lives with the tests. This script exists to load it into a test project.
sys.path.insert(0, str(REPO / "tests" / "fixtures"))

from content.field_manual_content import (  # noqa: E402
    CASE_STUDIES,
    CHAPTER_INTROS,
    CHAPTER_SUMMARIES,
    WORKED_EXAMPLES,
)

PROJECTS = REPO / "data" / "projects"

TEMPLATE_SENTENCES = (
    "It encompasses several key aspects that every beginner and intermediate",
    "First, the core principles involve understanding the underlying mechanics",
    "Second, practical application requires attention to context-specific factors.",
    "Third, common pitfalls can be avoided through systematic approaches.",
    "Throughout this section, we will examine real-world applications",
    "We will cover 4 key topics, each building on the previous",
    "Whether you are new to The Land Investor's Field Manual",
    "Remember to apply the frameworks and checklists provided",
    "The next chapter will build on these foundations.",
    "This chapter explores",
    "a critical aspect of The Land Investor's Field Manual",
    "Consider a scenario where you need to apply",
    "in a real The Land Investor's Field Manual situation",
    "This example demonstrates how the theoretical concepts translate",
)


def is_templated(text: str) -> bool:
    return any(s in text for s in TEMPLATE_SENTENCES)


def case_study_text(entry: dict) -> str:
    """Prose form of a case study, for readers who get it as running text."""
    return "\n\n".join(
        [
            "Situation: " + entry["situation"],
            "Analysis: " + entry["analysis"],
            "Decision: " + entry["decision"],
            "Lesson: " + entry["lesson"],
        ]
    )


def worked_example_text(entry: dict) -> str:
    parts = [entry["title"] + " — an illustrative hypothetical worked through step by step."]
    for i, step in enumerate(entry["steps"], 1):
        parts.append(f"{i}) {step}")
    parts.append(entry["result"])
    return " ".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default="prj_16f8a7fb56f2")
    ap.add_argument("--bundle", default="")
    args = ap.parse_args()

    bundle = Path(args.bundle) if args.bundle else PROJECTS / args.project / "source_bundle"
    path = bundle / "manuscript.json"
    doc = json.loads(path.read_text())

    applied = {"case_study": 0, "worked_example": 0, "intro": 0, "summary": 0}
    unresolved: list[str] = []

    for block in doc["content_blocks"]:
        bid = block.get("id")
        text = str(block.get("content") or "")
        if not is_templated(text):
            continue

        if bid in CASE_STUDIES:
            entry = CASE_STUDIES[bid]
            block["content"] = case_study_text(entry)
            block["metadata"] = {
                "title": entry["title"],
                "situation": entry["situation"],
                "analysis": entry["analysis"],
                "decision": entry["decision"],
                "lesson": entry["lesson"],
                "context": entry["situation"],
                "basis": entry["basis"],
            }
            applied["case_study"] += 1
        elif bid in WORKED_EXAMPLES:
            entry = WORKED_EXAMPLES[bid]
            block["content"] = worked_example_text(entry)
            block["metadata"] = {
                "title": entry["title"],
                "steps": entry["steps"],
                "result": entry["result"],
                "answer": entry["result"],
                "solution": entry["result"],
                "basis": entry["basis"],
            }
            applied["worked_example"] += 1
        elif bid in CHAPTER_INTROS:
            block["content"] = CHAPTER_INTROS[bid]
            applied["intro"] += 1
        elif bid in CHAPTER_SUMMARIES:
            block["content"] = CHAPTER_SUMMARIES[bid]
            applied["summary"] += 1
        else:
            unresolved.append(f"{bid} [{block.get('content_type')}] {text[:60]!r}")

    # Nothing templated may survive, whatever the table did not cover.
    leftover = [
        b.get("id")
        for b in doc["content_blocks"]
        if is_templated(str(b.get("content") or ""))
    ]

    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")

    print(f"wrote {path}")
    for k, v in applied.items():
        print(f"  {k:<15} {v}")
    print(f"  unresolved      {len(unresolved)}")
    for u in unresolved[:20]:
        print("    " + u)
    print(f"  templated text remaining: {len(leftover)}")
    for b in leftover[:20]:
        print("    " + str(b))
    return 1 if (unresolved or leftover) else 0


if __name__ == "__main__":
    raise SystemExit(main())
