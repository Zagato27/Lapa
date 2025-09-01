"""
Основной API роутер для Analytics Service v1
"""

from fastapi import APIRouter

from .events import router as events_router
from .metrics import router as metrics_router
from .kpis import router as kpis_router
from .dashboards import router as dashboards_router
from .reports import router as reports_router
from .segments import router as segments_router

# Создаем главный роутер для API v1
api_router = APIRouter()

# Подключаем все роутеры
api_router.include_router(events_router, prefix="/events", tags=["events"])
api_router.include_router(metrics_router, prefix="/metrics", tags=["metrics"])
api_router.include_router(kpis_router, prefix="/kpis", tags=["kpis"])
api_router.include_router(dashboards_router, prefix="/dashboards", tags=["dashboards"])
api_router.include_router(reports_router, prefix="/reports", tags=["reports"])
api_router.include_router(segments_router, prefix="/segments", tags=["segments"])
