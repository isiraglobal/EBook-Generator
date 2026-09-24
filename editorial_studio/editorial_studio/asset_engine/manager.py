from __future__ import annotations
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import json
import hashlib

from editorial_studio.core.models import Asset, VisualReference
from editorial_studio.core.database import Database
from editorial_studio.core.config import load_config


@dataclass
class AssetGenerationRequest:
    brief_id: str
    asset_type: str
    prompt: str
    style: str
    aspect_ratio: float
    width_px: int = 1024
    height_px: int = 768
    provider: str = "local"


class AssetManager:
    def __init__(self, database: Database):
        self.db = database
        self.config = load_config().data
        self.assets_root = Path(self.config.get("storage", {}).get("assets_root", "data/assets"))
        self.assets_root.mkdir(parents=True, exist_ok=True)
        self.references_root = self.assets_root / "references"
        self.references_root.mkdir(parents=True, exist_ok=True)
        self.generated_root = self.assets_root / "generated"
        self.generated_root.mkdir(parents=True, exist_ok=True)
        self.uploads_root = self.assets_root / "uploads"
        self.uploads_root.mkdir(parents=True, exist_ok=True)

    def create_asset(self, asset: Asset) -> Asset:
        return self.db.create_asset(asset)

    def get_asset(self, asset_id: str) -> Optional[Asset]:
        return self.db.get_asset(asset_id)

    def get_assets_for_page(self, page_id: str) -> list[Asset]:
        return self.db.get_assets_for_page(page_id)

    def register_uploaded_asset(
        self,
        file_path: str | Path,
        asset_type: str,
        intended_page_id: str = "",
        caption: str = "",
        alt_text: str = "",
    ) -> Asset:
        src = Path(file_path)
        if not src.exists():
            raise FileNotFoundError(f"Asset file not found: {file_path}")

        # Copy to uploads
        dst = self.uploads_root / src.name
        import shutil
        shutil.copy2(src, dst)

        # Get image dimensions
        width, height = 0, 0
        try:
            from PIL import Image
            with Image.open(dst) as img:
                width, height = img.size
        except Exception:
            pass

        asset = Asset(
            id=f"ast_{uuid.uuid4().hex[:12]}",
            asset_type=asset_type,
            local_path=str(dst),
            original_source=str(src),
            width_px=width,
            height_px=height,
            intended_page_id=intended_page_id,
            caption=caption,
            alt_text=alt_text,
            aspect_ratio=width / height if height > 0 else 1.0,
        )

        return self.create_asset(asset)

    def generate_asset(self, request: AssetGenerationRequest) -> Asset:
        """Generate an asset using configured provider."""
        provider = self._get_provider(request.provider)

        # Create generation directory
        gen_dir = self.generated_root / request.brief_id
        gen_dir.mkdir(parents=True, exist_ok=True)

        output_path = gen_dir / f"{request.brief_id}.png"

        # For now, create a placeholder
        # In production, this would call the actual image generation API
        self._create_placeholder_image(output_path, request)

        asset = Asset(
            id=f"ast_{uuid.uuid4().hex[:12]}",
            asset_type=request.asset_type,
            local_path=str(output_path),
            generation_provider=request.provider,
            prompt=request.prompt,
            generation_metadata={
                "style": request.style,
                "aspect_ratio": request.aspect_ratio,
                "width_px": request.width_px,
                "height_px": request.height_px,
            },
            width_px=request.width_px,
            height_px=request.height_px,
            aspect_ratio=request.aspect_ratio,
            caption=f"Generated: {request.prompt[:100]}",
        )

        return self.create_asset(asset)

    def _get_provider(self, provider_name: str):
        providers = self.config.get("providers", {}).get("image_generation", {})
        provider_config = providers.get(provider_name, providers.get("local", {}))
        return provider_config

    def _create_placeholder_image(self, path: Path, request: AssetGenerationRequest):
        """Create a placeholder image for testing."""
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new('RGB', (request.width_px, request.height_px), color='#e2e8f0')
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None
        text = f"Placeholder: {request.prompt[:50]}"
        draw.text((50, 50), text, fill='#64748b', font=font)
        img.save(path)

    def process_asset_briefs(self, briefs: list[dict[str, Any]]) -> list[Asset]:
        assets = []
        for brief in briefs:
            request = AssetGenerationRequest(
                brief_id=brief["id"],
                asset_type=brief.get("type", "illustration"),
                prompt=brief.get("description", ""),
                style=brief.get("style", "editorial"),
                aspect_ratio=brief.get("aspect_ratio", 4/3),
            )
            asset = self.generate_asset(request)
            assets.append(asset)
        return assets


