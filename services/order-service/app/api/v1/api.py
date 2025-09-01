"""
Основной API роутер для Order Service v1
"""

from fastapi import APIRouter

from .orders import router as orders_router

# Создаем главный роутер для API v1
api_router = APIRouter()

# Подключаем все роутеры
api_router.include_router(orders_router, prefix="/orders", tags=["orders"])
