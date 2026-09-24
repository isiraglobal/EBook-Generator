from __future__ import annotations
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from editorial_studio.core.config import load_config
from editorial_studio.core.database import Database
from editorial_studio.core.models import (
    Asset,
    BrandProfile,
    ContentType,
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


# Global instances
db: Optional[Database] = None
ingester: Optional[ManuscriptIngester] = None
intelligence: Optional[ContentIntelligenceEngine] = None
art_director: Optional[EditorialArtDirector] = None
asset_manager: Optional[AssetManager] = None
reference_library: Optional[VisualReferenceLibrary] = None
renderer: Optional[TypstRenderer] = None
qa_engine: Optional[QAEngine] = None
publisher: Optional[PublishingEngine] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global db, ingester, intelligence, art_director, asset_manager, reference_library, renderer, qa_engine, publisher

    config = load_config().data
    db_path = config["storage"]["database_path"]
    db = Database(db_path)

    ingester = ManuscriptIngester()
    intelligence = ContentIntelligenceEngine()
    art_director = EditorialArtDirector()
    asset_manager = AssetManager(db)
    reference_library = VisualReferenceLibrary(db)
    renderer = TypstRenderer(config)
    qa_engine = QAEngine(db)
    publisher = PublishingEngine(db)

    yield

    if db:
        db.close()


app = FastAPI(
    title="Editorial Studio API",
    description="AI Editorial Publishing Software API",
    version="1.0.0",
    lifespan=lifespan,
)

config = load_config().data
cors_origins = config.get("api", {}).get("cors_origins", ["http://localhost:3000"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class CreateProjectRequest(BaseModel):
    name: str
    description: str = ""
    tags: list[str] = []


class ImportManuscriptRequest(BaseModel):
    project_id: str
    format: str = "markdown"
    content: str = ""
    title: str = ""
    author: str = ""


class ConfigureDesignRequest(BaseModel):
    project_id: str
    brand_profile_id: str = ""
    preset_overrides: dict[str, Any] = {}


class AddReferenceRequest(BaseModel):
    project_id: str
    source_url: str = ""
    source_title: str = ""
    local_path: str = ""
    screenshot_path: str = ""
    tags: list[str] = []


class GeneratePlanRequest(BaseModel):
    project_id: str
    user_instructions: str = ""


class RenderRequest(BaseModel):
    project_id: str
    strict_layout: bool = False


class RepairRequest(BaseModel):
    project_id: str
    page_number: int
    issue_ids: list[str] = []
    strict_layout: bool = False


class ExportRequest(BaseModel):
    project_id: str


# API Endpoints
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Editorial Studio API"}


@app.post("/projects")
async def create_project(request: CreateProjectRequest):
    project = Project(
        id=f"prj_{uuid.uuid4().hex[:12]}",
        name=request.name,
        description=request.description,
        tags=request.tags,
    )
    db.create_project(project)
    return {"project_id": project.id, "project": project.__dict__}


@app.get("/projects")
async def list_projects(status: Optional[str] = None):
    projects = db.list_projects(status)
    return {"projects": [p.__dict__ for p in projects]}


@app.get("/projects/{project_id}")
async def get_project(project_id: str):
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project.__dict__


@app.post("/projects/{project_id}/manuscript")
async def import_manuscript(project_id: str, request: ImportManuscriptRequest):
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if request.content:
        result = ingester.ingest_from_api(request.content, request.format, request.title, request.author)
    else:
        raise HTTPException(status_code=400, detail="No content provided")

    if result.errors:
        raise HTTPException(status_code=400, detail={"errors": result.errors, "warnings": result.warnings})

    manuscript = result.manuscript
    db.create_manuscript(manuscript)

    project.manuscript_id = manuscript.id
    db.update_project(project)

    return {
        "manuscript_id": manuscript.id,
        "stats": result.stats,
        "warnings": result.warnings,
    }


@app.post("/projects/{project_id}/manuscript/file")
async def import_manuscript_file(
    project_id: str,
    file: UploadFile = File(...),
    title: str = Form(""),
    author: str = Form(""),
):
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Save uploaded file temporarily
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = ingester.ingest_file(tmp_path, title or file.filename, author)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if result.errors:
        raise HTTPException(status_code=400, detail={"errors": result.errors, "warnings": result.warnings})

    manuscript = result.manuscript
    db.create_manuscript(manuscript)

    project.manuscript_id = manuscript.id
    db.update_project(project)

    return {
        "manuscript_id": manuscript.id,
        "stats": result.stats,
        "warnings": result.warnings,
    }


@app.post("/projects/{project_id}/design")
async def configure_design(project_id: str, request: ConfigureDesignRequest):
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if request.brand_profile_id:
        profile = db.get_brand_profile(request.brand_profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Brand profile not found")
        project.brand_profile_id = profile.id

    db.update_project(project)
    return {"brand_profile_id": project.brand_profile_id}


@app.post("/projects/{project_id}/references")
async def add_reference(project_id: str, request: AddReferenceRequest):
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    ref = reference_library.add_reference(
        source_url=request.source_url,
        source_title=request.source_title,
        local_path=request.local_path,
        screenshot_path=request.screenshot_path,
        tags=request.tags,
    )

    return {"reference_id": ref.id, "reference": ref.__dict__}


@app.post("/projects/{project_id}/plan")
async def generate_editorial_plan(project_id: str, request: GeneratePlanRequest):
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.manuscript_id:
        raise HTTPException(status_code=400, detail="No manuscript imported")

    manuscript = db.get_manuscript(project.manuscript_id)
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")

    brand_profile = None
    if project.brand_profile_id:
        brand_profile = db.get_brand_profile(project.brand_profile_id)

    plan = art_director.create_publication_plan(
        manuscript, brand_profile, request.user_instructions
    )

    issues = art_director.validate_plan(plan)
    if issues:
        return {"plan_id": plan.id, "validation_issues": issues, "plan": plan.__dict__}

    db.create_editorial_plan(plan)
    project.editorial_plan_id = plan.id
    db.update_project(project)

    return {"plan_id": plan.id, "plan": plan.__dict__}


@app.post("/projects/{project_id}/render")
async def render_publication(project_id: str, request: RenderRequest):
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.editorial_plan_id:
        raise HTTPException(status_code=400, detail="No editorial plan generated")

    plan = db.get_editorial_plan(project.editorial_plan_id)
    manuscript = db.get_manuscript(project.manuscript_id)
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")

    # Get assets for this project
    assets = []
    # In a full implementation, we'd fetch assets associated with the plan

    # Create render job
    job = RenderJob(
        id=f"rj_{uuid.uuid4().hex[:12]}",
        project_id=project.id,
        editorial_plan_id=plan.id,
        status=JobStatus.RUNNING,
        started_at=datetime.now(),
    )
    db.create_render_job(job)

    project.render_job_id = job.id
    db.update_project(project)

    # Render PDF
    output_dir = Path(config["storage"]["projects_root"]) / project.id / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_pdf = output_dir / f"{project.name.replace(' ', '_')}.pdf"

    result = renderer.render_pdf(manuscript, plan, assets, str(output_pdf), request.strict_layout)

    if not result["success"]:
        job.status = JobStatus.FAILED
        job.error_message = result["error"]
        job.completed_at = datetime.now()
        db.update_render_job(job)
        raise HTTPException(status_code=500, detail=result["error"])

    job.status = JobStatus.COMPLETED
    job.output_pdf_path = result["output_path"]
    job.completed_at = datetime.now()
    db.update_render_job(job)

    # Run QA
    qa_report = qa_engine.inspect_publication(job, result["output_path"], plan.id)
    job.qa_report_id = qa_report.id
    db.update_render_job(job)

    return {
        "job_id": job.id,
        "pdf_path": job.output_pdf_path,
        "qa_report_id": qa_report.id,
        "qa_passed": qa_report.passed,
        "qa_score": qa_report.score,
    }


@app.get("/projects/{project_id}/status")
async def get_job_status(project_id: str):
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.render_job_id:
        return {"status": "no_job"}

    job = db.get_render_job(project.render_job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Render job not found")

    return job.__dict__


@app.get("/projects/{project_id}/qa")
async def get_qa_report(project_id: str):
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.render_job_id:
        raise HTTPException(status_code=404, detail="No render job")

    job = db.get_render_job(project.render_job_id)
    if not job or not job.qa_report_id:
        raise HTTPException(status_code=404, detail="No QA report")

    report = db.get_qa_report(job.qa_report_id)
    if not report:
        raise HTTPException(status_code=404, detail="QA report not found")

    return report.__dict__


@app.get("/projects/{project_id}/pages")
async def list_page_previews(project_id: str):
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.render_job_id:
        raise HTTPException(status_code=404, detail="No render job")

    job = db.get_render_job(project.render_job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Render job not found")

    return {"page_images": job.page_images}


@app.post("/projects/{project_id}/repair")
async def repair_page(project_id: str, request: RepairRequest):
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.render_job_id:
        raise HTTPException(status_code=404, detail="No render job")

    job = db.get_render_job(project.render_job_id)
    if not job or not job.qa_report_id:
        raise HTTPException(status_code=404, detail="No QA report")

    qa_report = db.get_qa_report(job.qa_report_id)
    if not qa_report:
        raise HTTPException(status_code=404, detail="QA report not found")

    success, messages = qa_engine.repair_defects(qa_report, job, project.manuscript_id, project.editorial_plan_id)

    if success and job.retry_count > 0:
        # Re-render
        manuscript = db.get_manuscript(project.manuscript_id)
        plan = db.get_editorial_plan(project.editorial_plan_id)
        assets = []

        output_dir = Path(config["storage"]["projects_root"]) / project.id / "output"
        output_pdf = output_dir / f"{project.name.replace(' ', '_')}_repaired.pdf"

        result = renderer.render_pdf(manuscript, plan, assets, str(output_pdf), request.strict_layout)

        if result["success"]:
            job.output_pdf_path = result["output_path"]
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            db.update_render_job(job)

            # Re-run QA
            qa_report = qa_engine.inspect_publication(job, result["output_path"], plan.id)
            job.qa_report_id = qa_report.id
            db.update_render_job(job)

    return {"success": success, "messages": messages, "retry_count": job.retry_count}


@app.post("/projects/{project_id}/export")
async def export_publication(project_id: str, request: ExportRequest):
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.render_job_id:
        raise HTTPException(status_code=404, detail="No render job")

    job = db.get_render_job(project.render_job_id)
    if not job or job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Publication not ready")

    manuscript = db.get_manuscript(project.manuscript_id)
    plan = db.get_editorial_plan(project.editorial_plan_id)
    qa_report = db.get_qa_report(job.qa_report_id)
    assets = []

    package = publisher.finalize_publication(project, manuscript, plan, job, qa_report, assets)

    return {
        "project_id": project.id,
        "pdf_path": package.pdf_path,
        "source_bundle_path": package.source_bundle_path,
        "export_package": package.__dict__,
    }


# Manuscript Endpoints
@app.get("/manuscripts/{manuscript_id}")
async def get_manuscript(manuscript_id: str):
    manuscript = db.get_manuscript(manuscript_id)
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")
    return manuscript.__dict__


# Editorial Plan Endpoints
@app.get("/editorial-plans/{plan_id}")
async def get_editorial_plan(plan_id: str):
    plan = db.get_editorial_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Editorial plan not found")
    return plan.__dict__


# Render Job Endpoints
@app.get("/render-jobs/{job_id}")
async def get_render_job(job_id: str):
    job = db.get_render_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Render job not found")
    return job.__dict__


# Visual Reference Endpoints
@app.post("/visual-references")
async def create_visual_reference(request: AddReferenceRequest):
    ref = reference_library.add_reference(
        source_url=request.source_url,
        source_title=request.source_title,
        local_path=request.local_path,
        screenshot_path=request.screenshot_path,
        tags=request.tags,
    )
    return {"reference_id": ref.id, "reference": ref.__dict__}


@app.get("/visual-references")
async def list_visual_references():
    refs = reference_library.list_references()
    return {"references": [r.__dict__ for r in refs]}


# Brand Profile Endpoints
@app.post("/brands")
async def create_brand_profile(profile: dict):
    bp = BrandProfile(
        id=f"bp_{uuid.uuid4().hex[:12]}",
        name=profile.get("name", ""),
        description=profile.get("description", ""),
        logo_path=profile.get("logo_path", ""),
        design_tokens=DesignTokens(**profile.get("design_tokens", {})),
        cover_conventions=profile.get("cover_conventions", {}),
        section_opener_conventions=profile.get("section_opener_conventions", {}),
        running_header_template=profile.get("running_header_template", ""),
        running_footer_template=profile.get("running_footer_template", ""),
    )
    db.create_brand_profile(bp)
    return {"brand_profile_id": bp.id}


@app.get("/brands")
async def list_brand_profiles():
    profiles = db.list_brand_profiles()
    return {"profiles": [p.__dict__ for p in profiles]}


@app.get("/brands/{profile_id}")
async def get_brand_profile(profile_id: str):
    profile = db.get_brand_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Brand profile not found")
    return profile.__dict__


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config["api"]["host"], port=config["api"]["port"])