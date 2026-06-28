from __future__ import annotations

from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select
from sqlalchemy import insert as sa_insert
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base


class BaseRepository[ModelT: Base]:
    def __init__(self, model: type[ModelT]) -> None:
        self.model = model

    async def get_by_id(self, db: AsyncSession, id: int) -> ModelT | None:
        return await db.get(self.model, id)

    async def count(self, db: AsyncSession) -> int:
        stmt = select(func.count()).select_from(self.model)
        result = await db.execute(stmt)
        return result.scalar_one()

    async def get_all(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> list[ModelT]:
        stmt = select(self.model).order_by(self.model.id).offset(skip).limit(limit)  # ty: ignore[unresolved-attribute]
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, data: dict) -> ModelT:
        stmt = sa_insert(self.model).values(**data).returning(self.model)
        result = await db.execute(stmt)
        instance = result.scalar_one()
        await db.flush()
        return instance

    async def update(self, db: AsyncSession, id: int, data: dict) -> ModelT | None:
        stmt = sa_update(self.model).where(self.model.id == id).values(**data).returning(self.model)  # ty: ignore[unresolved-attribute]
        result = await db.execute(stmt)
        instance = result.scalar_one_or_none()
        if instance is None:
            return None
        await db.flush()
        return instance

    async def delete(self, db: AsyncSession, id: int) -> bool:
        stmt = sa_delete(self.model).where(self.model.id == id).returning(self.model.id)  # ty: ignore[unresolved-attribute]
        result = await db.execute(stmt)
        deleted_id = result.scalar_one_or_none()
        if deleted_id is None:
            return False
        await db.flush()
        return True
