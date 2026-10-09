"""
AMAS Central Tool Registry & Policy Gate
=======================================
Implements dynamic discovery, schema validation, permission checks,
approval triggers, real reliability metrics, and tool execution dispatch.
"""

from __future__ import annotations
import time
import logging
from typing import Dict, List, Any, Optional

from amas.tools.base import AMASTool, ToolResult, ToolPermission
from amas.tools.adapters.praisonai_adapter import (
    PraisonAIDuckDuckGoTool,
    PraisonAIFileReadTool,
    PraisonAISandboxedPythonTool
)
from amas.tools.adapters.langchain_adapter import LangChainWikipediaTool
from amas.tools.official.yahoo_finance import OfficialYahooFinanceTool
from amas.tools.official.tavily_search import (
    OfficialTavilySearchTool,
    OfficialExaSearchTool,
    OfficialBraveSearchTool,
    OfficialSerperSearchTool,
    DDGSFallbackSearchTool
)
from amas.tools.web_search_manager import WebSearchTool
from amas.tools.custom.risk_calculator import FinancialRiskCalculatorTool
from amas.tools.custom.telemetry_detector import TelemetryAnomalyDetectorTool
from amas.tools.custom.artifact_writer import ArtifactWriterTool
from amas.storage.database import AMASDatabase

logger = logging.getLogger("amas.tools.registry")


