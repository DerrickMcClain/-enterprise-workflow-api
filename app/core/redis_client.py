import json
from typing import Any

import redis

from app.config import get_settings

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(
            get_settings().redis_url,
            decode_responses=True,
            socket_connect_timeout=1.0,
            socket_timeout=1.0,
        )
    return _client


def close_redis() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None


def blacklist_jti(jti: str, ttl_seconds: int) -> None:
    r = get_redis()
    r.setex(f"bl:jti:{jti}", ttl_seconds, "1")


def is_jti_blacklisted(jti: str) -> bool:
    r = get_redis()
    return bool(r.get(f"bl:jti:{jti}"))


def set_cache(key: str, value: Any, ttl_seconds: int) -> None:
    r = get_redis()
    r.setex(key, ttl_seconds, json.dumps(value))


def get_cache_json(key: str) -> Any | None:
    r = get_redis()
    raw = r.get(key)
    if not raw:
        return None
    return json.loads(raw)


def set_password_reset_token(user_id: str, token: str, ttl_seconds: int = 3600) -> None:
    r = get_redis()
    r.setex(f"pwreset:{token}", ttl_seconds, user_id)


def get_password_reset_user_id(token: str) -> str | None:
    r = get_redis()
    return r.get(f"pwreset:{token}")


def delete_key(key: str) -> None:
    get_redis().delete(key)


def set_email_verification_token(user_id: str, token: str, ttl_seconds: int = 86400) -> None:
    r = get_redis()
    r.setex(f"emverify:{token}", ttl_seconds, user_id)


def get_email_verification_user_id(token: str) -> str | None:
    r = get_redis()
    return r.get(f"emverify:{token}")
