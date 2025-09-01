"""
API роуты для управления платежами
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.payment import (
    PaymentCreate,
    PaymentResponse,
    PaymentsListResponse,
    PaymentRefundRequest,
    PaymentEstimateRequest,
    PaymentEstimateResponse,
    PaymentConfirmationRequest,
    PaymentCancelRequest
)
from app.services.payment_service import PaymentService

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


@router.post("", response_model=PaymentResponse, summary="Создание платежа")
async def create_payment(
    payment_data: PaymentCreate,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание нового платежа"""
    try:
        payment = await PaymentService.create_payment(db, current_user["user_id"], payment_data)

        return PaymentService.payment_to_response(payment)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating payment: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания платежа")


@router.get("", response_model=PaymentsListResponse, summary="Получение списка платежей")
async def get_payments(
    status: str = Query(None, description="Фильтр по статусу"),
    payment_type: str = Query(None, description="Фильтр по типу платежа"),
    page: int = Query(1, description="Номер страницы"),
    limit: int = Query(20, description="Количество платежей на странице"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка платежей пользователя"""
    try:
        payments_response = await PaymentService.get_payments_list(
            db, current_user["user_id"], page, limit, status, payment_type
        )

        return payments_response

    except Exception as e:
        logger.error(f"Error getting payments list: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения списка платежей")


@router.get("/{payment_id}", response_model=PaymentResponse, summary="Получение платежа по ID")
async def get_payment(
    payment_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение информации о конкретном платеже"""
    try:
        payment = await PaymentService.get_payment_by_id(db, payment_id, current_user["user_id"])

        if not payment:
            raise HTTPException(status_code=404, detail="Платеж не найден")

        return PaymentService.payment_to_response(payment)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting payment {payment_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения платежа")


@router.put("/{payment_id}/confirm", response_model=PaymentResponse, summary="Подтверждение платежа")
async def confirm_payment(
    payment_id: str,
    confirmation_data: PaymentConfirmationRequest = None,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Подтверждение платежа"""
    try:
        payment_data = confirmation_data.dict() if confirmation_data else None
        success = await PaymentService.process_payment(db, payment_id, current_user["user_id"], payment_data)

        if not success:
            raise HTTPException(status_code=400, detail="Невозможно подтвердить платеж")

        payment = await PaymentService.get_payment_by_id(db, payment_id, current_user["user_id"])
        return PaymentService.payment_to_response(payment)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming payment {payment_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка подтверждения платежа")


@router.put("/{payment_id}/cancel", response_model=PaymentResponse, summary="Отмена платежа")
async def cancel_payment(
    payment_id: str,
    cancel_data: PaymentCancelRequest = None,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Отмена платежа"""
    try:
        reason = cancel_data.reason if cancel_data else None
        success = await PaymentService.cancel_payment(db, payment_id, current_user["user_id"], reason)

        if not success:
            raise HTTPException(status_code=400, detail="Невозможно отменить платеж")

        payment = await PaymentService.get_payment_by_id(db, payment_id, current_user["user_id"])
        return PaymentService.payment_to_response(payment)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling payment {payment_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка отмены платежа")


@router.put("/{payment_id}/refund", response_model=PaymentResponse, summary="Возврат платежа")
async def refund_payment(
    payment_id: str,
    refund_data: PaymentRefundRequest,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Возврат платежа"""
    try:
        success = await PaymentService.refund_payment(
            db, payment_id, current_user["user_id"], refund_data
        )

        if not success:
            raise HTTPException(status_code=400, detail="Невозможно вернуть платеж")

        payment = await PaymentService.get_payment_by_id(db, payment_id, current_user["user_id"])
        return PaymentService.payment_to_response(payment)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refunding payment {payment_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка возврата платежа")


@router.post("/estimate", response_model=PaymentEstimateResponse, summary="Расчет стоимости платежа")
async def estimate_payment(
    estimate_data: PaymentEstimateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Расчет стоимости платежа с учетом комиссий"""
    try:
        estimate = await PaymentService.estimate_payment(db, estimate_data)

        return estimate

    except Exception as e:
        logger.error(f"Error estimating payment: {e}")
        raise HTTPException(status_code=500, detail="Ошибка расчета стоимости")


@router.get("/{payment_id}/status", summary="Получение статуса платежа")
async def get_payment_status(
    payment_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение статуса платежа"""
    try:
        payment = await PaymentService.get_payment_by_id(db, payment_id, current_user["user_id"])

        if not payment:
            raise HTTPException(status_code=404, detail="Платеж не найден")

        return {
            "payment_id": payment_id,
            "status": payment.status.value,
            "is_completed": payment.is_completed,
            "is_pending": payment.is_pending,
            "is_failed": payment.is_failed,
            "can_be_refunded": payment.can_be_refunded,
            "refundable_amount": payment.refundable_amount
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting payment status {payment_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения статуса платежа")


@router.post("/webhook/{provider}", summary="Webhook для платежных провайдеров")
async def payment_webhook(
    provider: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Webhook endpoint для обработки уведомлений от платежных провайдеров"""
    try:
        # Получение данных webhook
        body = await request.body()
        payload = body.decode()

        # Получение подписи
        signature = request.headers.get("X-Signature", "")

        # Получение менеджера платежных провайдеров
        from app.services.payment_provider import PaymentProviderManager
        payment_provider = PaymentProviderManager()

        # Определение провайдера
        provider_enum = None
        for p in ["stripe", "yookassa", "tinkoff"]:
            if provider.lower() == p:
                from app.models.payment import PaymentProvider
                provider_enum = getattr(PaymentProvider, p.upper())
                break

        if not provider_enum:
            raise HTTPException(status_code=400, detail="Неизвестный провайдер")

        # Проверка подписи
        if not payment_provider.verify_webhook(provider_enum, payload, signature):
            raise HTTPException(status_code=401, detail="Неверная подпись webhook")

        # Обработка webhook
        import json
        webhook_data = json.loads(payload)

        # Поиск платежа
        provider_payment_id = webhook_data.get("id") or webhook_data.get("payment_id")
        if not provider_payment_id:
            raise HTTPException(status_code=400, detail="Не найден ID платежа")

        # Поиск платежа в базе данных
        from app.models.payment import Payment
        payment_query = db.execute(
            select(Payment).where(Payment.provider_payment_id == provider_payment_id)
        )
        payment_result = await payment_query
        payment = payment_result.scalar_one_or_none()

        if not payment:
            logger.warning(f"Payment not found for provider payment ID: {provider_payment_id}")
            return {"status": "ok"}

        # Обновление статуса платежа
        new_status = webhook_data.get("status", "").lower()

        if new_status == "succeeded" or new_status == "completed":
            payment.mark_as_paid(provider_payment_id)
        elif new_status == "failed" or new_status == "error":
            payment.mark_as_failed("Payment failed via webhook")
        elif new_status == "cancelled":
            payment.mark_as_cancelled("Cancelled via webhook")

        await db.commit()

        logger.info(f"Webhook processed for payment {payment.id}: {new_status}")
        return {"status": "ok"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обработки webhook")
