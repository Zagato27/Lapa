"""
Основной API роутер для Notification Service v1
"""

from fastapi import APIRouter

from .notifications import router as notifications_router
from .templates import router as templates_router
from .subscriptions import router as subscriptions_router
from .campaigns import router as campaigns_router

# Создаем главный роутер для API v1
api_router = APIRouter()

# Подключаем все роутеры
api_router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
api_router.include_router(templates_router, prefix="/templates", tags=["templates"])
api_router.include_router(subscriptions_router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(campaigns_router, prefix="/campaigns", tags=["campaigns"])