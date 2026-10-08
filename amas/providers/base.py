"""
AMAS LLM Provider Interface
===========================
Defines the generic, provider-agnostic abstraction for all LLMs.
Agent logic interacts exclusively with this interface.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Generator


@dataclass
class ProviderCapabilities:
    streaming: bool = True
    tool_calling: bool = True
    structured_output: bool = True
    vision: bool = False
    reasoning: bool = False
    max_context: int = 128000
    available_models: List[str] = field(default_factory=list)


@dataclass
class LLMMessage:
    role: str  # "system", "user", "assistant", "tool"
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


@dataclass
class LLMResponse:
    content: str
    model: str
    provider_id: str
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    usage: Dict[str, int] = field(default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
    duration_ms: float = 0.0
    raw: Optional[Any] = None


class LLMProvider(ABC):
    """Abstract generic LLM provider for AMAS."""

    def __init__(
        self,
        provider_id: str,
        name: str,
        base_url: str = "",
        api_key: str = "",
        default_model: str = "",
        capabilities: Optional[ProviderCapabilities] = None
    ):
        self.provider_id = provider_id
        self.name = name
        self.base_url = base_url
        self.api_key = api_key
        self.default_model = default_model
        self.capabilities = capabilities or ProviderCapabilities()

    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str] | LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> LLMResponse:
        """Send chat messages and return the completion response."""
        pass

    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """Verify API key validity and connectivity."""
        pass

    @abstractmethod
    def list_models(self) -> List[str]:
        """Fetch available models from the provider API."""
        pass

    def is_configured(self) -> bool:
        """Return True if credentials are present and non-empty."""
        return bool(self.api_key and not self.api_key.startswith("MY_") and not self.api_key.startswith("your-"))
