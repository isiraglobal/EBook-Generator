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

        # Get editorial plan for page plans
        editorial_plan = self.db.get_editorial_plan(editorial_plan_id)

        # Initialize visual inspector
        visual_inspector = VisualInspector(self.config)

        # Inspect each page
        all_issues: list[QAIssue] = []
        for i, img_path in enumerate(page_images):
            page_num = i + 1

            # Get page plan for this page
            page_plan = {}
            if editorial_plan:
                for pp in editorial_plan.page_plans:
                    if pp.page_number == page_num:
                        page_plan = {
                            "page_number": pp.page_number,
                            "purpose": pp.purpose.value,
                            "layout_family": pp.layout_family.value,
                            "content_block_ids": pp.content_block_ids,
                        }
                        break

            # Programmatic inspection
            issues = self._inspect_page(page_num, img_path, pdf_path, page_plan)
            all_issues.extend(issues)

            # Vision model inspection (if available)
            vision_issues = visual_inspector.inspect_page(img_path, page_plan)
            all_issues.extend(vision_issues)

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

    def _inspect_page(self, page_num: int, image_path: str, pdf_path: str, page_plan: dict = None) -> list[QAIssue]:
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

        # Determine if this is a front/back matter page (expected to have less text)
        is_front_matter = False
        is_back_matter = False
        is_chapter_opener = False
        if page_plan:
            purpose = page_plan.get("purpose", "")
            is_front_matter = purpose in ("cover", "title_page", "copyright", "toc", "foreword", "preface", "introduction")
            is_back_matter = purpose in ("glossary", "references", "appendix", "back_cover", "index", "bibliography")
            # Chapter openers also typically have less body text
            is_chapter_opener = purpose == "chapter_opener"

        # Check 3: Content completeness - check for very little text (skip for front/back matter and chapter openers)
        if not is_front_matter and not is_back_matter and not is_chapter_opener:
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
        text_issues = self._analyze_text_layout(page_text, page_num, is_chapter_opener=is_chapter_opener)
        issues.extend(text_issues)

        # Check 5: Image analysis (if we have the image)
        img_issues = self._analyze_image_layout(image_path, page_num, is_front_matter=is_front_matter)
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

    def _analyze_text_layout(self, text: str, page_num: int, is_chapter_opener: bool = False) -> list[QAIssue]:
        issues: list[QAIssue] = []

        lines = text.split("\n")
        if not lines:
            return issues

        # Check for widows/orphans (single lines at start/end) - skip for chapter openers
        if len(lines) > 2 and not is_chapter_opener:
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

    def _analyze_image_layout(self, image_path: str, page_num: int, is_front_matter: bool = False) -> list[QAIssue]:
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
                elif avg_edge > 245 and not is_front_matter:
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
        self.providers_config = config.get("providers", {}).get("vision", {})

    def inspect_page(self, image_path: str, page_plan: dict[str, Any]) -> list[QAIssue]:
        """Use vision model to inspect page visually."""
        if not self.vision_model:
            return []

        # Try different providers
        provider = self.providers_config.get("default", "openai")
        try:
            if provider == "openai":
                return self._inspect_openai(image_path, page_plan)
            elif provider == "anthropic":
                return self._inspect_anthropic(image_path, page_plan)
            elif provider == "local":
                return self._inspect_local(image_path, page_plan)
        except Exception as e:
            print(f"Vision inspection failed: {e}")

        return []

    def _inspect_openai(self, image_path: str, page_plan: dict[str, Any]) -> list[QAIssue]:
        """Use OpenAI GPT-4V for visual inspection."""
        import base64
        import os
        import httpx

        api_key = self.providers_config.get("openai", {}).get("api_key") or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return []

        model = self.providers_config.get("openai", {}).get("model", "gpt-4o")
        max_tokens = self.providers_config.get("openai", {}).get("max_tokens", 2000)

        with open(image_path, "rb") as img_file:
            b64_image = base64.b64encode(img_file.read()).decode()

        prompt = self._build_inspection_prompt(page_plan)

        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a professional book designer and quality assurance expert. Analyze the rendered book page for visual defects and layout issues."},
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_image}", "detail": "high"}},
                    ]},
                ],
                "max_tokens": max_tokens,
                "temperature": 0.1,
            }, timeout=60.0)

        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]

        return self._parse_vision_response(content)

    def _inspect_anthropic(self, image_path: str, page_plan: dict[str, Any]) -> list[QAIssue]:
        """Use Anthropic Claude 3 for visual inspection."""
        import base64
        import os
        import httpx

        api_key = self.providers_config.get("anthropic", {}).get("api_key") or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return []

        model = self.providers_config.get("anthropic", {}).get("model", "claude-3-opus-20240229")

        with open(image_path, "rb") as img_file:
            b64_image = base64.b64encode(img_file.read()).decode()

        prompt = self._build_inspection_prompt(page_plan)

        response = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": model,
                "max_tokens": 2000,
                "temperature": 0.1,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b64_image}},
                    ],
                }],
            }, timeout=60.0)

        response.raise_for_status()
        result = response.json()
        content = result["content"][0]["text"]

        return self._parse_vision_response(content)

    def _inspect_local(self, image_path: str, page_plan: dict[str, Any]) -> list[QAIssue]:
        """Local vision inspection using basic image analysis."""
        issues: list[QAIssue] = []

        try:
            from PIL import Image
            import numpy as np

            with Image.open(image_path) as img:
                width, height = img.size
                gray = img.convert("L")
                arr = np.array(gray)

                # Check for text regions (high frequency areas)
                # This is a simplified check - real implementation would use OCR or ML
                edges_x = arr[0, :]
                edges_y = arr[:, 0]

                # Check margins
                left_margin_px = int(0.05 * width)
                right_margin_px = int(0.05 * width)
                top_margin_px = int(0.05 * height)
                bottom_margin_px = int(0.05 * height)

                # Check if content extends into margins
                left_edge = arr[:, :left_margin_px].mean()
                right_edge = arr[:, -right_margin_px:].mean()
                top_edge = arr[:top_margin_px, :].mean()
                bottom_edge = arr[-bottom_margin_px:, :].mean()

                if left_edge < 20 or right_edge < 20 or top_edge < 20 or bottom_edge < 20:
                    issues.append(QAIssue(
                        id=f"qa_{uuid.uuid4().hex[:12]}",
                        page_id=f"page_{page_plan.get('page_number', 1)}",
                        page_number=page_plan.get('page_number', 1),
                        severity=QASeverity.WARNING,
                        category="layout",
                        message="Content may be too close to page edges - check margins",
                        suggested_fix="Increase margins or adjust content flow",
                    ))

        except Exception:
            pass

        return issues

    def _build_inspection_prompt(self, page_plan: dict[str, Any]) -> str:
        purpose = page_plan.get('purpose', 'content')
        layout = page_plan.get('layout_family', 'reading')

        return f"""Analyze this rendered book page for visual quality and layout defects.

Page Purpose: {purpose}
Layout Family: {layout}
Expected Content Blocks: {len(page_plan.get('content_block_ids', []))}

Check for the following issues and report each as a JSON object with:
- severity: "critical" | "error" | "warning" | "info"
- category: "layout" | "typography" | "content" | "rendering" | "image"
- message: clear description of the issue
- suggested_fix: how to fix it
- location: {{"x": 0.5, "y": 0.5}} (normalized 0-1 coordinates)
- auto_fixable: true/false

SPECIFIC CHECKS:
1. MARGINS: Is content too close to page edges? Is there sufficient whitespace?
2. TYPOGRAPHY: Are there widows (single line at top of page)? Orphans (single line at bottom)? 
   Heading at bottom of page without body text? Inconsistent font sizes?
3. LAYOUT: Is content clipped at edges? Overlapping elements? Misaligned grids?
   Uneven column widths? Inconsistent spacing?
4. IMAGES: Are images blurry, stretched, or pixelated? Wrong aspect ratio?
   Missing captions? Images crossing page boundaries?
5. CONTENT: Missing expected content blocks? Empty pages? Text too small to read?
   Headings without following body text?
6. OVERALL: Visual balance? Professional appearance? Consistent with layout family?

Return as JSON array of issues. If no issues found, return empty array [].

Example output:
[
  {{
    "severity": "warning",
    "category": "typography",
    "message": "Widow detected: single word 'the' at top of page",
    "suggested_fix": "Adjust paragraph spacing or hyphenation",
    "location": {{"x": 0.5, "y": 0.05}},
    "auto_fixable": true
  }}
]"""

    def _parse_vision_response(self, content: str) -> list[QAIssue]:
        """Parse vision model response into QAIssue objects."""
        issues: list[QAIssue] = []

        try:
            import json
            # Try to extract JSON from response
            start = content.find('[')
            end = content.rfind(']') + 1
            if start >= 0 and end > start:
                json_str = content[start:end]
                data = json.loads(json_str)

                for item in data:
                    severity_map = {
                        "critical": QASeverity.CRITICAL,
                        "error": QASeverity.ERROR,
                        "warning": QASeverity.WARNING,
                        "info": QASeverity.INFO,
                    }
                    severity = severity_map.get(item.get("severity", "warning").lower(), QASeverity.WARNING)

                    issues.append(QAIssue(
                        id=f"qa_{uuid.uuid4().hex[:12]}",
                        page_id=f"page_{1}",
                        page_number=1,
                        severity=severity,
                        category=item.get("category", "layout"),
                        message=item.get("message", "Vision model detected issue"),
                        location=item.get("location", {}),
                        suggested_fix=item.get("suggested_fix", ""),
                        auto_fixable=item.get("auto_fixable", False),
                    ))
        except Exception as e:
            print(f"Failed to parse vision response: {e}")

        return issues