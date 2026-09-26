from __future__ import annotations
import json
import sys
import uuid
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

from editorial_studio.core.config import load_config
from editorial_studio.core.database import Database
from editorial_studio.core.models import (
    BrandProfile,
    DesignTokens,
    JobStatus,
    Project,
)
from editorial_studio.content.ingestion import ManuscriptIngester
from editorial_studio.content.intelligence import ContentIntelligenceEngine
from editorial_studio.art_director.planner import EditorialArtDirector
from editorial_studio.asset_engine.manager import AssetManager, VisualReferenceLibrary
from editorial_studio.export.publisher import PublishingEngine
from editorial_studio.qa.engine import QAEngine
from editorial_studio.renderer.typst_renderer import TypstRenderer


app = typer.Typer(
    name="editorial-studio",
    help="Editorial Studio - AI Editorial Publishing Software",
    add_completion=False,
)

console = Console()
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


@app.command()
def create(
    name: str = typer.Argument(..., help="Project name"),
    description: str = typer.Option("", help="Project description"),
    tags: str = typer.Option("", help="Comma-separated tags"),
):
    """Create a new publication project."""
    project = Project(
        id=f"prj_{uuid.uuid4().hex[:12]}",
        name=name,
        description=description,
        tags=[t.strip() for t in tags.split(",") if t.strip()],
    )
    db.create_project(project)
    console.print(f"[green]Created project:[/green] {project.id} - {project.name}")


@app.command()
def list_projects(
    status: Optional[str] = typer.Option(None, help="Filter by status"),
):
    """List all projects."""
    projects = db.list_projects(status)
    if not projects:
        console.print("[yellow]No projects found[/yellow]")
        return

    table = Table(title="Projects")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Version", style="blue")
    table.add_column("Updated", style="dim")

    for p in projects:
        table.add_row(p.id, p.name, p.status, str(p.version), p.updated_at.strftime("%Y-%m-%d %H:%M"))

    console.print(table)


@app.command()
def import_manuscript(
    project_id: str = typer.Argument(..., help="Project ID"),
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="Manuscript file path"),
    content: Optional[str] = typer.Option(None, "--content", "-c", help="Manuscript content"),
    format: str = typer.Option("markdown", "--format", help="Format: markdown, text, json, html, docx"),
    title: str = typer.Option("", "--title", help="Manuscript title"),
    author: str = typer.Option("", "--author", help="Manuscript author"),
):
    """Import manuscript into a project."""
    project = db.get_project(project_id)
    if not project:
        console.print(f"[red]Project {project_id} not found[/red]")
        raise typer.Exit(1)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task("Importing manuscript...", total=None)

        if file:
            result = ingester.ingest_file(file, title or file.stem, author)
        elif content:
            result = ingester.ingest_from_api(content, format, title, author)
        else:
            console.print("[red]Either --file or --content must be provided[/red]")
            raise typer.Exit(1)

    if result.errors:
        for err in result.errors:
            console.print(f"[red]Error:[/red] {err}")
        raise typer.Exit(1)

    manuscript = result.manuscript
    db.create_manuscript(manuscript)

    project.manuscript_id = manuscript.id
    db.update_project(project)

    console.print(f"[green]Imported manuscript:[/green] {manuscript.id}")
    console.print(f"  Words: {result.stats.get('word_count', 0)}")
    console.print(f"  Blocks: {result.stats.get('block_count', 0)}")
    if result.warnings:
        for w in result.warnings:
            console.print(f"[yellow]Warning:[/yellow] {w}")


