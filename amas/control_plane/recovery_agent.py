"""
AMAS Recovery Agent & Strategy Engine
======================================
Diagnoses execution faults, classifies error types, and selects
appropriate recovery strategies beyond simple retry.
"""

from __future__ import annotations
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("amas.control_plane.recovery")


class ErrorType(str, Enum):
    TIMEOUT = "TIMEOUT"
    RATE_LIMIT = "RATE_LIMIT"
    AUTHENTICATION = "AUTHENTICATION"
    INVALID_INPUT = "INVALID_INPUT"
    SCHEMA_ERROR = "SCHEMA_ERROR"
    TOOL_UNAVAILABLE = "TOOL_UNAVAILABLE"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    VERIFICATION_FAILURE = "VERIFICATION_FAILURE"
    NETWORK_ERROR = "NETWORK_ERROR"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    SECURITY_BLOCK = "SECURITY_BLOCK"
    UNKNOWN = "UNKNOWN"


class RecoveryStrategy(str, Enum):
    RETRY_SAME_TOOL = "retry_same_tool"
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    SWITCH_PROVIDER = "switch_provider"
    SWITCH_SEARCH_PROVIDER = "switch_search_provider"
    SWITCH_TOOL = "switch_tool"
    SIMPLIFY_REQUEST = "simplify_request"
    MODIFY_ARGUMENTS = "modify_arguments"
    REPLAN_TASK = "replan_task"
    REQUEST_HUMAN_APPROVAL = "request_human_approval"
    ABORT = "abort"


@dataclass
class RecoveryDecision:
    error_type: ErrorType
    retryable: bool
    strategy: RecoveryStrategy
    alternative_tool: Optional[str] = None
    alternative_provider: Optional[str] = None
    modified_arguments: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    max_attempts: int = 3
    backoff_delay: float = 1.0


