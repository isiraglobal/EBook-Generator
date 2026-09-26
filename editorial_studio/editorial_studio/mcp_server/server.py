from __future__ import annotations
import uuid
from pathlib import Path
from typing import Any, Optional

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from editorial_studio.core.config import load_config
from editorial_studio.core.database import Database
from editorial_studio.core.models import (
    Asset,
    BrandProfile,
    DesignTokens,
    JobStatus,
    Manuscript,
    PagePurpose,
    Project,
    QASeverity,
    RenderJob,
    SemanticRole,
)
from editorial_studio.content.ingestion import ManuscriptIngester
from editorial_studio.content.intelligence import ContentIntelligenceEngine
from editorial_studio.art_director.planner import EditorialArtDirector
from editorial_studio.asset_engine.manager import AssetManager, VisualReferenceLibrary
from editorial_studio.export.publisher import PublishingEngine
from editorial_studio.qa.engine import QAEngine
from editorial_studio.renderer.typst_renderer import TypstRenderer


config = load_config().data
db = Database(config["storage"]["database_path"])

ingester = ManuscriptIngester()
intelligence = ContentIntelligenceEngine()
art_director = EditorialArtDirector()
asset_manager = AssetManager(db)
reference_library = VisualReferenceLibrary(db)
renderer = TypstRenderer(config)
qa_engine = QAEngine(db)
publisher = PublishingEngine(db)


mcp = FastMCP("editorial-studio")


# Tool Models
class CreatePublicationParams(BaseModel):
    name: str = Field(description="Publication/project name")
    description: str = Field(default="", description="Project description")
    tags: list[str] = Field(default_factory=list, description="Project tags")


class ImportManuscriptParams(BaseModel):
    project_id: str = Field(description="Project ID")
    file_path: str = Field(default="", description="Path to manuscript file")
    content: str = Field(default="", description="Manuscript content (if no file)")
    format: str = Field(default="markdown", description="Format: markdown, text, json, html, docx")
    title: str = Field(default="", description="Manuscript title")
    author: str = Field(default="", description="Manuscript author")


class ConfigureDesignParams(BaseModel):
    project_id: str = Field(description="Project ID")
    brand_profile_id: str = Field(default="", description="Builtin or custom brand profile ID")
    preset_overrides: dict[str, Any] = Field(default_factory=dict, description="Design token overrides")


class AddVisualReferenceParams(BaseModel):
    project_id: str = Field(description="Project ID")
    source_url: str = Field(default="", description="Reference URL (e.g., Pinterest)")
    source_title: str = Field(default="", description="Reference title")
    local_path: str = Field(default="", description="Local reference image path")
    screenshot_path: str = Field(default="", description="Screenshot path")
    tags: list[str] = Field(default_factory=list, description="Reference tags")


class AnalyzeManuscriptParams(BaseModel):
    project_id: str = Field(description="Project ID")


class GenerateEditorialPlanParams(BaseModel):
    project_id: str = Field(description="Project ID")
    user_instructions: str = Field(default="", description="Additional editorial instructions")


class ValidateEditorialPlanParams(BaseModel):
    project_id: str = Field(description="Project ID")


class RenderPublicationParams(BaseModel):
    project_id: str = Field(description="Project ID")
    strict_layout: bool = Field(default=False, description="Fail on layout defects")


class InspectPublicationParams(BaseModel):
    project_id: str = Field(description="Project ID")


class InspectPageParams(BaseModel):
    project_id: str = Field(description="Project ID")
    page_number: int = Field(description="Page number to inspect")


class RepairPageParams(BaseModel):
    project_id: str = Field(description="Project ID")
    page_number: int = Field(description="Page number to repair")
    issue_ids: list[str] = Field(default_factory=list, description="Specific issue IDs to address")


class RegenerateChapterParams(BaseModel):
    project_id: str = Field(description="Project ID")
    chapter_number: int = Field(description="Chapter number to regenerate")


class GetJobStatusParams(BaseModel):
    project_id: str = Field(description="Project ID")


class GetQAReportParams(BaseModel):
    project_id: str = Field(description="Project ID")


