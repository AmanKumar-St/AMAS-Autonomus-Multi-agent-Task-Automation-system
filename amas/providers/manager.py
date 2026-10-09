"""
AMAS Provider Manager
=====================
Central orchestrator for LLM provider discovery, credential validation,
connection testing, live model cataloging, and intelligent fallback policies.
Never exposes raw API keys to external callers or the UI.
"""

from __future__ import annotations
import os
import time
import logging
from typing import Dict, List, Any, Optional
import dotenv

from amas.providers.base import LLMProvider, LLMResponse, ProviderCapabilities
from amas.providers.openai_compatible import OpenAICompatibleProvider
from amas.providers.gemini_provider import GeminiProvider

logger = logging.getLogger("amas.providers.manager")


class ProviderHealth:
    """Tracks health metrics for a provider."""
    def __init__(self):
        self.success_count = 0
        self.failure_count = 0
        self.total_latency_ms = 0.0
        self.last_success_time: Optional[float] = None
        self.last_failure_time: Optional[float] = None
        self.last_error: Optional[str] = None
        self.rate_limited = False
        self.rate_limit_reset_time: Optional[float] = None

    @property
    def avg_latency_ms(self) -> float:
        total = self.success_count + self.failure_count
        return self.total_latency_ms / total if total > 0 else 0.0

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 1.0

    def record_success(self, latency_ms: float):
        self.success_count += 1
        self.total_latency_ms += latency_ms
        self.last_success_time = time.time()
        self.rate_limited = False

    def record_failure(self, error: str):
        self.failure_count += 1
        self.last_failure_time = time.time()
        self.last_error = error
        if "429" in error or "rate limit" in error.lower():
            self.rate_limited = True
            self.rate_limit_reset_time = time.time() + 60  # Assume 60s reset

    def is_healthy(self) -> bool:
        if self.rate_limited and self.rate_limit_reset_time and time.time() < self.rate_limit_reset_time:
            return False
        return self.success_rate > 0.5 or (self.success_count + self.failure_count) < 5


