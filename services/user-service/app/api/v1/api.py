"""
Основной API роутер для User Service v1
"""

from fastapi import APIRouter

from .auth import router as auth_router
from .users import router as users_router

# Создаем главный роутер для API v1
api_router = APIRouter()

# Подключаем все роутеры
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
