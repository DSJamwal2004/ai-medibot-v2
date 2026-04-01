"""
LLM Client — clean provider abstraction.

Supports: openai | huggingface | anthropic | offline
Switch providers via LLM_PROVIDER env var. Zero code changes needed.
"""
from __future__ import annotations

import json
import re
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger("llm_client")


class LLMError(Exception):
    pass


def _clean_json_response(text: str) -> str:
    """Strip markdown code fences if present."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def parse_json_response(text: str) -> dict:
    """Parse LLM JSON output safely."""
    cleaned = _clean_json_response(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        # Try to extract JSON object with regex fallback
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
        raise LLMError(f"Could not parse LLM response as JSON: {e}\nRaw: {text[:300]}")


@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    retry=retry_if_exception_type(LLMError),
    reraise=True,
)
def call_llm(prompt: str, system: Optional[str] = None) -> str:
    """
    Single entry point for all LLM calls.
    Returns raw string — callers parse JSON if needed.
    """
    provider = settings.LLM_PROVIDER

    logger.debug("llm_call_start", provider=provider, prompt_len=len(prompt))

    if provider == "openai":
        return _call_openai(prompt, system)
    elif provider == "huggingface":
        return _call_huggingface(prompt, system)
    elif provider == "anthropic":
        return _call_anthropic(prompt, system)
    elif provider == "offline":
        raise LLMError("LLM_PROVIDER=offline — no LLM available")
    else:
        raise LLMError(f"Unknown LLM_PROVIDER: {provider}")


def _call_openai(prompt: str, system: Optional[str]) -> str:
    try:
        from openai import OpenAI
    except ImportError:
        raise LLMError("openai package not installed")

    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise LLMError("OPENAI_API_KEY not set")

    client = OpenAI(
        api_key=api_key,
        base_url=settings.OPENAI_BASE_URL or "https://api.openai.com/v1",
    )

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=messages,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        raise LLMError(f"OpenAI call failed: {e}")


def _call_huggingface(prompt: str, system: Optional[str]) -> str:
    import httpx

    token = settings.HF_API_TOKEN
    if not token:
        raise LLMError("HF_API_TOKEN not set")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        r = httpx.post(
            "https://router.huggingface.co/v1/chat/completions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "model": settings.HF_MODEL,
                "messages": messages,
                "temperature": settings.LLM_TEMPERATURE,
                "max_tokens": settings.LLM_MAX_TOKENS,
            },
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"] or ""
    except Exception as e:
        raise LLMError(f"HuggingFace call failed: {e}")


def _call_anthropic(prompt: str, system: Optional[str]) -> str:
    import httpx

    key = settings.ANTHROPIC_API_KEY
    if not key:
        raise LLMError("ANTHROPIC_API_KEY not set")

    body: dict = {
        "model": settings.LLM_MODEL,
        "max_tokens": settings.LLM_MAX_TOKENS,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        body["system"] = system

    try:
        r = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=body,
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
        r.raise_for_status()
        return r.json()["content"][0]["text"] or ""
    except Exception as e:
        raise LLMError(f"Anthropic call failed: {e}")
