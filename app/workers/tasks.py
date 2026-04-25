import logging
import smtplib
from email.message import EmailMessage
from datetime import datetime, timezone

from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.models import Notification, Project, Task, User, RefreshToken
from app.models.enums import TaskStatus
from app.workers.celery_app import celery_app

log = logging.getLogger(__name__)


@celery_app.task(name="app.workers.tasks.send_email_task")
def send_email_task(to_email: str, subject: str, body: str) -> None:
    s = get_settings()
    if not s.smtp_host:
        log.info("email_skipped_smtp_unconfigured: to=%s subject=%s", to_email, subject)
        return
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = s.mail_from
    msg["To"] = to_email
    msg.set_content(body)
    with smtplib.SMTP(s.smtp_host, s.smtp_port) as smtp:
        if s.smtp_user and s.smtp_password:
            smtp.starttls()
            smtp.login(s.smtp_user, s.smtp_password)
        smtp.send_message(msg)
    log.info("email_sent to=%s subject=%s", to_email, subject)


@celery_app.task(name="app.workers.tasks.generate_report")
def generate_report_task(workspace_id: str, user_id: str) -> str:
    log.info("report_started workspace=%s user=%s", workspace_id, user_id)
    return "report-ready-key-placeholder"


@celery_app.task(name="app.workers.tasks.overdue_reminder_task")
def overdue_reminder_task() -> int:
    session = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        count = 0
        for task, wid in session.execute(
            select(Task, Project.workspace_id)
            .join(Project, Project.id == Task.project_id)
            .where(
                Task.deleted_at.is_(None),
                Task.due_at.isnot(None),
                Task.due_at < now,
                Task.status.notin_([TaskStatus.DONE, TaskStatus.CANCELLED]),
            )
        ).all():
            if not task.assignee_user_id:
                continue
            session.add(
                Notification(
                    user_id=task.assignee_user_id,
                    workspace_id=wid,
                    title="Overdue task",
                    body=f"Task '{task.title[:200]}' is overdue.",
                )
            )
            count += 1
            u = session.get(User, task.assignee_user_id)
            if u:
                try:
                    send_email_task.delay(
                        to_email=u.email,
                        subject="Overdue task reminder",
                        body=f"Your task '{task.title}' is overdue.",
                    )
                except Exception as e:  # noqa: BLE001
                    log.warning("overdue_email_failed: %s", e)
        session.commit()
        return count
    finally:
        session.close()


@celery_app.task(name="app.workers.tasks.cleanup_expired_refresh_tokens")
def cleanup_expired_refresh_tokens() -> int:
    session = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        res = session.execute(
            delete(RefreshToken).where(RefreshToken.expires_at < now, RefreshToken.revoked.is_(True))
        )
        session.commit()
        return int(res.rowcount or 0)
    finally:
        session.close()