@app.command()
def configure_design(
    project_id: str = typer.Argument(..., help="Project ID"),
    brand: str = typer.Option("institutional", "--brand", "-b", help="Builtin brand profile"),
    preset_overrides: str = typer.Option("{}", "--overrides", "-o", help="JSON design token overrides"),
):
    """Configure design system for a project."""
    project = db.get_project(project_id)
    if not project:
        console.print(f"[red]Project {project_id} not found[/red]")
        raise typer.Exit(1)

    from editorial_studio.design_system.profiles import get_builtin_profile
    builtin = get_builtin_profile(brand)
    if not builtin:
        console.print(f"[red]Unknown brand profile: {brand}[/red]")
        console.print(
            "Available: institutional_editorial, institutional, educational, "
            "scientific, nature, minimalist"
        )
        raise typer.Exit(1)

    bp = BrandProfile(
        id=builtin.id,
        name=builtin.name,
        description=builtin.description,
        design_tokens=builtin.design_tokens,
        cover_conventions=builtin.cover_conventions,
        section_opener_conventions=builtin.section_opener_conventions,
    )
    db.create_brand_profile(bp)

    # Apply overrides
    try:
        overrides = json.loads(preset_overrides)
        for key, value in overrides.items():
            if hasattr(bp.design_tokens, key):
                setattr(bp.design_tokens, key, value)
        db.create_brand_profile(bp)
    except json.JSONDecodeError:
        console.print("[red]Invalid JSON in --overrides[/red]")
        raise typer.Exit(1)

    project.brand_profile_id = bp.id
    db.update_project(project)

    console.print(f"[green]Configured design:[/green] {bp.name} ({bp.id})")


@app.command()
def add_reference(
    project_id: str = typer.Argument(..., help="Project ID"),
    url: str = typer.Option("", "--url", help="Reference URL (e.g., Pinterest)"),
    title: str = typer.Option("", "--title", help="Reference title"),
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="Local reference image"),
    screenshot: Optional[Path] = typer.Option(None, "--screenshot", "-s", help="Screenshot image"),
    tags: str = typer.Option("", "--tags", help="Comma-separated tags"),
):
    """Add a visual reference."""
    project = db.get_project(project_id)
    if not project:
        console.print(f"[red]Project {project_id} not found[/red]")
        raise typer.Exit(1)

    ref = reference_library.add_reference(
        source_url=url,
        source_title=title,
        local_path=str(file) if file else "",
        screenshot_path=str(screenshot) if screenshot else "",
        tags=[t.strip() for t in tags.split(",") if t.strip()],
    )

    console.print(f"[green]Added reference:[/green] {ref.id} - {ref.retrieval_status}")


@app.command()
def analyze(
    project_id: str = typer.Argument(..., help="Project ID"),
):
    """Analyze manuscript structure and content."""
    project = db.get_project(project_id)
    if not project:
        console.print(f"[red]Project {project_id} not found[/red]")
        raise typer.Exit(1)

    if not project.manuscript_id:
        console.print("[red]No manuscript imported[/red]")
        raise typer.Exit(1)

    manuscript = db.get_manuscript(project.manuscript_id)
    if not manuscript:
        console.print("[red]Manuscript not found[/red]")
        raise typer.Exit(1)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task("Analyzing manuscript...", total=None)
        analysis = intelligence.analyze(manuscript)
        brief = intelligence.generate_publication_brief(analysis)

    console.print(Panel.fit(f"[bold]Manuscript Analysis: {manuscript.title}[/bold]"))
    console.print(f"  Total words: {analysis.total_words:,}")
    console.print(f"  Total blocks: {analysis.total_blocks}")
    console.print(f"  Chapters: {analysis.chapters}")
    console.print(f"  Sections: {analysis.sections}")
    console.print(f"  Reading level: {analysis.reading_level}")
    console.print(f"  Estimated pages: {analysis.estimated_pages}")
    console.print(f"  Has tables: {analysis.has_tables}")
    console.print(f"  Has code: {analysis.has_code}")
    console.print(f"  Has images: {analysis.has_images}")
    console.print(f"  Has exercises: {analysis.has_exercises}")
    console.print(f"  Has citations: {analysis.has_citations}")

    console.print("\n[bold]Content Types:[/bold]")
    for ct, count in analysis.content_type_distribution.items():
        console.print(f"  {ct}: {count}")

    console.print("\n[bold]Publication Brief:[/bold]")
    for key, value in brief.items():
        console.print(f"  {key}: {value}")


