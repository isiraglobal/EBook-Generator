from __future__ import annotations
import json
import uuid
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import re
import asyncio
import aiohttp

from editorial_studio.core.config import load_config


@dataclass
class Source:
    id: str
    url: str = ""
    title: str = ""
    publisher: str = ""
    access_date: str = ""
    relevant_passage: str = ""
    claims_supported: list[str] = field(default_factory=list)
    confidence: float = 0.0
    verification_status: str = "unverified"
    metadata: dict[str, Any] = field(default_factory=dict)
    content_hash: str = ""
    domain_authority: float = 0.0
    recency_days: int = 0

    def __post_init__(self):
        if not self.id:
            self.id = f"src_{uuid.uuid4().hex[:12]}"
        if self.url and not self.content_hash:
            self.content_hash = hashlib.md5(self.url.encode()).hexdigest()[:16]


@dataclass
class SearchResult:
    query: str
    sources: list[Source]
    total_results: int
    search_time_ms: int
    engine: str


class ResearchEngine:
    """Handles web search and source management for manuscript generation."""

    def __init__(self):
        self.config = load_config().data
        self.sources: list[Source] = []
        self.search_cache: dict[str, SearchResult] = {}
        self.provider_config = self.config.get("providers", {}).get("search", {})

    async def search(self, query: str, max_results: int = 10, engines: list[str] | None = None) -> list[Source]:
        """Search for sources on a topic using configured search engines."""
        cache_key = f"{query}:{max_results}"
        if cache_key in self.search_cache:
            return self.search_cache[cache_key].sources

        engines = engines or ["mock"]  # Default to mock for testing
        all_sources = []

        for engine in engines:
            try:
                if engine == "duckduckgo":
                    sources = await self._search_duckduckgo(query, max_results)
                elif engine == "bing":
                    sources = await self._search_bing(query, max_results)
                elif engine == "google":
                    sources = await self._search_google(query, max_results)
                elif engine == "mock":
                    sources = await self._search_mock(query, max_results)
                else:
                    sources = await self._search_mock(query, max_results)
                all_sources.extend(sources)
            except Exception as e:
                print(f"Search engine {engine} failed: {e}")

        # Deduplicate by URL
        seen_urls = set()
        unique_sources = []
        for source in all_sources:
            if source.url and source.url not in seen_urls:
                seen_urls.add(source.url)
                unique_sources.append(source)
            elif not source.url:
                unique_sources.append(source)

        # Rank and limit
        ranked = self._rank_sources(unique_sources, query)[:max_results]

        # Cache result
        self.search_cache[cache_key] = SearchResult(
            query=query,
            sources=ranked,
            total_results=len(ranked),
            search_time_ms=0,
            engine=",".join(engines),
        )

        self.sources.extend(ranked)
        return ranked

    async def _search_duckduckgo(self, query: str, max_results: int) -> list[Source]:
        """Search using DuckDuckGo HTML scrape."""
        try:
            import re
            from bs4 import BeautifulSoup

            url = f"https://html.duckduckgo.com/html/?q={aiohttp.helpers.quote(query)}"
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as resp:
                    html = await resp.text()

            soup = BeautifulSoup(html, "html.parser")
            results = soup.find_all("a", class_="result__snippet")

            sources = []
            for i, result in enumerate(results[:10]):
                snippet = result.get_text(strip=True)
                link = result.find_parent("a", class_="result__url")
                source_url = link.get("href") if link else ""

                source = Source(
                    id=f"src_{uuid.uuid4().hex[:10]}",
                    title=f"DuckDuckGo result {i+1}",
                    url=source_url,
                    publisher="DuckDuckGo",
                    access_date=datetime.now().strftime("%Y-%m-%d"),
                    relevant_passage=snippet[:500],
                    claims_supported=[query],
                    confidence=0.6,
                    verification_status="pending",
                    metadata={"engine": "duckduckgo"},
                )
                sources.append(source)
            return sources
        except Exception:
            return []

    async def _search_bing(self, query: str, max_results: int) -> list[Source]:
        """Search using Bing API (requires API key)."""
        api_key = self.provider_config.get("bing", {}).get("api_key")
        if not api_key:
            return []

        try:
            url = "https://api.bing.microsoft.com/v7.0/search"
            headers = {"Ocp-Apim-Subscription-Key": api_key}
            params = {"q": query, "count": min(max_results, 50), "responseFilter": "Webpages"}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params, timeout=10) as resp:
                    data = await resp.json()

            sources = []
            for item in data.get("webPages", {}).get("value", [])[:max_results]:
                source = Source(
                    id=f"src_{uuid.uuid4().hex[:10]}",
                    title=item.get("name", ""),
                    url=item.get("url", ""),
                    publisher=item.get("displayUrl", "").split("/")[0] if item.get("displayUrl") else "Bing",
                    access_date=datetime.now().strftime("%Y-%m-%d"),
                    relevant_passage=item.get("snippet", "")[:500],
                    claims_supported=[query],
                    confidence=0.7,
                    verification_status="pending",
                    metadata={"engine": "bing", "date_last_crawled": item.get("dateLastCrawled")},
                )
                sources.append(source)
            return sources
        except Exception:
            return []

    async def _search_google(self, query: str, max_results: int) -> list[Source]:
        """Search using Google Custom Search API."""
        api_key = self.provider_config.get("google", {}).get("api_key")
        cx = self.provider_config.get("google", {}).get("cx")
        if not api_key or not cx:
            return []

        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {"key": api_key, "cx": cx, "q": query, "num": min(max_results, 10)}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as resp:
                    data = await resp.json()

            sources = []
            for item in data.get("items", [])[:max_results]:
                source = Source(
                    id=f"src_{uuid.uuid4().hex[:10]}",
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    publisher=item.get("displayLink", ""),
                    access_date=datetime.now().strftime("%Y-%m-%d"),
                    relevant_passage=item.get("snippet", "")[:500],
                    claims_supported=[query],
                    confidence=0.75,
                    verification_status="pending",
                    metadata={"engine": "google"},
                )
                sources.append(source)
            return sources
        except Exception:
            return []

    async def _search_mock(self, query: str, max_results: int) -> list[Source]:
        """Mock search for testing without API keys."""
        sources = []
        for i in range(min(3, max_results)):
            source = Source(
                id=f"src_{uuid.uuid4().hex[:10]}",
                title=f"Research on {query} - Source {i+1}",
                url=f"https://example.com/research/{query.replace(' ', '-')}/{i}",
                publisher="Research Database",
                access_date=datetime.now().strftime("%Y-%m-%d"),
                relevant_passage=f"Comprehensive analysis of {query} including key findings, methodology, and implications for practitioners.",
                claims_supported=[query],
                confidence=0.6,
                verification_status="pending",
                metadata={"engine": "mock", "simulated": True},
            )
            sources.append(source)
        return sources

    def _rank_sources(self, sources: list[Source], query: str) -> list[Source]:
        """Rank sources by relevance and credibility."""
        def score(source: Source) -> float:
            score = source.confidence

            # Boost for verified sources
            if source.verification_status == "verified":
                score += 0.2

            # Boost for high domain authority
            score += source.domain_authority * 0.1

            # Boost for recency
            if source.recency_days < 30:
                score += 0.1
            elif source.recency_days < 365:
                score += 0.05

            # Boost for query term match in title
            if any(term.lower() in source.title.lower() for term in query.split()):
                score += 0.1

            return score

        return sorted(sources, key=score, reverse=True)

    def search_sync(self, query: str, max_results: int = 10) -> list[Source]:
        """Synchronous wrapper for search."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.search(query, max_results))

    def verify_source(self, source: Source) -> Source:
        """Verify a source's credibility and update its status."""
        # Check domain authority (simplified)
        domain = source.url.split("/")[2] if source.url.startswith("http") else ""
        trusted_domains = {
            "wikipedia.org": 0.9,
            "github.com": 0.8,
            "arxiv.org": 0.95,
            "pubmed.ncbi.nlm.nih.gov": 0.95,
            "sec.gov": 0.95,
            "irs.gov": 0.95,
            "census.gov": 0.9,
            "bls.gov": 0.9,
            "federalreserve.gov": 0.9,
        }
        source.domain_authority = trusted_domains.get(domain, 0.5)

        # Check recency
        if source.metadata.get("date_last_crawled"):
            try:
                crawl_date = datetime.fromisoformat(source.metadata["date_last_crawled"].replace("Z", "+00:00"))
                source.recency_days = (datetime.now() - crawl_date).days
            except Exception:
                pass

        # Update verification status
        if source.domain_authority > 0.8 and source.confidence > 0.7:
            source.verification_status = "verified"
            source.confidence = min(1.0, source.confidence + 0.1)
        elif source.domain_authority > 0.6:
            source.verification_status = "likely_reliable"
        else:
            source.verification_status = "unverified"

        return source

    def get_sources_for_claim(self, claim: str) -> list[Source]:
        """Find sources that support a specific claim."""
        claim_lower = claim.lower()
        return [
            s for s in self.sources
            if any(claim_lower in c.lower() for c in s.claims_supported)
        ]

    def add_manual_source(self, source: Source) -> Source:
        """Manually add a source to the database."""
        self.sources.append(source)
        return source

    def export_sources(self, path: str | Path) -> None:
        """Export all sources to JSON file."""
        data = [
            {
                "id": s.id,
                "url": s.url,
                "title": s.title,
                "publisher": s.publisher,
                "access_date": s.access_date,
                "relevant_passage": s.relevant_passage,
                "claims_supported": s.claims_supported,
                "confidence": s.confidence,
                "verification_status": s.verification_status,
                "metadata": s.metadata,
                "content_hash": s.content_hash,
                "domain_authority": s.domain_authority,
                "recency_days": s.recency_days,
            }
            for s in self.sources
        ]
        Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def import_sources(self, path: str | Path) -> int:
        """Import sources from JSON file."""
        data = json.loads(Path(path).read_text())
        count = 0
        for item in data:
            source = Source(**item)
            self.sources.append(source)
            count += 1
        return count