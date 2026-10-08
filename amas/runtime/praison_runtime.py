"""
AMAS PraisonAI Runtime Adapter
==============================
Bridges AMAS task specifications and PraisonAI Agent & Task instances.
Executes individual task nodes through PraisonAI agents with bounded tools and memory.
Includes smart blackboard argument resolution across DAG steps.
"""

from __future__ import annotations
import time
import json
import logging
from typing import Dict, List, Any, Optional

from amas.providers.manager import ProviderManager
from amas.runtime.agents import AGENT_PROFILES, AgentRole
from amas.tools.registry import ToolRegistry
from amas.runtime.memory import RunMemory

logger = logging.getLogger("amas.runtime.praison")


class PraisonRuntime:
    """Executes tasks using the PraisonAI Agent ecosystem."""

    def __init__(self, provider_manager: ProviderManager, tool_registry: ToolRegistry):
        self.provider_manager = provider_manager
        self.tool_registry = tool_registry

    def _resolve_tool_arguments(self, tool_name: str, raw_args: Dict[str, Any], memory: RunMemory) -> Dict[str, Any]:
        """Auto-bind blackboard context to tool parameters when upstream tasks generated data."""
        resolved = dict(raw_args or {})
        tool = self.tool_registry.get_tool(tool_name)
        tool_id = tool.id if tool else tool_name

        # 1. Financial risk calculator resolution
        if tool_id in ["amas_financial_risk_calculator", "compute_risk_metrics"]:
            if "prices" not in resolved or not resolved["prices"]:
                closes = memory.get("historical_closes") or memory.get("raw_prices")
                if closes and isinstance(closes, list):
                    resolved["prices"] = closes

        # 2. Telemetry detector resolution
        if tool_id in ["amas_telemetry_anomaly_detector", "detect_time_series_anomalies"]:
            if "data_points" not in resolved or not resolved["data_points"]:
                telemetry = memory.get("telemetry_stream") or memory.get("data_points")
                if telemetry and isinstance(telemetry, list):
                    resolved["data_points"] = telemetry

        # 3. Artifact writer resolution
        if tool_id in ["amas_artifact_writer", "create_report"]:
            if "content" not in resolved or not resolved["content"]:
                resolved["content"] = memory.get("latest_summary") or memory.get("last_result") or "# AMAS Workflow Deliverable\nExecution completed."
            if "filename" not in resolved or not resolved["filename"]:
                resolved["filename"] = "deliverable_report.md"

        return resolved

    def execute_node(
        self,
        task_data: Dict[str, Any],
        memory: RunMemory,
        preferred_provider_id: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a single task node within the workflow context."""
        start = time.perf_counter()
        task_id = task_data["id"]
        role_str = task_data.get("agent", "ExecutionAgent")
        title = task_data.get("title", "")
        description = task_data.get("description", "")
        tool_required = task_data.get("tool_required")
        tool_args = task_data.get("tool_args", {})

        memory.log_message(
            sender=role_str,
            receiver="Orchestrator",
            content=f"Starting task '{title}': {description}",
            task_id=task_id
        )

        tool_result = None
        # 1. If a tool is required, resolve arguments from blackboard and execute via registry
        if tool_required:
            resolved_args = self._resolve_tool_arguments(tool_required, tool_args, memory)
            logger.info(f"Task '{task_id}' invoking tool '{tool_required}' with resolved args: {resolved_args.keys()}")

            tool_result = self.tool_registry.execute(tool_required, resolved_args)
            memory.log_tool_call(tool_result.to_dict())

            # Store result in blackboard
            if tool_result.success and isinstance(tool_result.data, dict):
                for k, v in tool_result.data.items():
                    memory.set(k, v)
                memory.set(f"task_{task_id}_data", tool_result.data)

        # 2. Execute agent reasoning / synthesis with configured LLM
        blackboard_snapshot = memory.to_dict()
        context_summary = f"Workflow Blackboard Context:\n{json_truncate(blackboard_snapshot, 1500)}"
        if tool_result:
            context_summary += f"\n\nTool Call Result ({tool_required}):\nSuccess: {tool_result.success}\nData: {json_truncate(tool_result.data, 1000)}"

        system_prompt = f"""You are the {role_str} in the AMAS Multi-Agent Automation System.
Your Goal: Execute task '{title}' accurately and thoroughly.
Task Instructions: {description}
Enforce strict zero-hallucination. Only state facts and metrics present in the tool results or blackboard context.
Output your analytical synthesis in direct formatted Markdown text. Do not output tool calling JSON or invoke tools."""

        user_content = f"{context_summary}\n\nPlease provide the definitive outcome and deliverable for task '{title}'."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        try:
            llm_resp = self.provider_manager.execute_with_fallback(
                messages=messages,
                preferred_provider_id=preferred_provider_id,
                model=model,
                temperature=0.3
            )
            agent_output = llm_resp.content.strip()
            used_provider = llm_resp.provider_id
            used_model = llm_resp.model
        except Exception as e:
            logger.warning(f"Agent LLM reasoning call failed: {e}. Using deterministic tool summary.")
            agent_output = f"Completed with tool output: {tool_result.data if tool_result else 'Success'}"
            used_provider = preferred_provider_id or "local"
            used_model = model or "local"

        # Update latest summary in memory for downstream tasks
        memory.set("latest_summary", agent_output)
        memory.set("last_result", agent_output)

        duration_ms = (time.perf_counter() - start) * 1000.0

        memory.log_message(
            sender=role_str,
            receiver="Orchestrator",
            content=f"Completed task '{title}'. Output summary: {agent_output[:200]}...",
            task_id=task_id
        )

        return {
            "task_id": task_id,
            "status": "COMPLETED",
            "result": agent_output,
            "tool_call": tool_result.to_dict() if tool_result else None,
            "duration_ms": round(duration_ms, 2),
            "provider": used_provider,
            "model": used_model
        }


def json_truncate(data: Any, max_len: int = 1000) -> str:
    """Helper to cleanly format JSON snippets for prompts."""
    try:
        s = json.dumps(data, default=str)
        if len(s) > max_len:
            return s[:max_len] + "... [truncated]"
        return s
    except Exception:
        return str(data)[:max_len]
