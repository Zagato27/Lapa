"""
Основной API роутер для Media Service v1
"""

from fastapi import APIRouter

from .files import router as files_router
from .albums import router as albums_router
from .processing import router as processing_router
from .access import router as access_router

# Создаем главный роутер для API v1
api_router = APIRouter()

# Подключаем все роутеры
api_router.include_router(files_router, prefix="/files", tags=["files"])
api_router.include_router(albums_router, prefix="/albums", tags=["albums"])
api_router.include_router(processing_router, prefix="/processing", tags=["processing"])
api_router.include_router(access_router, prefix="/access", tags=["access"])