class ExportPublicationParams(BaseModel):
    project_id: str = Field(description="Project ID")


class AssemblePublicationParams(BaseModel):
    brief: dict = Field(
        description=(
            "What is being published. title, subtitle, author, audience, "
            "purpose, tone, format, target_words, domain_terms (the "
            "publication's own vocabulary for what it is about), sources "
            "(every source actually supplied), and optional front_matter / "
            "back_matter block lists."
        )
    )
    outline: list = Field(
        description=(
            "The chapters, in order. Each chapter: title, optional provenance, "
            "and sections. Each section: title and blocks. Each block: content, "
            "content_type, semantic_role, provenance (user_provided | "
            "researched | agent_inferred | user_instruction), metadata, and "
            "source_ids for anything it cites."
        )
    )
    project_name: str = Field(default="", description="Name for the created project")


class GetContentAccountParams(BaseModel):
    project_id: str = Field(description="Project ID")


@mcp.tool()
def assemble_publication(params: AssemblePublicationParams) -> dict:
    """Assemble agent-written content into a validated publication project.

    Use this once you have researched, planned and written the publication. The
    engine assembles the outline you supply and validates it, but it does not
    write for you and it does not know your subject.

    It will refuse the assembly, rather than produce a plausible-looking
    publication, if a block cites a source you did not supply, if provenance is
    unrecognised, if a chapter has headings but no prose, or if the manuscript
    falls far short of the requested length. Every block records where it came
    from: what the user supplied, what research produced, or what you inferred.
    """
    from editorial_studio.content.assembly import (
        ManuscriptAssembler,
        PublicationBrief,
    )

    if not str(params.brief.get("title", "")).strip():
        return {"ok": False, "errors": ["the brief must have a title"]}

    publication = PublicationBrief(
        title=str(params.brief.get("title", "")),
        subtitle=str(params.brief.get("subtitle", "")),
        author=str(params.brief.get("author", "")),
        audience=str(params.brief.get("audience", "")),
        purpose=str(params.brief.get("purpose", "")),
        tone=str(params.brief.get("tone", "")),
        format=str(params.brief.get("format", "book")),
        target_words=int(params.brief.get("target_words", 0) or 0),
        domain_terms=dict(params.brief.get("domain_terms", {}) or {}),
    )

    result = ManuscriptAssembler().assemble(
        publication,
        params.outline or [],
        sources=params.brief.get("sources", []) or [],
        front_matter=params.brief.get("front_matter", []) or [],
        back_matter=params.brief.get("back_matter", []) or [],
    )

    if result.errors:
        return {
            "ok": False,
            "errors": result.errors,
            "warnings": result.warnings,
            "provenance": result.provenance_counts,
        }

    project = Project(
        id=f"prj_{uuid.uuid4().hex[:12]}",
        name=params.project_name or publication.title,
    )
    db.create_project(project)
    db.create_manuscript(result.manuscript)
    project.manuscript_id = result.manuscript.id
    db.update_project(project)

    return {
        "ok": True,
        "project_id": project.id,
        "manuscript_id": result.manuscript.id,
        **result.to_dict(),
    }


@mcp.tool()
def get_content_account(params: GetContentAccountParams) -> dict:
    """Account for every content block: what was typeset, and what was not.

    Call this after rendering. It is the check that a publication contains what
    it was asked to contain, and it is the only check that catches a block
    silently discarded by a layout rule -- the kind of loss that leaves a PDF
    that looks finished.
    """
    project = db.get_project(params.project_id)
    if not project:
        return {"ok": False, "error": "project not found"}
    if not project.editorial_plan_id:
        return {"ok": False, "error": "no editorial plan; run generate_editorial_plan first"}

    plan = db.get_editorial_plan(project.editorial_plan_id)
    manuscript = db.get_manuscript(project.manuscript_id)
    if not manuscript:
        return {"ok": False, "error": "manuscript not found"}

    output_dir = Path(config["storage"]["projects_root"]) / project.id / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    result = renderer.render_pdf(
        manuscript, plan, [], str(output_dir / "account_check.pdf"))
    report = result.get("content_account")
    if not report:
        return {"ok": False, "error": result.get("error", "render produced no account")}
    return {"ok": bool(report["complete"]), "project_id": project.id, **report}


