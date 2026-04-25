from app.core.exceptions import ValidationError
from app.models.enums import ProjectStatus


def validate_project_status_transition(
    before: ProjectStatus, after: ProjectStatus
) -> None:
    if before == after:
        return
    # Completed and archived are terminal
    if before in (ProjectStatus.COMPLETED, ProjectStatus.ARCHIVED) and after != before:
        raise ValidationError("Cannot change status of a completed or archived project")
    # Allowed: ACTIVE <-> ON_HOLD, -> COMPLETED, -> ARCHIVED
    allowed: dict[ProjectStatus, set[ProjectStatus]] = {
        ProjectStatus.ACTIVE: {ProjectStatus.ON_HOLD, ProjectStatus.COMPLETED, ProjectStatus.ARCHIVED},
        ProjectStatus.ON_HOLD: {ProjectStatus.ACTIVE, ProjectStatus.ARCHIVED},
        ProjectStatus.COMPLETED: set(),
        ProjectStatus.ARCHIVED: {ProjectStatus.ACTIVE},  # re-open
    }
    if after not in allowed.get(before, set()):
        raise ValidationError(
            f"Invalid project status transition from {before.value} to {after.value}"
        )
