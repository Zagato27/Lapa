"""
Основной API роутер для Pet Service v1
"""

from fastapi import APIRouter

from .pets import router as pets_router
from .photos import router as photos_router
from .medical import router as medical_router

# Создаем главный роутер для API v1
api_router = APIRouter()

# Подключаем все роутеры
api_router.include_router(pets_router, prefix="/pets", tags=["pets"])
api_router.include_router(photos_router, prefix="/pets/{pet_id}/photos", tags=["photos"])
api_router.include_router(medical_router, prefix="/pets/{pet_id}/medical", tags=["medical"])
