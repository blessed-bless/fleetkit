import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from fleetkit_api.db import Base
from fleetkit_api.models import Project, User
from fleetkit_api.models_ext import ProjectMember
from fleetkit_api.security import hash_password
from fleetkit_api.security_suite.rbac import Permission, Role, role_allows
from fleetkit_api.services.membership import (
    assert_permission,
    ensure_owner_membership,
    list_accessible_projects,
    parse_assignable_role,
    resolve_project_access,
)


def test_viewer_cannot_reveal_secrets():
    assert role_allows(Role.viewer, Permission.job_read)
    assert not role_allows(Role.viewer, Permission.secret_reveal)
    assert not role_allows(Role.viewer, Permission.member_write)
    assert not role_allows(Role.operator, Permission.secret_reveal)
    assert role_allows(Role.admin, Permission.secret_reveal)
    assert role_allows(Role.admin, Permission.member_write)
    assert role_allows(Role.owner, Permission.import_cfg)


def test_parse_assignable_role_rejects_owner():
    assert parse_assignable_role("viewer") == Role.viewer
    assert parse_assignable_role("admin") == Role.admin
    with pytest.raises(HTTPException) as forbidden:
        parse_assignable_role("owner")
    assert forbidden.value.status_code == 400
    with pytest.raises(HTTPException) as bad:
        parse_assignable_role("superuser")
    assert bad.value.status_code == 400


def test_openapi_exposes_register_and_invite_accept():
    from fleetkit_api.main import create_app

    paths = create_app().openapi()["paths"]
    assert "/api/v1/auth/register" in paths
    assert "/api/v1/invites/{token}/accept" in paths
    assert "/api/v1/projects/{project_id}/members" in paths
    assert "/api/v1/me/invites" in paths


@pytest.mark.asyncio
async def test_resolve_access_owner_and_member():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as db:
        owner = User(
            email="owner@example.com",
            password_hash=hash_password("Str0ng!Pass99"),
            display_name="Owner",
        )
        viewer = User(
            email="viewer@example.com",
            password_hash=hash_password("Str0ng!Pass99"),
            display_name="Viewer",
        )
        stranger = User(
            email="stranger@example.com",
            password_hash=hash_password("Str0ng!Pass99"),
            display_name="Stranger",
        )
        db.add_all([owner, viewer, stranger])
        await db.flush()
        project = Project(owner_id=owner.id, slug="demo", name="Demo", description="")
        db.add(project)
        await db.flush()
        await ensure_owner_membership(db, project_id=project.id, user_id=owner.id)
        db.add(ProjectMember(project_id=project.id, user_id=viewer.id, role=Role.viewer.value))
        await db.commit()

        owner_access = await resolve_project_access(db, project_id=project.id, user=owner)
        assert owner_access.role == Role.owner
        assert_permission(owner_access, Permission.secret_reveal)

        viewer_access = await resolve_project_access(db, project_id=project.id, user=viewer)
        assert viewer_access.role == Role.viewer
        with pytest.raises(HTTPException) as denied:
            assert_permission(viewer_access, Permission.secret_reveal)
        assert denied.value.status_code == 403

        with pytest.raises(HTTPException) as missing:
            await resolve_project_access(db, project_id=project.id, user=stranger)
        assert missing.value.status_code == 404

        owned = await list_accessible_projects(db, owner)
        shared = await list_accessible_projects(db, viewer)
        none = await list_accessible_projects(db, stranger)
        assert len(owned) == 1 and owned[0][1] == Role.owner
        assert len(shared) == 1 and shared[0][1] == Role.viewer
        assert none == []

    await engine.dispose()
