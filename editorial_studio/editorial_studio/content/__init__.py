# Editorial Studio Content Package
#
# Content intake, analysis, research, and assembly. The engine has no subject.
# It can read a manuscript, understand its structure, register the sources a
# user's agent supplies, and assemble what that agent wrote into a validated
# manuscript. It does not write the publication: the user's own agent does,
# and this package gives it somewhere to put the result.

from editorial_studio.content.ingestion import ManuscriptIngester, IngestionResult
from editorial_studio.content.intelligence import ContentIntelligenceEngine, ContentAnalysis
from editorial_studio.content.assembly import (
    AssemblyResult,
    ManuscriptAssembler,
    PROVENANCE_INFERRED,
    PROVENANCE_INSTRUCTION,
    PROVENANCE_KINDS,
    PROVENANCE_RESEARCH,
    PROVENANCE_USER,
    PublicationBrief,
    SourceRecord,
)
from editorial_studio.content.research import ResearchEngine, Source, SearchResult

__all__ = [
    "ManuscriptIngester",
    "IngestionResult",
    "ContentIntelligenceEngine",
    "ContentAnalysis",
    # Assembly: the agent's outline becomes a validated manuscript.
    "ManuscriptAssembler",
    "PublicationBrief",
    "SourceRecord",
    "AssemblyResult",
    "PROVENANCE_USER",
    "PROVENANCE_RESEARCH",
    "PROVENANCE_INFERRED",
    "PROVENANCE_INSTRUCTION",
    "PROVENANCE_KINDS",
    # Research: the real engine, not the no-op stand-in.
    "ResearchEngine",
    "Source",
    "SearchResult",
]
