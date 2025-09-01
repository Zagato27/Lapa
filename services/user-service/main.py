"""
User Service - микросервис управления пользователями.

Назначение:
- Регистрация и аутентификация
- Управление профилями
- Поиск выгульщиков рядом

Файл инициализирует FastAPI-приложение, middleware, роуты и метрики.
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from prometheus_client import make_asgi_app

from app.config import settings
from app.database import create_tables
from app.api.v1.api import api_router


# Настройка структурированного логирования
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=logging.INFO,
)

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Управление жизненным циклом приложения (инициализация/завершение)."""
    logger.info("Starting User Service...")

    # Создание таблиц базы данных
    await create_tables()

    logger.info("User Service started successfully")

    yield

    logger.info("User Service shutting down...")


def create_application() -> FastAPI:
    """Создание FastAPI приложения и настройка middleware/роутов."""
    app = FastAPI(
        title="Lapa User Service",
        description="Микросервис управления пользователями платформы Lapa",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)

    # Метрики Prometheus
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    # API роуты
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health")
    async def health_check():
        """Проверка здоровья сервиса"""
        return {"status": "healthy", "service": "user-service"}

    @app.get("/")
    async def root():
        """Корневой endpoint"""
        return {
            "message": "Welcome to Lapa User Service",
            "version": "1.0.0",
            "docs": "/docs"
        }

    return app


app = create_application()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
