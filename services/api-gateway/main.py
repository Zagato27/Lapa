"""
API Gateway Service - единая точка входа для платформы Lapa
Маршрутизация, аутентификация, безопасность, мониторинг
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from prometheus_client import make_asgi_app
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.database import init_cache
from app.services.gateway_service import GatewayService
from app.services.auth_service import AuthService
from app.services.monitoring_service import MonitoringService
from app.api.v1.api import api_router
from app.middleware.auth import AuthMiddleware
# Пользовательские middleware отсутствуют (оставляем стандартные FastAPI/SlowAPI)


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
        structlog.stdlib.add_logger_name,
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
    """Управление жизненным циклом приложения"""
    logger.info("Starting API Gateway Service...")

    # Инициализация кэша
    await init_cache()

    # Инициализация сервисов
    app.state.gateway_service = GatewayService()
    app.state.auth_service = AuthService()
    app.state.monitoring_service = MonitoringService()

    # Запуск фоновых задач
    asyncio.create_task(start_background_tasks(app))

    logger.info("API Gateway Service started successfully")

    yield

    logger.info("API Gateway Service shutting down...")


async def start_background_tasks(app: FastAPI):
    """Запуск фоновых задач"""
    try:
        # Запуск мониторинга здоровья сервисов
        monitoring_service = app.state.monitoring_service
        asyncio.create_task(monitoring_service.start_health_checks())

        # Запуск очистки кэша
        asyncio.create_task(clean_cache_periodically())

        # Запуск обновления конфигурации маршрутизации
        gateway_service = app.state.gateway_service
        asyncio.create_task(gateway_service.start_route_updates())

    except Exception as e:
        logger.error(f"Error starting background tasks: {e}")


async def clean_cache_periodically():
    """Периодическая очистка кэша"""
    while True:
        try:
            # Здесь должна быть логика очистки устаревшего кэша
            await asyncio.sleep(3600)  # Каждые 60 минут
        except Exception as e:
            logger.error(f"Error cleaning cache: {e}")


def create_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Обработчик превышения лимита запросов"""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Too Many Requests",
            "message": f"Rate limit exceeded: {exc.detail}",
            "retry_after": exc.retry_after
        }
    )


def create_application() -> FastAPI:
    """Создание FastAPI приложения"""
    app = FastAPI(
        title="Lapa API Gateway",
        description="Единая точка входа для платформы Lapa - маршрутизация, аутентификация, безопасность",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Настройка rate limiting
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter

    # Middleware для обработки ошибок rate limiting
    app.add_exception_handler(RateLimitExceeded, create_rate_limit_exceeded_handler)

    # Пользовательские middleware (минимальная конфигурация)
    app.add_middleware(AuthMiddleware)
    app.add_middleware(SlowAPIMiddleware)

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Trusted host middleware
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)

    # Метрики Prometheus
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    # API роуты
    app.include_router(api_router, prefix="/api/v1")

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Проверка здоровья API Gateway"""
        return {"status": "healthy", "service": "api-gateway"}

    # Root endpoint
    @app.get("/")
    async def root():
        """Корневой endpoint"""
        return {
            "message": "Welcome to Lapa API Gateway",
            "version": "1.0.0",
            "docs": "/docs",
            "services": {
                "user": "/api/v1/user",
                "pet": "/api/v1/pet",
                "order": "/api/v1/order",
                "location": "/api/v1/location",
                "payment": "/api/v1/payment",
                "chat": "/api/v1/chat",
                "media": "/api/v1/media",
                "notification": "/api/v1/notification",
                "analytics": "/api/v1/analytics"
            }
        }

    # Service discovery endpoint
    @app.get("/services")
    async def list_services():
        """Список доступных сервисов"""
        gateway_service = app.state.gateway_service
        services = await gateway_service.get_service_registry()
        return {"services": services}

    # API Gateway statistics
    @app.get("/stats")
    async def gateway_stats():
        """Статистика API Gateway"""
        monitoring_service = app.state.monitoring_service
        stats = await monitoring_service.get_gateway_stats()
        return stats

    return app


app = create_application()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )