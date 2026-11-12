from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.crypto_box import decrypt_text, encrypt_text
from fleetkit_api.models_ext import SecretRecord


async def upsert_secret(
    db: AsyncSession,
    *,
    project_id: str,
    name: str,
    value: str,
    description: str = "",
) -> SecretRecord:
    result = await db.execute(
        select(SecretRecord).where(SecretRecord.project_id == project_id, SecretRecord.name == name)
    )
    row = result.scalar_one_or_none()
    blob, nonce = encrypt_text(value)
    if row is None:
        row = SecretRecord(
            project_id=project_id,
            name=name,
            ciphertext=blob,
            nonce=nonce,
            description=description,
        )
        db.add(row)
    else:
        row.ciphertext = blob
        row.nonce = nonce
        row.description = description
        row.updated_at = datetime.now(UTC)
    await db.flush()
    return row


async def read_secret(db: AsyncSession, *, project_id: str, name: str) -> str:
    result = await db.execute(
        select(SecretRecord).where(SecretRecord.project_id == project_id, SecretRecord.name == name)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise KeyError(name)
    return decrypt_text(row.ciphertext, row.nonce)


async def list_secrets(db: AsyncSession, *, project_id: str) -> list[SecretRecord]:
    result = await db.execute(
        select(SecretRecord)
        .where(SecretRecord.project_id == project_id)
        .order_by(SecretRecord.name.asc())
    )
    return list(result.scalars().all())
