"""
Сервис для управления выплатами исполнителям
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func

from app.config import settings
from app.models.payout import Payout, PayoutStatus, PayoutMethod
from app.schemas.payout import PayoutCreate, PayoutUpdate, PayoutResponse
from app.services.wallet_service import WalletService

logger = logging.getLogger(__name__)


class PayoutService:
    """Сервис для работы с выплатами"""

    @staticmethod
    async def create_payout(db: AsyncSession, user_id: str, payout_data: PayoutCreate) -> Payout:
        """Создание выплаты"""
        try:
            payout_id = str(uuid.uuid4())

            payout = Payout(
                id=payout_id,
                user_id=user_id,
                amount=payout_data.amount,
                currency=payout_data.currency,
                platform_fee=settings.platform_commission * payout_data.amount,
                net_amount=payout_data.amount - (settings.platform_commission * payout_data.amount),
                method=payout_data.method,
                recipient_name=payout_data.recipient_name,
                recipient_data=payout_data.recipient_data,
                period_start=payout_data.period_start,
                period_end=payout_data.period_end,
                description=payout_data.description,
                priority=payout_data.priority
            )

            db.add(payout)
            await db.commit()
            await db.refresh(payout)

            logger.info(f"Payout created: {payout.id} for user {user_id}")
            return payout

        except Exception as e:
            logger.error(f"Payout creation failed: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def get_payout_by_id(db: AsyncSession, payout_id: str, user_id: str) -> Optional[Payout]:
        """Получение выплаты по ID"""
        try:
            query = select(Payout).where(
                Payout.id == payout_id,
                Payout.user_id == user_id
            )
            result = await db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Error getting payout {payout_id}: {e}")
            return None

    @staticmethod
    async def get_user_payouts(
        db: AsyncSession,
        user_id: str,
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Получение выплат пользователя"""
        try:
            offset = (page - 1) * limit

            # Построение запроса
            query = select(Payout).where(Payout.user_id == user_id)

            if status:
                query = query.where(Payout.status == status)

            # Подсчет общего количества
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await db.execute(count_query)
            total = total_result.scalar()

            # Получение выплат с пагинацией
            query = query.order_by(Payout.created_at.desc()).offset(offset).limit(limit)
            result = await db.execute(query)
            payouts = result.scalars().all()

            pages = (total + limit - 1) // limit

            return {
                "payouts": [PayoutService.payout_to_response(payout) for payout in payouts],
                "total": total,
                "page": page,
                "limit": limit,
                "pages": pages
            }

        except Exception as e:
            logger.error(f"Error getting user payouts for {user_id}: {e}")
            return {
                "payouts": [],
                "total": 0,
                "page": page,
                "limit": limit,
                "pages": 0
            }

    @staticmethod
    async def process_payout(db: AsyncSession, payout_id: str, user_id: str) -> bool:
        """Обработка выплаты"""
        try:
            payout = await PayoutService.get_payout_by_id(db, payout_id, user_id)
            if not payout or payout.status != PayoutStatus.PENDING:
                return False

            # Проверка баланса кошелька
            wallet = await WalletService.get_wallet(db, user_id)
            if not wallet or wallet.balance < payout.net_amount:
                raise ValueError("Insufficient funds")

            # Холдирование средств
            success = wallet.withdraw(payout.net_amount, f"Payout {payout_id}")

            if success:
                payout.mark_as_processing()
                await db.commit()
                return True

            return False

        except Exception as e:
            logger.error(f"Error processing payout {payout_id}: {e}")
            await db.rollback()
            return False

    @staticmethod
    async def cancel_payout(db: AsyncSession, payout_id: str, user_id: str, reason: Optional[str] = None) -> bool:
        """Отмена выплаты"""
        try:
            payout = await PayoutService.get_payout_by_id(db, payout_id, user_id)
            if not payout or payout.status not in [PayoutStatus.PENDING, PayoutStatus.PROCESSING]:
                return False

            payout.mark_as_cancelled(reason)
            await db.commit()

            logger.info(f"Payout {payout_id} cancelled")
            return True

        except Exception as e:
            logger.error(f"Error cancelling payout {payout_id}: {e}")
            await db.rollback()
            return False

    @staticmethod
    async def calculate_earnings(
        db: AsyncSession,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Расчет заработка пользователя за период"""
        try:
            # Получение всех завершенных заказов пользователя
            from app.models.order import Order
            orders_query = select(Order).where(
                Order.walker_id == user_id,
                Order.status == "completed",
                Order.completed_at.between(start_date, end_date)
            )
            orders_result = await db.execute(orders_query)
            orders = orders_result.scalars().all()

            total_earnings = 0
            total_orders = len(orders)
            platform_fees = 0

            for order in orders:
                # Расчет комиссий и заработка
                walker_earnings = order.total_amount * (1 - settings.platform_commission)
                total_earnings += walker_earnings
                platform_fees += order.total_amount * settings.platform_commission

            return {
                "user_id": user_id,
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "total_orders": total_orders,
                "total_earnings": total_earnings,
                "platform_fees": platform_fees,
                "net_earnings": total_earnings,
                "average_order_value": total_earnings / max(total_orders, 1)
            }

        except Exception as e:
            logger.error(f"Error calculating earnings for user {user_id}: {e}")
            return {
                "user_id": user_id,
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "total_orders": 0,
                "total_earnings": 0,
                "platform_fees": 0,
                "net_earnings": 0,
                "average_order_value": 0
            }

    @staticmethod
    async def create_automatic_payouts(db: AsyncSession) -> List[Payout]:
        """Создание автоматических выплат для пользователей"""
        try:
            created_payouts = []

            # Получение пользователей с достаточным балансом для выплаты
            from app.models.wallet import Wallet
            wallets_query = select(Wallet).where(
                Wallet.balance >= settings.min_payout_amount,
                Wallet.is_active == True,
                Wallet.is_frozen == False
            )
            wallets_result = await db.execute(wallets_query)
            wallets = wallets_result.scalars().all()

            current_date = datetime.utcnow()
            period_start = current_date - timedelta(days=30)  # За последний месяц
            period_end = current_date

            for wallet in wallets:
                try:
                    # Расчет заработка за период
                    earnings = await PayoutService.calculate_earnings(
                        db, wallet.user_id, period_start, period_end
                    )

                    if earnings["net_earnings"] >= settings.min_payout_amount:
                        # Создание выплаты
                        payout_data = PayoutCreate(
                            amount=earnings["net_earnings"],
                            method=PayoutMethod.BANK_CARD,  # По умолчанию карта
                            recipient_name="Auto Payout",
                            recipient_data={"auto_generated": True},
                            period_start=period_start,
                            period_end=period_end,
                            description=f"Automatic payout for period {period_start.date()} - {period_end.date()}"
                        )

                        payout = await PayoutService.create_payout(db, wallet.user_id, payout_data)
                        created_payouts.append(payout)

                except Exception as e:
                    logger.error(f"Error creating automatic payout for user {wallet.user_id}: {e}")
                    continue

            logger.info(f"Created {len(created_payouts)} automatic payouts")
            return created_payouts

        except Exception as e:
            logger.error(f"Error creating automatic payouts: {e}")
            return []

    @staticmethod
    def payout_to_response(payout: Payout) -> PayoutResponse:
        """Преобразование модели Payout в схему PayoutResponse"""
        return PayoutResponse(
            id=payout.id,
            user_id=payout.user_id,
            amount=payout.amount,
            currency=payout.currency,
            platform_fee=payout.platform_fee,
            net_amount=payout.net_amount,
            status=payout.status,
            method=payout.method,
            period_start=payout.period_start,
            period_end=payout.period_end,
            recipient_name=payout.recipient_name,
            order_ids=payout.order_ids,
            provider_payout_id=payout.provider_payout_id,
            processed_by=payout.processed_by,
            processed_at=payout.processed_at,
            failure_reason=payout.failure_reason,
            is_test=payout.is_test,
            priority=payout.priority,
            created_at=payout.created_at,
            updated_at=payout.updated_at,
            scheduled_at=payout.scheduled_at,
            is_pending=payout.is_pending,
            is_processing=payout.is_processing,
            is_completed=payout.is_completed,
            is_failed=payout.is_failed,
            period_days=payout.period_days
        )
