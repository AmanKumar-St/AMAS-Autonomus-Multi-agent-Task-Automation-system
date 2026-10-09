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
import re
from typing import Dict, List, Any, Optional

from amas.providers.manager import ProviderManager
from amas.runtime.agents import AGENT_PROFILES, AgentRole
from amas.tools.registry import ToolRegistry
from amas.runtime.memory import RunMemory

logger = logging.getLogger("amas.runtime.praison")


def json_truncate(data: Any, max_len: int = 4000) -> str:
    """Helper to cleanly format JSON snippets for prompts without premature cutoff."""
    try:
        s = json.dumps(data, default=str)
        if len(s) > max_len:
            return s[:max_len] + "... [truncated]"
        return s
    except Exception:
        return str(data)[:max_len]


def format_tool_result_for_context(tool_name: str, tool_result: Any) -> str:
    """Format tool execution output into clean, structured readable text for LLM agents."""
    if not tool_result or not tool_result.success:
        err = getattr(tool_result, "error", "Execution failed") if tool_result else "No result"
        return f"Tool '{tool_name}' error: {err}"

    data = tool_result.data
    if isinstance(data, dict):
        # 1. Web search / Tavily results
        results = data.get("results")
        answer = data.get("answer")
        if results is not None or answer is not None:
            parts = []
            if answer:
                parts.append(f"AI Direct Answer:\n{answer}\n")
            if results and isinstance(results, list):
                parts.append("Factual Search Results & Citations:")
                for idx, r in enumerate(results[:8], 1):
                    title = r.get("title", "Untitled")
                    url = r.get("url", "")
                    snip = r.get("snippet") or r.get("content") or ""
                    parts.append(f"[{idx}] {title}\n    URL: {url}\n    Content: {snip[:700]}")
            return "\n".join(parts)

        # 2. Artifact writer result
        if "filename" in data and "file_path" in data:
            return f"Artifact '{data.get('filename')}' created at {data.get('file_path')} (size: {data.get('size_bytes', 0)} bytes)."

        # 3. Standard JSON data
        try:
            return json.dumps(data, indent=2, default=str)[:6000]
        except Exception:
            return str(data)[:6000]

    return str(data)[:6000]


