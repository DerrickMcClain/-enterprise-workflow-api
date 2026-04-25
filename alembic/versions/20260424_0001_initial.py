"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_email_verified", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table(
        "workspaces",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_workspaces_slug"),
    )
    op.create_index("ix_workspaces_slug", "workspaces", ["slug"], unique=False)
    workspace_role = sa.Enum("admin", "manager", "member", name="workspace_role")
    workspace_role.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "workspace_members",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", postgresql.ENUM("admin", "manager", "member", name="workspace_role", create_type=False), nullable=False),
        sa.Column("invited_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_pending", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", "user_id", name="uq_workspace_user"),
    )
    op.create_index("ix_workspace_members_workspace", "workspace_members", ["workspace_id"], unique=False)
    op.create_index("ix_workspace_members_user", "workspace_members", ["user_id"], unique=False)
    project_status = sa.Enum("active", "on_hold", "completed", "archived", name="project_status")
    project_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM("active", "on_hold", "completed", "archived", name="project_status", create_type=False),
            nullable=False,
        ),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("last_status_changed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_projects_workspace", "projects", ["workspace_id"], unique=False)
    op.create_index("ix_projects_status", "projects", ["status"], unique=False)
    task_status = sa.Enum("backlog", "in_progress", "in_review", "done", "cancelled", name="task_status")
    task_priority = sa.Enum("low", "medium", "high", "urgent", name="task_priority")
    task_status.create(op.get_bind(), checkfirst=True)
    task_priority.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM("backlog", "in_progress", "in_review", "done", "cancelled", name="task_status", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "priority",
            postgresql.ENUM("low", "medium", "high", "urgent", name="task_priority", create_type=False),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("assignee_user_id", sa.Uuid(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["assignee_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tasks_project", "tasks", ["project_id"], unique=False)
    op.create_index("ix_tasks_status", "tasks", ["status"], unique=False)
    op.create_index("ix_tasks_due", "tasks", ["due_at"], unique=False)
    op.create_index("ix_tasks_assignee", "tasks", ["assignee_user_id"], unique=False)
    op.create_table(
        "comments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_comments_task", "comments", ["task_id"], unique=False)
    op.create_table(
        "attachments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("uploaded_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("original_filename", sa.String(length=500), nullable=False),
        sa.Column("storage_path", sa.String(length=1000), nullable=False),
        sa.Column("content_type", sa.String(length=200), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("extra_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    # Fix: SQLAlchemy model uses "extra_metadata" in Python for JSON; column name in model is not specified - it maps to extra_metadata in DB. Check attachment model: field name `extra_metadata` - column will be `extra_metadata`
    # Migration used extra_metadata - the model has extra_metadata: Mapped[dict | None] = mapped_column(JSON) - column name extra_metadata
    op.create_index("ix_attachments_task", "attachments", ["task_id"], unique=False)
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("resource_type", sa.String(length=80), nullable=False),
        sa.Column("resource_id", sa.Uuid(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_workspace", "audit_logs", ["workspace_id"], unique=False)
    op.create_index("ix_audit_created", "audit_logs", ["created_at"], unique=False)
    op.create_index("ix_audit_resource", "audit_logs", ["resource_type", "resource_id"], unique=False)
    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_email_sent", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_user", "notifications", ["user_id"], unique=False)
    op.create_index("ix_notifications_workspace", "notifications", ["workspace_id"], unique=False)
    op.create_index("ix_notifications_unread", "notifications", ["read_at"], unique=False)
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("jti", sa.String(length=64), nullable=False),
        sa.Column("family_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("jti", name="uq_refresh_jti"),
    )
    op.create_index("ix_refresh_user", "refresh_tokens", ["user_id"], unique=False)
    op.create_index("ix_refresh_jti", "refresh_tokens", ["jti"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_refresh_jti", table_name="refresh_tokens")
    op.drop_index("ix_refresh_user", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_index("ix_notifications_unread", table_name="notifications")
    op.drop_index("ix_notifications_workspace", table_name="notifications")
    op.drop_index("ix_notifications_user", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_audit_resource", table_name="audit_logs")
    op.drop_index("ix_audit_created", table_name="audit_logs")
    op.drop_index("ix_audit_workspace", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_attachments_task", table_name="attachments")
    op.drop_table("attachments")
    op.drop_index("ix_comments_task", table_name="comments")
    op.drop_table("comments")
    op.drop_index("ix_tasks_assignee", table_name="tasks")
    op.drop_index("ix_tasks_due", table_name="tasks")
    op.drop_index("ix_tasks_status", table_name="tasks")
    op.drop_index("ix_tasks_project", table_name="tasks")
    op.drop_table("tasks")
    sa.Enum(name="task_priority").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="task_status").drop(op.get_bind(), checkfirst=True)
    op.drop_index("ix_projects_status", table_name="projects")
    op.drop_index("ix_projects_workspace", table_name="projects")
    op.drop_table("projects")
    sa.Enum(name="project_status").drop(op.get_bind(), checkfirst=True)
    op.drop_index("ix_workspace_members_user", table_name="workspace_members")
    op.drop_index("ix_workspace_members_workspace", table_name="workspace_members")
    op.drop_table("workspace_members")
    sa.Enum(name="workspace_role").drop(op.get_bind(), checkfirst=True)
    op.drop_index("ix_workspaces_slug", table_name="workspaces")
    op.drop_table("workspaces")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