# MCP Tools
@mcp.tool()
def create_publication(params: CreatePublicationParams) -> dict:
    """Create a new publication project."""
    project = Project(
        id=f"prj_{uuid.uuid4().hex[:12]}",
        name=params.name,
        description=params.description,
        tags=params.tags,
    )
    db.create_project(project)
    return {"project_id": project.id, "name": project.name, "status": "created"}


@mcp.tool()
def import_manuscript(params: ImportManuscriptParams) -> dict:
    """Import manuscript from file or content."""
    project = db.get_project(params.project_id)
    if not project:
        raise ValueError(f"Project {params.project_id} not found")

    if params.file_path:
        result = ingester.ingest_file(params.file_path, params.title, params.author)
    elif params.content:
        result = ingester.ingest_from_api(params.content, params.format, params.title, params.author)
    else:
        raise ValueError("Either file_path or content must be provided")

    if result.errors:
        return {"success": False, "errors": result.errors, "warnings": result.warnings}

    manuscript = result.manuscript
    db.create_manuscript(manuscript)

    project.manuscript_id = manuscript.id
    db.update_project(project)

    return {
        "success": True,
        "manuscript_id": manuscript.id,
        "word_count": result.stats.get("word_count", 0),
        "block_count": result.stats.get("block_count", 0),
        "warnings": result.warnings,
    }


@mcp.tool()
def configure_design_system(params: ConfigureDesignParams) -> dict:
    """Configure the design system for a project."""
    project = db.get_project(params.project_id)
    if not project:
        raise ValueError(f"Project {params.project_id} not found")

    if params.brand_profile_id:
        # Try builtin first
        from editorial_studio.design_system.profiles import get_builtin_profile
        builtin = get_builtin_profile(params.brand_profile_id)
        if builtin:
            # Create brand profile from builtin
            bp = BrandProfile(
                id=builtin.id,
                name=builtin.name,
                description=builtin.description,
                design_tokens=builtin.design_tokens,
                cover_conventions=builtin.cover_conventions,
                section_opener_conventions=builtin.section_opener_conventions,
            )
            db.create_brand_profile(bp)
            project.brand_profile_id = bp.id
        else:
            # Check custom profile
            profile = db.get_brand_profile(params.brand_profile_id)
            if profile:
                project.brand_profile_id = profile.id
            else:
                raise ValueError(f"Brand profile {params.brand_profile_id} not found")

    # Apply preset overrides
    if params.preset_overrides and project.brand_profile_id:
        profile = db.get_brand_profile(project.brand_profile_id)
        if profile:
            for key, value in params.preset_overrides.items():
                if hasattr(profile.design_tokens, key):
                    setattr(profile.design_tokens, key, value)
            db.create_brand_profile(profile)  # Update

    db.update_project(project)
    return {"success": True, "brand_profile_id": project.brand_profile_id}


@mcp.tool()
def add_visual_reference(params: AddVisualReferenceParams) -> dict:
    """Add a visual reference (Pinterest URL, screenshot, or local image)."""
    project = db.get_project(params.project_id)
    if not project:
        raise ValueError(f"Project {params.project_id} not found")

    ref = reference_library.add_reference(
        source_url=params.source_url,
        source_title=params.source_title,
        local_path=params.local_path,
        screenshot_path=params.screenshot_path,
        tags=params.tags,
    )

    return {"reference_id": ref.id, "status": ref.retrieval_status}


