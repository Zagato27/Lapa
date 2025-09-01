"""
Основной API роутер для Location Service v1
"""

from fastapi import APIRouter

from .locations import router as locations_router
from .geofences import router as geofences_router
from .tracking import router as tracking_router
from .websocket import router as websocket_router

# Создаем главный роутер для API v1
api_router = APIRouter()

# Подключаем все роутеры
api_router.include_router(locations_router, prefix="/locations", tags=["locations"])
api_router.include_router(geofences_router, prefix="/geofences", tags=["geofences"])
api_router.include_router(tracking_router, prefix="/tracking", tags=["tracking"])
api_router.include_router(websocket_router, prefix="/ws", tags=["websocket"])
