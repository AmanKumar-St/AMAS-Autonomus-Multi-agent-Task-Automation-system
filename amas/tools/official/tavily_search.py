"""
AMAS Official Tavily Search Tool (Priority 4)
=============================================
Integrates Tavily Search API for high-quality live web research.
Uses official tavily-python SDK with full citation support.
"""

from __future__ import annotations
import os
import time
import logging
from typing import Dict, List, Any, Optional

from amas.tools.base import AMASTool, ToolPermission, ToolResult

logger = logging.getLogger("amas.tools.tavily")


class OfficialTavilySearchTool(AMASTool):
    """Tavily Search API integration for live web research with citations."""

    def __init__(self):
        api_key = os.getenv("TAVILY_API_KEY", "").strip().strip('"').strip("'")
        super().__init__(
            id="official_tavily_search",
            name="Official Tavily Web Search",
            description="High-quality live web search with citations, answer extraction, and domain filtering via Tavily API.",
            source="official_sdk",
            category="research",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query or research question"},
                    "search_depth": {"type": "string", "enum": ["basic", "advanced"], "default": "advanced", "description": "Search depth: basic (fast) or advanced (comprehensive)"},
                    "max_results": {"type": "integer", "default": 10, "minimum": 1, "maximum": 20, "description": "Maximum number of results to return"},
                    "include_domains": {"type": "array", "items": {"type": "string"}, "description": "Optional list of domains to include"},
                    "exclude_domains": {"type": "array", "items": {"type": "string"}, "description": "Optional list of domains to exclude"},
                    "include_answer": {"type": "boolean", "default": True, "description": "Include AI-generated answer summary"},
                    "include_raw_content": {"type": "boolean", "default": False, "description": "Include full page content for top results"},
                    "include_images": {"type": "boolean", "default": False, "description": "Include image results"}
                },
                "required": ["query"]
            },
            permissions=ToolPermission(
                read_only=True,
                requires_approval=False,
                network_required=True
            ),
            justification="Official Tavily SDK provides best-in-class web search with citations and answer extraction."
        )
        self._api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from tavily import TavilyClient
                self._client = TavilyClient(api_key=self._api_key) if self._api_key else None
            except ImportError:
                logger.warning("tavily-python not installed. Run: pip install tavily-python")
                self._client = None
        return self._client

    def execute(
        self,
        query: str = "",
        search_depth: str = "advanced",
        max_results: int = 10,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        include_answer: bool = True,
        include_raw_content: bool = False,
        include_images: bool = False,
        **kwargs
    ) -> ToolResult:
        start = time.perf_counter()

        if not query:
            return ToolResult(
                success=False,
                data=None,
                error="Query string is required for Tavily search.",
                source=self.source,
                category=self.category,
                duration_ms=0.0
            )

        client = self._get_client()
        if client is None:
            duration_ms = (time.perf_counter() - start) * 1000.0
            return ToolResult(
                success=False,
                data={"query": query, "fallback": True},
                error="Tavily client unavailable. Install tavily-python and set TAVILY_API_KEY.",
                source=self.source,
                category=self.category,
                duration_ms=round(duration_ms, 2)
            )

        try:
            response = client.search(
                query=query,
                search_depth=search_depth,
                max_results=max_results,
                include_domains=include_domains,
                exclude_domains=exclude_domains,
                include_answer=include_answer,
                include_raw_content=include_raw_content,
                include_images=include_images
            )

            duration_ms = (time.perf_counter() - start) * 1000.0

            results = response.get("results", [])
            normalized = []
            citations = []

            for item in results:
                title = item.get("title", "")
                url = item.get("url", "")
                content = item.get("content", "")
                score = item.get("score", 0.0)
                published_date = item.get("published_date")

                normalized.append({
                    "title": title,
                    "url": url,
                    "snippet": content[:500] if content else "",
                    "content": content if include_raw_content else content[:500],
                    "score": score,
                    "published_at": published_date,
                    "source_domain": self._extract_domain(url)
                })

                if url:
                    citations.append({"title": title, "url": url})

            answer = response.get("answer") if include_answer else None

            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "provider": "tavily",
                    "search_depth": search_depth,
                    "results": normalized,
                    "answer": answer,
                    "count": len(normalized),
                    "retrieved_at": time.time()
                },
                source=self.source,
                category=self.category,
                duration_ms=round(duration_ms, 2),
                citations=citations,
                metadata={
                    "provider": "tavily",
                    "search_depth": search_depth,
                    "result_count": len(normalized)
                }
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000.0
            logger.error(f"Tavily search failed: {e}")
            return ToolResult(
                success=False,
                data={"query": query},
                error=f"Tavily search failed: {str(e)}",
                source=self.source,
                category=self.category,
                duration_ms=round(duration_ms, 2)
            )

    @staticmethod
    def _extract_domain(url: str) -> str:
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc.replace("www.", "")
        except Exception:
            return "unknown"


