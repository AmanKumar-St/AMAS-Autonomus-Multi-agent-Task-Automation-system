"""
AMAS Web Search Manager
=======================
Multi-provider search orchestration with automatic fallback.
Priority: Tavily → Exa → Brave → Serper → PraisonAI/DDGS → DDGS Fallback
"""

from __future__ import annotations
import os
import time
import logging
from typing import Dict, List, Any, Optional, TYPE_CHECKING

from amas.tools.base import AMASTool, ToolPermission, ToolResult

if TYPE_CHECKING:
    from amas.tools.registry import ToolRegistry

logger = logging.getLogger("amas.tools.web_search")


class WebSearchManager:
    """Manages multiple search providers with automatic fallback."""

    def __init__(self, tool_registry: Optional["ToolRegistry"] = None):
        self.tool_registry = tool_registry
        self._providers: List[Dict[str, Any]] = []
        self._initialize_providers()

    def _initialize_providers(self):
        """Register available search providers in priority order."""
        # Priority 1: Tavily (best quality, citations, answer extraction)
        if os.getenv("TAVILY_API_KEY"):
            self._providers.append({
                "id": "official_tavily_search",
                "name": "Tavily",
                "tool_id": "official_tavily_search",
                "priority": 1,
                "available": True
            })

        # Priority 2: Exa (neural search)
        if os.getenv("EXA_API_KEY"):
            self._providers.append({
                "id": "official_exa_search",
                "name": "Exa",
                "tool_id": "official_exa_search",
                "priority": 2,
                "available": True
            })

        # Priority 3: Brave Search
        if os.getenv("BRAVE_SEARCH_API_KEY"):
            self._providers.append({
                "id": "official_brave_search",
                "name": "Brave",
                "tool_id": "official_brave_search",
                "priority": 3,
                "available": True
            })

        # Priority 4: Serper (Google)
        if os.getenv("SERPER_API_KEY"):
            self._providers.append({
                "id": "official_serper_search",
                "name": "Serper",
                "tool_id": "official_serper_search",
                "priority": 4,
                "available": True
            })

        # Priority 5: PraisonAI DuckDuckGo (if available via tool registry)
        if self.tool_registry and self.tool_registry.get_tool("praison_web_search"):
            self._providers.append({
                "id": "praison_web_search",
                "name": "PraisonAI DuckDuckGo",
                "tool_id": "praison_web_search",
                "priority": 5,
                "available": True
            })

        # Priority 6: DDGS Fallback (always available, no API key)
        self._providers.append({
            "id": "ddgs_fallback_search",
            "name": "DDGS Fallback",
            "tool_id": "ddgs_fallback_search",
            "priority": 6,
            "available": True
        })

        # Sort by priority
        self._providers.sort(key=lambda p: p["priority"])

    def get_available_providers(self) -> List[Dict[str, Any]]:
        """Return list of configured providers."""
        return [p for p in self._providers if p["available"]]

    def search(
        self,
        query: str,
        preferred_provider: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        """
        Execute search with automatic fallback.
        Returns ToolResult with metadata about which provider was used.
        """
        if not query:
            return ToolResult(
                success=False,
                data=None,
                error="Query string is required.",
                source="web_search_manager",
                category="research",
                duration_ms=0.0,
                metadata={"error_type": "INVALID_INPUT"}
            )

        providers_to_try = self._providers
        if preferred_provider:
            # Move preferred to front if available
            providers_to_try = sorted(
                self._providers,
                key=lambda p: (0 if p["id"] == preferred_provider else 1, p["priority"])
            )

        last_error = None
        fallback_used = False
        fallback_reason = None
        attempted_providers = []

        for provider in providers_to_try:
            if not provider["available"]:
                continue

            attempted_providers.append(provider["id"])
            tool = self.tool_registry.get_tool(provider["tool_id"]) if self.tool_registry else None

            if not tool:
                # Try to import and create directly
                tool = self._create_tool_instance(provider["tool_id"])

            if not tool:
                logger.warning(f"Search provider {provider['id']} not available")
                continue

            try:
                logger.info(f"Attempting search via {provider['name']} ({provider['id']})")
                start = time.perf_counter()
                result = tool.execute(query=query, **kwargs)
                duration_ms = (time.perf_counter() - start) * 1000.0

                if result.success and result.data and (result.data.get("results") or result.data.get("articles")):
                    # Success - normalize response to have "articles" key for consistency
                    if result.data.get("results") and not result.data.get("articles"):
                        result.data["articles"] = result.data["results"]
                    elif result.data.get("articles") and not result.data.get("results"):
                        result.data["results"] = result.data["articles"]
                    
                    # Success - add manager metadata
                    result.metadata = result.metadata or {}
                    result.metadata.update({
                        "requested_provider": preferred_provider or "auto",
                        "actual_provider": provider["id"],
                        "provider_name": provider["name"],
                        "fallback_used": fallback_used,
                        "fallback_reason": fallback_reason,
                        "attempted_providers": attempted_providers,
                        "search_duration_ms": round(duration_ms, 2)
                    })
                    return result

                # Failed but no exception - try next provider
                last_error = result.error or "No results returned"
                fallback_used = True
                fallback_reason = f"{provider['name']} returned no results: {last_error}"
                logger.warning(f"{provider['name']} search failed: {last_error}")

            except Exception as e:
                last_error = str(e)
                fallback_used = True
                fallback_reason = f"{provider['name']} error: {last_error}"
                logger.warning(f"{provider['name']} search exception: {e}")
                continue

        # All providers exhausted
        return ToolResult(
            success=False,
            data={
                "query": query,
                "attempted_providers": attempted_providers,
                "error_type": "SEARCH_UNAVAILABLE"
            },
            error=f"No search provider available. Last error: {last_error}",
            source="web_search_manager",
            category="research",
            duration_ms=0.0,
            metadata={
                "error_type": "SEARCH_UNAVAILABLE",
                "attempted_providers": attempted_providers,
                "fallback_used": True,
                "fallback_reason": fallback_reason or "All providers failed"
            }
        )

    def _create_tool_instance(self, tool_id: str) -> Optional[AMASTool]:
        """Create tool instance directly for fallback providers."""
        try:
            if tool_id == "official_tavily_search":
                from amas.tools.official.tavily_search import OfficialTavilySearchTool
                return OfficialTavilySearchTool()
            elif tool_id == "official_exa_search":
                from amas.tools.official.tavily_search import OfficialExaSearchTool
                return OfficialExaSearchTool()
            elif tool_id == "official_brave_search":
                from amas.tools.official.tavily_search import OfficialBraveSearchTool
                return OfficialBraveSearchTool()
            elif tool_id == "official_serper_search":
                from amas.tools.official.tavily_search import OfficialSerperSearchTool
                return OfficialSerperSearchTool()
            elif tool_id == "ddgs_fallback_search":
                from amas.tools.official.tavily_search import DDGSFallbackSearchTool
                return DDGSFallbackSearchTool()
        except Exception as e:
            logger.warning(f"Failed to create {tool_id}: {e}")
        return None


class WebSearchTool(AMASTool):
    """Unified web search tool that uses WebSearchManager for multi-provider fallback."""

    def __init__(self, tool_registry: Optional["ToolRegistry"] = None):
        self.manager = WebSearchManager(tool_registry)
        super().__init__(
            id="web_search",
            name="Unified Web Search",
            description="Multi-provider web search with automatic fallback (Tavily → Exa → Brave → Serper → DDGS).",
            source="custom",
            category="research",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query or research question"},
                    "preferred_provider": {"type": "string", "description": "Preferred provider (tavily, exa, brave, serper, praisonai, ddgs)"},
                    "max_results": {"type": "integer", "default": 10},
                    "search_depth": {"type": "string", "enum": ["basic", "advanced"], "default": "advanced"}
                },
                "required": ["query"]
            },
            permissions=ToolPermission(read_only=True, requires_approval=False, network_required=True),
            justification="Unified search interface with provider fallback and provenance tracking."
        )

    def execute(self, query: str = "", preferred_provider: Optional[str] = None, **kwargs) -> ToolResult:
        return self.manager.search(query=query, preferred_provider=preferred_provider, **kwargs)