@mcp.tool()
def analyze_manuscript(params: AnalyzeManuscriptParams) -> dict:
    """Analyze manuscript structure and content."""
    project = db.get_project(params.project_id)
    if not project:
        raise ValueError(f"Project {params.project_id} not found")

    if not project.manuscript_id:
        raise ValueError("No manuscript imported")

    manuscript = db.get_manuscript(project.manuscript_id)
    if not manuscript:
        raise ValueError("Manuscript not found")

    analysis = intelligence.analyze(manuscript)
    brief = intelligence.generate_publication_brief(analysis)

    return {
        "analysis": {
            "total_blocks": analysis.total_blocks,
            "total_words": analysis.total_words,
            "chapters": analysis.chapters,
            "sections": analysis.sections,
            "content_types": analysis.content_type_distribution,
            "semantic_roles": analysis.semantic_role_distribution,
            "has_tables": analysis.has_tables,
            "has_code": analysis.has_code,
            "has_images": analysis.has_images,
            "has_math": analysis.has_math,
            "has_exercises": analysis.has_exercises,
            "has_citations": analysis.has_citations,
            "reading_level": analysis.reading_level,
            "estimated_pages": analysis.estimated_pages,
        },
        "publication_brief": brief,
    }


@mcp.tool()
def generate_editorial_plan(params: GenerateEditorialPlanParams) -> dict:
    """Generate the complete editorial plan for the publication."""
    project = db.get_project(params.project_id)
    if not project:
        raise ValueError(f"Project {params.project_id} not found")

    if not project.manuscript_id:
        raise ValueError("No manuscript imported")

    manuscript = db.get_manuscript(project.manuscript_id)
    if not manuscript:
        raise ValueError("Manuscript not found")

    brand_profile = None
    if project.brand_profile_id:
        brand_profile = db.get_brand_profile(project.brand_profile_id)

    plan = art_director.create_publication_plan(
        manuscript, brand_profile, params.user_instructions
    )

    issues = art_director.validate_plan(plan)
    db.create_editorial_plan(plan)
    project.editorial_plan_id = plan.id
    db.update_project(project)

    return {
        "plan_id": plan.id,
        "page_count": len(plan.page_plans),
        "asset_briefs": len(plan.asset_briefs),
        "validation_issues": issues,
        "structure_map": plan.structure_map,
    }


@mcp.tool()
def validate_editorial_plan(params: ValidateEditorialPlanParams) -> dict:
    """Validate an editorial plan for completeness and consistency."""
    project = db.get_project(params.project_id)
    if not project:
        raise ValueError(f"Project {params.project_id} not found")

    if not project.editorial_plan_id:
        raise ValueError("No editorial plan generated")

    plan = db.get_editorial_plan(project.editorial_plan_id)
    if not plan:
        raise ValueError("Editorial plan not found")

    issues = art_director.validate_plan(plan)

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "page_count": len(plan.page_plans),
        "asset_brief_count": len(plan.asset_briefs),
    }


@mcp.tool()
def render_publication(params: RenderPublicationParams) -> dict:
    """Render the publication to PDF."""
    project = db.get_project(params.project_id)
    if not project:
        raise ValueError(f"Project {params.project_id} not found")

    if not project.editorial_plan_id:
        raise ValueError("No editorial plan generated")

    plan = db.get_editorial_plan(project.editorial_plan_id)
    manuscript = db.get_manuscript(project.manuscript_id)
    if not manuscript:
        raise ValueError("Manuscript not found")

    assets = []  # Would fetch from asset manager

    job = RenderJob(
        id=f"rj_{uuid.uuid4().hex[:12]}",
        project_id=project.id,
        editorial_plan_id=plan.id,
        status=JobStatus.RUNNING,
    )
    db.create_render_job(job)

    project.render_job_id = job.id
    db.update_project(project)

    output_dir = Path(config["storage"]["projects_root"]) / project.id / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_pdf = output_dir / f"{project.name.replace(' ', '_')}.pdf"

    result = renderer.render_pdf(manuscript, plan, assets, str(output_pdf), params.strict_layout)

    if not result["success"]:
        job.status = JobStatus.FAILED
        job.error_message = result["error"]
        db.update_render_job(job)
        return {"success": False, "error": result["error"]}

    job.status = JobStatus.COMPLETED
    job.output_pdf_path = result["output_path"]
    db.update_render_job(job)

    # Run QA
    qa_report = qa_engine.inspect_publication(job, result["output_path"], plan.id)
    job.qa_report_id = qa_report.id
    db.update_render_job(job)

    return {
        "success": True,
        "job_id": job.id,
        "pdf_path": job.output_pdf_path,
        "qa_report_id": qa_report.id,
        "qa_passed": qa_report.passed,
        "qa_score": qa_report.score,
    }


