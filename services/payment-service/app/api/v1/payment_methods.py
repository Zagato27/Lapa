"""
API роуты для управления способами оплаты
"""

import logging
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.payment_method import (
    PaymentMethodCreate,
    PaymentMethodUpdate,
    PaymentMethodResponse,
    PaymentMethodsListResponse,
    PaymentMethodVerificationRequest
)
from app.services.payment_method_service import PaymentMethodService

router = APIRouter()
security = HTTPBearer(auto_error=False)

logger = logging.getLogger(__name__)


async def get_current_user(
    request: Request,
    credentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Зависимость для получения текущего пользователя"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Токен не предоставлен")

    # Здесь должна быть валидация токена через API Gateway
    # Пока что просто возвращаем данные из request
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Неверный токен")

    return {"user_id": user_id}


@router.post("", response_model=PaymentMethodResponse, summary="Создание способа оплаты")
async def create_payment_method(
    payment_method_data: PaymentMethodCreate,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание нового способа оплаты"""
    try:
        payment_method = await PaymentMethodService.create_payment_method(
            db, current_user["user_id"], payment_method_data
        )

        return PaymentMethodService.payment_method_to_response(payment_method)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating payment method: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания способа оплаты")


@router.get("", response_model=PaymentMethodsListResponse, summary="Получение списка способов оплаты")
async def get_payment_methods(
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка способов оплаты пользователя"""
    try:
        payment_methods = await PaymentMethodService.get_user_payment_methods(db, current_user["user_id"])

        # Определение основного способа оплаты
        default_method_id = None
        for pm in payment_methods:
            if pm.is_default:
                default_method_id = pm.id
                break

        return PaymentMethodsListResponse(
            payment_methods=[PaymentMethodService.payment_method_to_response(pm) for pm in payment_methods],
            total=len(payment_methods),
            default_method_id=default_method_id
        )

    except Exception as e:
        logger.error(f"Error getting payment methods: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения способов оплаты")


@router.get("/{payment_method_id}", response_model=PaymentMethodResponse, summary="Получение способа оплаты по ID")
async def get_payment_method(
    payment_method_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение конкретного способа оплаты"""
    try:
        payment_method = await PaymentMethodService.get_payment_method_by_id(
            db, payment_method_id, current_user["user_id"]
        )

        if not payment_method:
            raise HTTPException(status_code=404, detail="Способ оплаты не найден")

        return PaymentMethodService.payment_method_to_response(payment_method)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting payment method {payment_method_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения способа оплаты")


@router.put("/{payment_method_id}", response_model=PaymentMethodResponse, summary="Обновление способа оплаты")
async def update_payment_method(
    payment_method_id: str,
    payment_method_data: PaymentMethodUpdate,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновление способа оплаты"""
    try:
        payment_method = await PaymentMethodService.update_payment_method(
            db, payment_method_id, current_user["user_id"], payment_method_data
        )

        if not payment_method:
            raise HTTPException(status_code=404, detail="Способ оплаты не найден")

        return PaymentMethodService.payment_method_to_response(payment_method)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating payment method {payment_method_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления способа оплаты")


@router.delete("/{payment_method_id}", summary="Удаление способа оплаты")
async def delete_payment_method(
    payment_method_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удаление способа оплаты"""
    try:
        success = await PaymentMethodService.delete_payment_method(
            db, payment_method_id, current_user["user_id"]
        )

        if not success:
            raise HTTPException(status_code=404, detail="Способ оплаты не найден")

        return {"message": "Способ оплаты успешно удален"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting payment method {payment_method_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления способа оплаты")


@router.put("/{payment_method_id}/default", summary="Установка как способ оплаты по умолчанию")
async def set_default_payment_method(
    payment_method_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Установка способа оплаты по умолчанию"""
    try:
        success = await PaymentMethodService.set_as_default(
            db, payment_method_id, current_user["user_id"]
        )

        if not success:
            raise HTTPException(status_code=404, detail="Способ оплаты не найден")

        return {"message": "Способ оплаты установлен по умолчанию"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting default payment method {payment_method_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка установки способа оплаты по умолчанию")


@router.put("/{payment_method_id}/verify", summary="Верификация способа оплаты")
async def verify_payment_method(
    payment_method_id: str,
    verification_data: PaymentMethodVerificationRequest,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Верификация способа оплаты"""
    try:
        success = await PaymentMethodService.verify_payment_method(
            db, payment_method_id, current_user["user_id"], verification_data.verification_code
        )

        if not success:
            raise HTTPException(status_code=400, detail="Неверный код верификации")

        return {"message": "Способ оплаты успешно верифицирован"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying payment method {payment_method_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка верификации способа оплаты")


@router.get("/{payment_method_id}/statistics", summary="Статистика способа оплаты")
async def get_payment_method_statistics(
    payment_method_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение статистики использования способа оплаты"""
    try:
        statistics = await PaymentMethodService.get_payment_method_statistics(
            db, payment_method_id, current_user["user_id"]
        )

        if not statistics:
            raise HTTPException(status_code=404, detail="Способ оплаты не найден")

        return statistics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting payment method statistics {payment_method_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения статистики")