class OfficialExaSearchTool(AMASTool):
    """Exa Search API integration for neural web search."""

    def __init__(self):
        api_key = os.getenv("EXA_API_KEY", "").strip().strip('"').strip("'")
        super().__init__(
            id="official_exa_search",
            name="Official Exa Neural Search",
            description="Neural web search with semantic understanding and high-quality results via Exa API.",
            source="official_sdk",
            category="research",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "num_results": {"type": "integer", "default": 10},
                    "type": {"type": "string", "enum": ["neural", "keyword"], "default": "neural"}
                },
                "required": ["query"]
            },
            permissions=ToolPermission(read_only=True, requires_approval=False, network_required=True),
            justification="Exa provides neural search with semantic understanding."
        )
        self._api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from exa_py import Exa
                self._client = Exa(api_key=self._api_key) if self._api_key else None
            except ImportError:
                self._client = None
        return self._client

    def execute(self, query: str = "", num_results: int = 10, type: str = "neural", **kwargs) -> ToolResult:
        start = time.perf_counter()
        if not query:
            return ToolResult(success=False, data=None, error="Query required", source=self.source, category=self.category, duration_ms=0.0)

        client = self._get_client()
        if client is None:
            duration_ms = (time.perf_counter() - start) * 1000.0
            return ToolResult(success=False, data={"query": query}, error="Exa client unavailable. Install exa-py and set EXA_API_KEY.", source=self.source, category=self.category, duration_ms=round(duration_ms, 2))

        try:
            response = client.search(query, num_results=num_results, type=type)
            duration_ms = (time.perf_counter() - start) * 1000.0

            results = getattr(response, "results", [])
            normalized = []
            citations = []
            for item in results:
                title = getattr(item, "title", "")
                url = getattr(item, "url", "")
                text = getattr(item, "text", "")
                score = getattr(item, "score", 0.0)
                published_date = getattr(item, "published_date", None)

                normalized.append({
                    "title": title,
                    "url": url,
                    "snippet": text[:500] if text else "",
                    "content": text,
                    "score": score,
                    "published_at": published_date,
                    "source_domain": self._extract_domain(url)
                })
                if url:
                    citations.append({"title": title, "url": url})

            return ToolResult(
                success=True,
                data={"query": query, "provider": "exa", "results": normalized, "count": len(normalized), "retrieved_at": time.time()},
                source=self.source, category=self.category, duration_ms=round(duration_ms, 2),
                citations=citations, metadata={"provider": "exa", "result_count": len(normalized)}
            )
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000.0
            return ToolResult(success=False, data={"query": query}, error=f"Exa search failed: {str(e)}", source=self.source, category=self.category, duration_ms=round(duration_ms, 2))

    @staticmethod
    def _extract_domain(url: str) -> str:
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc.replace("www.", "")
        except Exception:
            return "unknown"