class ToolRegistry:
    """Central registry and policy orchestrator for all AMAS tools."""

    def __init__(self, database: Optional[AMASDatabase] = None):
        self._tools: Dict[str, AMASTool] = {}
        self._aliases: Dict[str, str] = {}
        self._metrics: Dict[str, Dict[str, Any]] = {}
        self._pending_approvals: Dict[str, Dict[str, Any]] = {}
        self._database = database

        self._discover_and_register_default_tools()
        if database:
            self._load_metrics_from_db()

    def _discover_and_register_default_tools(self):
        """Register tools adhering to the strict 5-tier source priority."""
        # Priority 1: Official PraisonAI Tools
        self.register(PraisonAIDuckDuckGoTool(), aliases=["praison_web_search", "duckduckgo_search"])
        self.register(PraisonAIFileReadTool(), aliases=["read_file", "file_reader"])
        self.register(PraisonAISandboxedPythonTool(), aliases=["execute_sandboxed_python", "code_interpreter"])

        # Priority 2: LangChain Community Integrations
        self.register(LangChainWikipediaTool(), aliases=["wikipedia_search", "query_knowledge_base"])

        # Priority 4: Official Service APIs (Web Search)
        # These are registered conditionally based on API key availability
        self.register(OfficialTavilySearchTool(), aliases=["tavily_search", "web_search"])
        self.register(OfficialExaSearchTool(), aliases=["exa_search"])
        self.register(OfficialBraveSearchTool(), aliases=["brave_search"])
        self.register(OfficialSerperSearchTool(), aliases=["serper_search"])

        # Priority 4: Official Service APIs (Finance)
        self.register(OfficialYahooFinanceTool(), aliases=["retrieve_financial_data", "yahoo_finance"])

        # Priority 5: Justified Custom AMAS Tools
        self.register(FinancialRiskCalculatorTool(), aliases=["compute_risk_metrics", "sharpe_calculator"])
        self.register(TelemetryAnomalyDetectorTool(), aliases=["detect_time_series_anomalies", "anomaly_detector"])
        self.register(ArtifactWriterTool(), aliases=["create_report", "write_artifact"])

        # Priority 6: Fallback (no API key required)
        self.register(DDGSFallbackSearchTool(), aliases=["ddgs_search", "fallback_search"])

        # Unified Web Search Manager (custom orchestration layer)
        self.register(WebSearchTool(self), aliases=["unified_web_search", "search"])

    def register(self, tool: AMASTool, aliases: Optional[List[str]] = None):
        """Register an AMASTool and its convenient caller aliases."""
        self._tools[tool.id] = tool
        self._metrics[tool.id] = {
            "calls": 0,
            "successes": 0,
            "failures": 0,
            "total_latency_ms": 0.0,
            "avg_latency_ms": 0.0,
            "last_status": "READY"
        }
        if aliases:
            for alias in aliases:
                self._aliases[alias] = tool.id

    def get_tool(self, name_or_alias: str) -> Optional[AMASTool]:
        """Resolve a tool by exact ID or common alias."""
        if name_or_alias in self._tools:
            return self._tools[name_or_alias]
        if name_or_alias in self._aliases:
            resolved_id = self._aliases[name_or_alias]
            return self._tools.get(resolved_id)
        return None

    def _load_metrics_from_db(self):
        """Load persisted tool metrics from database."""
        if not self._database:
            return
        try:
            with self._database._lock:
                conn = self._database._get_connection()
                rows = conn.execute("SELECT tool_id, calls, successes, failures, total_latency_ms, avg_latency_ms, last_status FROM tool_metrics").fetchall()
                for row in rows:
                    self._metrics[row["tool_id"]] = {
                        "calls": row["calls"],
                        "successes": row["successes"],
                        "failures": row["failures"],
                        "total_latency_ms": row["total_latency_ms"],
                        "avg_latency_ms": row["avg_latency_ms"],
                        "last_status": row["last_status"]
                    }
                conn.close()
            logger.info(f"Loaded metrics for {len(self._metrics)} tools from database")
        except Exception as e:
            logger.warning(f"Failed to load tool metrics from DB: {e}")

    def _save_metrics_to_db(self, tool_id: str):
        """Save tool metrics to database."""
        if not self._database:
            return
        try:
            metric = self._metrics.get(tool_id)
            if not metric:
                return
            with self._database._lock:
                conn = self._database._get_connection()
                conn.execute("""
                CREATE TABLE IF NOT EXISTS tool_metrics (
                    tool_id TEXT PRIMARY KEY,
                    calls INTEGER,
                    successes INTEGER,
                    failures INTEGER,
                    total_latency_ms REAL,
                    avg_latency_ms REAL,
                    last_status TEXT,
                    updated_at REAL
                )
                """)
                conn.execute("""
                INSERT INTO tool_metrics (tool_id, calls, successes, failures, total_latency_ms, avg_latency_ms, last_status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(tool_id) DO UPDATE SET
                    calls=excluded.calls,
                    successes=excluded.successes,
                    failures=excluded.failures,
                    total_latency_ms=excluded.total_latency_ms,
                    avg_latency_ms=excluded.avg_latency_ms,
                    last_status=excluded.last_status,
                    updated_at=excluded.updated_at
                """, (
                    tool_id,
                    metric["calls"],
                    metric["successes"],
                    metric["failures"],
                    metric["total_latency_ms"],
                    metric["avg_latency_ms"],
                    metric["last_status"],
                    time.time()
                ))
                conn.commit()
                conn.close()
        except Exception as e:
            logger.warning(f"Failed to save tool metrics to DB: {e}")

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return catalog of all registered tools with metadata and metrics for UI."""
        results = []
        for tid, tool in self._tools.items():
            info = tool.to_dict()
            info["metrics"] = self._metrics.get(tid, {})
            results.append(info)
        return results

    def execute(
        self,
        tool_name: str,
        kwargs: Dict[str, Any],
        require_approval_check: bool = True
    ) -> ToolResult:
        """Execute tool with permission checking, error classification, and metrics."""
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                data=None,
                error=f"Tool '{tool_name}' is not registered in the AMAS Tool Registry.",
                source="unknown",
                duration_ms=0.0
            )

        metric = self._metrics[tool.id]
        metric["calls"] += 1

        # Check Human Approval Policy
        if require_approval_check and tool.permissions.requires_approval:
            logger.info(f"Tool {tool.name} requires human approval before proceeding.")
            return ToolResult(
                success=False,
                data={"status": "APPROVAL_REQUIRED", "tool_id": tool.id, "kwargs": kwargs},
                error="Action halted: This sensitive tool requires user approval in the UI.",
                source=tool.source,
                category=tool.category,
                duration_ms=0.0,
                metadata={"approval_required": True}
            )

        start = time.perf_counter()
        try:
            result = tool.execute(**kwargs)
            duration_ms = (time.perf_counter() - start) * 1000.0
            if result.duration_ms == 0.0:
                result.duration_ms = round(duration_ms, 2)

            if result.success:
                metric["successes"] += 1
                metric["last_status"] = "SUCCESS"
            else:
                metric["failures"] += 1
                metric["last_status"] = "FAILED"

            metric["total_latency_ms"] += result.duration_ms
            metric["avg_latency_ms"] = round(metric["total_latency_ms"] / metric["calls"], 2)
            self._save_metrics_to_db(tool.id)
            return result
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000.0
            metric["failures"] += 1
            metric["last_status"] = "FAILED"
            metric["total_latency_ms"] += duration_ms
            metric["avg_latency_ms"] = round(metric["total_latency_ms"] / metric["calls"], 2)
            self._save_metrics_to_db(tool.id)

            return ToolResult(
                success=False,
                data=None,
                error=f"Tool execution exception: {str(e)}",
                source=tool.source,
                category=tool.category,
                duration_ms=round(duration_ms, 2)
            )
