from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.models import Project, User
from fleetkit_api.models_ext import ProjectMember
from fleetkit_api.security_suite.rbac import Permission, Role, role_allows


@dataclass(slots=True)
class ProjectAccess:
    project: Project
    role: Role
    user: User


async def ensure_owner_membership(
    db: AsyncSession, *, project_id: str, user_id: str
) -> ProjectMember:
    """Idempotent: owner row in project_members for bootstrap/create_project."""
    existing = await db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )
    if existing is not None:
        if existing.role != Role.owner:
            existing.role = Role.owner
        return existing
    row = ProjectMember(project_id=project_id, user_id=user_id, role=Role.owner)
    db.add(row)
    return row


async def backfill_owner_memberships(db: AsyncSession) -> int:
    """Ensure every Project.owner_id has a matching ProjectMember(owner)."""
    projects = (await db.execute(select(Project))).scalars().all()
    created = 0
    for project in projects:
        before = await db.scalar(
            select(ProjectMember.id).where(
                ProjectMember.project_id == project.id,
                ProjectMember.user_id == project.owner_id,
            )
        )
        await ensure_owner_membership(db, project_id=project.id, user_id=project.owner_id)
        if before is None:
            created += 1
    return created


async def resolve_project_access(
    db: AsyncSession, *, project_id: str, user: User
) -> ProjectAccess:
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Проект не найден")

    if project.owner_id == user.id:
        return ProjectAccess(project=project, role=Role.owner, user=user)

    member = await db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.id,
        )
    )
    if member is None:
        raise HTTPException(status_code=404, detail="Проект не найден")

    try:
        role = Role(member.role)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Неизвестная роль участника: {member.role}",
        ) from exc
    return ProjectAccess(project=project, role=role, user=user)


def assert_permission(access: ProjectAccess, permission: Permission) -> None:
    if not role_allows(access.role, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Недостаточно прав: нужно {permission.value}",
        )


async def list_accessible_projects(db: AsyncSession, user: User) -> list[tuple[Project, Role]]:
    owned = (
        await db.execute(select(Project).where(Project.owner_id == user.id))
    ).scalars().all()
    member_rows = (
        await db.execute(
            select(Project, ProjectMember.role)
            .join(ProjectMember, ProjectMember.project_id == Project.id)
            .where(ProjectMember.user_id == user.id)
        )
    ).all()

    by_id: dict[str, tuple[Project, Role]] = {}
    for project in owned:
        by_id[project.id] = (project, Role.owner)
    for project, role_raw in member_rows:
        if project.id in by_id and by_id[project.id][1] == Role.owner:
            continue
        try:
            role = Role(role_raw)
        except ValueError:
            role = Role.viewer
        # Owner flag on Project wins over a stale member row.
        if project.owner_id == user.id:
            role = Role.owner
        by_id[project.id] = (project, role)

    items = list(by_id.values())
    items.sort(key=lambda pair: pair[0].created_at or pair[0].name, reverse=True)
    return items


async def accessible_project_ids(db: AsyncSession, user: User) -> list[str]:
    rows = await list_accessible_projects(db, user)
    return [project.id for project, _ in rows]


def parse_assignable_role(raw: str) -> Role:
    try:
        role = Role(raw)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="Роль должна быть admin, operator или viewer",
        ) from exc
    if role == Role.owner:
        raise HTTPException(
            status_code=400,
            detail="Нельзя пригласить с ролью owner — передай владение отдельно",
        )
    return role