class RecoveryAgent:
    """Diagnoses faults and formulates recovery strategies."""

    # Error classification patterns
    ERROR_PATTERNS = {
        ErrorType.TIMEOUT: ["timeout", "timed out", "deadline exceeded", "read timed out"],
        ErrorType.RATE_LIMIT: ["429", "rate limit", "too many requests", "quota exceeded", "rate limited"],
        ErrorType.AUTHENTICATION: ["401", "403", "unauthorized", "authentication failed", "invalid api key", "api key", "auth failed"],
        ErrorType.INVALID_INPUT: ["invalid input", "validation error", "bad request", "400", "parameter", "schema"],
        ErrorType.SCHEMA_ERROR: ["schema", "json", "parse", "malformed", "invalid json"],
        ErrorType.TOOL_UNAVAILABLE: ["not found", "not registered", "tool unavailable", "no such tool"],
        ErrorType.PROVIDER_UNAVAILABLE: ["provider", "model not found", "endpoint", "connection refused", "dns"],
        ErrorType.VERIFICATION_FAILURE: ["verification", "audit", "constraint", "bounds", "failed verification"],
        ErrorType.NETWORK_ERROR: ["network", "connection", "dns", "socket", "unreachable"],
        ErrorType.PERMISSION_DENIED: ["permission", "forbidden", "access denied", "not authorized"],
        ErrorType.APPROVAL_REQUIRED: ["approval", "human", "sign-off", "requires approval"],
        ErrorType.SECURITY_BLOCK: ["security", "blocked", "violation", "restricted", "forbidden operation"],
    }

    # Strategy mapping by error type
    STRATEGY_MAP = {
        ErrorType.TIMEOUT: [RecoveryStrategy.RETRY_WITH_BACKOFF, RecoveryStrategy.SWITCH_PROVIDER, RecoveryStrategy.SIMPLIFY_REQUEST],
        ErrorType.RATE_LIMIT: [RecoveryStrategy.RETRY_WITH_BACKOFF, RecoveryStrategy.SWITCH_PROVIDER, RecoveryStrategy.SWITCH_TOOL],
        ErrorType.AUTHENTICATION: [RecoveryStrategy.SWITCH_PROVIDER, RecoveryStrategy.ABORT],
        ErrorType.INVALID_INPUT: [RecoveryStrategy.MODIFY_ARGUMENTS, RecoveryStrategy.SIMPLIFY_REQUEST, RecoveryStrategy.REPLAN_TASK],
        ErrorType.SCHEMA_ERROR: [RecoveryStrategy.MODIFY_ARGUMENTS, RecoveryStrategy.REPLAN_TASK],
        ErrorType.TOOL_UNAVAILABLE: [RecoveryStrategy.SWITCH_TOOL, RecoveryStrategy.REPLAN_TASK],
        ErrorType.PROVIDER_UNAVAILABLE: [RecoveryStrategy.SWITCH_PROVIDER, RecoveryStrategy.ABORT],
        ErrorType.VERIFICATION_FAILURE: [RecoveryStrategy.REPLAN_TASK, RecoveryStrategy.MODIFY_ARGUMENTS],
        ErrorType.NETWORK_ERROR: [RecoveryStrategy.RETRY_WITH_BACKOFF, RecoveryStrategy.SWITCH_PROVIDER, RecoveryStrategy.SWITCH_SEARCH_PROVIDER],
        ErrorType.PERMISSION_DENIED: [RecoveryStrategy.REQUEST_HUMAN_APPROVAL, RecoveryStrategy.ABORT],
        ErrorType.APPROVAL_REQUIRED: [RecoveryStrategy.REQUEST_HUMAN_APPROVAL],
        ErrorType.SECURITY_BLOCK: [RecoveryStrategy.ABORT],
        ErrorType.UNKNOWN: [RecoveryStrategy.RETRY_WITH_BACKOFF, RecoveryStrategy.REPLAN_TASK, RecoveryStrategy.ABORT],
    }

    def __init__(self, tool_registry: Optional[Any] = None, provider_manager: Optional[Any] = None):
        self.tool_registry = tool_registry
        self.provider_manager = provider_manager
        self.recovery_history: List[Dict[str, Any]] = []

    def classify_error(self, error_message: str, context: Optional[Dict[str, Any]] = None) -> ErrorType:
        """Classify error based on message content and context."""
        error_lower = error_message.lower()

        for error_type, patterns in self.ERROR_PATTERNS.items():
            for pattern in patterns:
                if pattern in error_lower:
                    logger.info(f"Classified error as {error_type.value}: matched '{pattern}'")
                    return error_type

        logger.warning(f"Could not classify error: {error_message[:100]}")
        return ErrorType.UNKNOWN

    def decide_recovery(
        self,
        error_message: str,
        task_data: Dict[str, Any],
        attempt: int,
        max_retries: int = 3,
        context: Optional[Dict[str, Any]] = None
    ) -> RecoveryDecision:
        """Generate structured recovery decision based on error classification."""
        error_type = self.classify_error(error_message, context)
        strategies = self.STRATEGY_MAP.get(error_type, self.STRATEGY_MAP[ErrorType.UNKNOWN])

        # Check if we've exhausted retries
        if attempt >= max_retries:
            return RecoveryDecision(
                error_type=error_type,
                retryable=False,
                strategy=RecoveryStrategy.ABORT,
                reason=f"Max retries ({max_retries}) exceeded for {error_type.value}",
                max_attempts=max_retries
            )

        # Select best strategy based on context and attempt number
        strategy = self._select_strategy(strategies, error_type, task_data, attempt, context)

        decision = RecoveryDecision(
            error_type=error_type,
            retryable=True,
            strategy=strategy,
            reason=f"Classified as {error_type.value}, selected {strategy.value} (attempt {attempt}/{max_retries})",
            max_attempts=max_retries,
            backoff_delay=self._calculate_backoff(attempt)
        )

        # Add strategy-specific parameters
        self._enrich_decision(decision, task_data, context)

        # Record for observability
        self.recovery_history.append({
            "task_id": task_data.get("id"),
            "error_type": error_type.value,
            "strategy": strategy.value,
            "attempt": attempt,
            "decision": decision.__dict__
        })

        logger.info(f"Recovery decision for task {task_data.get('id')}: {decision.strategy.value} - {decision.reason}")
        return decision

    def _select_strategy(
        self,
        strategies: List[RecoveryStrategy],
        error_type: ErrorType,
        task_data: Dict[str, Any],
        attempt: int,
        context: Optional[Dict[str, Any]]
    ) -> RecoveryStrategy:
        """Select the best strategy from available options."""
        tool_required = task_data.get("tool_required")

        # For first attempt, prefer simpler strategies
        if attempt == 1:
            if RecoveryStrategy.RETRY_WITH_BACKOFF in strategies:
                return RecoveryStrategy.RETRY_WITH_BACKOFF
            if RecoveryStrategy.MODIFY_ARGUMENTS in strategies:
                return RecoveryStrategy.MODIFY_ARGUMENTS

        # For subsequent attempts, escalate
        if attempt == 2:
            if error_type in [ErrorType.TIMEOUT, ErrorType.RATE_LIMIT, ErrorType.NETWORK_ERROR]:
                if RecoveryStrategy.SWITCH_PROVIDER in strategies:
                    return RecoveryStrategy.SWITCH_PROVIDER
                if RecoveryStrategy.SWITCH_SEARCH_PROVIDER in strategies and tool_required and "search" in tool_required:
                    return RecoveryStrategy.SWITCH_SEARCH_PROVIDER
            if error_type == ErrorType.TOOL_UNAVAILABLE and RecoveryStrategy.SWITCH_TOOL in strategies:
                return RecoveryStrategy.SWITCH_TOOL
            if RecoveryStrategy.SIMPLIFY_REQUEST in strategies:
                return RecoveryStrategy.SIMPLIFY_REQUEST

        # For later attempts, replan or abort
        if RecoveryStrategy.REPLAN_TASK in strategies:
            return RecoveryStrategy.REPLAN_TASK

        return RecoveryStrategy.ABORT

    def _enrich_decision(self, decision: RecoveryDecision, task_data: Dict[str, Any], context: Optional[Dict[str, Any]]):
        """Add strategy-specific parameters to the decision."""
        tool_required = task_data.get("tool_required")
        tool_args = task_data.get("tool_args", {})

        if decision.strategy == RecoveryStrategy.SWITCH_PROVIDER:
            # Find alternative configured provider
            if self.provider_manager:
                current = context.get("provider") if context else None
                providers = self.provider_manager.list_providers_metadata()
                for p in providers:
                    if p["is_configured"] and p["id"] != current:
                        decision.alternative_provider = p["id"]
                        decision.modified_arguments = dict(tool_args)
                        break

        elif decision.strategy == RecoveryStrategy.SWITCH_SEARCH_PROVIDER:
            # Switch to alternative search provider
            search_providers = ["official_tavily_search", "official_exa_search", "official_brave_search", "official_serper_search", "praison_web_search", "ddgs_fallback_search"]
            current_idx = search_providers.index(tool_required) if tool_required in search_providers else -1
            if current_idx >= 0 and current_idx + 1 < len(search_providers):
                decision.alternative_tool = search_providers[current_idx + 1]
                decision.modified_arguments = dict(tool_args)

        elif decision.strategy == RecoveryStrategy.SWITCH_TOOL:
            # Find alternative tool in same category
            if self.tool_registry:
                current_tool = self.tool_registry.get_tool(tool_required) if tool_required else None
                if current_tool:
                    category = current_tool.category
                    for tid, tool in self.tool_registry._tools.items():
                        if tool.category == category and tid != tool_required:
                            decision.alternative_tool = tid
                            break

        elif decision.strategy == RecoveryStrategy.MODIFY_ARGUMENTS:
            # Try to fix common argument issues
            decision.modified_arguments = self._fix_arguments(tool_required, tool_args, decision.error_type)

        elif decision.strategy == RecoveryStrategy.SIMPLIFY_REQUEST:
            # Reduce scope of request
            decision.modified_arguments = self._simplify_arguments(tool_required, tool_args)

    def _fix_arguments(self, tool_id: str, args: Dict[str, Any], error_type: ErrorType) -> Dict[str, Any]:
        """Attempt to fix common argument issues."""
        fixed = dict(args)

        if error_type == ErrorType.INVALID_INPUT:
            # Reduce max_results if too high
            if "max_results" in fixed and fixed["max_results"] > 10:
                fixed["max_results"] = 10
            # Reduce search depth
            if "search_depth" in fixed and fixed["search_depth"] == "advanced":
                fixed["search_depth"] = "basic"
            # Fix period_days
            if "period_days" in fixed and fixed["period_days"] > 365:
                fixed["period_days"] = 30

        elif error_type == ErrorType.SCHEMA_ERROR:
            # Ensure required fields
            if tool_id == "official_financial_retriever" and "ticker" not in fixed:
                fixed["ticker"] = "AAPL"
            if tool_id in ["compute_risk_metrics", "amas_financial_risk_calculator"] and "prices" not in fixed:
                # Will be resolved from blackboard at execution time
                pass

        return fixed

    def _simplify_arguments(self, tool_id: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Simplify request to reduce complexity."""
        simplified = dict(args)

        if "max_results" in simplified:
            simplified["max_results"] = min(simplified["max_results"], 5)
        if "search_depth" in simplified:
            simplified["search_depth"] = "basic"
        if "period_days" in simplified:
            simplified["period_days"] = min(simplified["period_days"], 14)

        return simplified

    def _calculate_backoff(self, attempt: int, base: float = 1.0, max_delay: float = 30.0) -> float:
        """Calculate exponential backoff with jitter."""
        import random
        delay = base * (2 ** (attempt - 1))
        delay = min(delay, max_delay)
        # Add jitter (±25%)
        jitter = delay * 0.25 * (2 * random.random() - 1)
        return round(delay + jitter, 2)

    def get_recovery_stats(self) -> Dict[str, Any]:
        """Return recovery statistics for observability."""
        if not self.recovery_history:
            return {"total_recoveries": 0}

        by_strategy = {}
        by_error = {}
        for r in self.recovery_history:
            strategy = r["decision"]["strategy"]
            error = r["error_type"]
            by_strategy[strategy] = by_strategy.get(strategy, 0) + 1
            by_error[error] = by_error.get(error, 0) + 1

        return {
            "total_recoveries": len(self.recovery_history),
            "by_strategy": by_strategy,
            "by_error_type": by_error,
            "recent": self.recovery_history[-5:] if len(self.recovery_history) > 5 else self.recovery_history
        }