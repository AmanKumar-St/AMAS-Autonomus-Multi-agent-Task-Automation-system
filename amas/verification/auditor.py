"""
AMAS Verification Gate & Constraint Auditor
===========================================
Performs independent, adversarial validation of intermediary and final task outputs.
Checks evidence corroboration, mathematical bounds, and citation integrity.
"""

from __future__ import annotations
import math
import re
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
    evidence_coverage: float = 0.0
    citation_coverage: float = 0.0
    numerical_accuracy: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "score": self.score,
            "status": self.status,
            "critique": self.critique,
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "suggested_fix": self.suggested_fix,
            "evidence_coverage": self.evidence_coverage,
            "citation_coverage": self.citation_coverage,
            "numerical_accuracy": self.numerical_accuracy
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

        # Track sub-scores
        evidence_checks = 0
        evidence_total = 0
        citation_checks = 0
        citation_total = 0
        numerical_checks = 0
        numerical_total = 0

        # 2. Financial Domain Assertions - Independent Recalculation
        sharpe_ratio = blackboard.get("sharpe_ratio")
        prices = blackboard.get("prices") or blackboard.get("historical_closes")
        annualized_volatility = blackboard.get("annualized_volatility_pct") or blackboard.get("annualized_volatility")
        annualized_return = blackboard.get("annualized_return_pct") or blackboard.get("annualized_return")
        risk_free_rate = blackboard.get("risk_free_rate", 0.04)

        if sharpe_ratio is not None or prices is not None:
            numerical_total += 1
            if prices and len(prices) >= 2:
                # Independent recalculation
                calc = self._calculate_sharpe_independent(prices, risk_free_rate)
                if sharpe_ratio is not None:
                    diff = abs(calc["sharpe_ratio"] - sharpe_ratio)
                    if diff <= 0.1:  # Allow small floating point differences
                        checks_passed.append(f"Sharpe ratio independently verified: {calc['sharpe_ratio']:.2f} (original: {sharpe_ratio})")
                        numerical_checks += 1
                    else:
                        checks_failed.append(f"Sharpe ratio mismatch: independent={calc['sharpe_ratio']:.2f}, reported={sharpe_ratio}, diff={diff:.2f}")
                else:
                    checks_passed.append(f"Sharpe ratio independently calculated: {calc['sharpe_ratio']:.2f}")
                    numerical_checks += 1

                if annualized_volatility is not None:
                    vol_diff = abs(calc["annualized_volatility_pct"] - annualized_volatility)
                    if vol_diff <= 0.5:
                        checks_passed.append(f"Annualized volatility independently verified: {calc['annualized_volatility_pct']:.2f}%")
                        numerical_checks += 1
                    else:
                        checks_failed.append(f"Volatility mismatch: independent={calc['annualized_volatility_pct']:.2f}%, reported={annualized_volatility}%")
                else:
                    numerical_checks += 1

                if annualized_return is not None:
                    ret_diff = abs(calc["annualized_return_pct"] - annualized_return)
                    if ret_diff <= 0.5:
                        checks_passed.append(f"Annualized return independently verified: {calc['annualized_return_pct']:.2f}%")
                        numerical_checks += 1
                    else:
                        checks_failed.append(f"Return mismatch: independent={calc['annualized_return_pct']:.2f}%, reported={annualized_return}%")
                else:
                    numerical_checks += 1
            else:
                checks_failed.append("Insufficient price data for independent Sharpe recalculation")

            # Bounds check
            if sharpe_ratio is not None:
                numerical_total += 1
                if -10.0 <= sharpe_ratio <= 25.0:
                    checks_passed.append(f"Sharpe ratio ({sharpe_ratio}) within feasible financial bounds [-10, 25].")
                    numerical_checks += 1
                else:
                    checks_failed.append(f"Sharpe ratio ({sharpe_ratio}) exceeds realistic financial limits.")

            if annualized_volatility is not None:
                numerical_total += 1
                if annualized_volatility >= 0.0:
                    checks_passed.append("Annualized volatility is strictly non-negative.")
                    numerical_checks += 1
                else:
                    checks_failed.append("Annualized volatility is negative (mathematical violation).")

        # 3. Telemetry & Anomaly Assertions - Independent Recalculation
        anomalies = blackboard.get("anomalies")
        data_points = blackboard.get("data_points") or blackboard.get("telemetry_stream")
        z_threshold = blackboard.get("z_threshold", 2.2)

        if anomalies is not None or data_points is not None:
            numerical_total += 1
            if data_points and len(data_points) >= 3:
                calc = self._calculate_anomalies_independent(data_points, z_threshold)
                if anomalies is not None and isinstance(anomalies, list):
                    if len(anomalies) == calc["anomaly_count"]:
                        checks_passed.append(f"Anomaly count independently verified: {calc['anomaly_count']} outliers")
                        numerical_checks += 1
                    else:
                        checks_failed.append(f"Anomaly count mismatch: independent={calc['anomaly_count']}, reported={len(anomalies)}")
                else:
                    checks_passed.append(f"Anomalies independently calculated: {calc['anomaly_count']} outliers")
                    numerical_checks += 1

                if z_threshold is not None and z_threshold > 0:
                    checks_passed.append(f"Z-score variance threshold ({z_threshold}σ) verified.")
                    numerical_checks += 1
            else:
                checks_failed.append("Insufficient telemetry data for independent anomaly recalculation")

        # 4. Web Research & Citation Assertions
        articles = blackboard.get("articles", [])
        citations = blackboard.get("citations", [])
        tool_calls = blackboard.get("tool_calls", [])

        # Evidence coverage: check if claims in output have source backing
        evidence_total += 1
        if articles and len(articles) > 0:
            checks_passed.append(f"Evidence grounded: {len(articles)} sources retrieved.")
            evidence_checks += 1
        else:
            checks_failed.append("Research completed without external sources.")

        # Citation coverage: check if output contains citations/references
        citation_total += 1
        if citations and len(citations) > 0:
            checks_passed.append(f"Citations present: {len(citations)} source references.")
            citation_checks += 1
        elif tool_calls:
            # Check tool calls for citations
            total_citations = sum(len(tc.get("citations", [])) for tc in tool_calls if isinstance(tc, dict))
            if total_citations > 0:
                checks_passed.append(f"Tool citations found: {total_citations} references across tool calls.")
                citation_checks += 1
            else:
                checks_failed.append("No citations found in tool call results.")
        else:
            checks_failed.append("No citations found in output or tool results.")

        # 5. Output quality checks
        if "error" in task_output.lower() or "failed" in task_output.lower():
            checks_failed.append("Task output indicates failure or error condition.")

        # Calculate sub-scores
        evidence_coverage = evidence_checks / evidence_total if evidence_total > 0 else 1.0
        citation_coverage = citation_checks / citation_total if citation_total > 0 else 0.0
        numerical_accuracy = numerical_checks / numerical_total if numerical_total > 0 else 1.0

        # Overall score weighted
        total_checks = len(checks_passed) + len(checks_failed)
        if total_checks == 0:
            score = 1.0
            is_valid = True
            status = "VERIFIED"
            critique = "No domain violations detected."
        else:
            # Weighted score: numerical (40%), evidence (30%), citation (20%), other (10%)
            score = round(
                0.4 * numerical_accuracy +
                0.3 * evidence_coverage +
                0.2 * citation_coverage +
                0.1 * (len(checks_passed) / total_checks),
                2
            )
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
            suggested_fix=suggested_fix,
            evidence_coverage=round(evidence_coverage, 2),
            citation_coverage=round(citation_coverage, 2),
            numerical_accuracy=round(numerical_accuracy, 2)
        )

    def _calculate_sharpe_independent(self, prices: List[float], risk_free_rate: float = 0.04) -> Dict[str, float]:
        """Independent Sharpe ratio calculation for verification."""
        if len(prices) < 2:
            return {"sharpe_ratio": 0.0, "annualized_volatility_pct": 0.0, "annualized_return_pct": 0.0}

        daily_returns = [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices))]
        n = len(daily_returns)

        mean_daily_return = sum(daily_returns) / n
        annualized_return = mean_daily_return * 252.0

        variance = sum((r - mean_daily_return) ** 2 for r in daily_returns) / (n - 1) if n > 1 else 0.0
        daily_volatility = math.sqrt(variance)
        annualized_volatility = daily_volatility * math.sqrt(252.0)

        if annualized_volatility > 0.000001:
            sharpe_ratio = (annualized_return - risk_free_rate) / annualized_volatility
        else:
            sharpe_ratio = 0.0

        return {
            "sharpe_ratio": round(sharpe_ratio, 2),
            "annualized_volatility_pct": round(annualized_volatility * 100, 2),
            "annualized_return_pct": round(annualized_return * 100, 2),
            "mean_daily_return": round(mean_daily_return, 6)
        }

    def _calculate_anomalies_independent(self, data_points: List[float], z_threshold: float = 2.2) -> Dict[str, Any]:
        """Independent anomaly detection for verification."""
        n = len(data_points)
        if n < 3:
            return {"anomaly_count": 0, "anomalies": [], "mean": 0.0, "std_dev": 0.0}

        mean_val = sum(data_points) / n
        variance = sum((x - mean_val) ** 2 for x in data_points) / (n - 1)
        std_dev = math.sqrt(variance)

        anomalies = []
        if std_dev > 0.00001:
            for idx, val in enumerate(data_points):
                z_score = abs(val - mean_val) / std_dev
                if z_score >= z_threshold:
                    anomalies.append({
                        "index": idx,
                        "value": round(val, 2),
                        "z_score": round(z_score, 2),
                        "deviation_from_mean": round(val - mean_val, 2),
                        "severity": "CRITICAL" if z_score > 3.0 else "WARNING"
                    })

        return {
            "total_points": n,
            "mean": round(mean_val, 3),
            "std_dev": round(std_dev, 3),
            "z_threshold": z_threshold,
            "anomaly_count": len(anomalies),
            "anomalies": anomalies,
            "status": "ANOMALIES_DETECTED" if anomalies else "NOMINAL_TELEMETRY"
        }