class ProviderManager:
    """Manages multi-provider registration, routing, and fallbacks."""

    def __init__(self, env_path: Optional[str] = None):
        if env_path and os.path.exists(env_path):
            dotenv.load_dotenv(env_path)
        else:
            dotenv.load_dotenv()

        self._providers: Dict[str, LLMProvider] = {}
        self._health: Dict[str, ProviderHealth] = {}
        self.default_provider_id: str = self._get_env("DEFAULT_LLM_PROVIDER", "groq").lower()
        self.default_model: str = self._get_env("DEFAULT_LLM_MODEL", "openai/gpt-oss-120b")
        self.provider_mode: str = self._get_env("LLM_PROVIDER_MODE", "fallback").lower()  # fixed | fallback | automatic

        self._initialize_providers()

    def _get_env(self, key: str, default: str = "") -> str:
        """Case-insensitive and delimiter-tolerant environment variable lookup."""
        val = os.getenv(key)
        if val:
            return val.strip().strip('"').strip("'")
        
        # Try alternate hyphen/underscore permutations
        for k, v in os.environ.items():
            normalized_k = k.upper().replace("-", "_")
            normalized_target = key.upper().replace("-", "_")
            if normalized_k == normalized_target:
                return v.strip().strip('"').strip("'")
        return default

    def _initialize_providers(self):
        """Register all supported providers from environment configuration."""
        # 1. Groq
        groq_key = self._get_env("GROQ_API_KEY")
        self._providers["groq"] = OpenAICompatibleProvider(
            provider_id="groq",
            name="Groq Ultra-Fast Inference",
            base_url="https://api.groq.com/openai/v1",
            api_key=groq_key,
            default_model="openai/gpt-oss-120b",
            capabilities=ProviderCapabilities(
                streaming=True,
                tool_calling=True,
                structured_output=True,
                vision=False,
                reasoning=True,
                max_context=131072,
                available_models=[
                    "openai/gpt-oss-120b",
                    "openai/gpt-oss-20b",
                    "qwen/qwen3.8-27b",
                    "meta-llama/llama-prompt-guard-2-86m"
                ]
            )
        )
        self._health["groq"] = ProviderHealth()

        # 2. OpenRouter
        or_key = self._get_env("OPENROUTER_API_KEY")
        self._providers["openrouter"] = OpenAICompatibleProvider(
            provider_id="openrouter",
            name="OpenRouter Unified API",
            base_url="https://openrouter.ai/api/v1",
            api_key=or_key,
            default_model="meta-llama/llama-3.3-70b-instruct",
            capabilities=ProviderCapabilities(
                streaming=True,
                tool_calling=True,
                structured_output=True,
                vision=True,
                reasoning=True,
                max_context=128000,
                available_models=[
                    "meta-llama/llama-3.3-70b-instruct",
                    "google/gemini-2.5-flash",
                    "anthropic/claude-3.5-sonnet",
                    "openai/gpt-4o-mini",
                    "deepseek/deepseek-chat"
                ]
            )
        )
        self._health["openrouter"] = ProviderHealth()

        # 3. CodeCraft (OpenAI-compatible)
        cc_key = self._get_env("CODECRAFT_API_KEY")
        cc_url = self._get_env("CODECRAFT_BASE_URL", "https://api.codecraft-ai.com/v1")
        cc_model = self._get_env("CODECRAFT_MODEL", "codecraft-standard")
        self._providers["codecraft"] = OpenAICompatibleProvider(
            provider_id="codecraft",
            name="CodeCraft AI Endpoint",
            base_url=cc_url,
            api_key=cc_key,
            default_model=cc_model,
            capabilities=ProviderCapabilities(
                streaming=True,
                tool_calling=True,
                structured_output=True,
                available_models=[cc_model]
            )
        )
        self._health["codecraft"] = ProviderHealth()

        # 4. Google Gemini
        gemini_key = self._get_env("GEMINI_API_KEY")
        self._providers["gemini"] = GeminiProvider(
            api_key=gemini_key,
            default_model="gemini-2.5-flash"
        )
        self._health["gemini"] = ProviderHealth()

        # 5. Custom OpenAI-compatible endpoint
        custom_url = self._get_env("CUSTOM_LLM_BASE_URL", "http://localhost:11434/v1")
        custom_key = self._get_env("CUSTOM_LLM_API_KEY", "local")
        custom_model = self._get_env("CUSTOM_LLM_MODEL", "llama3")
        self._providers["custom"] = OpenAICompatibleProvider(
            provider_id="custom",
            name="Custom OpenAI-Compatible API",
            base_url=custom_url,
            api_key=custom_key,
            default_model=custom_model,
            capabilities=ProviderCapabilities(
                streaming=True,
                tool_calling=True,
                structured_output=True,
                available_models=[custom_model]
            )
        )
        self._health["custom"] = ProviderHealth()

    def get_provider(self, provider_id: Optional[str] = None) -> LLMProvider:
        """Resolve requested provider or active default."""
        target = (provider_id or self.default_provider_id).lower()
        if target in self._providers:
            return self._providers[target]
        
        # Fallback to any configured provider if target is missing
        for p in self._providers.values():
            if p.is_configured():
                return p
        return self._providers.get("groq") or list(self._providers.values())[0]

    def list_providers_metadata(self) -> List[Dict[str, Any]]:
        """Return provider metadata for UI without exposing API keys."""
        results = []
        for pid, p in self._providers.items():
            health = self._health.get(pid)
            results.append({
                "id": pid,
                "name": p.name,
                "is_configured": p.is_configured(),
                "default_model": p.default_model,
                "base_url": p.base_url,
                "is_default": pid == self.default_provider_id,
                "capabilities": {
                    "streaming": p.capabilities.streaming,
                    "tool_calling": p.capabilities.tool_calling,
                    "structured_output": p.capabilities.structured_output,
                    "vision": p.capabilities.vision,
                    "reasoning": p.capabilities.reasoning,
                    "max_context": p.capabilities.max_context
                },
                "available_models": p.capabilities.available_models,
                "health": {
                    "success_count": health.success_count if health else 0,
                    "failure_count": health.failure_count if health else 0,
                    "avg_latency_ms": round(health.avg_latency_ms, 2) if health else 0.0,
                    "success_rate": round(health.success_rate, 2) if health else 1.0,
                    "is_healthy": health.is_healthy() if health else True,
                    "rate_limited": health.rate_limited if health else False,
                    "last_error": health.last_error if health else None
                } if health else None
            })
        return results

    def list_models(self, provider_id: str) -> List[str]:
        p = self.get_provider(provider_id)
        return p.list_models()

    def test_provider(self, provider_id: str) -> Dict[str, Any]:
        p = self.get_provider(provider_id)
        return p.test_connection()

    def execute_with_fallback(
        self,
        messages: List[Any],
        preferred_provider_id: Optional[str] = None,
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> LLMResponse:
        """Execute chat request respecting mode: fixed | fallback | automatic."""
        primary_id = preferred_provider_id or self.default_provider_id
        primary = self.get_provider(primary_id)

        # Mode FIXED: Never silently fallback
        if self.provider_mode == "fixed":
            return primary.chat(messages, model=model, tools=tools, **kwargs)

        # Determine fallback order
        if self.provider_mode == "automatic":
            # Sort by health: healthy providers first, then by success rate, then by latency
            configured = [pid for pid, p in self._providers.items() if p.is_configured()]
            fallback_order = sorted(
                configured,
                key=lambda pid: (
                    0 if self._health[pid].is_healthy() else 1,
                    -self._health[pid].success_rate,
                    self._health[pid].avg_latency_ms
                )
            )
            # Ensure preferred provider is tried first if it's in the list
            if primary_id in fallback_order:
                fallback_order.remove(primary_id)
            fallback_order = [primary_id] + fallback_order
        else:
            # FALLBACK mode: simple sequential order
            fallback_order = [primary_id] + [pid for pid in self._providers.keys() if pid != primary_id]

        last_error = None

        for pid in fallback_order:
            provider = self._providers[pid]
            if not provider.is_configured():
                continue
            try:
                logger.info(f"Attempting LLM call via provider: {pid}")
                start = time.perf_counter()
                response = provider.chat(messages, model=model if pid == primary_id else None, tools=tools, **kwargs)
                latency_ms = (time.perf_counter() - start) * 1000.0
                
                # Record health metrics
                self._health[pid].record_success(latency_ms)
                
                # Include provider info in response
                response.provider_id = pid
                return response
            except Exception as e:
                err_msg = str(e)
                logger.warning(f"Provider {pid} failed: {err_msg}. Evaluating fallback.")
                self._health[pid].record_failure(err_msg)
                last_error = e
                # Check for rate limit or timeout errors specifically
                if "429" in err_msg or "timeout" in err_msg.lower() or "not found" in err_msg.lower():
                    continue
                else:
                    # If it's a non-retryable error, still try fallback if in automatic mode
                    if self.provider_mode == "automatic":
                        continue
                    raise e

        if last_error:
            raise last_error
        raise RuntimeError("No configured LLM provider was able to fulfill the request.")
