import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["ENVIRONMENT"] = "test"
os.environ["SECRET_KEY"] = "test-secret-key-min-16-chars-ok"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/9"

from app import config  # noqa: E402
from app.core import redis_client  # noqa: E402
from app.core.security import create_access_token, hash_password, new_jti  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User  # noqa: E402


@pytest.fixture
def engine() -> Generator:  # type: ignore[no-untyped-def]
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=eng)
    try:
        yield eng
    finally:
        eng.dispose()


@pytest.fixture
def session(engine) -> Generator[Session, None, None]:  # type: ignore[no-untyped-def]
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


class _NoCelery:
    def delay(self, *a, **k) -> None:  # type: ignore[no-untyped-def]
        return None


class _FakeRedis:
    def __init__(self) -> None:
        self._d: dict[str, str] = {}

    def setex(self, k: str, _ttl: int, v: str) -> bool:
        self._d[k] = v
        return True

    def get(self, k: str) -> str | None:
        return self._d.get(k)

    def delete(self, *k: str) -> int:
        c = 0
        for x in k:
            if x in self._d:
                del self._d[x]
                c += 1
        return c

    def ping(self) -> bool:
        return True


@pytest.fixture
def client(session: Session, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    def override_db() -> Generator[Session, None, None]:
        yield session

    from app.workers import tasks

    fake = _FakeRedis()
    monkeypatch.setattr(redis_client, "get_redis", lambda: fake)  # type: ignore[assignment]
    redis_client._client = None  # type: ignore[attr-defined]
    monkeypatch.setattr(redis_client, "is_jti_blacklisted", lambda jti: False)  # type: ignore[arg-type]
    monkeypatch.setattr(tasks, "send_email_task", _NoCelery())
    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    config.get_settings.cache_clear()  # type: ignore[attr-defined]


@pytest.fixture
def admin_user(session: Session) -> User:
    u = User(
        email="admin@example.com",
        hashed_password=hash_password("password12"),
        full_name="Admin User",
        is_email_verified=True,
    )
    session.add(u)
    session.commit()
    session.refresh(u)
    return u


def auth_headers_for(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id=user.id, jti=new_jti())}"}