@mcp.tool()
def inspect_publication(params: InspectPublicationParams) -> dict:
    """Inspect the rendered publication."""
    project = db.get_project(params.project_id)
    if not project:
        raise ValueError(f"Project {params.project_id} not found")

    if not project.render_job_id:
        raise ValueError("No render job")

    job = db.get_render_job(project.render_job_id)
    if not job:
        raise ValueError("Render job not found")

    if not job.qa_report_id:
        raise ValueError("No QA report available")

    qa_report = db.get_qa_report(job.qa_report_id)
    if not qa_report:
        raise ValueError("QA report not found")

    return {
        "project_id": project.id,
        "job_status": job.status.value,
        "pdf_path": job.output_pdf_path,
        "page_count": qa_report.total_pages,
        "qa_passed": qa_report.passed,
        "qa_score": qa_report.score,
        "qa_summary": qa_report.summary,
        "hard_failures": len(qa_report.hard_failures()),
        "warnings": len(qa_report.warnings()),
        "page_images": job.page_images,
    }


@mcp.tool()
def inspect_page(params: InspectPageParams) -> dict:
    """Inspect a specific page for issues."""
    project = db.get_project(params.project_id)
    if not project:
        raise ValueError(f"Project {params.project_id} not found")

    if not project.render_job_id:
        raise ValueError("No render job")

    job = db.get_render_job(project.render_job_id)
    if not job or not job.qa_report_id:
        raise ValueError("No QA report available")

    qa_report = db.get_qa_report(job.qa_report_id)
    if not qa_report:
        raise ValueError("QA report not found")

    page_issues = [i for i in qa_report.issues if i.page_number == params.page_number]

    return {
        "page_number": params.page_number,
        "total_issues": len(page_issues),
        "hard_failures": len([i for i in page_issues if i.severity in (QASeverity.ERROR, QASeverity.CRITICAL)]),
        "warnings": len([i for i in page_issues if i.severity == QASeverity.WARNING]),
        "issues": [
            {
                "id": i.id,
                "severity": i.severity.value,
                "category": i.category,
                "message": i.message,
                "suggested_fix": i.suggested_fix,
                "auto_fixable": i.auto_fixable,
            }
            for i in page_issues
        ],
        "page_image": job.page_images[params.page_number - 1] if params.page_number <= len(job.page_images) else None,
    }


@mcp.tool()
def repair_page(params: RepairPageParams) -> dict:
    """Repair defects on a specific page."""
    project = db.get_project(params.project_id)
    if not project:
        raise ValueError(f"Project {params.project_id} not found")

    if not project.render_job_id:
        raise ValueError("No render job")

    job = db.get_render_job(project.render_job_id)
    if not job or not job.qa_report_id:
        raise ValueError("No QA report available")

    qa_report = db.get_qa_report(job.qa_report_id)
    if not qa_report:
        raise ValueError("QA report not found")

    # Filter issues for this page
    if params.issue_ids:
        target_issues = [i for i in qa_report.issues if i.id in params.issue_ids]
    else:
        target_issues = [i for i in qa_report.issues if i.page_number == params.page_number]

    if not target_issues:
        return {"success": True, "message": "No issues to repair on this page"}

    # Mark as fixable
    for issue in target_issues:
        issue.auto_fixable = True

    success, messages = qa_engine.repair_defects(qa_report, job, project.manuscript_id, project.editorial_plan_id)

    if success and job.retry_count > 0:
        # Re-render
        manuscript = db.get_manuscript(project.manuscript_id)
        plan = db.get_editorial_plan(project.editorial_plan_id)
        assets = []

        output_dir = Path(config["storage"]["projects_root"]) / project.id / "output"
        output_pdf = output_dir / f"{project.name.replace(' ', '_')}_repaired.pdf"

        result = renderer.render_pdf(manuscript, plan, assets, str(output_pdf), False)

        if result["success"]:
            job.output_pdf_path = result["output_path"]
            job.status = JobStatus.COMPLETED
            db.update_render_job(job)

            qa_report = qa_engine.inspect_publication(job, result["output_path"], plan.id)
            job.qa_report_id = qa_report.id
            db.update_render_job(job)

    return {
        "success": success,
        "messages": messages,
        "retry_count": job.retry_count,
        "remaining_hard_failures": len(qa_report.hard_failures()) if qa_report else 0,
    }