@app.command()
def plan(
    project_id: str = typer.Argument(..., help="Project ID"),
    instructions: str = typer.Option("", "--instructions", "-i", help="Editorial instructions"),
):
    """Generate editorial plan."""
    project = db.get_project(project_id)
    if not project:
        console.print(f"[red]Project {project_id} not found[/red]")
        raise typer.Exit(1)

    if not project.manuscript_id:
        console.print("[red]No manuscript imported[/red]")
        raise typer.Exit(1)

    manuscript = db.get_manuscript(project.manuscript_id)
    brand_profile = db.get_brand_profile(project.brand_profile_id) if project.brand_profile_id else None

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task("Generating editorial plan...", total=None)
        plan = art_director.create_publication_plan(manuscript, brand_profile, instructions)

    issues = art_director.validate_plan(plan)
    db.create_editorial_plan(plan)
    project.editorial_plan_id = plan.id
    db.update_project(project)

    console.print(f"[green]Generated editorial plan:[/green] {plan.id}")
    console.print(f"  Pages planned: {len(plan.page_plans)}")
    console.print(f"  Asset briefs: {len(plan.asset_briefs)}")

    if issues:
        console.print("[yellow]Validation issues:[/yellow]")
        for issue in issues:
            console.print(f"  - {issue}")

    # Show page plan summary
    table = Table(title="Page Plans")
    table.add_column("Page", style="cyan")
    table.add_column("Purpose", style="green")
    table.add_column("Layout", style="yellow")
    table.add_column("Blocks", style="blue")

    for p in plan.page_plans:
        table.add_row(str(p.page_number), p.purpose.value, p.layout_family.value, str(len(p.content_block_ids)))

    console.print(table)


@app.command()
def render(
    project_id: str = typer.Argument(..., help="Project ID"),
    strict: bool = typer.Option(False, "--strict", help="Fail on layout defects"),
    preview: bool = typer.Option(False, "--preview", help="Generate preview images only"),
):
    """Render publication to PDF."""
    project = db.get_project(project_id)
    if not project:
        console.print(f"[red]Project {project_id} not found[/red]")
        raise typer.Exit(1)

    if not project.editorial_plan_id:
        console.print("[red]No editorial plan generated[/red]")
        raise typer.Exit(1)

    plan = db.get_editorial_plan(project.editorial_plan_id)
    manuscript = db.get_manuscript(project.manuscript_id)
    if not manuscript:
        console.print("[red]Manuscript not found[/red]")
        raise typer.Exit(1)

    assets = []

    from editorial_studio.core.models import RenderJob
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

    if preview:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Generating preview...", total=None)
            result = renderer.render_preview(manuscript, plan, assets, str(output_dir))

        if result["success"]:
            console.print(f"[green]Preview generated:[/green] {len(result['preview_paths'])} pages")
            for p in result["preview_paths"]:
                console.print(f"  {p}")
        else:
            console.print(f"[red]Preview failed:[/red] {result['error']}")
        return

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task("Rendering PDF...", total=None)
        result = renderer.render_pdf(manuscript, plan, assets, str(output_dir / f"{project.name.replace(' ', '_')}.pdf"), strict)

    if not result["success"]:
        job.status = JobStatus.FAILED
        job.error_message = result["error"]
        db.update_render_job(job)
        console.print(f"[red]Render failed:[/red] {result['error']}")
        raise typer.Exit(1)

    job.status = JobStatus.COMPLETED
    job.output_pdf_path = result["output_path"]
    db.update_render_job(job)

    console.print(f"[green]PDF rendered:[/green] {job.output_pdf_path}")

    # Content accounting: every block the manuscript carried, and what became
    # of it. Reported before the visual QA because a dropped block is invisible
    # on the page -- the page looks fine precisely because the content is gone.
    account = result.get("content_account") or {}
    if account:
        counts = account.get("counts", {})
        colour = "green" if account.get("complete") else "red"
        console.print(
            f"\n[bold]Content account:[/bold] "
            f"[{colour}]{account.get('summary', '')}[/{colour}]"
        )
        for entry in account.get("unaccounted", [])[:20]:
            console.print(
                f"  [red]dropped[/red] {entry['block_id']} "
                f"({entry['content_type']}/{entry['semantic_role']}, "
                f"chapter {entry.get('chapter', 0)}): {entry.get('preview', '')}"
            )
        if len(account.get("unaccounted", [])) > 20:
            console.print(
                f"  [red]...and "
                f"{len(account['unaccounted']) - 20} more[/red]"
            )

    # Run QA
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task("Running quality checks...", total=None)
        qa_report = qa_engine.inspect_publication(job, result["output_path"], plan.id)

    # Content integrity is part of the report, not a side channel.
    drop_issues = qa_engine.check_content_accounting(manuscript, result)
    if drop_issues:
        qa_report.issues.extend(drop_issues)
        qa_report.score = min(qa_report.score, 100.0 - 10.0 * len(drop_issues))
        qa_report.passed = qa_report.passed and not drop_issues

    job.qa_report_id = qa_report.id
    db.update_render_job(job)

    console.print(f"\n[bold]QA Report:[/bold]")
    console.print(f"  Passed: {'[green]Yes[/green]' if qa_report.passed else '[red]No[/red]'}")
    console.print(f"  Score: {qa_report.score:.1f}/100")
    console.print(f"  Pages: {qa_report.total_pages}")
    console.print(f"  Hard failures: {len(qa_report.hard_failures())}")
    console.print(f"  Warnings: {len(qa_report.warnings())}")


