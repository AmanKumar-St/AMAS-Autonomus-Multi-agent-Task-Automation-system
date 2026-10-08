"""
AMAS Custom Tool: Financial Risk & Sharpe Calculator (Priority 5)
=================================================================
JUSTIFICATION:
No existing PraisonAI or LangChain tool performs this exact deterministic
financial risk computation (sample daily return series, annualized return,
annualized standard deviation, and risk-adjusted Sharpe ratio) required for
mathematical constraint verification in AMAS.
"""

from __future__ import annotations
import time
import math
from typing import Dict, List, Any, Optional

from amas.tools.base import AMASTool, ToolPermission, ToolResult


class FinancialRiskCalculatorTool(AMASTool):
    """Deterministic financial analytics engine for Sharpe ratio and risk metrics."""

    def __init__(self):
        super().__init__(
            id="amas_financial_risk_calculator",
            name="AMAS Financial Risk & Sharpe Calculator",
            description="Computes mean return, annualized volatility, and Sharpe ratio for an array of asset prices.",
            source="custom",
            category="finance",
            input_schema={
                "type": "object",
                "properties": {
                    "prices": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Chronological array of historical asset closing prices"
                    },
                    "risk_free_rate": {
                        "type": "number",
                        "description": "Annualized risk-free benchmark rate (e.g. 0.04 for 4%)"
                    }
                },
                "required": ["prices"]
            },
            permissions=ToolPermission(
                read_only=True,
                requires_approval=False,
                filesystem_access=False
            ),
            justification="Deterministic math engine for risk-adjusted returns and mathematical constraint verification."
        )

    def execute(self, prices: List[float] = None, risk_free_rate: float = 0.04, **kwargs) -> ToolResult:
        start = time.perf_counter()
        if not prices or len(prices) < 2:
            return ToolResult(
                success=False,
                data=None,
                error="At least 2 price observations are required to calculate returns.",
                source=self.source,
                category=self.category,
                duration_ms=0.0
            )

        try:
            # 1. Calculate percentage daily returns: (P_t - P_{t-1}) / P_{t-1}
            daily_returns = [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices))]
            n = len(daily_returns)

            mean_daily_return = sum(daily_returns) / n
            annualized_return = mean_daily_return * 252.0

            # 2. Daily standard deviation (sample volatility)
            variance = sum((r - mean_daily_return) ** 2 for r in daily_returns) / (n - 1) if n > 1 else 0.0
            daily_volatility = math.sqrt(variance)
            annualized_volatility = daily_volatility * math.sqrt(252.0)

            # 3. Sharpe Ratio: (R_annualized - R_free) / Vol_annualized
            if annualized_volatility > 0.000001:
                sharpe_ratio = (annualized_return - risk_free_rate) / annualized_volatility
            else:
                sharpe_ratio = 0.0

            # Cumulative total return
            cumulative_return = (prices[-1] - prices[0]) / prices[0]

            duration_ms = (time.perf_counter() - start) * 1000.0
            metrics = {
                "sample_size": len(prices),
                "trading_days": n,
                "first_price": round(prices[0], 2),
                "last_price": round(prices[-1], 2),
                "cumulative_return_pct": round(cumulative_return * 100, 2),
                "mean_daily_return": round(mean_daily_return, 6),
                "annualized_return_pct": round(annualized_return * 100, 2),
                "daily_volatility_pct": round(daily_volatility * 100, 2),
                "annualized_volatility_pct": round(annualized_volatility * 100, 2),
                "risk_free_rate": risk_free_rate,
                "sharpe_ratio": round(sharpe_ratio, 2),
                "risk_grade": "MODERATE" if 1.0 <= sharpe_ratio <= 2.0 else ("EXCELLENT" if sharpe_ratio > 2.0 else "HIGH_RISK")
            }

            return ToolResult(
                success=True,
                data=metrics,
                source=self.source,
                category=self.category,
                duration_ms=round(duration_ms, 2)
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Risk calculation failed: {str(e)}",
                source=self.source,
                category=self.category,
                duration_ms=round((time.perf_counter() - start) * 1000.0, 2)
            )
