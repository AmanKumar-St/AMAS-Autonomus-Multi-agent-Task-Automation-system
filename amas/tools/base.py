"""
AMAS Tool Architecture Base
===========================
Defines the unified tool abstraction, permission policies, and normalized
ToolResult model across all tool ecosystems (PraisonAI, LangChain, MCP, Official SDKs, and Custom).
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
import uuid


@dataclass
class ToolPermission:
    """Security and authorization policy for tools."""
    read_only: bool = True
    requires_approval: bool = False
    network_required: bool = False
    filesystem_access: bool = False
    external_side_effects: bool = False


@dataclass
class ToolResult:
    """Normalized tool execution result across all underlying tool ecosystems."""
    success: bool
    data: Any
    error: Optional[str] = None
    source: str = "praisonai"  # "praisonai" | "langchain" | "mcp" | "official_sdk" | "custom"
    category: str = "research"
    duration_ms: float = 0.0
    tool_call_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    citations: List[Dict[str, str]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "source": self.source,
            "category": self.category,
            "duration_ms": self.duration_ms,
            "tool_call_id": self.tool_call_id,
            "citations": self.citations,
            "metadata": self.metadata
        }


class AMASTool(ABC):
    """Abstract interface for all AMAS-compatible tools."""

    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        source: str,  # "praisonai" | "langchain" | "mcp" | "official_sdk" | "custom"
        category: str,
        input_schema: Dict[str, Any],
        output_schema: Optional[Dict[str, Any]] = None,
        permissions: Optional[ToolPermission] = None,
        justification: Optional[str] = None
    ):
        self.id = id
        self.name = name
        self.description = description
        self.source = source
        self.category = category
        self.input_schema = input_schema
        self.output_schema = output_schema or {}
        self.permissions = permissions or ToolPermission()
        self.justification = justification  # Required for custom AMAS tools

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given arguments and return normalized ToolResult."""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Metadata description for planning and UI inspection."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "source": self.source,
            "category": self.category,
            "input_schema": self.input_schema,
            "permissions": {
                "read_only": self.permissions.read_only,
                "requires_approval": self.permissions.requires_approval,
                "network_required": self.permissions.network_required,
                "filesystem_access": self.permissions.filesystem_access,
                "external_side_effects": self.permissions.external_side_effects
            },
            "justification": self.justification
        }
