"""
AMAS Real-Time Event Bus & Streaming Observability
==================================================
Dispatches structured execution events to Server-Sent Event (SSE) clients
and writes durable audit logs into SQLite.
"""

from __future__ import annotations
import time
import json
import queue
import logging
from typing import Dict, List, Any, Optional

from amas.storage.database import AMASDatabase

logger = logging.getLogger("amas.control_plane.events")


class EventBus:
    """Manages real-time event distribution and subscription channels."""

    def __init__(self, database: AMASDatabase):
        self.database = database
        self._subscribers: Dict[str, List[queue.Queue]] = {}

    def subscribe(self, run_id: str) -> queue.Queue:
        """Create a FIFO queue for an SSE subscriber listening to run_id."""
        q = queue.Queue(maxsize=100)
        if run_id not in self._subscribers:
            self._subscribers[run_id] = []
        self._subscribers[run_id].append(q)
        return q

    def unsubscribe(self, run_id: str, q: queue.Queue):
        if run_id in self._subscribers and q in self._subscribers[run_id]:
            self._subscribers[run_id].remove(q)

    def emit(
        self,
        run_id: str,
        event_type: str,
        agent: str = "Orchestrator",
        tool: Optional[str] = None,
        duration_ms: float = 0.0,
        payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Broadcast a structured event to all active streams and persist to database."""
        event = {
            "event_id": f"evt_{int(time.time() * 1000)}_{event_type.lower()}",
            "run_id": run_id,
            "timestamp": time.time(),
            "event_type": event_type,
            "agent": agent,
            "tool": tool,
            "duration_ms": duration_ms,
            "payload": payload or {}
        }

        # 1. Persist to DB
        try:
            self.database.save_event(event)
        except Exception as e:
            logger.warning(f"Failed to persist event to DB: {e}")

        # 2. Push to SSE queues
        if run_id in self._subscribers:
            for subscriber_queue in list(self._subscribers[run_id]):
                try:
                    subscriber_queue.put_nowait(event)
                except queue.Full:
                    pass

        return event
