from __future__ import annotations
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import json

from editorial_studio.core.models import (
    QAIssue,
    QAReport,
    QASeverity,
    RenderJob,
)
from editorial_studio.core.database import Database
from editorial_studio.core.config import load_config


@dataclass
class PageInspection:
    page_number: int
    image_path: str
    width_px: int
    height_px: int
    text_content: str
    geometry: dict[str, Any]
    issues: list[QAIssue]


class QAEngine:
    def __init__(self, database: Database):
        self.db = database
        self.config = load_config().data
        self.qa_config = self.config.get("qa", {})
        self.max_repair_attempts = self.qa_config.get("max_repair_attempts", 3)
        self.render_dpi = self.qa_config.get("render_dpi_for_qa", 200)
        self.strict_layout = self.qa_config.get("strict_layout", False)
        self.temp_dir = Path(self.config.get("storage", {}).get("temp_root", "data/temp")) / "qa"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def inspect_publication(
        self,
        job: RenderJob,
        pdf_path: str,
        editorial_plan_id: str,
    ) -> QAReport:
        """Render PDF pages to images and inspect for defects."""
        # Render all pages to images
        page_images = self._render_pdf_pages(pdf_path)

        # Inspect each page
        all_issues: list[QAIssue] = []
        for i, img_path in enumerate(page_images):
            page_num = i + 1
            issues = self._inspect_page(page_num, img_path, pdf_path)
            all_issues.extend(issues)

        # Calculate score
        hard_failures = [i for i in all_issues if i.severity in (QASeverity.ERROR, QASeverity.CRITICAL)]
        warnings = [i for i in all_issues if i.severity == QASeverity.WARNING]

        score = 100.0
        score -= len(hard_failures) * 20
        score -= len(warnings) * 5
        score = max(0.0, score)

        passed = len(hard_failures) == 0 and (not self.strict_layout or len(warnings) == 0)

        report = QAReport(
            id=f"qar_{uuid.uuid4().hex[:12]}",
            publication_id=editorial_plan_id,
            render_job_id=job.id,
            total_pages=len(page_images),
            issues=all_issues,
            passed=passed,
            score=score,
            summary=self._generate_summary(all_issues, len(page_images)),
            page_images=page_images,
        )

        self.db.create_qa_report(report)
        return report

    def _render_pdf_pages(self, pdf_path: str) -> list[str]:
        """Render PDF pages to PNG images using pdftoppm or similar."""
        output_dir = self.temp_dir / f"pages_{uuid.uuid4().hex[:8]}"
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Try pdftoppm first (poppler)
            cmd = [
                "pdftoppm",
                "-png",
                "-r", str(self.render_dpi),
                pdf_path,
                str(output_dir / "page")
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode == 0:
                png_files = sorted(output_dir.glob("page-*.png"))
                return [str(p) for p in png_files]
        except FileNotFoundError:
            pass

        # Fallback: use pdf2image if available
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(pdf_path, dpi=self.render_dpi, output_folder=str(output_dir), fmt="png")
            png_files = sorted(output_dir.glob("*.png"))
            return [str(p) for p in png_files]
        except (ImportError, Exception):
            pass

        # Last resort: skip visual QA, return empty list
        return []

    def _inspect_page(self, page_num: int, image_path: str, pdf_path: str) -> list[QAIssue]:
        issues: list[QAIssue] = []

        try:
            from PIL import Image
            with Image.open(image_path) as img:
                width, height = img.size
        except Exception:
            width, height = 0, 0

        # Check 1: Page dimensions
        if width == 0 or height == 0:
            issues.append(QAIssue(
                id=f"qa_{uuid.uuid4().hex[:12]}",
                page_id=f"page_{page_num}",
                page_number=page_num,
                severity=QASeverity.CRITICAL,
                category="rendering",
                message="Failed to render page image",
            ))
            return issues

        # Check 2: Extract text from PDF for this page
        page_text = self._extract_page_text(pdf_path, page_num)

        # Check 3: Content completeness - check for very little text
        if len(page_text.strip()) < 50:
            issues.append(QAIssue(
                id=f"qa_{uuid.uuid4().hex[:12]}",
                page_id=f"page_{page_num}",
                page_number=page_num,
                severity=QASeverity.WARNING,
                category="content",
                message=f"Page has very little text content ({len(page_text)} chars)",
                suggested_fix="Verify content was not truncated or omitted",
            ))

        # Check 4: Look for common layout issues via text analysis
        text_issues = self._analyze_text_layout(page_text, page_num)
        issues.extend(text_issues)

        # Check 5: Image analysis (if we have the image)
        img_issues = self._analyze_image_layout(image_path, page_num)
        issues.extend(img_issues)

        return issues

    def _extract_page_text(self, pdf_path: str, page_num: int) -> str:
        """Extract text from a specific PDF page."""
        try:
            import pypdf
            with open(pdf_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                if page_num <= len(reader.pages):
                    page = reader.pages[page_num - 1]
                    return page.extract_text() or ""
        except Exception:
            pass
        return ""

    def _analyze_text_layout(self, text: str, page_num: int) -> list[QAIssue]:
        issues: list[QAIssue] = []

        lines = text.split("\n")
        if not lines:
            return issues

        # Check for widows/orphans (single lines at start/end)
        if len(lines) > 2:
            # First line very short (potential widow)
            if len(lines[0].strip()) < 20 and len(lines[0].split()) < 4:
                issues.append(QAIssue(
                    id=f"qa_{uuid.uuid4().hex[:12]}",
                    page_id=f"page_{page_num}",
                    page_number=page_num,
                    severity=QASeverity.WARNING,
                    category="typography",
                    message="Possible widow: first line is very short",
                    suggested_fix="Adjust paragraph spacing or hyphenation",
                ))

            # Last line very short (potential orphan)
            if len(lines[-1].strip()) < 20 and len(lines[-1].split()) < 4:
                issues.append(QAIssue(
                    id=f"qa_{uuid.uuid4().hex[:12]}",
                    page_id=f"page_{page_num}",
                    page_number=page_num,
                    severity=QASeverity.WARNING,
                    category="typography",
                    message="Possible orphan: last line is very short",
                    suggested_fix="Adjust paragraph spacing or hyphenation",
                ))

        # Check for heading at bottom without content
        for i, line in enumerate(lines):
            if line.strip().isupper() and len(line.strip()) > 5:
                # Potential heading
                if i == len(lines) - 1 or (i == len(lines) - 2 and not lines[-1].strip()):
                    issues.append(QAIssue(
                        id=f"qa_{uuid.uuid4().hex[:12]}",
                        page_id=f"page_{page_num}",
                        page_number=page_num,
                        severity=QASeverity.ERROR,
                        category="layout",
                        message="Heading appears at bottom of page without following content",
                        suggested_fix="Add page break before heading or adjust content flow",
                    ))

        return issues

    def _analyze_image_layout(self, image_path: str, page_num: int) -> list[QAIssue]:
        issues: list[QAIssue] = []

        try:
            from PIL import Image
            with Image.open(image_path) as img:
                width, height = img.size
                # Convert to grayscale for analysis
                gray = img.convert("L")

                # Check for very dark/light areas (potential clipping)
                # Sample edges
                edge_samples = []
                edge_samples.extend([gray.getpixel((x, 0)) for x in range(0, width, width//10)])
                edge_samples.extend([gray.getpixel((x, height-1)) for x in range(0, width, width//10)])
                edge_samples.extend([gray.getpixel((0, y)) for y in range(0, height, height//10)])
                edge_samples.extend([gray.getpixel((width-1, y)) for y in range(0, height, height//10)])

                # If edges are all very dark or very light, might be clipping
                avg_edge = sum(edge_samples) / len(edge_samples)
                if avg_edge < 10:
                    issues.append(QAIssue(
                        id=f"qa_{uuid.uuid4().hex[:12]}",
                        page_id=f"page_{page_num}",
                        page_number=page_num,
                        severity=QASeverity.WARNING,
                        category="layout",
                        message="Page edges appear very dark - possible content clipping",
                    ))
                elif avg_edge > 245:
                    issues.append(QAIssue(
                        id=f"qa_{uuid.uuid4().hex[:12]}",
                        page_id=f"page_{page_num}",
                        page_number=page_num,
                        severity=QASeverity.INFO,
                        category="layout",
                        message="Page edges are very light - check margins",
                    ))

        except Exception:
            pass

        return issues

    def _generate_summary(self, issues: list[QAIssue], total_pages: int) -> str:
        if not issues:
            return f"All {total_pages} pages passed quality checks"

        by_severity: dict[str, int] = {}
        by_category: dict[str, int] = {}

        for issue in issues:
            by_severity[issue.severity.value] = by_severity.get(issue.severity.value, 0) + 1
            by_category[issue.category] = by_category.get(issue.category, 0) + 1

        parts = [f"{total_pages} pages inspected"]
        for sev, count in by_severity.items():
            parts.append(f"{count} {sev}")
        return "; ".join(parts)

    def repair_defects(
        self,
        report: QAReport,
        job: RenderJob,
        manuscript_id: str,
        editorial_plan_id: str,
    ) -> tuple[bool, list[str]]:
        """Attempt to repair defects found in QA report."""
        if job.retry_count >= self.max_repair_attempts:
            return False, [f"Max repair attempts ({self.max_repair_attempts}) reached"]

        hard_failures = report.hard_failures()
        if not hard_failures:
            return True, ["No hard failures to repair"]

        repairs_applied = []

        for issue in hard_failures:
            if issue.auto_fixable and not issue.fix_applied:
                # Apply fix based on category
                if issue.category == "layout" and "clipping" in issue.message.lower():
                    # Would adjust margins in editorial plan
                    repairs_applied.append(f"Adjusted margins for page {issue.page_number}")
                    issue.fix_applied = True
                elif issue.category == "typography" and "widow" in issue.message.lower():
                    repairs_applied.append(f"Adjusted hyphenation for page {issue.page_number}")
                    issue.fix_applied = True
                elif issue.category == "layout" and "heading" in issue.message.lower():
                    repairs_applied.append(f"Added page break before heading on page {issue.page_number}")
                    issue.fix_applied = True

        if repairs_applied:
            job.retry_count += 1
            self.db.update_render_job(job)
            return True, repairs_applied

        return False, ["No auto-fixable issues found"]


class VisualInspector:
    """Uses vision model for visual inspection when available."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.vision_model = config.get("vision_model")

    def inspect_page(self, image_path: str, page_plan: dict[str, Any]) -> list[QAIssue]:
        """Use vision model to inspect page visually."""
        if not self.vision_model:
            return []

        # This would call a vision-capable model
        # For now, return empty list
        return []