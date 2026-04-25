from app.models.enums import WorkspaceRole

# ordering for min-role checks: higher index = more privilege
_ROLE_ORDER: dict[WorkspaceRole, int] = {
    WorkspaceRole.MEMBER: 0,
    WorkspaceRole.MANAGER: 1,
    WorkspaceRole.ADMIN: 2,
}


def role_at_least(actual: WorkspaceRole, minimum: WorkspaceRole) -> bool:
    return _ROLE_ORDER[actual] >= _ROLE_ORDER[minimum]


def can_manage_projects(role: WorkspaceRole) -> bool:
    return role in (WorkspaceRole.MANAGER, WorkspaceRole.ADMIN)


def can_manage_workspace_settings(role: WorkspaceRole) -> bool:
    return role == WorkspaceRole.ADMIN


def can_delete_tasks(role: WorkspaceRole) -> bool:
    return role in (WorkspaceRole.MANAGER, WorkspaceRole.ADMIN)
