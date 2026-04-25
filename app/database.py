from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase
from typing import TypeVar

from app.config import get_settings

settings = get_settings()

_engine_kwargs: dict = {
    "echo": settings.environment == "local",
}
if "sqlite" in settings.database_url:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs["pool_pre_ping"] = True
    _engine_kwargs["pool_size"] = 5
    _engine_kwargs["max_overflow"] = 10

engine = create_engine(settings.database_url, **_engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


T = TypeVar("T", bound=Base)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
