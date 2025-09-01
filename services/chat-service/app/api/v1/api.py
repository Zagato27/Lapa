"""
Основной API роутер для Chat Service v1
"""

from fastapi import APIRouter

from .chats import router as chats_router
from .messages import router as messages_router
from .files import router as files_router
from .websocket import router as websocket_router

# Создаем главный роутер для API v1
api_router = APIRouter()

# Подключаем все роутеры
api_router.include_router(chats_router, prefix="/chats", tags=["chats"])
api_router.include_router(messages_router, prefix="/messages", tags=["messages"])
api_router.include_router(files_router, prefix="/files", tags=["files"])
api_router.include_router(websocket_router, prefix="/ws", tags=["websocket"])
