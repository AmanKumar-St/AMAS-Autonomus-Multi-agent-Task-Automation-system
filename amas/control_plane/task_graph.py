"""
AMAS Dynamic Task Graph & Dependency Resolver
=============================================
Manages DAG nodes, tracks execution states, and determines next ready tasks.
"""

from __future__ import annotations
from typing import Dict, List, Any, Optional
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"


class TaskGraph:
    """Manages execution states of a Directed Acyclic Graph."""

    def __init__(self, tasks: List[Dict[str, Any]]):
        self._nodes: Dict[str, Dict[str, Any]] = {}
        for t in tasks:
            node = dict(t)
            node["status"] = TaskStatus.PENDING.value
            node["retry_count"] = 0
            node["max_retries"] = 3
            node["error_log"] = []
            node["execution_time_ms"] = 0.0
            node["result"] = None
            node["verification"] = None
            self._nodes[t["id"]] = node

    def get_ready_tasks(self) -> List[Dict[str, Any]]:
        """Return all tasks whose dependencies are COMPLETED or VERIFIED."""
        ready = []
        for tid, node in self._nodes.items():
            if node["status"] in [TaskStatus.PENDING.value, TaskStatus.RETRYING.value]:
                deps = node.get("dependencies", [])
                deps_satisfied = all(
                    self._nodes.get(d, {}).get("status") in [TaskStatus.COMPLETED.value, TaskStatus.VERIFIED.value]
                    for d in deps
                )
                if deps_satisfied:
                    ready.append(node)
        return ready

    def mark_in_progress(self, task_id: str):
        if task_id in self._nodes:
            self._nodes[task_id]["status"] = TaskStatus.IN_PROGRESS.value

    def mark_completed(self, task_id: str, result: Any, duration_ms: float):
        if task_id in self._nodes:
            self._nodes[task_id]["status"] = TaskStatus.COMPLETED.value
            self._nodes[task_id]["result"] = result
            self._nodes[task_id]["execution_time_ms"] = duration_ms

    def mark_verified(self, task_id: str, verification: Dict[str, Any]):
        if task_id in self._nodes:
            self._nodes[task_id]["status"] = TaskStatus.VERIFIED.value if verification.get("is_valid") else TaskStatus.FAILED.value
            self._nodes[task_id]["verification"] = verification

    def mark_failed(self, task_id: str, error: str) -> bool:
        """Increment retry count. Return True if retry should be attempted."""
        if task_id in self._nodes:
            node = self._nodes[task_id]
            node["retry_count"] += 1
            node["error_log"].append(error)
            if node["retry_count"] <= node["max_retries"]:
                node["status"] = TaskStatus.RETRYING.value
                return True
            else:
                node["status"] = TaskStatus.FAILED.value
                return False
        return False

    def is_finished(self) -> bool:
        """Return True if all nodes are completed/verified or non-retryable failed."""
        for node in self._nodes.values():
            if node["status"] in [TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value, TaskStatus.RETRYING.value]:
                return False
        return True

    def to_list(self) -> List[Dict[str, Any]]:
        return list(self._nodes.values())
