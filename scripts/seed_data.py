"""
Seed a demo user, workspace, project, and task. Run after migrations.

  DATABASE_URL=... python -m scripts.seed_data
"""
import os
import sys
import uuid

# Allow running as script from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

os.environ.setdefault("SECRET_KEY", "dev-secret-for-seed-min-16-chars")

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.security import hash_password
from app.models import (
    User,
    Workspace,
    WorkspaceMember,
    WorkspaceRole,
    Project,
    Task,
    TaskStatus,
    TaskPriority,
    ProjectStatus,
)
from app.config import get_settings

settings = get_settings()


def run() -> None:
    eng = create_engine(settings.database_url)
    Session = sessionmaker(bind=eng)
    db = Session()
    email = "seed@example.com"
    if db.execute(select(User).where(User.email == email)).scalar_one_or_none():
        print("seed user exists; nothing to do")
        return
    u = User(
        email=email,
        full_name="Seed User",
        hashed_password=hash_password("password12"),
        is_email_verified=True,
    )
    db.add(u)
    db.flush()
    ws = Workspace(name="Demo Co", slug="demo-co")
    db.add(ws)
    db.flush()
    db.add(WorkspaceMember(workspace_id=ws.id, user_id=u.id, role=WorkspaceRole.ADMIN, is_pending=False))
    p = Project(
        workspace_id=ws.id,
        name="Q2 Launch",
        description="Demo project",
        status=ProjectStatus.ACTIVE,
        created_by_user_id=u.id,
    )
    db.add(p)
    db.flush()
    t = Task(
        project_id=p.id,
        title="API integration",
        description="Build REST client",
        status=TaskStatus.IN_PROGRESS,
        priority=TaskPriority.HIGH,
        position=0,
        created_by_user_id=u.id,
    )
    db.add(t)
    db.commit()
    print("seeded user", email, "password: password12")


if __name__ == "__main__":
    run()
