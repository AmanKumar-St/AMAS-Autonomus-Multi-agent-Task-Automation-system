"""
AMAS Policy Manager & Security Gate
===================================
Enforces tool access controls, human-in-the-loop approvals, execution timeouts,
and exponential backoff retry policies.
"""

from __future__ import annotations
import time
import math
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger("amas.control_plane.policy")


class PolicyManager:
    """Evaluates security permissions, approval requirements, and retry schedules."""

    def __init__(self):
        self._pending_approvals: Dict[str, Dict[str, Any]] = {}

    def requires_human_approval(self, tool_id: str, tool_permissions: Any) -> bool:
        """Return True if tool flags external side effects or requires explicit sign-off."""
        if getattr(tool_permissions, "requires_approval", False):
            return True
        if getattr(tool_permissions, "external_side_effects", False):
            return True
        return False

    def create_approval_request(self, run_id: str, task_id: str, tool_id: str, kwargs: Dict[str, Any]) -> str:
        """Register an action awaiting user sign-off in the UI."""
        req_id = f"appr_{run_id}_{task_id}"
        self._pending_approvals[req_id] = {
            "req_id": req_id,
            "run_id": run_id,
            "task_id": task_id,
            "tool_id": tool_id,
            "kwargs": kwargs,
            "status": "PENDING",
            "created_at": time.time()
        }
        return req_id

    def resolve_approval(self, req_id: str, approved: bool) -> Optional[Dict[str, Any]]:
        """Process user action from the frontend modal."""
        if req_id in self._pending_approvals:
            req = self._pending_approvals[req_id]
            req["status"] = "APPROVED" if approved else "REJECTED"
            req["resolved_at"] = time.time()
            return req
        return None

    def calculate_backoff_delay(self, attempt: int, base_seconds: float = 0.5, max_seconds: float = 5.0) -> float:
        """Calculate exponential backoff delay: t = base * 2^(attempt-1)."""
        delay = base_seconds * (2 ** max(0, attempt - 1))
        return min(delay, max_seconds)
