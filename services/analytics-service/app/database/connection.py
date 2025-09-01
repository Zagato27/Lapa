"""
Подключение к PostgreSQL и управление асинхронными сессиями SQLAlchemy.

Экспортируемые функции:
- get_db: зависимость FastAPI для выдачи `AsyncSession`
- create_tables: создание таблиц на основе общего `Base`
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models import Base


# Формируем DSN к БД Postgres (asyncpg)
DATABASE_URL = (
    f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}"
    f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
)

engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Выдает асинхронную сессию БД и закрывает ее по завершении запроса."""
    async with SessionLocal() as session:
        yield session


async def create_tables() -> None:
    """Создает все таблицы, зарегистрированные в общем `Base`.

    Вызывать на старте приложения (в lifespan).
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


