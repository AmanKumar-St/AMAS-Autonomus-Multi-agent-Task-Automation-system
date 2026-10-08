"""
AMAS PraisonAI Tool Adapter (Priority 1)
========================================
Adapts official, built-in tools from the PraisonAI ecosystem into AMAS.
PraisonAI tools take top priority whenever a capability exists.
"""

from __future__ import annotations
import time
import os
from typing import Dict, List, Any, Optional

from amas.tools.base import AMASTool, ToolPermission, ToolResult


class PraisonAIDuckDuckGoTool(AMASTool):
    """PraisonAI built-in Web Search Tool using DuckDuckGo."""

    def __init__(self):
        super().__init__(
            id="praison_web_search",
            name="PraisonAI Web Search",
            description="Searches the live public internet for current facts, articles, wire stories, and references.",
            source="praisonai",
            category="research",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search keywords or objective"}
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
                error="Query string is required for web search.",
                source=self.source,
                category=self.category,
                duration_ms=0.0
            )

        try:
            from praisonaiagents.tools import duckduckgo
            raw_results = duckduckgo(query)
            duration_ms = (time.perf_counter() - start) * 1000.0

            citations = []
            normalized_articles = []
            if isinstance(raw_results, list):
                for item in raw_results:
                    if isinstance(item, dict):
                        title = item.get("title", "")
                        url = item.get("url") or item.get("href", "")
                        snippet = item.get("snippet") or item.get("body", "")
                        normalized_articles.append({
                            "title": title,
                            "url": url,
                            "snippet": snippet
                        })
                        if url:
                            citations.append({"title": title, "url": url})
            elif isinstance(raw_results, str):
                normalized_articles.append({"snippet": raw_results})

            if not normalized_articles:
                return ToolResult(
                    success=False,
                    data={"articles": [], "query": query},
                    error="Live web search returned no matching results.",
                    source=self.source,
                    category=self.category,
                    duration_ms=round(duration_ms, 2)
                )

            return ToolResult(
                success=True,
                data={"articles": normalized_articles, "query": query, "count": len(normalized_articles)},
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
                error=f"PraisonAI duckduckgo tool failed: {str(e)}",
                source=self.source,
                category=self.category,
                duration_ms=round(duration_ms, 2)
            )


class PraisonAIFileReadTool(AMASTool):
    """PraisonAI built-in file reader tool with workspace sandboxing."""

    def __init__(self, workspace_root: Optional[str] = None):
        self.workspace_root = workspace_root or os.getcwd()
        super().__init__(
            id="praison_file_read",
            name="PraisonAI File Reader",
            description="Reads local text/code files within the approved project workspace.",
            source="praisonai",
            category="files",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative or absolute file path"}
                },
                "required": ["path"]
            },
            permissions=ToolPermission(
                read_only=True,
                requires_approval=False,
                filesystem_access=True
            )
        )

    def execute(self, path: str = "", **kwargs) -> ToolResult:
        start = time.perf_counter()
        target = os.path.abspath(path if os.path.isabs(path) else os.path.join(self.workspace_root, path))
        
        # Prevent path traversal outside approved directory
        if not target.startswith(os.path.abspath(self.workspace_root)):
            return ToolResult(
                success=False,
                data=None,
                error="Path traversal denied. Access restricted to project workspace.",
                source=self.source,
                category=self.category,
                duration_ms=0.0
            )

        if not os.path.exists(target):
            return ToolResult(
                success=False,
                data=None,
                error=f"File not found: {path}",
                source=self.source,
                category=self.category,
                duration_ms=round((time.perf_counter() - start) * 1000.0, 2)
            )

        try:
            with open(target, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(50000)  # Safe limit
            return ToolResult(
                success=True,
                data={"content": content, "path": path, "size_bytes": os.path.getsize(target)},
                source=self.source,
                category=self.category,
                duration_ms=round((time.perf_counter() - start) * 1000.0, 2)
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to read file: {str(e)}",
                source=self.source,
                category=self.category,
                duration_ms=round((time.perf_counter() - start) * 1000.0, 2)
            )


class PraisonAISandboxedPythonTool(AMASTool):
    """PraisonAI sandboxed code execution tool for math & transformations."""

    def __init__(self):
        super().__init__(
            id="praison_code_interpreter",
            name="PraisonAI Sandboxed Python Runner",
            description="Safely executes Python math, statistical formulas, or data transformations in a restricted environment.",
            source="praisonai",
            category="code",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python code snippet to execute"}
                },
                "required": ["code"]
            },
            permissions=ToolPermission(
                read_only=True,
                requires_approval=False,
                filesystem_access=False
            )
        )

    def execute(self, code: str = "", **kwargs) -> ToolResult:
        start = time.perf_counter()
        # Security checks: block forbidden words
        forbidden = ["os.system", "subprocess", "eval(", "exec(", "shutil", "socket", "open(", "importlib"]
        for f in forbidden:
            if f in code:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Security Violation: '{f}' is restricted in sandboxed execution.",
                    source=self.source,
                    category=self.category,
                    duration_ms=0.0
                )

        import math
        safe_globals = {
            "__builtins__": {
                "abs": abs, "all": all, "any": any, "bool": bool, "dict": dict,
                "enumerate": enumerate, "float": float, "int": int, "len": len,
                "list": list, "max": max, "min": min, "range": range, "round": round,
                "set": set, "sorted": sorted, "str": str, "sum": sum, "zip": zip,
                "print": lambda *args: None
            },
            "math": math
        }
        safe_locals: Dict[str, Any] = {}

        try:
            # Execute in strictly sandboxed namespace
            exec(code, safe_globals, safe_locals)
            duration_ms = (time.perf_counter() - start) * 1000.0
            output_vars = {k: v for k, v in safe_locals.items() if not k.startswith("_")}
            return ToolResult(
                success=True,
                data={"output": output_vars, "status": "executed"},
                source=self.source,
                category=self.category,
                duration_ms=round(duration_ms, 2)
            )
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000.0
            return ToolResult(
                success=False,
                data=None,
                error=f"Execution error: {str(e)}",
                source=self.source,
                category=self.category,
                duration_ms=round(duration_ms, 2)
            )
