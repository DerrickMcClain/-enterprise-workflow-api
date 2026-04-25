import enum


class WorkspaceRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"


class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TaskStatus(str, enum.Enum):
    BACKLOG = "backlog"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"
    CANCELLED = "cancelled"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
