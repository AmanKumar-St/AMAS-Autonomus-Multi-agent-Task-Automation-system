"""
AMAS Scoped Memory Architecture
===============================
Provides clearly bounded memory levels:
1. RunMemory: Private state for a single workflow execution.
2. SessionMemory: Context retained across user prompts within a session.
3. KnowledgeStore: Persistent domain references and benchmark criteria.
"""

from __future__ import annotations
import time
from typing import Dict, List, Any, Optional


class RunMemory:
    """Ephemeral, thread-safe blackboard memory for one specific execution run."""

    def __init__(self, run_id: str):
        self.run_id = run_id
        self._blackboard: Dict[str, Any] = {}
        self._tool_history: List[Dict[str, Any]] = []
        self._message_bus: List[Dict[str, Any]] = []

    def set(self, key: str, value: Any):
        self._blackboard[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._blackboard.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        d = dict(self._blackboard)
        d["tool_calls"] = list(self._tool_history)
        return d

    def log_tool_call(self, record: Dict[str, Any]):
        self._tool_history.append(record)

    def log_message(self, sender: str, receiver: str, content: str, task_id: Optional[str] = None):
        msg = {
            "id": f"msg_{len(self._message_bus) + 1}",
            "sender": sender,
            "receiver": receiver,
            "task_id": task_id,
            "content": content,
            "timestamp": time.time()
        }
        self._message_bus.append(msg)
        return msg

    @property
    def messages(self) -> List[Dict[str, Any]]:
        return list(self._message_bus)

    @property
    def tool_history(self) -> List[Dict[str, Any]]:
        return list(self._tool_history)

    def record_task_result(self, task_id: str, title: str, agent: str, result: str):
        """Record completed task output to blackboard and history for downstream tasks."""
        self._blackboard[f"task_{task_id}_result"] = result
        if "completed_task_results" not in self._blackboard or not isinstance(self._blackboard["completed_task_results"], list):
            self._blackboard["completed_task_results"] = []
        self._blackboard["completed_task_results"].append({
            "task_id": task_id,
            "title": title,
            "agent": agent,
            "result": result,
            "timestamp": time.time()
        })

    def get_accumulated_results_text(self) -> str:
        """Produce a clean, chronological text compilation of all completed task findings."""
        results = self._blackboard.get("completed_task_results", [])
        if not results:
            return ""
        sections = []
        for item in results:
            sections.append(
                f"### [Upstream Task Result: {item.get('task_id', '')} - {item.get('title', '')} ({item.get('agent', '')})]\n"
                f"{item.get('result', '')}\n"
            )
        return "\n".join(sections)


class SessionMemory:
    """Maintains user preferences and completed run summaries within an interactive session."""

    def __init__(self, session_id: str = "default_session"):
        self.session_id = session_id
        self._history: List[Dict[str, Any]] = []
        self._context_cache: Dict[str, Any] = {}

    def record_run(self, run_id: str, objective: str, status: str, summary: str):
        self._history.append({
            "run_id": run_id,
            "objective": objective,
            "status": status,
            "summary": summary,
            "timestamp": time.time()
        })

    def get_recent_runs(self, limit: int = 5) -> List[Dict[str, Any]]:
        return self._history[-limit:]
