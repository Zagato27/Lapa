"""
API роуты для управления выплатами
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.payout import (
    PayoutCreate,
    PayoutUpdate,
    PayoutResponse,
    PayoutProcessRequest
)
from app.services.payout_service import PayoutService

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


@router.post("", response_model=PayoutResponse, summary="Создание выплаты")
async def create_payout(
    payout_data: PayoutCreate,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание новой выплаты"""
    try:
        payout = await PayoutService.create_payout(db, current_user["user_id"], payout_data)

        return PayoutService.payout_to_response(payout)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating payout: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания выплаты")


@router.get("", summary="Получение списка выплат")
async def get_payouts(
    status: str = Query(None, description="Фильтр по статусу"),
    page: int = Query(1, description="Номер страницы"),
    limit: int = Query(20, description="Количество выплат на странице"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка выплат пользователя"""
    try:
        payouts_data = await PayoutService.get_user_payouts(
            db, current_user["user_id"], page, limit, status
        )

        return payouts_data

    except Exception as e:
        logger.error(f"Error getting payouts list: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения списка выплат")


@router.get("/{payout_id}", response_model=PayoutResponse, summary="Получение выплаты по ID")
async def get_payout(
    payout_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение информации о конкретной выплате"""
    try:
        payout = await PayoutService.get_payout_by_id(db, payout_id, current_user["user_id"])

        if not payout:
            raise HTTPException(status_code=404, detail="Выплата не найдена")

        return PayoutService.payout_to_response(payout)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting payout {payout_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения выплаты")


@router.put("/{payout_id}/process", response_model=PayoutResponse, summary="Обработка выплаты")
async def process_payout(
    payout_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обработка выплаты"""
    try:
        success = await PayoutService.process_payout(db, payout_id, current_user["user_id"])

        if not success:
            raise HTTPException(status_code=400, detail="Невозможно обработать выплату")

        payout = await PayoutService.get_payout_by_id(db, payout_id, current_user["user_id"])
        return PayoutService.payout_to_response(payout)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing payout {payout_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обработки выплаты")


@router.put("/{payout_id}/cancel", summary="Отмена выплаты")
async def cancel_payout(
    payout_id: str,
    reason: str = Query(..., description="Причина отмены"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Отмена выплаты"""
    try:
        success = await PayoutService.cancel_payout(db, payout_id, current_user["user_id"], reason)

        if not success:
            raise HTTPException(status_code=400, detail="Невозможно отменить выплату")

        return {"message": "Выплата успешно отменена"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling payout {payout_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка отмены выплаты")


@router.get("/earnings/calculate", summary="Расчет заработка")
async def calculate_earnings(
    start_date: str = Query(..., description="Дата начала периода (YYYY-MM-DD)"),
    end_date: str = Query(..., description="Дата окончания периода (YYYY-MM-DD)"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Расчет заработка пользователя за период"""
    try:
        from datetime import datetime
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)

        earnings = await PayoutService.calculate_earnings(db, current_user["user_id"], start, end)

        return earnings

    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат даты")
    except Exception as e:
        logger.error(f"Error calculating earnings: {e}")
        raise HTTPException(status_code=500, detail="Ошибка расчета заработка")


@router.post("/auto/create", summary="Создание автоматических выплат")
async def create_automatic_payouts(
    db: AsyncSession = Depends(get_db)
):
    """Создание автоматических выплат для всех подходящих пользователей"""
    try:
        payouts = await PayoutService.create_automatic_payouts(db)

        return {
            "message": f"Создано {len(payouts)} автоматических выплат",
            "payouts": [PayoutService.payout_to_response(payout) for payout in payouts]
        }

    except Exception as e:
        logger.error(f"Error creating automatic payouts: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания автоматических выплат")


@router.put("/{payout_id}", response_model=PayoutResponse, summary="Обновление выплаты")
async def update_payout(
    payout_id: str,
    payout_data: PayoutUpdate,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновление параметров выплаты"""
    try:
        # Получение текущей выплаты
        payout = await PayoutService.get_payout_by_id(db, payout_id, current_user["user_id"])

        if not payout:
            raise HTTPException(status_code=404, detail="Выплата не найдена")

        if payout.status not in ["pending", "on_hold"]:
            raise HTTPException(status_code=400, detail="Невозможно обновить выплату в текущем статусе")

        # Обновление полей
        update_data = payout_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(payout, field, value)

        payout.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(payout)

        return PayoutService.payout_to_response(payout)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating payout {payout_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления выплаты")
