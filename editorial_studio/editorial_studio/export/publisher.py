from __future__ import annotations
import json
import shutil
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from editorial_studio.core.models import (
    Asset,
    EditorialPlan,
    Manuscript,
    Project,
    QAReport,
    RenderJob,
)
from editorial_studio.core.database import Database
from editorial_studio.core.config import load_config


@dataclass
class ExportPackage:
    project_id: str
    pdf_path: str
    source_bundle_path: str
    asset_manifest_path: str
    editorial_plan_path: str
    qa_report_path: str
    metadata_path: str


class PublishingEngine:
    def __init__(self, database: Database):
        self.db = database
        self.config = load_config().data
        self.projects_root = Path(self.config.get("storage", {}).get("projects_root", "data/projects"))
        self.projects_root.mkdir(parents=True, exist_ok=True)
        self.output_root = Path(self.config.get("cli", {}).get("default_output_dir", "output"))
        self.output_root.mkdir(parents=True, exist_ok=True)

    def finalize_publication(
        self,
        project: Project,
        manuscript: Manuscript,
        plan: EditorialPlan,
        job: RenderJob,
        qa_report: QAReport,
        assets: list[Asset],
    ) -> ExportPackage:
        """Create final publication package with all artifacts."""
        project_dir = self.projects_root / project.id
        project_dir.mkdir(parents=True, exist_ok=True)

        # 1. Copy final PDF to project directory
        final_pdf = project_dir / f"{project.name.replace(' ', '_')}.pdf"
        if job.output_pdf_path and Path(job.output_pdf_path).exists():
            shutil.copy2(job.output_pdf_path, final_pdf)

        # 2. Create source bundle (editable project)
        source_bundle = self._create_source_bundle(
            project_dir, project, manuscript, plan, job, qa_report, assets
        )

        # 3. Create asset manifest
        asset_manifest = self._create_asset_manifest(project_dir, assets, plan)

        # 4. Save editorial plan
        editorial_plan_path = self._save_editorial_plan(project_dir, plan)

        # 5. Save QA report
        qa_report_path = self._save_qa_report(project_dir, qa_report)

        # 6. Save metadata
        metadata_path = self._save_metadata(project_dir, project, manuscript, plan, job, qa_report)

        # 7. Create distribution ZIP
        dist_zip = self.output_root / f"{project.id}_publication.zip"
        self._create_distribution_zip(
            dist_zip, final_pdf, source_bundle, asset_manifest,
            editorial_plan_path, qa_report_path, metadata_path
        )

        # Update project
        project.output_pdf_path = str(final_pdf)
        project.source_bundle_path = str(source_bundle)
        project.status = "published"
        project.version += 1
        self.db.update_project(project)

        return ExportPackage(
            project_id=project.id,
            pdf_path=str(final_pdf),
            source_bundle_path=str(source_bundle),
            asset_manifest_path=str(asset_manifest),
            editorial_plan_path=str(editorial_plan_path),
            qa_report_path=str(qa_report_path),
            metadata_path=str(metadata_path),
        )

    def _create_source_bundle(
        self,
        project_dir: Path,
        project: Project,
        manuscript: Manuscript,
        plan: EditorialPlan,
        job: RenderJob,
        qa_report: QAReport,
        assets: list[Asset],
    ) -> Path:
        """Create editable source bundle with all project data."""
        bundle_dir = project_dir / "source_bundle"
        bundle_dir.mkdir(parents=True, exist_ok=True)

        # Manuscript
        manuscript_data = {
            "id": manuscript.id,
            "title": manuscript.title,
            "author": manuscript.author,
            "description": manuscript.description,
            "source_format": manuscript.source_format,
            "source_files": manuscript.source_files,
            "content_blocks": [
                {
                    "id": b.id,
                    "content": b.content,
                    "content_type": b.content_type.value,
                    "semantic_role": b.semantic_role.value,
                    "chapter": b.chapter,
                    "section": b.section,
                    "subsection": b.subsection,
                    "order": b.order,
                    "level": b.level,
                    "source_ref": b.source_ref,
                    "source_file": b.source_file,
                    "source_line": b.source_line,
                    "citations": b.citations,
                    "hyperlinks": b.hyperlinks,
                    "references": b.references,
                    "editorial_constraints": b.editorial_constraints,
                    "user_instructions": b.user_instructions,
                    "is_generated": b.is_generated,
                    "traceability": b.traceability,
                    "metadata": b.metadata,
                }
                for b in manuscript.content_blocks
            ],
            "structure": manuscript.structure,
            "metadata": manuscript.metadata,
        }
        (bundle_dir / "manuscript.json").write_text(json.dumps(manuscript_data, indent=2, ensure_ascii=False))

        # Editorial plan
        plan_data = {
            "id": plan.id,
            "manuscript_id": plan.manuscript_id,
            "brand_profile_id": plan.brand_profile_id,
            "design_tokens": self._tokens_to_dict(plan.design_tokens),
            "publication_brief": plan.publication_brief,
            "page_plans": [
                {
                    "id": p.id,
                    "page_number": p.page_number,
                    "purpose": p.purpose.value,
                    "layout_family": p.layout_family.value,
                    "content_block_ids": p.content_block_ids,
                    "page_width_mm": p.page_width_mm,
                    "page_height_mm": p.page_height_mm,
                    "safe_area": p.safe_area,
                    "margins": p.margins,
                    "grid": p.grid,
                    "regions": p.regions,
                    "typography": p.typography,
                    "image_briefs": p.image_briefs,
                    "components": p.components,
                    "header_footer": p.header_footer,
                    "accessibility": p.accessibility,
                    "validation_criteria": p.validation_criteria,
                    "density_target": p.density_target,
                    "notes": p.notes,
                }
                for p in plan.page_plans
            ],
            "asset_briefs": plan.asset_briefs,
            "structure_map": plan.structure_map,
            "pagination_strategy": plan.pagination_strategy,
        }
        (bundle_dir / "editorial_plan.json").write_text(json.dumps(plan_data, indent=2, ensure_ascii=False))

        # Render job
        job_data = {
            "id": job.id,
            "project_id": job.project_id,
            "editorial_plan_id": job.editorial_plan_id,
            "status": job.status.value,
            "progress": job.progress,
            "current_step": job.current_step,
            "output_pdf_path": job.output_pdf_path,
            "page_images": job.page_images,
            "qa_report_id": job.qa_report_id,
            "error_message": job.error_message,
            "logs": job.logs,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "retry_count": job.retry_count,
        }
        (bundle_dir / "render_job.json").write_text(json.dumps(job_data, indent=2, ensure_ascii=False))

        # Assets manifest
        assets_data = [
            {
                "id": a.id,
                "asset_type": a.asset_type,
                "local_path": a.local_path,
                "original_source": a.original_source,
                "generation_provider": a.generation_provider,
                "prompt": a.prompt,
                "generation_metadata": a.generation_metadata,
                "source_url": a.source_url,
                "license": a.license,
                "provenance": a.provenance,
                "width_px": a.width_px,
                "height_px": a.height_px,
                "dpi": a.dpi,
                "intended_page_id": a.intended_page_id,
                "placement": a.placement,
                "crop_settings": a.crop_settings,
                "focal_point": a.focal_point,
                "aspect_ratio": a.aspect_ratio,
                "caption": a.caption,
                "alt_text": a.alt_text,
            }
            for a in assets
        ]
        (bundle_dir / "assets.json").write_text(json.dumps(assets_data, indent=2, ensure_ascii=False))

        # Project info
        project_data = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "manuscript_id": project.manuscript_id,
            "brand_profile_id": project.brand_profile_id,
            "editorial_plan_id": project.editorial_plan_id,
            "render_job_id": project.render_job_id,
            "output_pdf_path": project.output_pdf_path,
            "source_bundle_path": project.source_bundle_path,
            "version": project.version,
            "status": project.status,
            "tags": project.tags,
            "metadata": project.metadata,
        }
        (bundle_dir / "project.json").write_text(json.dumps(project_data, indent=2, ensure_ascii=False))

        return bundle_dir

    def _create_asset_manifest(self, project_dir: Path, assets: list[Asset], plan: EditorialPlan) -> Path:
        manifest_path = project_dir / "asset_manifest.json"
        manifest = {
            "project_id": plan.manuscript_id,
            "generated_at": datetime.now().isoformat(),
            "assets": [
                {
                    "id": a.id,
                    "type": a.asset_type,
                    "file": Path(a.local_path).name,
                    "source": a.original_source or a.generation_provider,
                    "license": a.license,
                    "dimensions": f"{a.width_px}x{a.height_px}",
                    "dpi": a.dpi,
                    "page": a.intended_page_id,
                    "caption": a.caption,
                }
                for a in assets
            ],
            "asset_briefs": plan.asset_briefs,
        }
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
        return manifest_path

    def _save_editorial_plan(self, project_dir: Path, plan: EditorialPlan) -> Path:
        path = project_dir / "editorial_plan.json"
        data = {
            "id": plan.id,
            "manuscript_id": plan.manuscript_id,
            "brand_profile_id": plan.brand_profile_id,
            "design_tokens": self._tokens_to_dict(plan.design_tokens),
            "publication_brief": plan.publication_brief,
            "page_plans": [
                {
                    "id": p.id,
                    "page_number": p.page_number,
                    "purpose": p.purpose.value,
                    "layout_family": p.layout_family.value,
                    "content_block_ids": p.content_block_ids,
                    "image_briefs": p.image_briefs,
                }
                for p in plan.page_plans
            ],
            "asset_briefs": plan.asset_briefs,
        }
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        return path

    def _save_qa_report(self, project_dir: Path, qa_report: QAReport) -> Path:
        path = project_dir / "qa_report.json"
        data = {
            "id": qa_report.id,
            "publication_id": qa_report.publication_id,
            "render_job_id": qa_report.render_job_id,
            "total_pages": qa_report.total_pages,
            "passed": qa_report.passed,
            "score": qa_report.score,
            "summary": qa_report.summary,
            "issues": [
                {
                    "id": i.id,
                    "page_id": i.page_id,
                    "page_number": i.page_number,
                    "severity": i.severity.value,
                    "category": i.category,
                    "message": i.message,
                    "location": i.location,
                    "suggested_fix": i.suggested_fix,
                    "auto_fixable": i.auto_fixable,
                    "fix_applied": i.fix_applied,
                }
                for i in qa_report.issues
            ],
        }
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        return path

    def _save_metadata(self, project_dir: Path, project: Project, manuscript: Manuscript,
                       plan: EditorialPlan, job: RenderJob, qa_report: QAReport) -> Path:
        path = project_dir / "metadata.json"
        data = {
            "project": {
                "id": project.id,
                "name": project.name,
                "version": project.version,
                "status": project.status,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat(),
            },
            "manuscript": {
                "id": manuscript.id,
                "title": manuscript.title,
                "author": manuscript.author,
                "word_count": manuscript.total_word_count(),
                "block_count": len(manuscript.content_blocks),
                "chapters": max((b.chapter for b in manuscript.content_blocks), default=0),
            },
            "editorial_plan": {
                "id": plan.id,
                "page_count": len(plan.page_plans),
                "asset_brief_count": len(plan.asset_briefs),
            },
            "render_job": {
                "id": job.id,
                "status": job.status.value,
                "retry_count": job.retry_count,
                "output_pdf": job.output_pdf_path,
            },
            "qa_report": {
                "id": qa_report.id,
                "passed": qa_report.passed,
                "score": qa_report.score,
                "total_issues": len(qa_report.issues),
                "hard_failures": len(qa_report.hard_failures()),
            },
            "exported_at": datetime.now().isoformat(),
        }
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        return path

    def _create_distribution_zip(
        self,
        zip_path: Path,
        pdf_path: Path,
        source_bundle: Path,
        asset_manifest: Path,
        editorial_plan: Path,
        qa_report: Path,
        metadata: Path,
    ) -> Path:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(pdf_path, f"publication/{pdf_path.name}")
            for file_path in source_bundle.rglob("*"):
                if file_path.is_file():
                    rel = file_path.relative_to(source_bundle.parent)
                    zf.write(file_path, f"source_bundle/{rel}")
            zf.write(asset_manifest, f"publication/{asset_manifest.name}")
            zf.write(editorial_plan, f"publication/{editorial_plan.name}")
            zf.write(qa_report, f"publication/{qa_report.name}")
            zf.write(metadata, f"publication/{metadata.name}")
        return zip_path

    def _tokens_to_dict(self, tokens) -> dict:
        return {
            "brand_name": tokens.brand_name,
            "page_width_mm": tokens.page_width_mm,
            "page_height_mm": tokens.page_height_mm,
            "margin_top_mm": tokens.margin_top_mm,
            "margin_bottom_mm": tokens.margin_bottom_mm,
            "margin_inner_mm": tokens.margin_inner_mm,
            "margin_outer_mm": tokens.margin_outer_mm,
            "columns": tokens.columns,
            "column_gutter_mm": tokens.column_gutter_mm,
            "body_font_family": tokens.body_font_family,
            "heading_font_family": tokens.heading_font_family,
            "mono_font_family": tokens.mono_font_family,
            "body_font_size_pt": tokens.body_font_size_pt,
            "heading_font_sizes": tokens.heading_font_sizes,
            "line_height_em": tokens.line_height_em,
            "paragraph_spacing_em": tokens.paragraph_spacing_em,
            "first_line_indent_em": tokens.first_line_indent_em,
            "colors": tokens.colors,
            "heading_weights": tokens.heading_weights,
            "numbered_headings": tokens.numbered_headings,
            "show_toc": tokens.show_toc,
            "show_header_footer": tokens.show_header_footer,
            "header_rule": tokens.header_rule,
            "page_num_position": tokens.page_num_position,
            "chapter_break": tokens.chapter_break,
            "indent_style": tokens.indent_style,
            "hyphenate": tokens.hyphenate,
            "justify": tokens.justify,
            "image_treatment": tokens.image_treatment,
            "illustration_style": tokens.illustration_style,
        }

    def regenerate_chapter(
        self,
        project: Project,
        manuscript: Manuscript,
        plan: EditorialPlan,
        chapter_num: int,
        assets: list[Asset],
    ) -> RenderJob:
        """Regenerate a specific chapter."""
        # Filter page plans for this chapter
        chapter_pages = [p for p in plan.page_plans
                         if any(bid for bid in p.content_block_ids
                                if any(b.id == bid and b.chapter == chapter_num
                                       for b in manuscript.content_blocks))]

        # Create new render job for chapter
        job = RenderJob(
            id=f"rj_{uuid.uuid4().hex[:12]}",
            project_id=project.id,
            editorial_plan_id=plan.id,
            status="pending",
        )
        return self.db.create_render_job(job)

    def regenerate_page(
        self,
        project: Project,
        manuscript: Manuscript,
        plan: EditorialPlan,
        page_num: int,
        assets: list[Asset],
    ) -> RenderJob:
        """Regenerate a specific page."""
        job = RenderJob(
            id=f"rj_{uuid.uuid4().hex[:12]}",
            project_id=project.id,
            editorial_plan_id=plan.id,
            status="pending",
        )
        return self.db.create_render_job(job)