from datetime import datetime, timezone

from app.models.enums import TaskStatus
from app.models import Task


def apply_task_status_side_effects(task: Task) -> None:
    now = datetime.now(timezone.utc)
    if task.status == TaskStatus.DONE and task.completed_at is None:
        task.completed_at = now
    elif task.status != TaskStatus.DONE:
        task.completed_at = None


def is_overdue(task: Task) -> bool:
    if task.due_at is None or task.deleted_at is not None:
        return False
    if task.status == TaskStatus.DONE:
        return False
    return task.due_at < datetime.now(timezone.utc)
