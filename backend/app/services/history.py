"""Persist investigation progress and history in Supabase (user JWT, RLS)."""

from datetime import datetime, timezone
from typing import Any

import httpx
from loguru import logger

from app.core.config import get_settings

PROGRESS_STEPS = [
    {"key": "pods", "label": "Checking Pods", "done": False},
    {"key": "logs", "label": "Reading Logs", "done": False},
    {"key": "events", "label": "Analyzing Events", "done": False},
    {"key": "deployments", "label": "Inspecting Deployments", "done": False},
    {"key": "network", "label": "Checking Networking", "done": False},
    {"key": "ai", "label": "AI Reasoning", "done": False},
    {"key": "done", "label": "Root Cause Found", "done": False},
]


def patch_investigation(
    access_token: str | None,
    investigation_id: str | None,
    payload: dict[str, Any],
) -> None:
    if not access_token or not investigation_id:
        return
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_anon_key:
        return
    body = {**payload, "updated_at": datetime.now(timezone.utc).isoformat()}
    try:
        response = httpx.patch(
            f"{settings.supabase_url.rstrip('/')}/rest/v1/investigations",
            params={"id": f"eq.{investigation_id}"},
            headers={**_headers(access_token), "Prefer": "return=minimal"},
            json=body,
            timeout=15,
        )
        if response.status_code >= 400:
            logger.warning("Supabase history update failed status={}", response.status_code)
    except httpx.HTTPError:
        logger.warning("Supabase history update failed")


def mark_step(
    access_token: str | None,
    investigation_id: str | None,
    steps: list[dict],
    key: str,
) -> list[dict]:
    updated = []
    for item in steps:
        row = dict(item)
        if row.get("key") == key:
            row["done"] = True
        updated.append(row)
    patch_investigation(
        access_token,
        investigation_id,
        {"current_step": key, "steps": updated, "status": "running"},
    )
    return updated


def _headers(access_token: str) -> dict[str, str]:
    settings = get_settings()
    return {
        "apikey": settings.supabase_anon_key,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