@app.command()
def inspect(
    project_id: str = typer.Argument(..., help="Project ID"),
    page: Optional[int] = typer.Option(None, "--page", "-p", help="Specific page to inspect"),
):
    """Inspect publication quality."""
    project = db.get_project(project_id)
    if not project:
        console.print(f"[red]Project {project_id} not found[/red]")
        raise typer.Exit(1)

    if not project.render_job_id:
        console.print("[red]No render job[/red]")
        raise typer.Exit(1)

    job = db.get_render_job(project.render_job_id)
    if not job or not job.qa_report_id:
        console.print("[red]No QA report available[/red]")
        raise typer.Exit(1)

    qa_report = db.get_qa_report(job.qa_report_id)
    if not qa_report:
        console.print("[red]QA report not found[/red]")
        raise typer.Exit(1)

    if page:
        page_issues = [i for i in qa_report.issues if i.page_number == page]
        console.print(f"[bold]Page {page} Issues:[/bold]")
        if not page_issues:
            console.print("  No issues found")
        for issue in page_issues:
            color = "red" if issue.severity in (QASeverity.ERROR, QASeverity.CRITICAL) else "yellow"
            console.print(f"  [{color}]{issue.severity.value.upper()}[/{color}] [{issue.category}] {issue.message}")
            if issue.suggested_fix:
                console.print(f"    Fix: {issue.suggested_fix}")
    else:
        console.print(Panel.fit(f"[bold]QA Report: {project.name}[/bold]"))
        console.print(f"  Status: {'[green]PASSED[/green]' if qa_report.passed else '[red]FAILED[/red]'}")
        console.print(f"  Score: {qa_report.score:.1f}/100")
        console.print(f"  Pages: {qa_report.total_pages}")
        console.print(f"  Hard failures: {len(qa_report.hard_failures())}")
        console.print(f"  Warnings: {len(qa_report.warnings())}")
        console.print(f"  Summary: {qa_report.summary}")


