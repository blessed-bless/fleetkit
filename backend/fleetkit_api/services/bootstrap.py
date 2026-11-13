from __future__ import annotations

import logging

from sqlalchemy import select

from fleetkit_api.config import get_settings
from fleetkit_api.db import SessionLocal
from fleetkit_api.models import Project, User
from fleetkit_api.models_ext import ProjectMember
from fleetkit_api.security import hash_password

logger = logging.getLogger("fleetkit.bootstrap")


async def ensure_bootstrap_admin() -> None:
    settings = get_settings()
    async with SessionLocal() as db:
        result = await db.execute(select(User).where(User.email == settings.bootstrap_email))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(
                email=settings.bootstrap_email,
                password_hash=hash_password(settings.bootstrap_password),
                display_name="Admin",
            )
            db.add(user)
            await db.flush()
            project = Project(
                owner_id=user.id,
                slug="default",
                name="Default",
                description="Автосозданный проект для быстрого старта",
            )
            db.add(project)
            await db.flush()
            db.add(ProjectMember(project_id=project.id, user_id=user.id, role="owner"))
            await db.commit()
            logger.info("Bootstrap admin created: %s / project=default", settings.bootstrap_email)
            return

        result = await db.execute(select(Project).where(Project.owner_id == user.id).limit(1))
        project = result.scalar_one_or_none()
        if project is None:
            project = Project(
                owner_id=user.id,
                slug="default",
                name="Default",
                description="Автосозданный проект для быстрого старта",
            )
            db.add(project)
            await db.flush()
            db.add(ProjectMember(project_id=project.id, user_id=user.id, role="owner"))
            await db.commit()
            logger.info("Bootstrap project created for %s", settings.bootstrap_email)
            return

        member = await db.scalar(
            select(ProjectMember).where(
                ProjectMember.project_id == project.id,
                ProjectMember.user_id == user.id,
            )
        )
        if member is None:
            db.add(ProjectMember(project_id=project.id, user_id=user.id, role="owner"))
            await db.commit()
            logger.info("Bootstrap owner membership backfilled for %s", settings.bootstrap_email)
