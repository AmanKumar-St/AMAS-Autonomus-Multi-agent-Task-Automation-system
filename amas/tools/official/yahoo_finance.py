"""
AMAS Official Service Tool (Priority 4)
=======================================
Integrates official service endpoints (Yahoo Finance public chart API).
Fetches real, verified historical closing price series.
"""

from __future__ import annotations
import time
import json
import urllib.request
from typing import Dict, List, Any, Optional

from amas.tools.base import AMASTool, ToolPermission, ToolResult


class OfficialYahooFinanceTool(AMASTool):
    """Fetches real market prices from Yahoo Finance API without synthetic fabrication."""

    def __init__(self):
        super().__init__(
            id="official_financial_retriever",
            name="Official Yahoo Finance Data Retriever",
            description="Retrieves authentic historical closing prices, trading volumes, and company metadata for equities.",
            source="official_sdk",
            category="finance",
            input_schema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker symbol (e.g. AAPL, NVDA, MSFT)"},
                    "period_days": {"type": "integer", "description": "Number of days of history (default 30)"}
                },
                "required": ["ticker"]
            },
            permissions=ToolPermission(
                read_only=True,
                requires_approval=False,
                network_required=True
            )
        )

    def execute(self, ticker: str = "AAPL", period_days: int = 30, **kwargs) -> ToolResult:
        start = time.perf_counter()
        clean_ticker = ticker.strip().upper()
        
        # Yahoo Finance ranges: 1mo, 3mo, 6mo, 1y
        range_str = "1mo" if period_days <= 30 else ("3mo" if period_days <= 90 else "1y")
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{clean_ticker}?range={range_str}&interval=1d"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

        try:
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode())
                result = data.get("chart", {}).get("result", [])
                if not result:
                    raise ValueError(f"No chart data returned for symbol '{clean_ticker}'.")

                meta = result[0].get("meta", {})
                quote = result[0].get("indicators", {}).get("quote", [{}])[0]
                closes = quote.get("close", [])
                volumes = quote.get("volume", [])
                timestamps = result[0].get("timestamp", [])

                valid_prices = [round(float(c), 2) for c in closes if c is not None]
                if not valid_prices:
                    raise ValueError(f"No valid closing prices found for '{clean_ticker}'.")

                duration_ms = (time.perf_counter() - start) * 1000.0
                currency = meta.get("currency", "USD")
                current_price = meta.get("regularMarketPrice", valid_prices[-1])

                return ToolResult(
                    success=True,
                    data={
                        "ticker": clean_ticker,
                        "currency": currency,
                        "current_price": current_price,
                        "price_count": len(valid_prices),
                        "historical_closes": valid_prices,
                        "source_type": "official_live_market_data",
                        "exchange": meta.get("exchangeName", "NASDAQ")
                    },
                    source=self.source,
                    category=self.category,
                    duration_ms=round(duration_ms, 2),
                    citations=[{"title": f"Yahoo Finance Chart: {clean_ticker}", "url": f"https://finance.yahoo.com/quote/{clean_ticker}"}]
                )
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000.0
            # Explicit failure - Never silently invent prices and pretend they are live!
            return ToolResult(
                success=False,
                data={
                    "ticker": clean_ticker,
                    "source_type": "unavailable",
                    "historical_closes": []
                },
                error=f"Live financial data could not be retrieved: {str(e)}",
                source=self.source,
                category=self.category,
                duration_ms=round(duration_ms, 2)
            )
