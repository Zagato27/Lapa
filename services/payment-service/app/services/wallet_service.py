"""
Сервис для управления кошельками
"""

import logging
import uuid
from typing import List, Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func

from app.config import settings
from app.database.session import get_session
from app.models.wallet import Wallet
from app.models.transaction import Transaction
from app.schemas.wallet import (
    WalletResponse,
    WalletOperationRequest,
    WalletDepositRequest,
    WalletWithdrawRequest,
    WalletTransferRequest,
    WalletSettingsUpdate
)

logger = logging.getLogger(__name__)


class WalletService:
    """Сервис для работы с кошельками"""

    @staticmethod
    async def create_wallet(db: AsyncSession, user_id: str) -> Wallet:
        """Создание кошелька для пользователя"""
        try:
            wallet_id = str(uuid.uuid4())

            wallet = Wallet(
                id=wallet_id,
                user_id=user_id,
                balance=0,
                currency=settings.default_currency,
                min_balance=settings.wallet_min_balance,
                max_balance=settings.wallet_max_balance
            )

            db.add(wallet)
            await db.commit()
            await db.refresh(wallet)

            logger.info(f"Wallet created for user {user_id}")
            return wallet

        except Exception as e:
            logger.error(f"Wallet creation failed: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def get_wallet(db: AsyncSession, user_id: str) -> Optional[Wallet]:
        """Получение кошелька пользователя"""
        try:
            # Проверка кэша
            redis_session = await get_session()
            cached_wallet = await redis_session.get_cached_wallet(user_id)

            if cached_wallet:
                return Wallet(**cached_wallet)

            # Получение из базы данных
            query = select(Wallet).where(Wallet.user_id == user_id)
            result = await db.execute(query)
            wallet = result.scalar_one_or_none()

            if wallet:
                # Кэширование
                wallet_data = WalletService.wallet_to_dict(wallet)
                await redis_session.cache_wallet(user_id, wallet_data)

            return wallet

        except Exception as e:
            logger.error(f"Error getting wallet for user {user_id}: {e}")
            return None

    @staticmethod
    async def get_or_create_wallet(db: AsyncSession, user_id: str) -> Wallet:
        """Получение кошелька или его создание"""
        wallet = await WalletService.get_wallet(db, user_id)
        if not wallet:
            wallet = await WalletService.create_wallet(db, user_id)
        return wallet

    @staticmethod
    async def deposit(
        db: AsyncSession,
        user_id: str,
        deposit_data: WalletDepositRequest
    ) -> bool:
        """Пополнение кошелька"""
        try:
            wallet = await WalletService.get_or_create_wallet(db, user_id)

            if wallet.is_frozen:
                raise ValueError("Wallet is frozen")

            success = wallet.deposit(deposit_data.amount, deposit_data.description)

            if success:
                # Создание транзакции
                await WalletService._create_transaction(
                    db, wallet, "deposit", deposit_data.amount, deposit_data.description
                )

                await db.commit()

                # Инвалидация кэша
                redis_session = await get_session()
                await redis_session.invalidate_wallet_cache(user_id)

                logger.info(f"Deposit {deposit_data.amount} to wallet {wallet.id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error depositing to wallet: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def withdraw(
        db: AsyncSession,
        user_id: str,
        withdraw_data: WalletWithdrawRequest
    ) -> bool:
        """Снятие средств с кошелька"""
        try:
            wallet = await WalletService.get_wallet(db, user_id)
            if not wallet:
                raise ValueError("Wallet not found")

            if wallet.is_frozen:
                raise ValueError("Wallet is frozen")

            # Проверка дневного лимита
            redis_session = await get_session()
            daily_spent = await redis_session.get_daily_limit(user_id)

            if wallet.daily_limit and daily_spent + withdraw_data.amount > wallet.daily_limit:
                raise ValueError("Daily limit exceeded")

            success = wallet.withdraw(withdraw_data.amount, withdraw_data.description)

            if success:
                # Создание транзакции
                await WalletService._create_transaction(
                    db, wallet, "withdrawal", -withdraw_data.amount, withdraw_data.description
                )

                # Обновление дневного лимита
                await redis_session.increment_daily_limit(user_id, withdraw_data.amount)

                await db.commit()

                # Инвалидация кэша
                await redis_session.invalidate_wallet_cache(user_id)

                logger.info(f"Withdrawal {withdraw_data.amount} from wallet {wallet.id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error withdrawing from wallet: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def transfer(
        db: AsyncSession,
        from_user_id: str,
        transfer_data: WalletTransferRequest
    ) -> bool:
        """Перевод средств между кошельками"""
        try:
            # Получение кошельков
            from_wallet = await WalletService.get_wallet(db, from_user_id)
            to_wallet = await WalletService.get_or_create_wallet(db, transfer_data.recipient_id)

            if not from_wallet:
                raise ValueError("Sender wallet not found")

            if from_wallet.is_frozen:
                raise ValueError("Sender wallet is frozen")

            if to_wallet.is_frozen:
                raise ValueError("Recipient wallet is frozen")

            # Проверка баланса
            if not from_wallet.can_afford(transfer_data.amount):
                raise ValueError("Insufficient funds")

            # Выполнение перевода
            success = (
                from_wallet.withdraw(transfer_data.amount, transfer_data.description) and
                to_wallet.deposit(transfer_data.amount, transfer_data.description)
            )

            if success:
                # Создание транзакций
                await WalletService._create_transaction(
                    db, from_wallet, "transfer", -transfer_data.amount,
                    f"Transfer to {transfer_data.recipient_id}: {transfer_data.description}"
                )

                await WalletService._create_transaction(
                    db, to_wallet, "transfer", transfer_data.amount,
                    f"Transfer from {from_user_id}: {transfer_data.description}"
                )

                await db.commit()

                # Инвалидация кэша
                redis_session = await get_session()
                await redis_session.invalidate_wallet_cache(from_user_id)
                await redis_session.invalidate_wallet_cache(transfer_data.recipient_id)

                logger.info(f"Transfer {transfer_data.amount} from {from_user_id} to {transfer_data.recipient_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error transferring funds: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def update_settings(
        db: AsyncSession,
        user_id: str,
        settings_data: WalletSettingsUpdate
    ) -> bool:
        """Обновление настроек кошелька"""
        try:
            wallet = await WalletService.get_wallet(db, user_id)
            if not wallet:
                raise ValueError("Wallet not found")

            update_data = settings_data.dict(exclude_unset=True)

            if not update_data:
                return True

            stmt = (
                update(Wallet)
                .where(Wallet.user_id == user_id)
                .values(**update_data, updated_at=datetime.utcnow())
            )

            result = await db.execute(stmt)
            await db.commit()

            if result.rowcount > 0:
                # Инвалидация кэша
                redis_session = await get_session()
                await redis_session.invalidate_wallet_cache(user_id)

                logger.info(f"Wallet settings updated for user {user_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error updating wallet settings: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def freeze_wallet(db: AsyncSession, user_id: str, reason: Optional[str] = None) -> bool:
        """Заморозка кошелька"""
        try:
            wallet = await WalletService.get_wallet(db, user_id)
            if not wallet:
                raise ValueError("Wallet not found")

            wallet.freeze(reason)
            await db.commit()

            # Инвалидация кэша
            redis_session = await get_session()
            await redis_session.invalidate_wallet_cache(user_id)

            logger.info(f"Wallet frozen for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error freezing wallet: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def unfreeze_wallet(db: AsyncSession, user_id: str) -> bool:
        """Разморозка кошелька"""
        try:
            wallet = await WalletService.get_wallet(db, user_id)
            if not wallet:
                raise ValueError("Wallet not found")

            wallet.unfreeze()
            await db.commit()

            # Инвалидация кэша
            redis_session = await get_session()
            await redis_session.invalidate_wallet_cache(user_id)

            logger.info(f"Wallet unfrozen for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error unfreezing wallet: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def get_transaction_history(
        db: AsyncSession,
        user_id: str,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Получение истории транзакций кошелька"""
        try:
            offset = (page - 1) * limit

            # Получение транзакций
            query = select(Transaction).where(
                Transaction.user_id == user_id
            ).order_by(Transaction.created_at.desc()).offset(offset).limit(limit)

            result = await db.execute(query)
            transactions = result.scalars().all()

            # Подсчет общего количества
            count_query = select(func.count()).where(Transaction.user_id == user_id)
            total_result = await db.execute(count_query)
            total = total_result.scalar()

            return {
                "transactions": [WalletService.transaction_to_dict(t) for t in transactions],
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit
            }

        except Exception as e:
            logger.error(f"Error getting transaction history for user {user_id}: {e}")
            return {
                "transactions": [],
                "total": 0,
                "page": page,
                "limit": limit,
                "pages": 0
            }

    @staticmethod
    async def _create_transaction(
        db: AsyncSession,
        wallet: Wallet,
        transaction_type: str,
        amount: float,
        description: Optional[str] = None
    ):
        """Создание записи транзакции"""
        try:
            balance_before = wallet.balance

            transaction = Transaction(
                id=str(uuid.uuid4()),
                user_id=wallet.user_id,
                transaction_type=transaction_type,
                amount=abs(amount),
                currency=wallet.currency,
                fee=0,
                net_amount=abs(amount),
                balance_before=balance_before,
                balance_after=wallet.balance,
                description=description or f"{transaction_type.title()} transaction",
                is_test=False
            )

            db.add(transaction)

        except Exception as e:
            logger.error(f"Error creating transaction: {e}")

    @staticmethod
    def wallet_to_response(wallet: Wallet) -> WalletResponse:
        """Преобразование модели Wallet в схему WalletResponse"""
        return WalletResponse(
            id=wallet.id,
            user_id=wallet.user_id,
            balance=wallet.balance,
            currency=wallet.currency,
            bonus_balance=wallet.bonus_balance,
            referral_balance=wallet.referral_balance,
            available_balance=wallet.available_balance,
            is_active=wallet.is_active,
            is_frozen=wallet.is_frozen,
            frozen_reason=wallet.frozen_reason,
            min_balance=wallet.min_balance,
            max_balance=wallet.max_balance,
            daily_limit=wallet.daily_limit,
            monthly_limit=wallet.monthly_limit,
            total_deposits=wallet.total_deposits,
            total_withdrawals=wallet.total_withdrawals,
            total_earnings=wallet.total_earnings,
            auto_topup_enabled=wallet.auto_topup_enabled,
            auto_topup_amount=wallet.auto_topup_amount,
            auto_topup_threshold=wallet.auto_topup_threshold,
            two_factor_enabled=wallet.two_factor_enabled,
            created_at=wallet.created_at,
            updated_at=wallet.updated_at,
            last_operation_at=wallet.last_operation_at,
            can_spend=wallet.can_spend,
            is_overdrawn=wallet.is_overdrawn,
            is_at_limit=wallet.is_at_limit
        )

    @staticmethod
    def wallet_to_dict(wallet: Wallet) -> Dict[str, Any]:
        """Преобразование модели Wallet в словарь для кэширования"""
        return {
            "id": wallet.id,
            "user_id": wallet.user_id,
            "balance": wallet.balance,
            "currency": wallet.currency,
            "bonus_balance": wallet.bonus_balance,
            "referral_balance": wallet.referral_balance,
            "is_active": wallet.is_active,
            "is_frozen": wallet.is_frozen,
            "frozen_reason": wallet.frozen_reason,
            "min_balance": wallet.min_balance,
            "max_balance": wallet.max_balance,
            "daily_limit": wallet.daily_limit,
            "monthly_limit": wallet.monthly_limit,
            "total_deposits": wallet.total_deposits,
            "total_withdrawals": wallet.total_withdrawals,
            "total_earnings": wallet.total_earnings,
            "auto_topup_enabled": wallet.auto_topup_enabled,
            "auto_topup_amount": wallet.auto_topup_amount,
            "auto_topup_threshold": wallet.auto_topup_threshold,
            "two_factor_enabled": wallet.two_factor_enabled,
            "created_at": wallet.created_at.isoformat(),
            "updated_at": wallet.updated_at.isoformat(),
            "last_operation_at": wallet.last_operation_at.isoformat() if wallet.last_operation_at else None
        }

    @staticmethod
    def transaction_to_dict(transaction: Transaction) -> Dict[str, Any]:
        """Преобразование модели Transaction в словарь"""
        return {
            "id": transaction.id,
            "transaction_type": transaction.transaction_type.value,
            "amount": transaction.amount,
            "balance_before": transaction.balance_before,
            "balance_after": transaction.balance_after,
            "description": transaction.description,
            "created_at": transaction.created_at.isoformat()
        }
