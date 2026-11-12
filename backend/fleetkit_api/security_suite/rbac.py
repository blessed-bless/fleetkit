from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    owner = "owner"
    admin = "admin"
    operator = "operator"
    viewer = "viewer"


class Permission(StrEnum):
    project_read = "project.read"
    project_write = "project.write"
    app_write = "app.write"
    job_enqueue = "job.enqueue"
    job_read = "job.read"
    worker_read = "worker.read"
    secret_read = "secret.read"
    secret_write = "secret.write"
    secret_reveal = "secret.reveal"
    alert_write = "alert.write"
    audit_read = "audit.read"
    member_write = "member.write"
    export = "export"
    import_cfg = "import"


_ROLE_PERMS: dict[Role, set[Permission]] = {
    Role.viewer: {
        Permission.project_read,
        Permission.job_read,
        Permission.worker_read,
        Permission.audit_read,
    },
    Role.operator: set(),  # filled below
    Role.admin: set(),
    Role.owner: set(Permission),
}

_ROLE_PERMS[Role.operator] = _ROLE_PERMS[Role.viewer] | {
    Permission.job_enqueue,
    Permission.app_write,
    Permission.alert_write,
    Permission.export,
}

_ROLE_PERMS[Role.admin] = _ROLE_PERMS[Role.operator] | {
    Permission.project_write,
    Permission.secret_read,
    Permission.secret_write,
    Permission.secret_reveal,
    Permission.member_write,
    Permission.import_cfg,
}


def role_allows(role: str | Role, permission: Permission) -> bool:
    try:
        role_e = Role(role)
    except ValueError:
        return False
    return permission in _ROLE_PERMS.get(role_e, set())


def require_role(role: str | Role, permission: Permission) -> None:
    if not role_allows(role, permission):
        raise PermissionError(f"role {role} missing {permission}")
