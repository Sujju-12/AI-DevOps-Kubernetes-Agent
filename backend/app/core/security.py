import hashlib
import hmac
import json
import secrets
import time
from typing import Any


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, _digest = stored.split("$", 1)
    except ValueError:
        return False
    return hmac.compare_digest(hash_password(password, salt), stored)


def create_token(payload: dict[str, Any], secret: str, ttl_seconds: int = 86_400) -> str:
    body = {**payload, "exp": int(time.time()) + ttl_seconds}
    raw = json.dumps(body, separators=(",", ":"), sort_keys=True)
    signature = hmac.new(secret.encode(), raw.encode(), hashlib.sha256).hexdigest()
    return f"{_b64(raw)}.{signature}"


def decode_token(token: str, secret: str) -> dict[str, Any]:
    encoded, signature = token.split(".", 1)
    raw = _unb64(encoded)
    expected = hmac.new(secret.encode(), raw.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise ValueError("Invalid token")
    payload = json.loads(raw)
    if int(payload.get("exp", 0)) < int(time.time()):
        raise ValueError("Token expired")
    return payload


def _b64(value: str) -> str:
    import base64

    return base64.urlsafe_b64encode(value.encode()).decode().rstrip("=")


def _unb64(value: str) -> str:
    import base64

    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding).decode()
