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
        return dict(self._blackboard)

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
