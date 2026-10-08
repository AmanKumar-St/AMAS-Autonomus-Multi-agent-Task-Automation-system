"""
AMAS Custom Tool: Telemetry & Anomaly Detector (Priority 5)
===========================================================
JUSTIFICATION:
No existing PraisonAI or LangChain tool performs this structured time-series
Z-score distribution analysis with outlier classification, variance estimation,
and critical threshold flagging required by AMAS operational workflows.
"""

from __future__ import annotations
import time
import math
from typing import Dict, List, Any, Optional

from amas.tools.base import AMASTool, ToolPermission, ToolResult


class TelemetryAnomalyDetectorTool(AMASTool):
    """Detects numerical glitches, telemetry spikes, and statistical outliers."""

    def __init__(self):
        super().__init__(
            id="amas_telemetry_anomaly_detector",
            name="AMAS Telemetry & Outlier Detector",
            description="Analyzes ingested telemetry data streams or numerical arrays to identify statistical outliers (> 2.0 sigma).",
            source="custom",
            category="telemetry",
            input_schema={
                "type": "object",
                "properties": {
                    "data_points": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Chronological array of sensor readings or telemetry measurements"
                    },
                    "z_threshold": {
                        "type": "number",
                        "description": "Z-score threshold for outlier flagging (default 2.2)"
                    }
                },
                "required": ["data_points"]
            },
            permissions=ToolPermission(
                read_only=True,
                requires_approval=False,
                filesystem_access=False
            ),
            justification="Deterministic statistical Z-score outlier detection and telemetry anomaly distribution analysis."
        )

    def execute(self, data_points: List[float] = None, z_threshold: float = 2.2, **kwargs) -> ToolResult:
        start = time.perf_counter()
        if not data_points or len(data_points) < 3:
            return ToolResult(
                success=False,
                data=None,
                error="At least 3 telemetry data points are required to calculate distribution statistics.",
                source=self.source,
                category=self.category,
                duration_ms=0.0
            )

        try:
            n = len(data_points)
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

            duration_ms = (time.perf_counter() - start) * 1000.0
            result = {
                "total_points": n,
                "mean": round(mean_val, 3),
                "std_dev": round(std_dev, 3),
                "z_threshold": z_threshold,
                "anomaly_count": len(anomalies),
                "anomalies": anomalies,
                "status": "ANOMALIES_DETECTED" if anomalies else "NOMINAL_TELEMETRY"
            }

            return ToolResult(
                success=True,
                data=result,
                source=self.source,
                category=self.category,
                duration_ms=round(duration_ms, 2)
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Anomaly detection failed: {str(e)}",
                source=self.source,
                category=self.category,
                duration_ms=round((time.perf_counter() - start) * 1000.0, 2)
            )
