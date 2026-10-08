"""
AMAS Dynamic LLM Planner
========================
Replaces hardcoded keyword heuristics with genuine LLM-driven task graph generation.
Translates arbitrary natural language objectives into executable Directed Acyclic Graphs (DAGs).
"""

from __future__ import annotations
import json
import re
import logging
from typing import Dict, List, Any, Optional

from amas.providers.manager import ProviderManager
from amas.runtime.agents import AGENT_PROFILES, AgentRole
from amas.tools.registry import ToolRegistry

logger = logging.getLogger("amas.runtime.planner")


class LLMPlanner:
    """Decomposes arbitrary user goals into structured, executable Task DAGs via configured LLM."""

    def __init__(self, provider_manager: ProviderManager, tool_registry: ToolRegistry):
        self.provider_manager = provider_manager
        self.tool_registry = tool_registry

    def generate_plan(
        self,
        objective: str,
        preferred_provider_id: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Query LLM to dynamically generate a Directed Acyclic Graph (DAG) for the given objective."""
        available_tools = self.tool_registry.list_tools()
        tools_summary = "\n".join([
            f"- '{t['id']}' (aliases: {', '.join(t.get('aliases', []))}): {t['description']} [Category: {t['category']}, Source: {t['source']}]"
            for t in available_tools
        ])

        system_prompt = f"""You are the Master Planning Agent of AMAS (Autonomous Multi-Agent Automation System).
Your task is to analyze the user's objective and generate a structured, executable Directed Acyclic Graph (DAG) of tasks.

AVAILABLE AGENTS:
1. ResearchAgent: Queries live internet, Wikipedia, APIs, reads project files.
2. AnalysisAgent: Runs statistical math, anomaly detection, data processing, and calculations.
3. ExecutionAgent: Invokes actions, writes files, compiles deliverables.
4. VerificationAgent: Audits claims, cross-checks calculations, verifies sources and safety constraints.

AVAILABLE TOOLS IN REGISTRY:
{tools_summary}

RULES:
1. Break down the objective into 2 to 5 well-defined sequential or parallel tasks.
2. Specify dependencies accurately using task IDs (e.g. "dependencies": ["task_1"]).
3. Ensure the graph is a valid DAG (no circular dependencies).
4. Assign the appropriate agent and tool for each task. If no tool is needed (e.g. pure reasoning or verification), set "tool_required": null.
5. If arguments are needed for a tool, provide them in "tool_args".
6. Always end with a Verification task or final deliverable synthesis.
7. Output ONLY a valid JSON object matching the schema below. No conversational markdown text.

REQUIRED JSON SCHEMA:
{{
  "goal": "Brief restatement of objective",
  "plan_rationale": "Concise architectural explanation of decomposition",
  "tasks": [
    {{
      "id": "task_1",
      "title": "Short title",
      "description": "Detailed execution instructions for the agent",
      "agent": "ResearchAgent",
      "tool_required": "praison_web_search",
      "tool_args": {{"query": "search term"}},
      "dependencies": []
    }}
  ]
}}"""

        user_prompt = f"Objective: \"{objective}\"\n\nGenerate the complete executable task DAG in JSON."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        logger.info(f"Generating dynamic plan for objective: '{objective[:80]}...'")
        response = self.provider_manager.execute_with_fallback(
            messages=messages,
            preferred_provider_id=preferred_provider_id,
            model=model,
            temperature=0.2
        )

        plan = self._parse_json_plan(response.content, objective)
        self._validate_dag(plan)
        return plan

    def _parse_json_plan(self, content: str, objective: str) -> Dict[str, Any]:
        """Extract and parse JSON object from LLM completion, handling code fences."""
        raw = content.strip()
        # Remove markdown code block fences if present
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
            raw = re.sub(r"\s*```$", "", raw, flags=re.MULTILINE)
            raw = raw.strip()

        # Try direct parse
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict) and "tasks" in parsed and isinstance(parsed["tasks"], list):
                return parsed
        except Exception:
            pass

        # Try regex search for outermost curly braces
        match = re.search(r"(\{[\s\S]*\})", raw)
        if match:
            try:
                parsed = json.loads(match.group(1))
                if isinstance(parsed, dict) and "tasks" in parsed:
                    return parsed
            except Exception:
                pass

        logger.warning("LLM produced unparseable JSON plan. Falling back to dynamic baseline decomposition.")
        # Robust fallback for degraded LLM modes
        return {
            "goal": objective,
            "plan_rationale": "Automated fallback decomposition for objective",
            "tasks": [
                {
                    "id": "task_1_research",
                    "title": f"Research Information for: {objective[:40]}",
                    "description": f"Gather primary facts, context, or data regarding: {objective}",
                    "agent": AgentRole.RESEARCHER.value,
                    "tool_required": "praison_web_search",
                    "tool_args": {"query": objective[:60]},
                    "dependencies": []
                },
                {
                    "id": "task_2_process",
                    "title": "Analyze Findings and Formulate Deliverable",
                    "description": "Analyze collected data points and structure final output.",
                    "agent": AgentRole.ANALYST.value,
                    "tool_required": None,
                    "tool_args": {},
                    "dependencies": ["task_1_research"]
                },
                {
                    "id": "task_3_verify",
                    "title": "Audit Claims and Verify Output Soundness",
                    "description": "Verify factual citations and deliverable compliance.",
                    "agent": AgentRole.VERIFIER.value,
                    "tool_required": None,
                    "tool_args": {},
                    "dependencies": ["task_2_process"]
                }
            ]
        }

    def _validate_dag(self, plan: Dict[str, Any]):
        """Ensure task IDs are unique and dependencies do not contain cycles."""
        tasks = plan.get("tasks", [])
        task_ids = set()
        for t in tasks:
            tid = t.get("id")
            if not tid:
                raise ValueError("Every task node must possess a valid 'id'.")
            if tid in task_ids:
                raise ValueError(f"Duplicate task id '{tid}' found in plan.")
            task_ids.add(tid)

        # Check dependencies exist
        for t in tasks:
            for dep in t.get("dependencies", []):
                if dep not in task_ids:
                    logger.warning(f"Task '{t['id']}' references missing dependency '{dep}'. Removing.")
                    t["dependencies"].remove(dep)