@mcp.tool()
def regenerate_chapter(params: RegenerateChapterParams) -> dict:
    """Regenerate a specific chapter."""
    project = db.get_project(params.project_id)
    if not project:
        raise ValueError(f"Project {params.project_id} not found")

    if not project.editorial_plan_id:
        raise ValueError("No editorial plan generated")

    manuscript = db.get_manuscript(project.manuscript_id)
    plan = db.get_editorial_plan(project.editorial_plan_id)
    assets = []

    job = publisher.regenerate_chapter(project, manuscript, plan, params.chapter_number, assets)
    db.create_render_job(job)

    return {"job_id": job.id, "status": "started", "chapter": params.chapter_number}


@mcp.tool()
def get_job_status(params: GetJobStatusParams) -> dict:
    """Get the status of a render job."""
    project = db.get_project(params.project_id)
    if not project:
        raise ValueError(f"Project {params.project_id} not found")

    if not project.render_job_id:
        return {"status": "no_job"}

    job = db.get_render_job(project.render_job_id)
    if not job:
        raise ValueError("Render job not found")

    return {
        "job_id": job.id,
        "status": job.status.value,
        "progress": job.progress,
        "current_step": job.current_step,
        "retry_count": job.retry_count,
        "error_message": job.error_message,
    }


@mcp.tool()
def get_qa_report(params: GetQAReportParams) -> dict:
    """Get the QA report for a publication."""
    project = db.get_project(params.project_id)
    if not project:
        raise ValueError(f"Project {params.project_id} not found")

    if not project.render_job_id:
        raise ValueError("No render job")

    job = db.get_render_job(project.render_job_id)
    if not job or not job.qa_report_id:
        raise ValueError("No QA report available")

    qa_report = db.get_qa_report(job.qa_report_id)
    if not qa_report:
        raise ValueError("QA report not found")

    return {
        "report_id": qa_report.id,
        "passed": qa_report.passed,
        "score": qa_report.score,
        "summary": qa_report.summary,
        "total_pages": qa_report.total_pages,
        "hard_failures": [
            {
                "id": i.id,
                "page": i.page_number,
                "category": i.category,
                "message": i.message,
            }
            for i in qa_report.hard_failures()
        ],
        "warnings": [
            {
                "id": i.id,
                "page": i.page_number,
                "category": i.category,
                "message": i.message,
            }
            for i in qa_report.warnings()
        ],
    }


@mcp.tool()
def export_publication(params: ExportPublicationParams) -> dict:
    """Export the final publication package."""
    project = db.get_project(params.project_id)
    if not project:
        raise ValueError(f"Project {params.project_id} not found")

    if not project.render_job_id:
        raise ValueError("No render job")

    job = db.get_render_job(project.render_job_id)
    if not job or job.status != JobStatus.COMPLETED:
        raise ValueError("Publication not ready")

    manuscript = db.get_manuscript(project.manuscript_id)
    plan = db.get_editorial_plan(project.editorial_plan_id)
    qa_report = db.get_qa_report(job.qa_report_id)
    assets = []

    package = publisher.finalize_publication(project, manuscript, plan, job, qa_report, assets)

    return {
        "project_id": project.id,
        "pdf_path": package.pdf_path,
        "source_bundle_path": package.source_bundle_path,
        "asset_manifest_path": package.asset_manifest_path,
        "editorial_plan_path": package.editorial_plan_path,
        "qa_report_path": package.qa_report_path,
        "metadata_path": package.metadata_path,
    }


if __name__ == "__main__":
    mcp.run()