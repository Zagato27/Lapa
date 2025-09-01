"""
Инициализация кэша (Redis) для API Gateway и экспорт утилит.

Экспортируемые элементы:
- init_cache: асинхронная инициализация глобального Redis-клиента
- get_db: заглушка зависимость БД (шлюз не использует БД напрямую)
- redis_client: общий экземпляр Redis-клиента
"""

from typing import AsyncGenerator, Optional

from redis import asyncio as aioredis

from app.config import settings


redis_client: Optional[aioredis.Redis] = None


async def init_cache() -> None:
    """Инициализирует глобальный Redis-клиент для кэширования/лимитов.

    Вызывается из lifespan в `main.py`.
    """
    global redis_client
    if redis_client is not None:
        return

    redis_client = aioredis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password,
        encoding="utf-8",
        decode_responses=True,
    )

    # Легкая проверка доступности
    try:
        await redis_client.ping()
    except Exception:
        # Продолжаем без Redis, если он недоступен (шлюз продолжит работу)
        redis_client = None


async def get_db() -> AsyncGenerator[None, None]:
    """Заглушка зависимости БД (для единообразия с другими сервисами)."""
    yield None


