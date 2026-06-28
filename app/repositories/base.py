from __future__ import annotations

from typing import TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository[ModelT]:
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
        instance = self.model(**data)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def update(self, db: AsyncSession, id: int, data: dict) -> ModelT | None:
        instance = await self.get_by_id(db, id)
        if instance is None:
            return None
        for key, value in data.items():
            setattr(instance, key, value)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def delete(self, db: AsyncSession, id: int) -> bool:
        instance = await self.get_by_id(db, id)
        if instance is None:
            return False
        await db.delete(instance)
        await db.flush()
        return True