@app.command()
def repair(
    project_id: str = typer.Argument(..., help="Project ID"),
    page: Optional[int] = typer.Option(None, "--page", "-p", help="Specific page to repair"),
    max_retries: int = typer.Option(3, "--max-retries", help="Maximum repair attempts"),
):
    """Repair publication defects."""
    project = db.get_project(project_id)
    if not project:
        console.print(f"[red]Project {project_id} not found[/red]")
        raise typer.Exit(1)

    if not project.render_job_id:
        console.print("[red]No render job[/red]")
        raise typer.Exit(1)

    job = db.get_render_job(project.render_job_id)
    if not job or not job.qa_report_id:
        console.print("[red]No QA report available[/red]")
        raise typer.Exit(1)

    qa_report = db.get_qa_report(job.qa_report_id)
    if not qa_report:
        console.print("[red]QA report not found[/red]")
        raise typer.Exit(1)

    if job.retry_count >= max_retries:
        console.print(f"[red]Max retries ({max_retries}) reached[/red]")
        raise typer.Exit(1)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task("Attempting repairs...", total=None)
        success, messages = qa_engine.repair_defects(qa_report, job, project.manuscript_id, project.editorial_plan_id)

    console.print(f"Repair {'[green]successful[/green]' if success else '[red]failed[/red]'}:")
    for msg in messages:
        console.print(f"  - {msg}")

    if success and job.retry_count > 0:
        manuscript = db.get_manuscript(project.manuscript_id)
        plan = db.get_editorial_plan(project.editorial_plan_id)
        assets = []

        output_dir = Path(config["storage"]["projects_root"]) / project.id / "output"
        output_pdf = output_dir / f"{project.name.replace(' ', '_')}_repaired.pdf"

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Re-rendering...", total=None)
            result = renderer.render_pdf(manuscript, plan, assets, str(output_pdf), False)

        if result["success"]:
            job.output_pdf_path = result["output_path"]
            job.status = JobStatus.COMPLETED
            db.update_render_job(job)

            qa_report = qa_engine.inspect_publication(job, result["output_path"], plan.id)
            job.qa_report_id = qa_report.id
            db.update_render_job(job)

            console.print(f"[green]Re-rendered:[/green] {job.output_pdf_path}")
            console.print(f"  QA Passed: {'Yes' if qa_report.passed else 'No'}")


@app.command()
def export(
    project_id: str = typer.Argument(..., help="Project ID"),
):
    """Export final publication package."""
    project = db.get_project(project_id)
    if not project:
        console.print(f"[red]Project {project_id} not found[/red]")
        raise typer.Exit(1)

    if not project.render_job_id:
        console.print("[red]No render job[/red]")
        raise typer.Exit(1)

    job = db.get_render_job(project.render_job_id)
    if not job or job.status != JobStatus.COMPLETED:
        console.print("[red]Publication not ready[/red]")
        raise typer.Exit(1)

    manuscript = db.get_manuscript(project.manuscript_id)
    plan = db.get_editorial_plan(project.editorial_plan_id)
    qa_report = db.get_qa_report(job.qa_report_id)
    assets = []

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task("Creating publication package...", total=None)
        package = publisher.finalize_publication(project, manuscript, plan, job, qa_report, assets)

    console.print(f"[green]Exported publication package:[/green]")
    console.print(f"  PDF: {package.pdf_path}")
    console.print(f"  Source bundle: {package.source_bundle_path}")
    console.print(f"  Asset manifest: {package.asset_manifest_path}")
    console.print(f"  Editorial plan: {package.editorial_plan_path}")
    console.print(f"  QA report: {package.qa_report_path}")
    console.print(f"  Metadata: {package.metadata_path}")


