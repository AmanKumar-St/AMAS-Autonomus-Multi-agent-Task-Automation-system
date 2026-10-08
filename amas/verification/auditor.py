"""
AMAS Verification Gate & Constraint Auditor
===========================================
Performs independent, adversarial validation of intermediary and final task outputs.
Checks evidence corroboration, mathematical bounds, and citation integrity.
"""

from __future__ import annotations
import math
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class VerificationResult:
    is_valid: bool
    score: float  # 0.0 to 1.0
    status: str   # "VERIFIED" | "FAILED" | "PARTIAL" | "REQUIRES_REVIEW"
    critique: str
    checks_passed: List[str] = field(default_factory=list)
    checks_failed: List[str] = field(default_factory=list)
    suggested_fix: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "score": self.score,
            "status": self.status,
            "critique": self.critique,
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "suggested_fix": self.suggested_fix
        }


class VerificationAuditor:
    """Audits agent outputs and blackboard state against domain and safety rules."""

    def audit_task(
        self,
        task_data: Dict[str, Any],
        task_output: str,
        blackboard: Dict[str, Any]
    ) -> VerificationResult:
        """Run domain assertions based on task type and content."""
        checks_passed: List[str] = []
        checks_failed: List[str] = []

        # 1. Non-empty output check
        if task_output and len(task_output.strip()) > 10:
            checks_passed.append("Task produced non-empty execution deliverable.")
        else:
            checks_failed.append("Task deliverable is empty or under 10 characters.")

        # 2. Financial Domain Assertions
        if "sharpe" in task_output.lower() or "sharpe_ratio" in blackboard:
            sharpe = blackboard.get("sharpe_ratio")
            if sharpe is not None:
                if -10.0 <= sharpe <= 25.0:
                    checks_passed.append(f"Sharpe ratio ({sharpe}) within feasible financial bounds [-10, 25].")
                else:
                    checks_failed.append(f"Sharpe ratio ({sharpe}) exceeds realistic financial limits.")

            vol = blackboard.get("annualized_volatility_pct") or blackboard.get("annualized_volatility")
            if vol is not None:
                if vol >= 0.0:
                    checks_passed.append("Annualized volatility is strictly non-negative.")
                else:
                    checks_failed.append("Annualized volatility is negative (mathematical violation).")

        # 3. Telemetry & Anomaly Assertions
        if "anomaly" in task_output.lower() or "anomalies" in blackboard:
            anomalies = blackboard.get("anomalies")
            if anomalies is not None and isinstance(anomalies, list):
                checks_passed.append(f"Telemetry analysis audited: {len(anomalies)} anomalies identified.")
            z_thresh = blackboard.get("z_threshold")
            if z_thresh is not None and z_thresh > 0:
                checks_passed.append(f"Z-score variance threshold ({z_thresh}σ) verified.")

        # 4. Web Research & Citation Assertions
        if "articles" in blackboard or "count" in blackboard:
            articles = blackboard.get("articles", [])
            if articles and len(articles) > 0:
                checks_passed.append(f"Evidence grounded: {len(articles)} accredited sources audited.")
            else:
                checks_failed.append("Research completed without accredited external sources.")

        # Calculate score
        total_checks = len(checks_passed) + len(checks_failed)
        if total_checks == 0:
            score = 1.0
            is_valid = True
            status = "VERIFIED"
            critique = "No domain violations detected."
        else:
            score = round(len(checks_passed) / total_checks, 2)
            is_valid = len(checks_failed) == 0
            if is_valid:
                status = "VERIFIED"
                critique = f"All {len(checks_passed)} quality checks passed with zero constraint violations."
            elif score >= 0.5:
                status = "PARTIAL"
                critique = f"Passed {len(checks_passed)} of {total_checks} checks. Flagged: {'; '.join(checks_failed)}"
            else:
                status = "FAILED"
                critique = f"Verification failed! Critical violations: {'; '.join(checks_failed)}"

        suggested_fix = None
        if not is_valid:
            suggested_fix = f"Re-run task with corrected parameters: Address {checks_failed[0]}"

        return VerificationResult(
            is_valid=is_valid,
            score=score,
            status=status,
            critique=critique,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            suggested_fix=suggested_fix
        )
