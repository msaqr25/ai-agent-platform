from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


def ensure_db_dir(database_url: str) -> None:
    if database_url.startswith("sqlite"):
        path = database_url.removeprefix("sqlite+aiosqlite:///")
        Path(path).parent.mkdir(parents=True, exist_ok=True)


ensure_db_dir(settings.DATABASE_URL)

engine = create_async_engine(
    settings.DATABASE_URL,
)

AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # Commit on success, rollback on any exception
            await session.commit()
        except Exception:
            await session.rollback()
            raise


GetDB = Annotated[AsyncSession, Depends(get_db)]
