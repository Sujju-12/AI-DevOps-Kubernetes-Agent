from loguru import logger

from app.core.config import get_settings


async def complete_with_ollama(prompt: str) -> dict | None:
    """Call a local Ollama server. Returns None if Ollama is unavailable."""
    import json

    import httpx

    settings = get_settings()
    url = settings.ollama_base_url.rstrip("/") + "/api/chat"
    payload = {
        "model": settings.ollama_model,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": "You are a Senior Kubernetes SRE. Reply with JSON only."},
            {"role": "user", "content": prompt},
        ],
    }
    try:
        async with httpx.AsyncClient(timeout=settings.ollama_timeout_seconds) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            content = (response.json().get("message") or {}).get("content") or "{}"
            return json.loads(content)
    except Exception as exc:  # noqa: BLE001 - local optional dependency
        logger.info("Local Ollama unavailable, using heuristic engine: {}", exc)
        return None
