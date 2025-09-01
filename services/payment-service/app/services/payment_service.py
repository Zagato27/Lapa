"""
Основной сервис для управления платежами
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, desc
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database.session import get_session
from app.models.payment import Payment, PaymentStatus, PaymentType, PaymentProvider
from app.models.wallet import Wallet
from app.models.transaction import Transaction
from app.schemas.payment import (
    PaymentCreate,
    PaymentUpdate,
    PaymentResponse,
    PaymentsListResponse,
    PaymentRefundRequest,
    PaymentEstimateRequest,
    PaymentEstimateResponse
)

logger = logging.getLogger(__name__)


class PaymentService:
    """Сервис для работы с платежами"""

    @staticmethod
    async def create_payment(db: AsyncSession, user_id: str, payment_data: PaymentCreate) -> Payment:
        """Создание платежа"""
        try:
            payment_id = str(uuid.uuid4())

            # Расчет комиссий
            platform_commission = payment_data.amount * settings.platform_commission
            net_amount = payment_data.amount - platform_commission

            payment = Payment(
                id=payment_id,
                order_id=payment_data.order_id,
                user_id=user_id,
                payment_type=payment_data.payment_type,
                status=PaymentStatus.PENDING,
                provider=PaymentProvider.STRIPE if payment_data.payment_method_id else PaymentProvider.WALLET,
                amount=payment_data.amount,
                currency=payment_data.currency,
                platform_commission=platform_commission,
                net_amount=net_amount,
                payment_method_id=payment_data.payment_method_id,
                description=payment_data.description,
                extra_metadata=payment_data.metadata
            )

            db.add(payment)
            await db.commit()
            await db.refresh(payment)

            # Инвалидация кэша
            redis_session = await get_session()
            await redis_session.invalidate_payment_cache(payment_id)

            logger.info(f"Payment created: {payment.id} for user {user_id}")
            return payment

        except Exception as e:
            logger.error(f"Payment creation failed: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def get_payment_by_id(db: AsyncSession, payment_id: str, user_id: str) -> Optional[Payment]:
        """Получение платежа по ID"""
        try:
            query = select(Payment).where(
                Payment.id == payment_id,
                Payment.user_id == user_id
            )
            result = await db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Error getting payment {payment_id}: {e}")
            return None

    @staticmethod
    async def get_payments_list(
        db: AsyncSession,
        user_id: str,
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None,
        payment_type: Optional[str] = None
    ) -> PaymentsListResponse:
        """Получение списка платежей пользователя"""
        try:
            offset = (page - 1) * limit

            # Проверка кэша
            redis_session = await get_session()
            cache_key = f"{user_id}:{page}:{limit}:{status}:{payment_type}"
            cached_payments = await redis_session.get_cached_payment(cache_key)

            if cached_payments:
                return PaymentsListResponse(
                    payments=[PaymentService.payment_to_response(Payment(**p)) for p in cached_payments],
                    total=len(cached_payments),
                    page=page,
                    limit=limit,
                    pages=1
                )

            # Построение запроса
            query = select(Payment).where(Payment.user_id == user_id)

            if status:
                query = query.where(Payment.status == status)
            if payment_type:
                query = query.where(Payment.payment_type == payment_type)

            # Подсчет общего количества
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await db.execute(count_query)
            total = total_result.scalar()

            # Получение платежей с пагинацией
            query = query.order_by(desc(Payment.created_at)).offset(offset).limit(limit)
            result = await db.execute(query)
            payments = result.scalars().all()

            # Кэширование результатов
            if page == 1 and len(payments) < 100:  # Кэшируем только первую страницу
                payments_data = [PaymentService.payment_to_dict(payment) for payment in payments]
                await redis_session.cache_payment(cache_key, payments_data)

            pages = (total + limit - 1) // limit

            return PaymentsListResponse(
                payments=[PaymentService.payment_to_response(payment) for payment in payments],
                total=total,
                page=page,
                limit=limit,
                pages=pages
            )

        except Exception as e:
            logger.error(f"Error getting payments list for user {user_id}: {e}")
            return PaymentsListResponse(payments=[], total=0, page=page, limit=limit, pages=0)

    @staticmethod
    async def process_payment(
        db: AsyncSession,
        payment_id: str,
        user_id: str,
        payment_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Обработка платежа"""
        try:
            payment = await PaymentService.get_payment_by_id(db, payment_id, user_id)
            if not payment or payment.status != PaymentStatus.PENDING:
                return False

            # Проверка блокировки платежа
            redis_session = await get_session()
            if await redis_session.check_payment_lock(payment_id):
                logger.warning(f"Payment {payment_id} is already being processed")
                return False

            # Установка блокировки
            await redis_session.set_payment_lock(payment_id)

            try:
                # Обработка платежа в зависимости от провайдера
                if payment.provider == PaymentProvider.WALLET:
                    success = await PaymentService._process_wallet_payment(db, payment)
                elif payment.provider == PaymentProvider.STRIPE:
                    success = await PaymentService._process_stripe_payment(db, payment, payment_data)
                elif payment.provider == PaymentProvider.YOOKASSA:
                    success = await PaymentService._process_yookassa_payment(db, payment, payment_data)
                else:
                    success = False

                if success:
                    payment.mark_as_paid()
                    await PaymentService._create_transaction(db, payment, "payment")
                    await db.commit()
                else:
                    payment.mark_as_failed("Payment processing failed")
                    await db.commit()

                return success

            finally:
                # Снятие блокировки
                await redis_session.release_payment_lock(payment_id)

        except Exception as e:
            logger.error(f"Error processing payment {payment_id}: {e}")
            await db.rollback()
            return False

    @staticmethod
    async def refund_payment(
        db: AsyncSession,
        payment_id: str,
        user_id: str,
        refund_data: PaymentRefundRequest
    ) -> bool:
        """Возврат платежа"""
        try:
            payment = await PaymentService.get_payment_by_id(db, payment_id, user_id)
            if not payment or not payment.can_be_refunded:
                return False

            if refund_data.amount > payment.refundable_amount:
                return False

            # Обработка возврата в зависимости от провайдера
            if payment.provider == PaymentProvider.WALLET:
                success = await PaymentService._process_wallet_refund(db, payment, refund_data.amount)
            elif payment.provider == PaymentProvider.STRIPE:
                success = await PaymentService._process_stripe_refund(db, payment, refund_data.amount)
            else:
                success = False

            if success:
                payment.process_refund(refund_data.amount, refund_data.reason)
                await PaymentService._create_transaction(db, payment, "refund", refund_data.amount)
                await db.commit()
                return True

            return False

        except Exception as e:
            logger.error(f"Error refunding payment {payment_id}: {e}")
            await db.rollback()
            return False

    @staticmethod
    async def cancel_payment(db: AsyncSession, payment_id: str, user_id: str, reason: Optional[str] = None) -> bool:
        """Отмена платежа"""
        try:
            payment = await PaymentService.get_payment_by_id(db, payment_id, user_id)
            if not payment or payment.status not in [PaymentStatus.PENDING, PaymentStatus.PROCESSING]:
                return False

            payment.mark_as_cancelled(reason)
            await db.commit()

            # Инвалидация кэша
            redis_session = await get_session()
            await redis_session.invalidate_payment_cache(payment_id)

            logger.info(f"Payment {payment_id} cancelled")
            return True

        except Exception as e:
            logger.error(f"Error cancelling payment {payment_id}: {e}")
            await db.rollback()
            return False

    @staticmethod
    async def estimate_payment(db: AsyncSession, estimate_data: PaymentEstimateRequest) -> PaymentEstimateResponse:
        """Расчет стоимости платежа"""
        try:
            # Расчет комиссий
            platform_commission = estimate_data.amount * settings.platform_commission

            # Получение комиссий провайдера (зависит от способа оплаты)
            provider_commission = await PaymentService._calculate_provider_commission(
                db, estimate_data.payment_method_id, estimate_data.amount
            )

            total_amount = estimate_data.amount + platform_commission + provider_commission
            net_amount = estimate_data.amount

            return PaymentEstimateResponse(
                amount=estimate_data.amount,
                currency=estimate_data.currency,
                platform_commission=platform_commission,
                provider_commission=provider_commission,
                total_amount=total_amount,
                net_amount=net_amount,
                payment_method_fee=provider_commission,
                estimated_processing_time="instant"
            )

        except Exception as e:
            logger.error(f"Error estimating payment: {e}")
            return PaymentEstimateResponse(
                amount=estimate_data.amount,
                currency=estimate_data.currency,
                platform_commission=0,
                provider_commission=0,
                total_amount=estimate_data.amount,
                net_amount=estimate_data.amount,
                payment_method_fee=0,
                estimated_processing_time="unknown"
            )

    @staticmethod
    async def _process_wallet_payment(db: AsyncSession, payment: Payment) -> bool:
        """Обработка платежа из кошелька"""
        try:
            # Получение кошелька пользователя
            wallet = await db.execute(
                select(Wallet).where(Wallet.user_id == payment.user_id)
            )
            wallet = wallet.scalar_one_or_none()

            if not wallet or not wallet.can_afford(payment.amount):
                return False

            # Холдирование средств
            return wallet.withdraw(payment.amount, payment.description)

        except Exception as e:
            logger.error(f"Error processing wallet payment: {e}")
            return False

    @staticmethod
    async def _process_stripe_payment(db: AsyncSession, payment: Payment, payment_data: Optional[Dict[str, Any]]) -> bool:
        """Обработка платежа через Stripe"""
        try:
            # Здесь должна быть интеграция с Stripe API
            # Для демонстрации возвращаем успех
            logger.info(f"Processing Stripe payment {payment.id}")
            return True

        except Exception as e:
            logger.error(f"Error processing Stripe payment: {e}")
            return False

    @staticmethod
    async def _process_yookassa_payment(db: AsyncSession, payment: Payment, payment_data: Optional[Dict[str, Any]]) -> bool:
        """Обработка платежа через ЮKassa"""
        try:
            # Здесь должна быть интеграция с ЮKassa API
            # Для демонстрации возвращаем успех
            logger.info(f"Processing YooKassa payment {payment.id}")
            return True

        except Exception as e:
            logger.error(f"Error processing YooKassa payment: {e}")
            return False

    @staticmethod
    async def _process_wallet_refund(db: AsyncSession, payment: Payment, amount: float) -> bool:
        """Возврат средств на кошелек"""
        try:
            wallet = await db.execute(
                select(Wallet).where(Wallet.user_id == payment.user_id)
            )
            wallet = wallet.scalar_one_or_none()

            if not wallet:
                return False

            return wallet.deposit(amount, f"Refund for payment {payment.id}")

        except Exception as e:
            logger.error(f"Error processing wallet refund: {e}")
            return False

    @staticmethod
    async def _process_stripe_refund(db: AsyncSession, payment: Payment, amount: float) -> bool:
        """Возврат средств через Stripe"""
        try:
            # Здесь должна быть интеграция с Stripe API для возврата
            logger.info(f"Processing Stripe refund for payment {payment.id}")
            return True

        except Exception as e:
            logger.error(f"Error processing Stripe refund: {e}")
            return False

    @staticmethod
    async def _calculate_provider_commission(
        db: AsyncSession,
        payment_method_id: Optional[str],
        amount: float
    ) -> float:
        """Расчет комиссии провайдера"""
        try:
            if not payment_method_id:
                return amount * 0.02  # 2% для неизвестного метода

            # Получение способа оплаты
            from app.models.payment_method import PaymentMethod
            payment_method = await db.execute(
                select(PaymentMethod).where(PaymentMethod.id == payment_method_id)
            )
            payment_method = payment_method.scalar_one_or_none()

            if not payment_method:
                return amount * 0.02

            # Расчет комиссии в зависимости от типа
            if payment_method.type == "bank_card":
                return amount * 0.015  # 1.5% для карт
            elif payment_method.type == "electronic_wallet":
                return amount * 0.01   # 1% для электронных кошельков
            else:
                return amount * 0.02   # 2% для остальных

        except Exception as e:
            logger.error(f"Error calculating provider commission: {e}")
            return amount * 0.02

    @staticmethod
    async def _create_transaction(
        db: AsyncSession,
        payment: Payment,
        transaction_type: str,
        amount: Optional[float] = None
    ):
        """Создание записи транзакции"""
        try:
            transaction_amount = amount if amount else payment.amount

            transaction = Transaction(
                id=str(uuid.uuid4()),
                payment_id=payment.id,
                user_id=payment.user_id,
                transaction_type=transaction_type,
                amount=transaction_amount,
                currency=payment.currency,
                fee=payment.platform_commission,
                net_amount=transaction_amount - payment.platform_commission,
                description=f"{transaction_type.title()} for payment {payment.id}",
                is_test=payment.is_test
            )

            db.add(transaction)

        except Exception as e:
            logger.error(f"Error creating transaction: {e}")

    @staticmethod
    def payment_to_response(payment: Payment) -> PaymentResponse:
        """Преобразование модели Payment в схему PaymentResponse"""
        return PaymentResponse(
            id=payment.id,
            order_id=payment.order_id,
            user_id=payment.user_id,
            payment_type=payment.payment_type,
            status=payment.status,
            provider=payment.provider,
            amount=payment.amount,
            currency=payment.currency,
            platform_commission=payment.platform_commission,
            provider_commission=payment.provider_commission,
            net_amount=payment.net_amount,
            provider_payment_id=payment.provider_payment_id,
            payment_method_id=payment.payment_method_id,
            description=payment.description,
            metadata=payment.extra_metadata,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
            paid_at=payment.paid_at,
            cancelled_at=payment.cancelled_at,
            refunded_at=payment.refunded_at,
            refund_amount=payment.refund_amount,
            refund_reason=payment.refund_reason,
            is_test=payment.is_test,
            is_pending=payment.is_pending,
            is_processing=payment.is_processing,
            is_completed=payment.is_completed,
            is_failed=payment.is_failed,
            is_refunded=payment.is_refunded,
            can_be_refunded=payment.can_be_refunded,
            refundable_amount=payment.refundable_amount
        )

    @staticmethod
    def payment_to_dict(payment: Payment) -> Dict[str, Any]:
        """Преобразование модели Payment в словарь для кэширования"""
        return {
            "id": payment.id,
            "order_id": payment.order_id,
            "user_id": payment.user_id,
            "payment_type": payment.payment_type.value,
            "status": payment.status.value,
            "provider": payment.provider.value,
            "amount": payment.amount,
            "currency": payment.currency,
            "platform_commission": payment.platform_commission,
            "net_amount": payment.net_amount,
            "provider_payment_id": payment.provider_payment_id,
            "payment_method_id": payment.payment_method_id,
            "description": payment.description,
            "created_at": payment.created_at.isoformat(),
            "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
            "is_test": payment.is_test
        }
