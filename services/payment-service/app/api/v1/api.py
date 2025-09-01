"""
Основной API роутер для Payment Service v1
"""

from fastapi import APIRouter

from .payments import router as payments_router
from .wallets import router as wallets_router
from .payment_methods import router as payment_methods_router
from .payouts import router as payouts_router

# Создаем главный роутер для API v1
api_router = APIRouter()

# Подключаем все роутеры
api_router.include_router(payments_router, prefix="/payments", tags=["payments"])
api_router.include_router(wallets_router, prefix="/wallets", tags=["wallets"])
api_router.include_router(payment_methods_router, prefix="/payment-methods", tags=["payment_methods"])
api_router.include_router(payouts_router, prefix="/payouts", tags=["payouts"])
