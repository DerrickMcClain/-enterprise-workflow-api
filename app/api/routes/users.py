from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas.user import UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def me(user: Annotated[User, Depends(get_current_user)]) -> UserOut:
    return UserOut.model_validate(user)


@router.patch("/me", response_model=UserOut)
def update_me(
    body: UserUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> UserOut:
    if body.full_name is not None:
        user.full_name = body.full_name
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)
