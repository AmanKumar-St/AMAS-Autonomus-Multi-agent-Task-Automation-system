"""
AMAS LangChain Tool Adapter (Priority 2)
========================================
Adapts maintained LangChain community tools into the AMAS tool framework.
Used when PraisonAI does not natively provide a specific specialized integration.
"""

from __future__ import annotations
import time
from typing import Dict, List, Any, Optional

from amas.tools.base import AMASTool, ToolPermission, ToolResult


class LangChainWikipediaTool(AMASTool):
    """LangChain Wikipedia lookup integration for encyclopedic knowledge."""

    def __init__(self):
        super().__init__(
            id="langchain_wikipedia",
            name="LangChain Wikipedia Lookup",
            description="Queries Wikipedia for authoritative encyclopedic definitions, historical timelines, and reference facts.",
            source="langchain",
            category="research",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Subject or entity to look up"}
                },
                "required": ["query"]
            },
            permissions=ToolPermission(
                read_only=True,
                requires_approval=False,
                network_required=True
            )
        )

    def execute(self, query: str = "", **kwargs) -> ToolResult:
        start = time.perf_counter()
        if not query:
            return ToolResult(
                success=False,
                data=None,
                error="Query required for Wikipedia lookup.",
                source=self.source,
                category=self.category,
                duration_ms=0.0
            )

        try:
            # Use LangChain Community Wikipedia tool if available, or official Wikipedia API
            import urllib.request, urllib.parse, json
            clean_q = urllib.parse.quote(query[:80])
            url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={clean_q}&format=json"
            req = urllib.request.Request(url, headers={"User-Agent": "AMASAutonomousAgent/2.0"})
            
            with urllib.request.urlopen(req, timeout=5) as res:
                data = json.loads(res.read().decode())
                search_results = data.get("query", {}).get("search", [])

            if not search_results:
                duration_ms = (time.perf_counter() - start) * 1000.0
                return ToolResult(
                    success=False,
                    data={"query": query, "found": False},
                    error=f"No Wikipedia articles found for '{query}'.",
                    source=self.source,
                    category=self.category,
                    duration_ms=round(duration_ms, 2)
                )

            top_page = search_results[0]["title"]
            summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(top_page)}"
            s_req = urllib.request.Request(summary_url, headers={"User-Agent": "AMASAutonomousAgent/2.0"})
            with urllib.request.urlopen(s_req, timeout=5) as s_res:
                s_data = json.loads(s_res.read().decode())
                extract = s_data.get("extract", "")
                page_url = s_data.get("content_urls", {}).get("desktop", {}).get("page", f"https://en.wikipedia.org/wiki/{top_page}")

            duration_ms = (time.perf_counter() - start) * 1000.0
            citations = [{"title": f"Wikipedia: {top_page}", "url": page_url}]
            return ToolResult(
                success=True,
                data={
                    "title": top_page,
                    "extract": extract,
                    "url": page_url,
                    "source": "Wikipedia Official"
                },
                source=self.source,
                category=self.category,
                duration_ms=round(duration_ms, 2),
                citations=citations
            )
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000.0
            return ToolResult(
                success=False,
                data=None,
                error=f"LangChain/Wikipedia lookup failed: {str(e)}",
                source=self.source,
                category=self.category,
                duration_ms=round(duration_ms, 2)
            )