class PraisonRuntime:
    """Executes tasks using the PraisonAI Agent ecosystem."""

    def __init__(self, provider_manager: ProviderManager, tool_registry: ToolRegistry):
        self.provider_manager = provider_manager
        self.tool_registry = tool_registry
        self._agent_cache: Dict[str, Any] = {}

    def _get_llm_config(self, preferred_provider_id: Optional[str] = None, model: Optional[str] = None) -> Dict[str, Any]:
        """Get LLM configuration for PraisonAI agent."""
        provider = self.provider_manager.get_provider(preferred_provider_id)
        chosen_model = model or provider.default_model

        # Ensure correct litellm provider prefix so litellm routes correctly
        pid = provider.provider_id.lower()
        if pid == "groq" and not chosen_model.startswith("groq/"):
            chosen_model = f"groq/{chosen_model}"
        elif pid == "openrouter" and not chosen_model.startswith("openrouter/"):
            chosen_model = f"openrouter/{chosen_model}"
        elif pid == "gemini" and not chosen_model.startswith("gemini/"):
            chosen_model = f"gemini/{chosen_model}"

        return {
            "llm": provider.provider_id,
            "model": chosen_model,
            "base_url": provider.base_url if hasattr(provider, 'base_url') else None,
            "api_key": provider.api_key if hasattr(provider, 'api_key') else None
        }

    def _resolve_tool_arguments(
        self,
        tool_name: str,
        raw_args: Dict[str, Any],
        memory: RunMemory,
        task_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Auto-bind blackboard context to tool parameters when upstream tasks generated data."""
        resolved = dict(raw_args or {})
        tool = self.tool_registry.get_tool(tool_name)
        tool_id = tool.id if tool else tool_name
        task_data = task_data or {}

        # 0. Search tools query sanitization (strip template placeholders and syntax errors)
        if tool_id in ["praison_web_search", "duckduckgo_search", "official_tavily_search", "tavily_search", "web_search", "ddgs_search"]:
            if "query" in resolved:
                q = str(resolved["query"])
                # Strip curly brace placeholders like {region}, {date}, {{deaths}}
                q = re.sub(r'\{[^{}]*\}', '', q)
                q = re.sub(r'\{\{[^{}]*\}\}', '', q)
                # Strip restrictive site: directives if they cause 0 hits
                q = re.sub(r'site:\S+', '', q)
                q = re.sub(r'\s+', ' ', q).strip().strip('"').strip("'")
                if not q or len(q) < 4:
                    q = task_data.get("description", task_data.get("title", ""))
                    q = re.sub(r'\{[^{}]*\}', '', q).strip()
                resolved["query"] = q

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
        if tool_id in ["amas_artifact_writer", "create_report", "write_artifact"]:
            content = str(resolved.get("content", "") or "").strip()
            # If content is absent or is an unpopulated template skeleton with curly braces
            if not content or "{{" in content or "{" in content:
                accumulated = memory.get_accumulated_results_text() or memory.get("latest_summary") or memory.get("last_result")
                if accumulated and len(accumulated.strip()) > 30:
                    resolved["content"] = accumulated
                else:
                    resolved["content"] = f"# AMAS Deliverable Report: {task_data.get('title', 'Execution Deliverable')}\n\nExecution completed successfully."

            if "filename" not in resolved or not resolved["filename"]:
                safe_title = re.sub(r'[^a-zA-Z0-9_-]', '_', task_data.get("title", "deliverable_report")).strip('_')[:35]
                resolved["filename"] = f"{safe_title or 'deliverable_report'}.md"

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
            model=llm_config.get("model"),
            base_url=llm_config.get("base_url"),
            api_key=llm_config.get("api_key"),
            tools=None,  # Tools executed safely via AMAS ToolRegistry; Agent focuses on reasoning/synthesis
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
            resolved_args = self._resolve_tool_arguments(tool_required, tool_args, memory, task_data)
            logger.info(f"Task '{task_id}' invoking tool '{tool_required}' with resolved args: {list(resolved_args.keys())}")

            tool_result = self.tool_registry.execute(tool_required, resolved_args)
            memory.log_tool_call(tool_result.to_dict())

            # Store result in blackboard
            if tool_result.success and isinstance(tool_result.data, dict):
                if tool_required in ["amas_artifact_writer", "create_report", "write_artifact"]:
                    memory.set("latest_artifact", tool_result.data)
                    memory.set("artifact_file_path", tool_result.data.get("file_path"))
                    memory.set("artifact_filename", tool_result.data.get("filename"))
                else:
                    for k, v in tool_result.data.items():
                        memory.set(k, v)
                memory.set(f"task_{task_id}_data", tool_result.data)

        # 2. Execute agent reasoning / synthesis with PraisonAI Agent
        blackboard_snapshot = {k: v for k, v in memory.to_dict().items() if k not in ["tool_calls", "completed_task_results"]}
        accumulated_tasks = memory.get_accumulated_results_text()
        formatted_tool = format_tool_result_for_context(tool_required, tool_result) if tool_result else ""

        context_summary = f"Workflow Blackboard Context:\n{json_truncate(blackboard_snapshot, 2500)}"
        if accumulated_tasks:
            context_summary += f"\n\n--- Upstream Task Results & Research Data ---\n{accumulated_tasks[:8000]}"
        if formatted_tool:
            context_summary += f"\n\n--- Current Tool Execution Result ({tool_required}) ---\n{formatted_tool}"

        # Try PraisonAI Agent first
        praison_agent = self._create_praison_agent(role_str, task_data, preferred_provider_id, model)
        used_provider = preferred_provider_id or "local"
        used_model = model or "local"

        if praison_agent:
            try:
                praison_task = self._create_praison_task(task_data, praison_agent, tool_required, resolved_args if tool_required else {})
                if praison_task:
                    # Execute via PraisonAI - pass task description as prompt
                    logger.info(f"Executing task '{task_id}' via PraisonAI Agent")
                    # Use the task description along with blackboard context as the prompt for the agent
                    task_prompt = f"{praison_task.description}\n\n{context_summary}\n\nExpected output: {praison_task.expected_output}"
                    task_output = praison_agent.start(task_prompt)
                    agent_output = str(task_output) if task_output else ""
                    if not agent_output or len(agent_output.strip()) < 10 or agent_output.strip().lower() in ["none", "null"]:
                        logger.info(f"PraisonAI returned empty output for '{task_id}'. Falling back to LLM.")
                        agent_output = self._execute_llm_fallback(context_summary, role_str, title, description, preferred_provider_id, model)
                        used_provider = preferred_provider_id or "fallback"
                        used_model = model or "fallback"
                    else:
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

        # Update and accumulate task findings in memory for downstream tasks and final deliverable
        memory.record_task_result(task_id, title, role_str, agent_output)
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
Your Goal: Execute task '{title}' accurately, thoroughly, and professionally.
Task Instructions: {description}
Factual Grounding:
- Base your analysis directly on the facts, statistics, numbers, and tool results provided in the context.
- Maintain zero-hallucination, but make full use of all verified data points present in the Upstream Task Results or Tool Execution Output.
Deliverable Formatting:
- Synthesize findings into a rich, structured Markdown deliverable with clear headings, comparison tables, key metrics, and source citations.
- Never state that data is unavailable if relevant facts or figures are present in the provided context.
- Output direct formatted Markdown text without tool-calling JSON fences."""

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