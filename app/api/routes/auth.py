from typing import Annotated, Optional

from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import bearer
from app.core.security import decode_token
from app.database import get_db
from app.schemas.auth import (
    EmailVerify,
    LoginIn,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshIn,
    RegisterIn,
    TokenOut,
)
from app.schemas.user import UserOut, UserRegister
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(body: UserRegister, db: Annotated[Session, Depends(get_db)]) -> UserOut:
    u = auth_service.register_user(
        db,
        RegisterIn(email=body.email, password=body.password, full_name=body.full_name),
    )
    return UserOut.model_validate(u)


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Annotated[Session, Depends(get_db)]) -> TokenOut:
    return auth_service.login(db, str(body.email), body.password)


@router.post("/refresh", response_model=TokenOut)
def refresh(body: RefreshIn, db: Annotated[Session, Depends(get_db)]) -> TokenOut:
    return auth_service.refresh_session(db, body.refresh_token)


class LogoutIn(BaseModel):
    refresh_token: str | None = None


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    body: LogoutIn,
    db: Annotated[Session, Depends(get_db)],
    cred: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer)],
) -> None:
    access: str | None = cred.credentials if cred and cred.credentials else None
    access_jti: str | None = None
    if access:
        c = decode_token(access)
        access_jti = str(c.get("jti", ""))
    auth_service.logout(
        db,
        access_jti=access_jti,
        access_raw=access,
        refresh_token=body.refresh_token,
    )
    return None


@router.post("/password-reset/request", status_code=status.HTTP_204_NO_CONTENT)
def password_reset_request(body: PasswordResetRequest, db: Annotated[Session, Depends(get_db)]) -> None:
    auth_service.request_password_reset(db, str(body.email))


@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
def password_reset_confirm(body: PasswordResetConfirm, db: Annotated[Session, Depends(get_db)]) -> None:
    auth_service.confirm_password_reset(db, body.token, body.new_password)


@router.post("/verify-email", status_code=status.HTTP_204_NO_CONTENT)
def verify_email(body: EmailVerify, db: Annotated[Session, Depends(get_db)]) -> None:
    auth_service.verify_email_token(db, body.token)
