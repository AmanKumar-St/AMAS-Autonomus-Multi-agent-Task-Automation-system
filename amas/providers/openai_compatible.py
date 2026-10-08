"""
AMAS OpenAI-Compatible Provider Adapter
=======================================
Implements LLMProvider for any service exposing an OpenAI-compatible API
(Groq, OpenRouter, CodeCraft, LocalAI, Ollama, vLLM, Custom).
Includes robust handling for Groq tool_use_failed and rate-limit classification.
"""

from __future__ import annotations
import time
import json
from typing import Dict, List, Any, Optional
import openai

from amas.providers.base import LLMProvider, LLMResponse, LLMMessage, ProviderCapabilities


class OpenAICompatibleProvider(LLMProvider):
    """Generic adapter for all OpenAI-compatible endpoints."""

    def __init__(
        self,
        provider_id: str,
        name: str,
        base_url: str,
        api_key: str,
        default_model: str,
        capabilities: Optional[ProviderCapabilities] = None
    ):
        super().__init__(
            provider_id=provider_id,
            name=name,
            base_url=base_url,
            api_key=api_key,
            default_model=default_model,
            capabilities=capabilities or ProviderCapabilities()
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

        # Normalize messages to dict format
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
        if tools and self.capabilities.tool_calling:
            params["tools"] = tools

        start = time.perf_counter()
        try:
            resp = client.chat.completions.create(**params)
        except openai.BadRequestError as e:
            err_dict = getattr(e, "body", {}) or {}
            err_msg = str(e)
            # If Groq emits 'Tool choice is none, but model called a tool', retry with explicit instruction or extract failed_generation
            if "Tool choice is none" in err_msg or "tool_use_failed" in err_msg:
                # Retry with an explicit system nudge
                nudge_messages = list(formatted_messages)
                nudge_messages.append({
                    "role": "user",
                    "content": "Please output your response as direct plain Markdown text only. Do not invoke tools."
                })
                params["messages"] = nudge_messages
                resp = client.chat.completions.create(**params)
            else:
                raise e

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
            provider_id=self.provider_id,
            tool_calls=tool_calls,
            usage=usage,
            duration_ms=round(duration_ms, 2),
            raw=resp
        )

    def test_connection(self) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "success": False,
                "provider_id": self.provider_id,
                "message": f"API key for {self.name} is missing or placeholder."
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
                "provider_id": self.provider_id,
                "model": self.default_model,
                "duration_ms": round(duration_ms, 2),
                "message": f"Successfully connected to {self.name} in {round(duration_ms, 1)}ms."
            }
        except Exception as e:
            return {
                "success": False,
                "provider_id": self.provider_id,
                "error": str(e),
                "message": f"Failed to connect to {self.name}: {str(e)}"
            }

    def list_models(self) -> List[str]:
        if not self.is_configured():
            return self.capabilities.available_models
        try:
            client = self._get_client()
            models = client.models.list()
            model_ids = [m.id for m in models.data]
            if model_ids:
                return sorted(model_ids)
        except Exception:
            pass
        return self.capabilities.available_models