class VisualReferenceLibrary:
    def __init__(self, database: Database):
        self.db = database
        self.config = load_config().data
        self.references_root = Path(self.config.get("storage", {}).get("assets_root", "data/assets")) / "references"
        self.references_root.mkdir(parents=True, exist_ok=True)
        self.screenshots_root = self.references_root / "screenshots"
        self.screenshots_root.mkdir(parents=True, exist_ok=True)

    def add_reference(
        self,
        source_url: str = "",
        source_title: str = "",
        local_path: str = "",
        screenshot_path: str = "",
        tags: list[str] | None = None,
    ) -> VisualReference:
        ref = VisualReference(
            id=f"vr_{uuid.uuid4().hex[:12]}",
            source_url=source_url,
            source_title=source_title,
            local_path=local_path,
            screenshot_path=screenshot_path,
            retrieval_status="pending" if source_url and not local_path else "available",
            tags=tags or [],
        )

        # If local path provided, copy to references
        if local_path and Path(local_path).exists():
            import shutil
            dst = self.references_root / Path(local_path).name
            shutil.copy2(local_path, dst)
            ref.local_path = str(dst)

        if screenshot_path and Path(screenshot_path).exists():
            import shutil
            dst = self.screenshots_root / Path(screenshot_path).name
            shutil.copy2(screenshot_path, dst)
            ref.screenshot_path = str(dst)

        # Analyze if image available
        if ref.local_path or ref.screenshot_path:
            ref.retrieval_status = "available"
            ref.analysis = self._analyze_reference(ref)
            ref.design_principles = self._extract_principles(ref.analysis)

        return self.db.create_visual_reference(ref)

    def add_pinterest_reference(
        self,
        url: str,
        screenshot_path: str = "",
        title: str = "",
    ) -> VisualReference:
        return self.add_reference(
            source_url=url,
            source_title=title or "Pinterest Reference",
            screenshot_path=screenshot_path,
            tags=["pinterest", "reference"],
        )

    def get_reference(self, ref_id: str) -> Optional[VisualReference]:
        return self.db.get_visual_reference(ref_id)

    def list_references(self, tags: list[str] | None = None) -> list[VisualReference]:
        return self.db.list_visual_references(tags)

    def search_references(self, query: str, tags: list[str] | None = None) -> list[VisualReference]:
        all_refs = self.list_references(tags)
        query_lower = query.lower()
        results = []
        for ref in all_refs:
            if (query_lower in ref.source_title.lower() or
                query_lower in str(ref.analysis).lower() or
                query_lower in " ".join(ref.tags).lower() or
                query_lower in " ".join(ref.design_principles).lower()):
                results.append(ref)
        return results

    def _analyze_reference(self, ref: VisualReference) -> dict[str, Any]:
        """Analyze a reference image for design principles."""
        image_path = ref.local_path or ref.screenshot_path
        if not image_path or not Path(image_path).exists():
            return {}

        try:
            from PIL import Image
            with Image.open(image_path) as img:
                width, height = img.size
                aspect = width / height

            analysis = {
                "dimensions": {"width": width, "height": height, "aspect_ratio": aspect},
                "orientation": "landscape" if aspect > 1.2 else "portrait" if aspect < 0.8 else "square",
            }

            # Color analysis (simplified)
            with Image.open(image_path) as img:
                small = img.resize((50, 50))
                pixels = list(small.getdata())
                # Dominant colors
                from collections import Counter
                color_counts = Counter(pixels)
                dominant = color_counts.most_common(5)
                analysis["dominant_colors"] = [{"rgb": c[0], "count": c[1]} for c in dominant]

            return analysis
        except Exception as e:
            return {"error": str(e)}

    def _extract_principles(self, analysis: dict[str, Any]) -> list[str]:
        principles = []

        if "dimensions" in analysis:
            aspect = analysis["dimensions"].get("aspect_ratio", 1)
            if aspect > 1.5:
                principles.append("Wide landscape format for panoramic content")
            elif aspect < 0.7:
                principles.append("Tall portrait format for vertical reading")

        if "dominant_colors" in analysis:
            principles.append("Consistent color palette with clear hierarchy")

        # Add generic principles
        principles.extend([
            "Clear visual hierarchy with distinct heading levels",
            "Generous whitespace for readability",
            "Consistent grid alignment",
            "Meaningful image placement related to content",
        ])

        return principles

    def get_design_recipes(self, tags: list[str] | None = None) -> list[dict[str, Any]]:
        """Extract reusable design recipes from references."""
        refs = self.list_references(tags)
        recipes = []

        for ref in refs:
            if ref.analysis and ref.design_principles:
                recipes.append({
                    "source_id": ref.id,
                    "source_title": ref.source_title,
                    "principles": ref.design_principles,
                    "analysis": ref.analysis,
                    "tags": ref.tags,
                })

        return recipes