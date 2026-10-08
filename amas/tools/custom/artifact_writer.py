"""
AMAS Custom Tool: Artifact Formatter & Writer (Priority 5)
=========================================================
JUSTIFICATION:
Formatted deliverable export (Markdown, CSV, JSON) tied directly to the AMAS run_id
and persistence repository for interactive viewing, PDF generation, and download.
"""

from __future__ import annotations
import os
import time
import json
from typing import Dict, List, Any, Optional

from amas.tools.base import AMASTool, ToolPermission, ToolResult


class ArtifactWriterTool(AMASTool):
    """Formats and persists deliverables and reports into AMAS storage."""

    def __init__(self, artifacts_dir: Optional[str] = None):
        self.artifacts_dir = artifacts_dir or os.path.join(os.getcwd(), "amas", "storage", "artifacts")
        os.makedirs(self.artifacts_dir, exist_ok=True)

        super().__init__(
            id="amas_artifact_writer",
            name="AMAS Deliverable & Artifact Exporter",
            description="Formats and saves markdown reports, analysis tables, or structured summaries as downloadable project deliverables.",
            source="custom",
            category="automation",
            input_schema={
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Target filename (e.g. analysis_report.md)"},
                    "content": {"type": "string", "description": "Report or deliverable content string"},
                    "file_type": {"type": "string", "description": "markdown | json | csv | text"}
                },
                "required": ["filename", "content"]
            },
            permissions=ToolPermission(
                read_only=False,
                requires_approval=False,
                filesystem_access=True
            ),
            justification="Formatted deliverable export and persistent artifact cataloging for UI download."
        )

    def execute(self, filename: str = "report.md", content: str = "", file_type: str = "markdown", **kwargs) -> ToolResult:
        start = time.perf_counter()
        if not filename or not content:
            return ToolResult(
                success=False,
                data=None,
                error="Filename and content are required.",
                source=self.source,
                category=self.category,
                duration_ms=0.0
            )

        # Sanitize filename
        safe_name = os.path.basename(filename).replace(" ", "_")
        target_path = os.path.join(self.artifacts_dir, safe_name)

        try:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)

            duration_ms = (time.perf_counter() - start) * 1000.0
            return ToolResult(
                success=True,
                data={
                    "filename": safe_name,
                    "file_path": target_path,
                    "file_type": file_type,
                    "size_bytes": os.path.getsize(target_path),
                    "created_at": time.time()
                },
                source=self.source,
                category=self.category,
                duration_ms=round(duration_ms, 2)
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to write artifact: {str(e)}",
                source=self.source,
                category=self.category,
                duration_ms=round((time.perf_counter() - start) * 1000.0, 2)
            )
