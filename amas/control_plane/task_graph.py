"""
AMAS Dynamic Task Graph & Dependency Resolver
=============================================
Manages DAG nodes, tracks execution states, and determines next ready tasks.
Includes cycle detection and topological validation.
"""

from __future__ import annotations
from typing import Dict, List, Any, Optional, Set
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
        self._adjacency: Dict[str, Set[str]] = {}  # task_id -> set of dependent task_ids
        self._reverse_adjacency: Dict[str, Set[str]] = {}  # task_id -> set of prerequisite task_ids

        for t in tasks:
            node = dict(t)
            node["status"] = TaskStatus.PENDING.value
            node["retry_count"] = 0
            node["max_retries"] = node.get("max_retries", 3)
            node["error_log"] = []
            node["execution_time_ms"] = 0.0
            node["result"] = None
            node["verification"] = None
            tid = t["id"]
            self._nodes[tid] = node
            self._adjacency[tid] = set()
            self._reverse_adjacency[tid] = set()

        # Build adjacency lists from dependencies
        for t in tasks:
            tid = t["id"]
            for dep in t.get("dependencies", []):
                if dep in self._nodes:
                    self._adjacency[dep].add(tid)
                    self._reverse_adjacency[tid].add(dep)

        # Validate DAG on construction
        self._validate_dag()

    def _validate_dag(self):
        """Validate that the task graph is a valid DAG (no cycles)."""
        # Check for duplicate task IDs
        task_ids = list(self._nodes.keys())
        if len(task_ids) != len(set(task_ids)):
            duplicates = [tid for tid in task_ids if task_ids.count(tid) > 1]
            raise ValueError(f"Duplicate task IDs found: {duplicates}")

        # Check that all dependencies exist
        for tid, node in self._nodes.items():
            for dep in node.get("dependencies", []):
                if dep not in self._nodes:
                    raise ValueError(f"Task '{tid}' references missing dependency '{dep}'")

        # Detect cycles using DFS
        cycle = self._detect_cycle()
        if cycle:
            raise ValueError(f"Circular dependency detected in task graph: {' -> '.join(cycle)}")

    def _detect_cycle(self) -> Optional[List[str]]:
        """Detect cycles in the graph using DFS. Returns cycle path if found."""
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        path: List[str] = []

        def dfs(node: str) -> Optional[List[str]]:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self._adjacency.get(node, []):
                if neighbor not in visited:
                    result = dfs(neighbor)
                    if result:
                        return result
                elif neighbor in rec_stack:
                    # Cycle found - extract cycle path
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]

            rec_stack.remove(node)
            path.pop()
            return None

        for node in self._nodes:
            if node not in visited:
                cycle = dfs(node)
                if cycle:
                    return cycle

        return None

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

    def mark_completed(self, task_id: str, result: Any, duration_ms: float = 0.0):
        if task_id in self._nodes:
            self._nodes[task_id]["status"] = TaskStatus.COMPLETED.value
            self._nodes[task_id]["result"] = result
            self._nodes[task_id]["execution_time_ms"] = duration_ms

    def mark_verified(self, task_id: str, verification: Dict[str, Any]):
        if task_id in self._nodes:
            is_valid = verification.get("is_valid", False)
            v_status = verification.get("status", "")
            should_verify = is_valid or v_status in ["VERIFIED", "PARTIAL"]
            self._nodes[task_id]["status"] = TaskStatus.VERIFIED.value if should_verify else TaskStatus.FAILED.value
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

    def get_topological_order(self) -> List[str]:
        """Return tasks in topological order (Kahn's algorithm)."""
        in_degree = {tid: len(self._reverse_adjacency[tid]) for tid in self._nodes}
        queue = [tid for tid, deg in in_degree.items() if deg == 0]
        topo_order = []

        while queue:
            node = queue.pop(0)
            topo_order.append(node)
            for neighbor in self._adjacency.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(topo_order) != len(self._nodes):
            # Cycle detected (should not happen if validated)
            raise ValueError("Graph contains cycle - cannot produce topological order")

        return topo_order