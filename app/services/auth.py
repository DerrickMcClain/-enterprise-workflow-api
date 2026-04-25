import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.exceptions import AuthError, ConflictError
from app.core.redis_client import (
    delete_key,
    get_email_verification_user_id,
    get_password_reset_user_id,
    set_email_verification_token,
    set_password_reset_token,
    blacklist_jti,
)
from app.core.security import (
    create_access_token,
    create_refresh_token_payload,
    decode_token,
    hash_password,
    hash_token_value,
    new_jti,
    verify_password,
)
from app.models import RefreshToken, User, Workspace, WorkspaceMember, WorkspaceRole
from app.schemas.auth import RegisterIn, TokenOut
from app.workers.tasks import send_email_task

log = logging.getLogger(__name__)


def _refresh_expires_at() -> datetime:
    s = get_settings()
    return datetime.now(timezone.utc) + timedelta(days=s.refresh_token_expire_days)


def _unique_workspace_slug(db: Session, base: str) -> str:
    slug = base
    n = 1
    while True:
        if db.execute(select(Workspace).where(Workspace.slug == slug)).scalar_one_or_none() is None:
            return slug
        slug = f"{base}-{n}"
        n += 1


def _issue_tokens(db: Session, user: User) -> TokenOut:
    settings = get_settings()
    access_jti = new_jti()
    r_jti = new_jti()
    fam = uuid.uuid4()
    expires = _refresh_expires_at()
    tr = RefreshToken(
        user_id=user.id,
        jti=r_jti,
        family_id=fam,
        token_hash=hash_token_value(f"{r_jti}:{user.id}"),
        expires_at=expires,
    )
    db.add(tr)
    db.commit()
    access = create_access_token(user_id=user.id, jti=access_jti)
    refresh = create_refresh_token_payload(
        user_id=user.id, jti=r_jti, family_id=fam, expires_at=expires
    )
    return TokenOut(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.access_token_expire_minutes * 60,
    )


def register_user(db: Session, data: RegisterIn) -> User:
    existing = db.execute(select(User).where(User.email == str(data.email).lower())).scalar_one_or_none()
    if existing:
        raise ConflictError("Email already registered")
    user = User(
        email=str(data.email).lower(),
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        is_email_verified=False,
    )
    db.add(user)
    db.flush()
    local = str(data.email).split("@")[0]
    base = "".join(c if c.isalnum() or c == "-" else "-" for c in local.lower()).strip("-")[:40] or "workspace"
    ws = Workspace(name=f"{data.full_name}'s Workspace", slug=_unique_workspace_slug(db, base))
    db.add(ws)
    db.flush()
    db.add(WorkspaceMember(workspace_id=ws.id, user_id=user.id, role=WorkspaceRole.ADMIN, is_pending=False))
    vtoken = secrets.token_urlsafe(32)
    set_email_verification_token(str(user.id), vtoken, ttl_seconds=86_400)
    try:
        send_email_task.delay(
            to_email=user.email,
            subject="Verify your email",
            body=f"Submit POST /api/auth/verify-email with token: {vtoken}",
        )
    except Exception as e:  # noqa: BLE001
        log.warning("celery_send_skipped", extra={"error": str(e)})
    db.commit()
    db.refresh(user)
    return user


def login(db: Session, email: str, password: str) -> TokenOut:
    user = db.execute(select(User).where(User.email == email.lower())).scalar_one_or_none()
    if not user or not user.is_active or user.deleted_at is not None:
        raise AuthError("Invalid credentials")
    if not verify_password(password, user.hashed_password):
        raise AuthError("Invalid credentials")
    return _issue_tokens(db, user)


def refresh_session(db: Session, refresh_token: str) -> TokenOut:
    try:
        claims = decode_token(refresh_token)
    except JWTError as e:
        raise AuthError("Invalid refresh token") from e
    if claims.get("typ") != "refresh":
        raise AuthError("Not a refresh token")
    r_jti = str(claims.get("jti", ""))
    sub = str(claims.get("sub", ""))
    if not r_jti or not sub:
        raise AuthError("Invalid refresh token")
    user_id = uuid.UUID(sub)
    row = db.execute(
        select(RefreshToken).where(RefreshToken.jti == r_jti, RefreshToken.user_id == user_id)
    ).scalar_one_or_none()
    if not row or row.revoked:
        raise AuthError("Refresh token revoked or invalid")
    if row.expires_at < datetime.now(timezone.utc):
        raise AuthError("Refresh token expired")
    user = db.get(User, user_id)
    if not user or not user.is_active or user.deleted_at is not None:
        raise AuthError("User invalid")
    # rotate: revoke this refresh and issue a new family (simple rotation; family reuse can be stricter)
    row.revoked = True
    db.commit()
    return _issue_tokens(db, user)


def logout(db: Session, access_jti: str | None, access_raw: str | None, refresh_token: str | None) -> None:
    settings = get_settings()
    if access_jti and access_raw:
        try:
            claims = decode_token(access_raw)
        except JWTError:
            pass
        else:
            exp_ts = int(claims.get("exp", 0))
            now = int(datetime.now(timezone.utc).timestamp())
            ttl = max(0, exp_ts - now)
            if ttl:
                blacklist_jti(access_jti, ttl)
    if refresh_token:
        try:
            c = decode_token(refresh_token)
        except JWTError:
            return
        if c.get("typ") != "refresh":
            return
        rj = str(c.get("jti", ""))
        su = str(c.get("sub", ""))
        if rj and su:
            row = db.execute(
                select(RefreshToken).where(RefreshToken.jti == rj, RefreshToken.user_id == uuid.UUID(su))
            ).scalar_one_or_none()
            if row:
                row.revoked = True
                db.commit()


def request_password_reset(db: Session, email: str) -> None:
    user = db.execute(select(User).where(User.email == email.lower())).scalar_one_or_none()
    if not user:
        return
    raw = secrets.token_urlsafe(32)
    set_password_reset_token(str(user.id), raw, ttl_seconds=3600)
    try:
        send_email_task.delay(
            to_email=user.email,
            subject="Password reset",
            body=f"POST /api/auth/password-reset/confirm with token: {raw}",
        )
    except Exception as e:  # noqa: BLE001
        log.warning("celery_send_skipped", extra={"error": str(e)})


def confirm_password_reset(db: Session, token: str, new_password: str) -> None:
    uid = get_password_reset_user_id(token)
    if not uid:
        raise AuthError("Invalid or expired token")
    user = db.get(User, uuid.UUID(uid))
    if not user:
        raise AuthError("Invalid token")
    user.hashed_password = hash_password(new_password)
    delete_key(f"pwreset:{token}")
    # revoke all refresh rows for this user
    for row in db.execute(select(RefreshToken).where(RefreshToken.user_id == user.id)).scalars():
        row.revoked = True
    db.commit()


def verify_email_token(db: Session, token: str) -> None:
    uid = get_email_verification_user_id(token)
    if not uid:
        raise AuthError("Invalid or expired token")
    user = db.get(User, uuid.UUID(uid))
    if not user:
        raise AuthError("Invalid token")
    user.is_email_verified = True
    delete_key(f"emverify:{token}")
    db.commit()
