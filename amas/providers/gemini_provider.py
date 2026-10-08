"""
AMAS Google Gemini Provider Adapter
===================================
Implements LLMProvider for Google Gemini models via official SDK or OpenAI endpoint.
"""

from __future__ import annotations
import os
import time
from typing import Dict, List, Any, Optional
import openai

from amas.providers.base import LLMProvider, LLMResponse, LLMMessage, ProviderCapabilities


class GeminiProvider(LLMProvider):
    """Google Gemini provider implementation."""

    def __init__(
        self,
        api_key: str = "",
        default_model: str = "gemini-2.5-flash",
        capabilities: Optional[ProviderCapabilities] = None
    ):
        caps = capabilities or ProviderCapabilities(
            streaming=True,
            tool_calling=True,
            structured_output=True,
            vision=True,
            reasoning=True,
            max_context=1000000,
            available_models=[
                "gemini-2.5-flash",
                "gemini-2.5-pro",
                "gemini-2.0-flash",
                "gemini-1.5-flash",
                "gemini-1.5-pro"
            ]
        )
        super().__init__(
            provider_id="gemini",
            name="Google Gemini",
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=api_key,
            default_model=default_model,
            capabilities=caps
        )
        self._client: Optional[openai.OpenAI] = None

    def _get_client(self) -> openai.OpenAI:
        if self._client is None:
            self._client = openai.OpenAI(
                base_url=self.base_url,
                api_key=self.api_key or "none",
                timeout=30.0
            )
        return self._client

    def chat(
        self,
        messages: List[Dict[str, str] | LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> LLMResponse:
        client = self._get_client()
        active_model = model or self.default_model

        formatted_messages: List[Dict[str, Any]] = []
        for m in messages:
            if isinstance(m, LLMMessage):
                entry: Dict[str, Any] = {"role": m.role, "content": m.content}
                if m.name:
                    entry["name"] = m.name
                if m.tool_calls:
                    entry["tool_calls"] = m.tool_calls
                if m.tool_call_id:
                    entry["tool_call_id"] = m.tool_call_id
                formatted_messages.append(entry)
            elif isinstance(m, dict):
                formatted_messages.append(m)

        params: Dict[str, Any] = {
            "model": active_model,
            "messages": formatted_messages,
            "temperature": temperature,
        }
        if max_tokens:
            params["max_tokens"] = max_tokens
        if tools:
            params["tools"] = tools

        start = time.perf_counter()
        resp = client.chat.completions.create(**params)
        duration_ms = (time.perf_counter() - start) * 1000.0

        choice = resp.choices[0]
        content = choice.message.content or ""
        tool_calls: List[Dict[str, Any]] = []
        if getattr(choice.message, "tool_calls", None):
            for tc in choice.message.tool_calls:
                tool_calls.append({
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                })

        usage: Dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        if getattr(resp, "usage", None):
            usage = {
                "prompt_tokens": getattr(resp.usage, "prompt_tokens", 0) or 0,
                "completion_tokens": getattr(resp.usage, "completion_tokens", 0) or 0,
                "total_tokens": getattr(resp.usage, "total_tokens", 0) or 0,
            }

        return LLMResponse(
            content=content,
            model=resp.model or active_model,
            provider_id="gemini",
            tool_calls=tool_calls,
            usage=usage,
            duration_ms=round(duration_ms, 2),
            raw=resp
        )

    def test_connection(self) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "success": False,
                "provider_id": "gemini",
                "message": "Gemini API key is not configured."
            }
        try:
            client = self._get_client()
            start = time.perf_counter()
            resp = client.chat.completions.create(
                model=self.default_model,
                messages=[{"role": "user", "content": "Respond with 'ok'."}],
                max_tokens=10
            )
            duration_ms = (time.perf_counter() - start) * 1000.0
            return {
                "success": True,
                "provider_id": "gemini",
                "model": self.default_model,
                "duration_ms": round(duration_ms, 2),
                "message": f"Successfully connected to Google Gemini in {round(duration_ms, 1)}ms."
            }
        except Exception as e:
            return {
                "success": False,
                "provider_id": "gemini",
                "error": str(e),
                "message": f"Failed to connect to Google Gemini: {str(e)}"
            }

    def list_models(self) -> List[str]:
        return self.capabilities.available_models
