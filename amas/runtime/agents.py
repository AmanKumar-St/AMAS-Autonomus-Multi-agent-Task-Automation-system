"""
AMAS Specialized Agent Definitions
==================================
Defines the specialized agent roles for AMAS.
Each agent has a specific responsibility and strictly bounded tools.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional


class AgentRole(str, Enum):
    ORCHESTRATOR = "Orchestrator"
    PLANNER = "PlanningAgent"
    RESEARCHER = "ResearchAgent"
    ANALYST = "AnalysisAgent"
    EXECUTOR = "ExecutionAgent"
    VERIFIER = "VerificationAgent"
    RECOVERY = "RecoveryAgent"


@dataclass
class AgentProfile:
    role: AgentRole
    name: str
    goal: str
    backstory: str
    allowed_tool_categories: List[str]
    default_tools: List[str] = field(default_factory=list)


AGENT_PROFILES: Dict[AgentRole, AgentProfile] = {
    AgentRole.PLANNER: AgentProfile(
        role=AgentRole.PLANNER,
        name="Master Planning Agent",
        goal="Decompose complex user directives into an optimal Directed Acyclic Graph (DAG) of actionable tasks.",
        backstory="Strategic systems architect adept at isolating prerequisites, scheduling dependencies, and delegating to specialized agents.",
        allowed_tool_categories=["planning"],
        default_tools=[]
    ),
    AgentRole.RESEARCHER: AgentProfile(
        role=AgentRole.RESEARCHER,
        name="External Research Agent",
        goal="Retrieve verified external facts, market data, and references without guessing or hallucinating.",
        backstory="Rigorous research investigator with controlled access to live search engines, Wikipedia, and public APIs.",
        allowed_tool_categories=["research", "finance", "files"],
        default_tools=["web_search", "wikipedia_search", "retrieve_financial_data", "read_file"]
    ),
    AgentRole.ANALYST: AgentProfile(
        role=AgentRole.ANALYST,
        name="Quantitative Analysis Agent",
        goal="Perform deterministic statistical modeling, anomaly classification, and numerical transformations.",
        backstory="Quantitative scientist specializing in mathematical precision, time-series distributions, and variance metrics.",
        allowed_tool_categories=["finance", "telemetry", "code"],
        default_tools=["compute_risk_metrics", "detect_time_series_anomalies", "execute_sandboxed_python"]
    ),
    AgentRole.EXECUTOR: AgentProfile(
        role=AgentRole.EXECUTOR,
        name="Task Execution Agent",
        goal="Invoke execution tools, format structured deliverables, and generate persistent artifacts.",
        backstory="Operational automation specialist executing sandboxed transformations and generating clean deliverables.",
        allowed_tool_categories=["code", "automation", "files"],
        default_tools=["execute_sandboxed_python", "write_artifact", "read_file"]
    ),
    AgentRole.VERIFIER: AgentProfile(
        role=AgentRole.VERIFIER,
        name="Independent Verification Agent",
        goal="Adversarially audit all intermediary and final results against mathematical, factual, and safety constraints.",
        backstory="Independent quality auditor with zero tolerance for hallucinations, out-of-bounds calculations, or missing citations.",
        allowed_tool_categories=["verification", "research"],
        default_tools=["web_search", "wikipedia_search"]
    ),
    AgentRole.RECOVERY: AgentProfile(
        role=AgentRole.RECOVERY,
        name="Self-Healing & Reflection Agent",
        goal="Diagnose execution faults or verification rejections, determine retryability, and formulate revised task directives.",
        backstory="Fault tolerance expert experienced in exponential backoff retries, alternative tool selection, and dynamic replanning.",
        allowed_tool_categories=["planning", "recovery"],
        default_tools=[]
    )
}
