from __future__ import annotations
import asyncio
import base64
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import aiohttp
import httpx

from editorial_studio.core.config import load_config
from editorial_studio.core.models import Asset


@dataclass
class ImageGenerationRequest:
    prompt: str
    negative_prompt: str = ""
    style: str = "editorial"
    aspect_ratio: float = 4/3
    width: int = 1024
    height: int = 768
    provider: str = "local"
    model: str = ""
    seed: int | None = None
    guidance_scale: float = 7.5
    num_inference_steps: int = 30
    brief_id: str = ""


@dataclass
class ImageGenerationResult:
    asset: Asset
    provider: str
    model: str
    generation_time_ms: int
    success: bool
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class ImageGenerator:
    """Handles image generation using various providers (Replicate, OpenAI, Stability, Local)."""

    def __init__(self):
        self.config = load_config().data
        self.providers_config = self.config.get("providers", {}).get("image_generation", {})
        self.generated_root = Path(self.config.get("storage", {}).get("assets_root", "data/assets")) / "generated"
        self.generated_root.mkdir(parents=True, exist_ok=True)

    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        """Generate an image using the specified provider."""
        provider = request.provider or self._get_default_provider()
        start_time = datetime.now()

        try:
            if provider == "replicate":
                result = await self._generate_replicate(request)
            elif provider == "openai":
                result = await self._generate_openai(request)
            elif provider == "stability":
                result = await self._generate_stability(request)
            elif provider == "local":
                result = await self._generate_local(request)
            else:
                result = await self._generate_local(request)

            generation_time = int((datetime.now() - start_time).total_seconds() * 1000)
            result.generation_time_ms = generation_time
            return result

        except Exception as e:
            generation_time = int((datetime.now() - start_time).total_seconds() * 1000)
            return ImageGenerationResult(
                asset=Asset(id="", asset_type="error", local_path=""),
                provider=provider,
                model=request.model or "unknown",
                generation_time_ms=generation_time,
                success=False,
                error=str(e),
            )

    def _get_default_provider(self) -> str:
        providers = self.providers_config.get("providers", {})
        for name, config in providers.items():
            if config.get("enabled", False):
                return name
        return "local"

    def get_available_providers(self) -> list[str]:
        """Get list of enabled providers."""
        providers = []
        providers_config = self.providers_config.get("providers", {})
        for name, config in providers_config.items():
            if config.get("enabled", False):
                providers.append(name)
        if not providers:
            providers.append("local")
        return providers

    async def _generate_replicate(self, request: ImageGenerationRequest) -> "ImageGenerationResult":
        """Generate image using Replicate API."""
        api_token = self.providers_config.get("replicate", {}).get("api_token") or os.environ.get("REPLICATE_API_TOKEN")
        if not api_token:
            raise ValueError("Replicate API token not configured")

        model = request.model or "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"

        input_data = {
            "prompt": request.prompt,
            "negative_prompt": request.negative_prompt,
            "width": request.width,
            "height": request.height,
            "guidance_scale": request.guidance_scale,
            "num_inference_steps": request.num_inference_steps,
        }
        if request.seed is not None:
            input_data["seed"] = request.seed

        async with aiohttp.ClientSession() as session:
            # Create prediction
            headers = {
                "Authorization": f"Token {api_token}",
                "Content-Type": "application/json",
            }
            async with session.post(
                "https://api.replicate.com/v1/predictions",
                headers={"Authorization": f"Token {api_token}", "Content-Type": "application/json"},
                json={"version": model.split(":")[-1] if ":" in model else model, "input": input_data},
            ) as resp:
                prediction = await resp.json()

            prediction_id = prediction["id"]
            # Poll for completion
            for _ in range(60):  # Max 60 seconds
                await asyncio.sleep(1)
                async with session.get(
                    f"https://api.replicate.com/v1/predictions/{prediction_id}",
                    headers={"Authorization": f"Token {api_token}"},
                ) as resp:
                    prediction = await resp.json()
                    if prediction["status"] == "succeeded":
                        break
                    elif prediction["status"] == "failed":
                        raise ValueError(f"Replicate generation failed: {prediction.get('error')}")

            output_url = prediction["output"][0] if prediction["output"] else None
            if not output_url:
                raise ValueError("No output from Replicate")

            # Download image
            async with session.get(output_url) as resp:
                image_data = await resp.read()

        # Save image
        output_path = self.generated_root / f"{request.brief_id or uuid.uuid4().hex[:8]}.png"
        output_path.write_bytes(image_data)

        asset = Asset(
            id=f"ast_{uuid.uuid4().hex[:12]}",
            asset_type="illustration",
            local_path=str(output_path),
            generation_provider="replicate",
            prompt=request.prompt,
            generation_metadata={
                "model": model,
                "width": request.width,
                "height": request.height,
                "aspect_ratio": request.aspect_ratio,
            },
            width_px=request.width,
            height_px=request.height,
            aspect_ratio=request.aspect_ratio,
            caption=f"Generated via Replicate: {request.prompt[:100]}",
        )

        return ImageGenerationResult(
            asset=asset,
            provider="replicate",
            model=model,
            generation_time_ms=0,
            success=True,
        )

    async def _generate_openai(self, request: ImageGenerationRequest) -> "ImageGenerationResult":
        """Generate image using OpenAI DALL-E API."""
        api_key = self.providers_config.get("openai", {}).get("api_key") or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not configured")

        model = request.model or "dall-e-3"
        size = f"{request.width}x{request.height}"
        if model == "dall-e-3":
            # DALL-E 3 supports specific sizes
            if request.aspect_ratio >= 1.5:
                size = "1792x1024"
            elif request.aspect_ratio <= 0.67:
                size = "1024x1792"
            else:
                size = "1024x1024"

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.openai.com/v1/images/generations",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "prompt": request.prompt,
                    "size": size,
                    "quality": "hd",
                    "n": 1,
                },
                timeout=60,
            ) as resp:
                data = await resp.json()

            if "error" in data:
                raise ValueError(f"OpenAI error: {data['error']['message']}")

            image_url = data["data"][0]["url"]

            # Download image
            async with session.get(image_url) as resp:
                image_data = await resp.read()

        # Save image
        output_path = self.generated_root / f"{request.brief_id or uuid.uuid4().hex[:8]}.png"
        output_path.write_bytes(image_data)

        # Get actual dimensions from downloaded image
        from PIL import Image
        with Image.open(output_path) as img:
            actual_width, actual_height = img.size

        asset = Asset(
            id=f"ast_{uuid.uuid4().hex[:12]}",
            asset_type="illustration",
            local_path=str(output_path),
            generation_provider="openai",
            prompt=request.prompt,
            generation_metadata={
                "model": model,
                "width": actual_width,
                "height": actual_height,
                "aspect_ratio": actual_width / actual_height,
            },
            width_px=actual_width,
            height_px=actual_height,
            aspect_ratio=actual_width / actual_height,
            caption=f"Generated via OpenAI DALL-E: {request.prompt[:100]}",
        )

        return ImageGenerationResult(
            asset=asset,
            provider="openai",
            model=model,
            generation_time_ms=0,
            success=True,
        )

    async def _generate_stability(self, request: ImageGenerationRequest) -> "ImageGenerationResult":
        """Generate image using Stability AI API."""
        api_key = self.providers_config.get("stability", {}).get("api_key") or os.environ.get("STABILITY_API_KEY")
        if not api_key:
            raise ValueError("Stability AI API key not configured")

        model = request.model or "sd3.5"
        aspect_ratio_str = f"{request.aspect_ratio:.2f}".rstrip('0').rstrip('.')

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.stability.ai/v2beta/stable-image/generate/{model}",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Accept": "image/*",
                },
                data={
                    "prompt": request.prompt,
                    "negative_prompt": request.negative_prompt,
                    "aspect_ratio": aspect_ratio_str,
                    "output_format": "png",
                },
                timeout=60,
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise ValueError(f"Stability AI error: {error_text}")

                image_data = await resp.read()

        # Save image
        output_path = self.generated_root / f"{request.brief_id or uuid.uuid4().hex[:8]}.png"
        output_path.write_bytes(image_data)

        from PIL import Image
        with Image.open(output_path) as img:
            actual_width, actual_height = img.size

        asset = Asset(
            id=f"ast_{uuid.uuid4().hex[:12]}",
            asset_type="illustration",
            local_path=str(output_path),
            generation_provider="stability",
            prompt=request.prompt,
            generation_metadata={
                "model": model,
                "width": actual_width,
                "height": actual_height,
                "aspect_ratio": actual_width / actual_height,
            },
            width_px=actual_width,
            height_px=actual_height,
            aspect_ratio=actual_width / actual_height,
            caption=f"Generated via Stability AI: {request.prompt[:100]}",
        )

        return ImageGenerationResult(
            asset=asset,
            provider="stability",
            model=model,
            generation_time_ms=0,
            success=True,
        )

    async def _generate_local(self, request: ImageGenerationRequest) -> "ImageGenerationResult":
        """Generate a local placeholder image (for testing without API keys)."""
        from PIL import Image, ImageDraw, ImageFont

        # Create a more sophisticated placeholder
        img = Image.new('RGB', (request.width, request.height), color='#f8f9fa')
        draw = ImageDraw.Draw(img)

        # Add a border
        draw.rectangle([0, 0, request.width-1, request.height-1], outline='#c4a35a', width=4)

        # Add title area
        draw.rectangle([40, 40, request.width-40, 120], fill='#0f172a')
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 24)
        except Exception:
            font = ImageFont.load_default()

        # Draw title
        title = "Generated Illustration"
        draw.text((60, 60), title, fill='#c4a35a', font=font)

        # Draw prompt text (wrapped)
        prompt_text = f"Prompt: {request.prompt[:200]}"
        try:
            font_small = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 14)
        except Exception:
            font_small = ImageFont.load_default()

        # Simple text wrapping
        y_pos = 160
        words = request.prompt.split()
        line = ""
        for word in words:
            test_line = line + " " + word if line else word
            bbox = draw.textbbox((0, 0), test_line, font=font_small)
            if bbox[2] - bbox[0] > request.width - 80:
                draw.text((40, y_pos), line, fill='#1e293b', font=font_small)
                y_pos += 22
                line = word
            else:
                line = test_line
        if line:
            draw.text((40, y_pos), line, fill='#1e293b', font=font_small)

        # Add style badge
        draw.rectangle([40, request.height - 80, 200, request.height - 40], fill='#c4a35a')
        draw.text((50, request.height - 70), f"Style: {request.style}", fill='#0f172a', font=font_small)

        # Add aspect ratio badge
        draw.rectangle([request.width - 200, request.height - 80, request.width - 40, request.height - 40], fill='#1e293b')
        draw.text((request.width - 190, request.height - 70), f"AR: {request.aspect_ratio:.2f}", fill='#c4a35a', font=font_small)

        # Save image
        output_path = self.generated_root / f"{request.brief_id or uuid.uuid4().hex[:8]}.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path)

        asset = Asset(
            id=f"ast_{uuid.uuid4().hex[:12]}",
            asset_type="illustration",
            local_path=str(output_path),
            generation_provider="local",
            prompt=request.prompt,
            generation_metadata={
                "style": request.style,
                "aspect_ratio": request.aspect_ratio,
                "width_px": request.width,
                "height_px": request.height,
            },
            width_px=request.width,
            height_px=request.height,
            aspect_ratio=request.aspect_ratio,
            caption=f"Local placeholder: {request.prompt[:100]}",
        )

        return ImageGenerationResult(
            asset=asset,
            provider="local",
            model="local-placeholder",
            generation_time_ms=0,
            success=True,
        )

    async def generate_batch(self, requests: list[ImageGenerationRequest]) -> list[ImageGenerationResult]:
        """Generate multiple images concurrently."""
        tasks = [self.generate(req) for req in requests]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def generate_sync(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        """Synchronous wrapper for image generation."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.generate(request))