@app.command()
def assemble(
    brief: Path = typer.Argument(..., help="Publication brief JSON"),
    outline: Path = typer.Argument(..., help="Outline JSON written by your agent"),
    project_name: str = typer.Option("", "--project-name", help="Name for the created project"),
):
    """Turn an agent-written brief and outline into a validated project.

    This is the entry point for an agent that has already done the thinking.
    The brief says what is being published and in whose vocabulary; the outline
    carries the chapters, sections and blocks. The engine assembles them,
    records where each block came from, refuses citations to sources that were
    never supplied, and creates a project ready for `plan` and `render`.

    Nothing here interprets the subject. The engine has no opinion about what
    the publication is about, and will not fill a gap the outline leaves.
    """
    from editorial_studio.content.assembly import (
        ManuscriptAssembler,
        PublicationBrief,
    )

    try:
        brief_raw = json.loads(brief.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        console.print(f"[red]Cannot read brief:[/red] {exc}")
        raise typer.Exit(1)
    try:
        outline_raw = json.loads(outline.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        console.print(f"[red]Cannot read outline:[/red] {exc}")
        raise typer.Exit(1)

    chapters = outline_raw.get("outline", outline_raw) if isinstance(outline_raw, dict) else outline_raw
    if not isinstance(chapters, list):
        console.print("[red]Outline must be a list of chapters, or an object with an 'outline' list[/red]")
        raise typer.Exit(1)

    publication = PublicationBrief(
        title=str(brief_raw.get("title", "")),
        subtitle=str(brief_raw.get("subtitle", "")),
        author=str(brief_raw.get("author", "")),
        audience=str(brief_raw.get("audience", "")),
        purpose=str(brief_raw.get("purpose", "")),
        tone=str(brief_raw.get("tone", "")),
        format=str(brief_raw.get("format", "book")),
        target_words=int(brief_raw.get("target_words", 0) or 0),
        domain_terms=dict(brief_raw.get("domain_terms", {}) or {}),
    )
    if not publication.title:
        console.print("[red]The brief must have a title[/red]")
        raise typer.Exit(1)

    result = ManuscriptAssembler().assemble(
        publication,
        chapters,
        sources=brief_raw.get("sources", []) or [],
        front_matter=brief_raw.get("front_matter", []) or [],
        back_matter=brief_raw.get("back_matter", []) or [],
    )

    if result.errors:
        console.print(f"[red]Assembly failed with {len(result.errors)} problem(s):[/red]")
        for error in result.errors[:40]:
            console.print(f"  [red]-[/red] {error}")
        if len(result.errors) > 40:
            console.print(f"  [red]...and {len(result.errors) - 40} more[/red]")
        raise typer.Exit(1)

    project = Project(
        id=f"prj_{uuid.uuid4().hex[:12]}",
        name=project_name or publication.title,
    )
    db.create_project(project)
    db.create_manuscript(result.manuscript)
    project.manuscript_id = result.manuscript.id
    db.update_project(project)

    console.print(f"[green]Assembled:[/green] {project.id}")
    console.print(f"  Title: {result.manuscript.title}")
    console.print(f"  Blocks: {len(result.manuscript.content_blocks)}")
    console.print(f"  Words: {result.manuscript.total_word_count()}")
    console.print(f"  Sources registered: {len(result.sources)}")
    console.print("\n[bold]Provenance[/bold] (what each block is):")
    for kind, count in sorted(result.provenance_counts.items()):
        console.print(f"  {kind:>18}: {count}")
    for warning in result.warnings:
        console.print(f"  [yellow]warning:[/yellow] {warning}")
    console.print(
        f"\nNext: [cyan]plan {project.id}[/cyan] then [cyan]render {project.id}[/cyan]"
    )


@app.command()
def account(
    project_id: str = typer.Argument(..., help="Project ID"),
):
    """Report what became of every content block in a project.

    Renders without keeping the PDF's image output, then prints the account: how
    many blocks were typeset, how many were used as section titles, and -- the
    part that matters -- any that reached no page at all. A block that reached
    no page is a defect, and this is how you find out.
    """
    project = db.get_project(project_id)
    if not project:
        console.print(f"[red]Project {project_id} not found[/red]")
        raise typer.Exit(1)
    if not project.editorial_plan_id:
        console.print("[red]No editorial plan generated[/red]")
        raise typer.Exit(1)

    plan = db.get_editorial_plan(project.editorial_plan_id)
    manuscript = db.get_manuscript(project.manuscript_id)
    if not manuscript:
        console.print("[red]Manuscript not found[/red]")
        raise typer.Exit(1)

    output_dir = Path(config["storage"]["projects_root"]) / project.id / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    result = renderer.render_pdf(
        manuscript, plan, [], str(output_dir / "account_check.pdf"))

    report = result.get("content_account")
    if not report:
        console.print(f"[red]No content account. Render error:[/red] {result.get('error', '')}")
        raise typer.Exit(1)

    colour = "green" if report["complete"] else "red"
    console.print(f"[bold]Content account for[/bold] {project.name} "
                  f"[{colour}]{report['summary']}[/{colour}]")
    counts = report["counts"]
    table = Table(show_header=True, header_style="bold")
    table.add_column("Disposition", style="cyan")
    table.add_column("Count", justify="right")
    table.add_row("rendered", str(counts["rendered"]))
    table.add_row("consumed as a section title", str(counts["consumed"]))
    table.add_row("unaccounted", str(counts["unaccounted"]))
    console.print(table)

    if report["unaccounted"]:
        console.print("[red]The following blocks reached no page:[/red]")
        for entry in report["unaccounted"][:40]:
            console.print(
                f"  [red]{entry['block_id']}[/red] "
                f"{entry['content_type']}/{entry['semantic_role']} "
                f"chapter {entry.get('chapter', 0)}: {entry.get('preview', '')}"
            )
        raise typer.Exit(1)


@app.command()
def brands():
    """List available brand profiles."""
    from editorial_studio.design_system.profiles import list_builtin_profiles

    profiles = list_builtin_profiles()
    table = Table(title="Builtin Brand Profiles")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Description", style="white")

    for p in profiles:
        table.add_row(p.id, p.name, p.description)

    console.print(table)


@app.command()
def end_to_end(
    manuscript: Path = typer.Argument(..., help="Manuscript file"),
    brand: str = typer.Option("institutional", "--brand", "-b", help="Brand profile"),
    title: str = typer.Option("", "--title", help="Publication title"),
    author: str = typer.Option("", "--author", help="Author name"),
    output: Path = typer.Option(Path("output.pdf"), "--output", "-o", help="Output PDF path"),
    strict: bool = typer.Option(False, "--strict", help="Strict layout mode"),
):
    """Run complete end-to-end publishing pipeline."""
    project_name = title or manuscript.stem

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        # Create project
        task = progress.add_task("Creating project...", total=None)
        project = Project(id=f"prj_{uuid.uuid4().hex[:12]}", name=project_name)
        db.create_project(project)

        # Import manuscript
        progress.update(task, description="Importing manuscript...")
        result = ingester.ingest_file(manuscript, title or manuscript.stem, author)
        if result.errors:
            for err in result.errors:
                console.print(f"[red]Error:[/red] {err}")
            raise typer.Exit(1)

        ms = result.manuscript
        db.create_manuscript(ms)
        project.manuscript_id = ms.id

        # Configure design
        progress.update(task, description="Configuring design...")
        from editorial_studio.design_system.profiles import get_builtin_profile
        builtin = get_builtin_profile(brand)
        if builtin:
            bp = BrandProfile(id=builtin.id, name=builtin.name, description=builtin.description,
                            design_tokens=builtin.design_tokens, cover_conventions=builtin.cover_conventions,
                            section_opener_conventions=builtin.section_opener_conventions)
            if not db.get_brand_profile(bp.id):
                db.create_brand_profile(bp)
            project.brand_profile_id = bp.id

        # Generate plan
        progress.update(task, description="Generating editorial plan...")
        plan = art_director.create_publication_plan(ms, bp)
        issues = art_director.validate_plan(plan)
        db.create_editorial_plan(plan)
        project.editorial_plan_id = plan.id

        # Render
        progress.update(task, description="Rendering PDF...")
        assets = []
        result = renderer.render_pdf(ms, plan, assets, str(output), strict)

        if not result["success"]:
            console.print(f"[red]Render failed:[/red] {result['error']}")
            raise typer.Exit(1)

        # QA
        progress.update(task, description="Running quality checks...")
        from editorial_studio.core.models import RenderJob
        job = RenderJob(id=f"rj_{uuid.uuid4().hex[:12]}", project_id=project.id, editorial_plan_id=plan.id,
                       status=JobStatus.COMPLETED, output_pdf_path=result["output_path"])
        db.create_render_job(job)

        qa_report = qa_engine.inspect_publication(job, result["output_path"], plan.id)

        # Export
        progress.update(task, description="Creating package...")
        assets = []
        package = publisher.finalize_publication(project, ms, plan, job, qa_report, assets)

    console.print(Panel.fit(f"[bold green]Publication Complete![/bold green]"))
    console.print(f"  PDF: {package.pdf_path}")
    console.print(f"  QA Score: {qa_report.score:.1f}/100")
    console.print(f"  Pages: {qa_report.total_pages}")
    console.print(f"  Source bundle: {package.source_bundle_path}")


if __name__ == "__main__":
    app()