class OfficialBraveSearchTool(AMASTool):
    """Brave Search API integration."""

    def __init__(self):
        api_key = os.getenv("BRAVE_SEARCH_API_KEY", "").strip().strip('"').strip("'")
        super().__init__(
            id="official_brave_search",
            name="Official Brave Search",
            description="Privacy-focused web search via Brave Search API.",
            source="official_sdk",
            category="research",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "count": {"type": "integer", "default": 10}
                },
                "required": ["query"]
            },
            permissions=ToolPermission(read_only=True, requires_approval=False, network_required=True),
            justification="Brave Search provides privacy-focused web search."
        )
        self._api_key = api_key

    def execute(self, query: str = "", count: int = 10, **kwargs) -> ToolResult:
        start = time.perf_counter()
        if not query:
            return ToolResult(success=False, data=None, error="Query required", source=self.source, category=self.category, duration_ms=0.0)

        if not self._api_key:
            duration_ms = (time.perf_counter() - start) * 1000.0
            return ToolResult(success=False, data={"query": query}, error="Brave Search API key not configured.", source=self.source, category=self.category, duration_ms=round(duration_ms, 2))

        try:
            import requests
            headers = {"Accept": "application/json", "X-Subscription-Token": self._api_key}
            params = {"q": query, "count": count}
            resp = requests.get("https://api.search.brave.com/res/v1/web/search", headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            duration_ms = (time.perf_counter() - start) * 1000.0
            results = data.get("web", {}).get("results", [])
            normalized = []
            citations = []
            for item in results:
                title = item.get("title", "")
                url = item.get("url", "")
                desc = item.get("description", "")
                age = item.get("age")

                normalized.append({
                    "title": title,
                    "url": url,
                    "snippet": desc,
                    "content": desc,
                    "published_at": age,
                    "source_domain": self._extract_domain(url)
                })
                if url:
                    citations.append({"title": title, "url": url})

            return ToolResult(
                success=True,
                data={"query": query, "provider": "brave", "results": normalized, "count": len(normalized), "retrieved_at": time.time()},
                source=self.source, category=self.category, duration_ms=round(duration_ms, 2),
                citations=citations, metadata={"provider": "brave", "result_count": len(normalized)}
            )
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000.0
            return ToolResult(success=False, data={"query": query}, error=f"Brave search failed: {str(e)}", source=self.source, category=self.category, duration_ms=round(duration_ms, 2))

    @staticmethod
    def _extract_domain(url: str) -> str:
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc.replace("www.", "")
        except Exception:
            return "unknown"


class OfficialSerperSearchTool(AMASTool):
    """Serper (Google Search) API integration."""

    def __init__(self):
        api_key = os.getenv("SERPER_API_KEY", "").strip().strip('"').strip("'")
        super().__init__(
            id="official_serper_search",
            name="Official Serper Google Search",
            description="Google search results via Serper API.",
            source="official_sdk",
            category="research",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "num": {"type": "integer", "default": 10}
                },
                "required": ["query"]
            },
            permissions=ToolPermission(read_only=True, requires_approval=False, network_required=True),
            justification="Serper provides Google search results programmatically."
        )
        self._api_key = api_key

    def execute(self, query: str = "", num: int = 10, **kwargs) -> ToolResult:
        start = time.perf_counter()
        if not query:
            return ToolResult(success=False, data=None, error="Query required", source=self.source, category=self.category, duration_ms=0.0)

        if not self._api_key:
            duration_ms = (time.perf_counter() - start) * 1000.0
            return ToolResult(success=False, data={"query": query}, error="Serper API key not configured.", source=self.source, category=self.category, duration_ms=round(duration_ms, 2))

        try:
            import requests
            headers = {"X-API-KEY": self._api_key, "Content-Type": "application/json"}
            payload = {"q": query, "num": num}
            resp = requests.post("https://google.serper.dev/search", headers=headers, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            duration_ms = (time.perf_counter() - start) * 1000.0
            results = data.get("organic", [])
            normalized = []
            citations = []
            for item in results:
                title = item.get("title", "")
                url = item.get("link", "")
                snippet = item.get("snippet", "")
                date = item.get("date")

                normalized.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "content": snippet,
                    "published_at": date,
                    "source_domain": self._extract_domain(url)
                })
                if url:
                    citations.append({"title": title, "url": url})

            return ToolResult(
                success=True,
                data={"query": query, "provider": "serper", "results": normalized, "count": len(normalized), "retrieved_at": time.time()},
                source=self.source, category=self.category, duration_ms=round(duration_ms, 2),
                citations=citations, metadata={"provider": "serper", "result_count": len(normalized)}
            )
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000.0
            return ToolResult(success=False, data={"query": query}, error=f"Serper search failed: {str(e)}", source=self.source, category=self.category, duration_ms=round(duration_ms, 2))

    @staticmethod
    def _extract_domain(url: str) -> str:
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc.replace("www.", "")
        except Exception:
            return "unknown"


class DDGSFallbackSearchTool(AMASTool):
    """DuckDuckGo fallback search (no API key required)."""

    def __init__(self):
        super().__init__(
            id="ddgs_fallback_search",
            name="DuckDuckGo Fallback Search",
            description="No-API-key fallback web search using DuckDuckGo HTML scraping.",
            source="custom",
            category="research",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "default": 10}
                },
                "required": ["query"]
            },
            permissions=ToolPermission(read_only=True, requires_approval=False, network_required=True),
            justification="Zero-config fallback when no commercial search API is available."
        )

    def execute(self, query: str = "", max_results: int = 10, **kwargs) -> ToolResult:
        start = time.perf_counter()
        if not query:
            return ToolResult(success=False, data=None, error="Query required", source=self.source, category=self.category, duration_ms=0.0)

        try:
            from duckduckgo_search import DDGS
            ddgs = DDGS()
            results = list(ddgs.text(query, max_results=max_results))

            duration_ms = (time.perf_counter() - start) * 1000.0
            normalized = []
            citations = []
            for item in results:
                title = item.get("title", "")
                url = item.get("href", "") or item.get("url", "")
                body = item.get("body", "")

                normalized.append({
                    "title": title,
                    "url": url,
                    "snippet": body,
                    "content": body,
                    "source_domain": self._extract_domain(url)
                })
                if url:
                    citations.append({"title": title, "url": url})

            return ToolResult(
                success=True,
                data={"query": query, "provider": "ddgs", "results": normalized, "count": len(normalized), "retrieved_at": time.time()},
                source=self.source, category=self.category, duration_ms=round(duration_ms, 2),
                citations=citations, metadata={"provider": "ddgs", "result_count": len(normalized), "fallback": True}
            )
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000.0
            return ToolResult(success=False, data={"query": query}, error=f"DDGS search failed: {str(e)}", source=self.source, category=self.category, duration_ms=round(duration_ms, 2))

    @staticmethod
    def _extract_domain(url: str) -> str:
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc.replace("www.", "")
        except Exception:
            return "unknown"