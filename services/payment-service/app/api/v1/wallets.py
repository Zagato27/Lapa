"""
API роуты для управления кошельками
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.wallet import (
    WalletResponse,
    WalletOperationRequest,
    WalletDepositRequest,
    WalletWithdrawRequest,
    WalletTransferRequest,
    WalletSettingsUpdate
)
from app.services.wallet_service import WalletService

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


@router.get("", response_model=WalletResponse, summary="Получение кошелька")
async def get_wallet(
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение кошелька пользователя"""
    try:
        wallet = await WalletService.get_wallet(db, current_user["user_id"])

        if not wallet:
            raise HTTPException(status_code=404, detail="Кошелек не найден")

        return WalletService.wallet_to_response(wallet)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting wallet: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения кошелька")


@router.post("/deposit", response_model=WalletResponse, summary="Пополнение кошелька")
async def deposit_wallet(
    deposit_data: WalletDepositRequest,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Пополнение кошелька"""
    try:
        success = await WalletService.deposit(db, current_user["user_id"], deposit_data)

        if not success:
            raise HTTPException(status_code=400, detail="Невозможно пополнить кошелек")

        wallet = await WalletService.get_wallet(db, current_user["user_id"])
        return WalletService.wallet_to_response(wallet)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error depositing to wallet: {e}")
        raise HTTPException(status_code=500, detail="Ошибка пополнения кошелька")


@router.post("/withdraw", response_model=WalletResponse, summary="Снятие с кошелька")
async def withdraw_wallet(
    withdraw_data: WalletWithdrawRequest,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Снятие средств с кошелька"""
    try:
        success = await WalletService.withdraw(db, current_user["user_id"], withdraw_data)

        if not success:
            raise HTTPException(status_code=400, detail="Невозможно снять средства с кошелька")

        wallet = await WalletService.get_wallet(db, current_user["user_id"])
        return WalletService.wallet_to_response(wallet)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error withdrawing from wallet: {e}")
        raise HTTPException(status_code=500, detail="Ошибка снятия с кошелька")


@router.post("/transfer", response_model=WalletResponse, summary="Перевод между кошельками")
async def transfer_wallet(
    transfer_data: WalletTransferRequest,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Перевод средств между кошельками"""
    try:
        success = await WalletService.transfer(db, current_user["user_id"], transfer_data)

        if not success:
            raise HTTPException(status_code=400, detail="Невозможно выполнить перевод")

        wallet = await WalletService.get_wallet(db, current_user["user_id"])
        return WalletService.wallet_to_response(wallet)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error transferring funds: {e}")
        raise HTTPException(status_code=500, detail="Ошибка перевода")


@router.put("/settings", response_model=WalletResponse, summary="Обновление настроек кошелька")
async def update_wallet_settings(
    settings_data: WalletSettingsUpdate,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновление настроек кошелька"""
    try:
        success = await WalletService.update_settings(db, current_user["user_id"], settings_data)

        if not success:
            raise HTTPException(status_code=400, detail="Невозможно обновить настройки кошелька")

        wallet = await WalletService.get_wallet(db, current_user["user_id"])
        return WalletService.wallet_to_response(wallet)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating wallet settings: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления настроек кошелька")


@router.put("/freeze", summary="Заморозка кошелька")
async def freeze_wallet(
    reason: str = Query(..., description="Причина заморозки"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Заморозка кошелька"""
    try:
        success = await WalletService.freeze_wallet(db, current_user["user_id"], reason)

        if not success:
            raise HTTPException(status_code=400, detail="Невозможно заморозить кошелек")

        return {"message": "Кошелек заморожен", "reason": reason}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error freezing wallet: {e}")
        raise HTTPException(status_code=500, detail="Ошибка заморозки кошелька")


@router.put("/unfreeze", summary="Разморозка кошелька")
async def unfreeze_wallet(
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Разморозка кошелька"""
    try:
        success = await WalletService.unfreeze_wallet(db, current_user["user_id"])

        if not success:
            raise HTTPException(status_code=400, detail="Невозможно разморозить кошелек")

        return {"message": "Кошелек разморожен"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unfreezing wallet: {e}")
        raise HTTPException(status_code=500, detail="Ошибка разморозки кошелька")


@router.get("/transactions", summary="Получение истории транзакций")
async def get_wallet_transactions(
    page: int = Query(1, description="Номер страницы"),
    limit: int = Query(20, description="Количество транзакций на странице"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение истории транзакций кошелька"""
    try:
        transactions_data = await WalletService.get_transaction_history(
            db, current_user["user_id"], page, limit
        )

        return transactions_data

    except Exception as e:
        logger.error(f"Error getting wallet transactions: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения истории транзакций")


@router.get("/balance", summary="Получение баланса кошелька")
async def get_wallet_balance(
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение баланса кошелька"""
    try:
        wallet = await WalletService.get_wallet(db, current_user["user_id"])

        if not wallet:
            raise HTTPException(status_code=404, detail="Кошелек не найден")

        return {
            "balance": wallet.balance,
            "bonus_balance": wallet.bonus_balance,
            "available_balance": wallet.available_balance,
            "currency": wallet.currency,
            "is_frozen": wallet.is_frozen
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting wallet balance: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения баланса")
