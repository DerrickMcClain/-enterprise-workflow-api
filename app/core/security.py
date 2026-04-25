import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from app.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _token_expiry(minutes: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)


def _encode(payload: dict[str, Any], expires: datetime) -> str:
    settings = get_settings()
    to_encode = {**payload, "exp": int(expires.timestamp())}
    return str(jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm))


def create_access_token(*, user_id: uuid.UUID, jti: str) -> str:
    settings = get_settings()
    exp = _token_expiry(settings.access_token_expire_minutes)
    return _encode(
        {
            "sub": str(user_id),
            "jti": jti,
            "typ": "access",
        },
        exp,
    )


def create_refresh_token_payload(
    *, user_id: uuid.UUID, jti: str, family_id: uuid.UUID, expires_at: datetime
) -> str:
    return _encode(
        {
            "sub": str(user_id),
            "jti": jti,
            "fam": str(family_id),
            "typ": "refresh",
        },
        expires_at,
    )


def hash_token_value(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])  # type: ignore[no-any-return]


def new_jti() -> str:
    return secrets.token_urlsafe(32)
