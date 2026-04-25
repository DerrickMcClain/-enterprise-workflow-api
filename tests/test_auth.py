import pytest

from app.core.security import create_access_token, new_jti
from app.models import User


def _auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id=user.id, jti=new_jti())}"}


def test_register_login_flow(client) -> None:
    r = client.post(
        "/api/auth/register",
        json={
            "email": "u1@example.com",
            "password": "password12",
            "full_name": "U One",
        },
    )
    assert r.status_code == 201, r.text
    r2 = client.post(
        "/api/auth/login", json={"email": "u1@example.com", "password": "password12"}
    )
    assert r2.status_code == 200, r2.text
    data = r2.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_me_requires_auth(client) -> None:
    r = client.get("/api/users/me")
    assert r.status_code == 401


def test_me_with_token(client, admin_user: User) -> None:
    h = _auth(admin_user)
    r = client.get("/api/users/me", headers=h)
    assert r.status_code == 200
    assert r.json()["email"] == "admin@example.com"
