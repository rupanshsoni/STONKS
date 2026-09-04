"""Unified LLM client with failover chain (ARCHITECTURE.md §5).

Route table lives in config.LLM_ROUTES. Failover: primary -> fallbacks ->
LLMBusError (callers implement deterministic fallbacks so the desk never dies).
"""
from __future__ import annotations

import json
from typing import Any

import httpx

from stonks.config import ENV, LLM_ROUTES

# Model per provider for cross-provider fallbacks: a glm-route fallback onto
# minimax must use MINIMAX's model, not glm's. Verified live 2026-09-03.
_MODEL_BY_PROVIDER: dict[str, str] = {
    "glm": "z-ai/glm-5.2:free",
    "minimax": "minimax/minimax-m3:free",
    "gemini": "gemini-2.0-flash",
    "openai": "gpt-4o",
    "featherless": "featherless/quill-72b",
}


class LLMBusError(RuntimeError):
    pass


class _UpstreamRateLimit(LLMBusError):
    """Free-tier upstream 429 — retryable with an alternate model/endpoint."""


def _strip_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        first = t.find("\n")
        if first != -1:
            t = t[first + 1:]
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    return t.strip()


def _parse_json(text: str) -> dict:
    cleaned = _strip_fences(text)
    try:
        return json.loads(cleaned)
    except Exception:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end > start:
            return json.loads(cleaned[start:end + 1])
        raise LLMBusError(f"unparseable LLM response: {cleaned[:120]}")


class LLMClient:
    def __init__(self, test_mode: bool = False) -> None:
        self.test_mode = test_mode or ENV.test_mode
        self._http = httpx.AsyncClient(timeout=120.0)

    async def _openrouter(
        self, model: str, system: str, user: str, json_mode: bool, key: str,
    ) -> str:
        """OpenRouter chat completion. Both GLM and MiniMax are reasoning
        models on this route — max_tokens is generous so the answer token
        budget survives the reasoning budget and content is always present."""
        if not key:
            raise LLMBusError("no openrouter key")
        body: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": 4000,
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        resp = await self._http.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json=body,
        )
        if resp.status_code == 429:
            raise _UpstreamRateLimit(f"openrouter {model} 429: {resp.text[:120]}")
        resp.raise_for_status()
        msg = resp.json()["choices"][0]["message"]
        content = msg.get("content")
        if not content:
            # reasoning models can exhaust the budget on thinking; retry hint
            raise LLMBusError(f"openrouter {model} returned empty content")
        return content

    async def _glm(self, model: str, system: str, user: str, json_mode: bool) -> str:
        """GLM via OpenRouter: free tier first, escalate to glm-5.3-flash on
        upstream 429 (free pools rate-limit hard; the flash variant is the
        same family at trivial cost and was verified live)."""
        key = ENV.openrouter_glm_key
        try:
            return await self._openrouter(model, system, user, json_mode, key)
        except _UpstreamRateLimit:
            if model.endswith(":free"):
                paid = model.replace(":free", "").rsplit("/", 1)
                escalation = f"{paid[0]}/glm-5.3-flash"
                return await self._openrouter(escalation, system, user, json_mode, key)
            raise

    async def _minimax(self, model: str, system: str, user: str, json_mode: bool) -> str:
        return await self._openrouter(model, system, user, json_mode,
                                      ENV.openrouter_minimax_key)

    async def _gemini(self, model: str, system: str, user: str, json_mode: bool) -> str:
        key = ENV.gemini_key
        if not key:
            raise LLMBusError("no gemini key")
        body: dict[str, Any] = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
        }
        if json_mode:
            body["generation_config"] = {"response_mime_type": "application/json"}
        resp = await self._http.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            params={"key": key},
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as exc:
            raise LLMBusError(f"gemini shape error: {exc}") from exc

    async def _openai(self, model: str, system: str, user: str, json_mode: bool) -> str:
        if not ENV.openai_key:
            raise LLMBusError("no openai key")
        headers = {"Authorization": f"Bearer {ENV.openai_key}"}
        body: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        resp = await self._http.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=body,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    async def _featherless(self, model: str, system: str, user: str, json_mode: bool) -> str:
        if not ENV.featherless_key:
            raise LLMBusError("no featherless key")
        headers = {"Authorization": f"Bearer {ENV.featherless_key}"}
        body: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        resp = await self._http.post(
            "https://api.featherless.ai/v1/chat/completions",
            headers=headers,
            json=body,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    _PROVIDERS = {
        "gemini": _gemini,
        "openai": _openai,
        "featherless": _featherless,
        "glm": _glm,
        "minimax": _minimax,
    }

    async def complete(
        self,
        route: str,
        system: str,
        user: str,
        json_mode: bool = True,
    ) -> dict[str, Any]:
        if self.test_mode:
            raise LLMBusError("test mode: no live LLM")
        spec = LLM_ROUTES.get(route)
        if spec is None:
            raise LLMBusError(f"unknown route {route}")
        chain = [spec.primary, *spec.fallbacks]
        errors: list[str] = []
        for provider in chain:
            model = _MODEL_BY_PROVIDER.get(provider, spec.model)
            fn = self._PROVIDERS.get(provider)
            if fn is None:
                errors.append(f"no provider {provider}")
                continue
            try:
                raw = await fn(self, model, system, user, json_mode)
                parsed = _parse_json(raw)
                parsed["_model"] = model
                parsed["_provider"] = provider
                return parsed
            except Exception as exc:
                errors.append(f"{provider}: {exc}")
                continue
        raise LLMBusError(" | ".join(errors) or "llm chain exhausted")

    async def complete_text(self, route: str, system: str, user: str) -> str:
        if self.test_mode:
            raise LLMBusError("test mode: no live LLM")
        spec = LLM_ROUTES.get(route)
        if spec is None:
            raise LLMBusError(f"unknown route {route}")
        chain = [spec.primary, *spec.fallbacks]
        errors: list[str] = []
        for provider in chain:
            model = _MODEL_BY_PROVIDER.get(provider, spec.model)
            fn = self._PROVIDERS.get(provider)
            if fn is None:
                errors.append(f"no provider {provider}")
                continue
            try:
                return await fn(self, model, system, user, False)
            except Exception as exc:
                errors.append(f"{provider}: {exc}")
        raise LLMBusError(" | ".join(errors) or "llm chain exhausted")
