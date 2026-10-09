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
import os
from typing import Dict, List, Any, Optional

from amas.providers.manager import ProviderManager
from amas.runtime.agents import AGENT_PROFILES, AgentRole
from amas.tools.registry import ToolRegistry
from amas.runtime.memory import RunMemory

logger = logging.getLogger("amas.runtime.praison")


def json_truncate(data: Any, max_len: int = 1000) -> str:
    """Helper to cleanly format JSON snippets for prompts."""
    try:
        s = json.dumps(data, default=str)
        if len(s) > max_len:
            return s[:max_len] + "... [truncated]"
        return s
    except Exception:
        return str(data)[:max_len]


class PraisonRuntime:
    """Executes tasks using the PraisonAI Agent ecosystem."""

    def __init__(self, provider_manager: ProviderManager, tool_registry: ToolRegistry):
        self.provider_manager = provider_manager
        self.tool_registry = tool_registry
        self._agent_cache: Dict[str, Any] = {}

    def _get_llm_config(self, preferred_provider_id: Optional[str] = None, model: Optional[str] = None) -> Dict[str, Any]:
        """Get LLM configuration for PraisonAI agent."""
        provider = self.provider_manager.get_provider(preferred_provider_id)
        return {
            "llm": provider.provider_id,
            "model": model or provider.default_model,
            "base_url": provider.base_url if hasattr(provider, 'base_url') else None,
            "api_key": provider.api_key if hasattr(provider, 'api_key') else None
        }

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

    def _create_praison_agent(self, role_str: str, task_data: Dict[str, Any], preferred_provider_id: Optional[str] = None, model: Optional[str] = None):
        """Create a PraisonAI Agent for the given role."""
        try:
            from praisonaiagents import Agent
        except ImportError:
            logger.warning("praisonaiagents not installed, using LLM fallback")
            return None

        profile = AGENT_PROFILES.get(AgentRole(role_str))
        if not profile:
            logger.warning(f"No profile for role {role_str}")
            return None

        llm_config = self._get_llm_config(preferred_provider_id, model)

        # Map AMAS tool IDs to PraisonAI tool names
        tool_mapping = {
            "praison_web_search": "duckduckgo",
            "official_tavily_search": "tavily",
            "official_exa_search": "exa",
            "official_brave_search": "brave",
            "official_serper_search": "serper",
            "langchain_wikipedia": "wikipedia",
            "official_financial_retriever": "yahoo_finance",
            "praison_file_read": "file_read",
            "praison_code_interpreter": "code_interpreter",
            "amas_financial_risk_calculator": None,  # Custom - no direct PraisonAI equivalent
            "amas_telemetry_anomaly_detector": None,  # Custom - no direct PraisonAI equivalent
            "amas_artifact_writer": None,  # Custom - no direct PraisonAI equivalent
        }

        # Get allowed tools for this agent
        allowed_tool_ids = profile.default_tools
        praison_tools = []
        for tool_id in allowed_tool_ids:
            mapped = tool_mapping.get(tool_id)
            if mapped:
                praison_tools.append(mapped)
            else:
                # Custom AMAS tools - we'll handle via AMAS tool registry
                logger.debug(f"Tool {tool_id} is custom AMAS tool, will use AMAS registry")

        agent = Agent(
            name=profile.name,
            role=profile.role,
            goal=profile.goal,
            backstory=profile.backstory,
            llm=llm_config.get("llm"),
            model=llm_config.get("model"),
            base_url=llm_config.get("base_url"),
            api_key=llm_config.get("api_key"),
            tools=praison_tools if praison_tools else None,
            instructions=f"You are the {profile.name}. {profile.backstory} Execute the task: {task_data.get('description', '')}"
        )
        return agent

    def _create_praison_task(self, task_data: Dict[str, Any], agent, tool_required: Optional[str], resolved_args: Dict[str, Any]):
        """Create a PraisonAI Task for the given task data."""
        try:
            from praisonaiagents import Task
        except ImportError:
            return None

        # Build task description with tool context
        description = task_data.get("description", "")
        if tool_required:
            tool_info = self.tool_registry.get_tool(tool_required)
            if tool_info:
                description += f"\n\nUse the tool '{tool_info.name}' with arguments: {json.dumps(resolved_args)}"
                description += "\nTool source: " + tool_info.source
                description += "\nTool category: " + tool_info.category

        task = Task(
            description=description,
            expected_output=f"Complete the task: {task_data.get('title', '')}. Provide detailed output with any findings, calculations, or results.",
            agent=agent,
            name=task_data.get("title", task_data.get("id", "task")),
            tools=None  # We handle tools via AMAS registry
        )
        return task

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
        agent_output = ""

        # 1. If a tool is required, resolve arguments from blackboard and execute via registry
        if tool_required:
            resolved_args = self._resolve_tool_arguments(tool_required, tool_args, memory)
            logger.info(f"Task '{task_id}' invoking tool '{tool_required}' with resolved args: {list(resolved_args.keys())}")

            tool_result = self.tool_registry.execute(tool_required, resolved_args)
            memory.log_tool_call(tool_result.to_dict())

            # Store result in blackboard
            if tool_result.success and isinstance(tool_result.data, dict):
                for k, v in tool_result.data.items():
                    memory.set(k, v)
                memory.set(f"task_{task_id}_data", tool_result.data)

        # 2. Execute agent reasoning / synthesis with PraisonAI Agent
        blackboard_snapshot = memory.to_dict()
        context_summary = f"Workflow Blackboard Context:\n{json_truncate(blackboard_snapshot, 1500)}"
        if tool_result:
            context_summary += f"\n\nTool Call Result ({tool_required}):\nSuccess: {tool_result.success}\nData: {json_truncate(tool_result.data, 1000)}"

        # Try PraisonAI Agent first
        praison_agent = self._create_praison_agent(role_str, task_data, preferred_provider_id, model)
        used_provider = preferred_provider_id or "local"
        used_model = model or "local"

        if praison_agent:
            try:
                praison_task = self._create_praison_task(task_data, praison_agent, tool_required, resolved_args if tool_required else {})
                if praison_task:
                    # Execute via PraisonAI
                    logger.info(f"Executing task '{task_id}' via PraisonAI Agent")
                    task_output = praison_agent.start(praison_task)
                    agent_output = str(task_output)
                    logger.info(f"PraisonAI task completed for '{task_id}'")
                else:
                    raise ValueError("Failed to create PraisonAI task")
            except Exception as e:
                logger.warning(f"PraisonAI Agent execution failed for '{task_id}': {e}. Falling back to LLM.")
                agent_output = self._execute_llm_fallback(context_summary, role_str, title, description, preferred_provider_id, model)
                used_provider = preferred_provider_id or "fallback"
                used_model = model or "fallback"
        else:
            # Fallback to direct LLM call
            agent_output = self._execute_llm_fallback(context_summary, role_str, title, description, preferred_provider_id, model)

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

    def _execute_llm_fallback(
        self,
        context_summary: str,
        role_str: str,
        title: str,
        description: str,
        preferred_provider_id: Optional[str],
        model: Optional[str]
    ) -> str:
        """Fallback to direct LLM call when PraisonAI is unavailable."""
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
            return llm_resp.content.strip()
        except Exception as e:
            logger.warning(f"Agent LLM reasoning call failed: {e}. Using deterministic tool summary.")
            return f"Completed with tool output: {context_summary}"