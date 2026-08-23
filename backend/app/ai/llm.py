from loguru import logger

from app.core.config import get_settings


async def complete_with_openrouter(prompt: str) -> dict | None:
    """Optional OpenRouter call from OPENROUTER_API_KEY. Returns None if unset or failing."""
    import json

    import httpx

    settings = get_settings()
    if not settings.openrouter_api_key:
        return None
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {"role": "system", "content": "You are a Senior Kubernetes SRE. Reply with JSON only."},
            {"role": "user", "content": prompt},
        ],
    }
    last_error = None
    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=settings.openrouter_timeout_seconds) as client:
                response = await client.post(settings.openrouter_base_url, headers=headers, json=payload)
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                return json.loads(content)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            logger.warning("OpenRouter attempt {} failed: {}", attempt + 1, exc)
    logger.info("OpenRouter unavailable, using local SRE engine: {}", last_error)
    return None
