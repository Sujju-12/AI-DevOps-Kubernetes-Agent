"""OpenRouter LLM client. The API key is read from env (set from InsForge, never hardcoded)."""

import time

import httpx
from loguru import logger

from app.core.config import get_settings

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class LlmError(RuntimeError):
    pass


class LlmNotConfiguredError(LlmError):
    pass


def complete(messages: list[dict]) -> str:
    """Call OpenRouter chat completions. Never logs the API key."""
    settings = get_settings()
    api_key = (settings.openrouter_api_key or "").strip()
    if not api_key:
        raise LlmNotConfiguredError(
            "OPENROUTER_API_KEY is not set. Store the key in InsForge and export it as an env var."
        )

    model = (settings.openrouter_model or "").strip() or "openai/gpt-4o-mini"
    timeout = settings.openrouter_timeout_seconds
    retries = max(0, settings.openrouter_max_retries)
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/Sujju-12/AI-DevOps-Kubernetes-Agent",
        "X-Title": "AI Kubernetes Agent",
    }

    last_error = "OpenRouter request failed"
    for attempt in range(retries + 1):
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(OPENROUTER_URL, headers=headers, json=payload)
            if response.status_code in {429, 500, 502, 503, 529} and attempt < retries:
                logger.warning("OpenRouter returned {} (attempt {})", response.status_code, attempt + 1)
                time.sleep(0.5 * (attempt + 1))
                continue
            if response.status_code >= 400:
                logger.error("OpenRouter HTTP error status={}", response.status_code)
                raise LlmError(f"OpenRouter returned HTTP {response.status_code}")
            content = _message_content(response.json())
            if not content:
                raise LlmError("OpenRouter returned an empty message")
            return content
        except httpx.TimeoutException:
            last_error = "OpenRouter request timed out"
            logger.error("OpenRouter timeout (attempt {})", attempt + 1)
            if attempt >= retries:
                raise LlmError(last_error) from None
            time.sleep(0.5 * (attempt + 1))
        except httpx.HTTPError as exc:
            last_error = "OpenRouter network error"
            logger.error("OpenRouter network error (attempt {})", attempt + 1)
            if attempt >= retries:
                raise LlmError(last_error) from exc
            time.sleep(0.5 * (attempt + 1))
    raise LlmError(last_error)


def _message_content(body: dict) -> str:
    choices = body.get("choices") or []
    if not choices:
        return ""
    message = (choices[0] or {}).get("message") or {}
    return (message.get("content") or "").strip()
