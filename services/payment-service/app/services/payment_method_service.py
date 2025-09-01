"""
Сервис для управления способами оплаты
"""

import logging
import uuid
from typing import List, Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from app.config import settings
from app.database.session import get_session
from app.models.payment_method import PaymentMethod, PaymentMethodType
from app.schemas.payment_method import PaymentMethodCreate, PaymentMethodUpdate, PaymentMethodResponse

logger = logging.getLogger(__name__)


class PaymentMethodService:
    """Сервис для работы со способами оплаты"""

    @staticmethod
    async def create_payment_method(
        db: AsyncSession,
        user_id: str,
        payment_method_data: PaymentMethodCreate
    ) -> PaymentMethod:
        """Создание способа оплаты"""
        try:
            payment_method_id = str(uuid.uuid4())

            # Шифрование чувствительных данных
            encrypted_data = await PaymentMethodService._encrypt_sensitive_data(payment_method_data)

            payment_method = PaymentMethod(
                id=payment_method_id,
                user_id=user_id,
                type=payment_method_data.type,
                provider="platform",  # По умолчанию платформа
                name=payment_method_data.title or await PaymentMethodService._generate_name(payment_method_data),
                title=payment_method_data.title,
                encrypted_data=encrypted_data,
                masked_number=await PaymentMethodService._generate_masked_number(payment_method_data),
                is_default=await PaymentMethodService._should_be_default(db, user_id, payment_method_data.is_default)
            )

            # Для банковских карт устанавливаем срок действия
            if payment_method_data.type == PaymentMethodType.BANK_CARD and payment_method_data.expiry_date:
                import datetime
                month, year = payment_method_data.expiry_date[:2], payment_method_data.expiry_date[2:]
                if len(year) == 2:
                    year = f"20{year}"
                payment_method.expires_at = datetime.datetime(int(year), int(month), 1)

            db.add(payment_method)
            await db.commit()
            await db.refresh(payment_method)

            # Инвалидация кэша
            redis_session = await get_session()
            await redis_session.invalidate_payment_method_cache(payment_method_id)

            logger.info(f"Payment method created for user {user_id}: {payment_method.type.value}")
            return payment_method

        except Exception as e:
            logger.error(f"Payment method creation failed: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def get_payment_method_by_id(
        db: AsyncSession,
        payment_method_id: str,
        user_id: str
    ) -> Optional[PaymentMethod]:
        """Получение способа оплаты по ID"""
        try:
            # Проверка кэша
            redis_session = await get_session()
            cached_method = await redis_session.get_cached_payment_method(payment_method_id)

            if cached_method:
                return PaymentMethod(**cached_method)

            # Получение из базы данных
            query = select(PaymentMethod).where(
                PaymentMethod.id == payment_method_id,
                PaymentMethod.user_id == user_id
            )
            result = await db.execute(query)
            payment_method = result.scalar_one_or_none()

            if payment_method:
                # Кэширование
                method_data = PaymentMethodService.payment_method_to_dict(payment_method)
                await redis_session.cache_payment_method(payment_method_id, method_data)

            return payment_method

        except Exception as e:
            logger.error(f"Error getting payment method {payment_method_id}: {e}")
            return None

    @staticmethod
    async def get_user_payment_methods(db: AsyncSession, user_id: str) -> List[PaymentMethod]:
        """Получение способов оплаты пользователя"""
        try:
            query = select(PaymentMethod).where(
                PaymentMethod.user_id == user_id,
                PaymentMethod.is_active == True
            ).order_by(PaymentMethod.is_default.desc(), PaymentMethod.created_at.desc())

            result = await db.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error getting user payment methods for {user_id}: {e}")
            return []

    @staticmethod
    async def update_payment_method(
        db: AsyncSession,
        payment_method_id: str,
        user_id: str,
        payment_method_data: PaymentMethodUpdate
    ) -> Optional[PaymentMethod]:
        """Обновление способа оплаты"""
        try:
            update_data = payment_method_data.dict(exclude_unset=True)

            if not update_data:
                return await PaymentMethodService.get_payment_method_by_id(db, payment_method_id, user_id)

            stmt = (
                update(PaymentMethod)
                .where(PaymentMethod.id == payment_method_id, PaymentMethod.user_id == user_id)
                .values(**update_data, updated_at=datetime.utcnow())
            )

            result = await db.execute(stmt)
            await db.commit()

            if result.rowcount == 0:
                return None

            # Получение обновленного метода оплаты
            payment_method = await PaymentMethodService.get_payment_method_by_id(db, payment_method_id, user_id)

            # Инвалидация кэша
            if payment_method:
                redis_session = await get_session()
                await redis_session.invalidate_payment_method_cache(payment_method_id)

            return payment_method

        except Exception as e:
            logger.error(f"Payment method update failed for {payment_method_id}: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def delete_payment_method(db: AsyncSession, payment_method_id: str, user_id: str) -> bool:
        """Удаление способа оплаты"""
        try:
            # Получение метода оплаты для проверки доступа
            payment_method = await PaymentMethodService.get_payment_method_by_id(db, payment_method_id, user_id)
            if not payment_method:
                return False

            # Мягкое удаление
            stmt = (
                update(PaymentMethod)
                .where(PaymentMethod.id == payment_method_id)
                .values(is_active=False, updated_at=datetime.utcnow())
            )

            result = await db.execute(stmt)
            await db.commit()

            if result.rowcount > 0:
                # Инвалидация кэша
                redis_session = await get_session()
                await redis_session.invalidate_payment_method_cache(payment_method_id)

                logger.info(f"Payment method {payment_method_id} deleted successfully")
                return True

            return False

        except Exception as e:
            logger.error(f"Payment method deletion failed for {payment_method_id}: {e}")
            await db.rollback()
            return False

    @staticmethod
    async def set_as_default(db: AsyncSession, payment_method_id: str, user_id: str) -> bool:
        """Установка способа оплаты по умолчанию"""
        try:
            # Снятие флага по умолчанию со всех методов пользователя
            stmt1 = (
                update(PaymentMethod)
                .where(PaymentMethod.user_id == user_id)
                .values(is_default=False, updated_at=datetime.utcnow())
            )
            await db.execute(stmt1)

            # Установка флага по умолчанию для выбранного метода
            stmt2 = (
                update(PaymentMethod)
                .where(PaymentMethod.id == payment_method_id, PaymentMethod.user_id == user_id)
                .values(is_default=True, updated_at=datetime.utcnow())
            )

            result = await db.execute(stmt2)
            await db.commit()

            if result.rowcount > 0:
                # Инвалидация кэша
                redis_session = await get_session()
                await redis_session.invalidate_payment_method_cache(payment_method_id)

                logger.info(f"Payment method {payment_method_id} set as default")
                return True

            return False

        except Exception as e:
            logger.error(f"Error setting default payment method {payment_method_id}: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def verify_payment_method(
        db: AsyncSession,
        payment_method_id: str,
        user_id: str,
        verification_code: str
    ) -> bool:
        """Верификация способа оплаты"""
        try:
            payment_method = await PaymentMethodService.get_payment_method_by_id(db, payment_method_id, user_id)
            if not payment_method:
                return False

            # Здесь должна быть логика верификации с платежным провайдером
            # Для демонстрации просто проверяем, что код не пустой
            if not verification_code or len(verification_code) < 4:
                return False

            payment_method.mark_as_verified()
            await db.commit()

            # Инвалидация кэша
            redis_session = await get_session()
            await redis_session.invalidate_payment_method_cache(payment_method_id)

            logger.info(f"Payment method {payment_method_id} verified successfully")
            return True

        except Exception as e:
            logger.error(f"Error verifying payment method {payment_method_id}: {e}")
            await db.rollback()
            return False

    @staticmethod
    async def get_payment_method_statistics(
        db: AsyncSession,
        payment_method_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Получение статистики способа оплаты"""
        try:
            payment_method = await PaymentMethodService.get_payment_method_by_id(db, payment_method_id, user_id)
            if not payment_method:
                return None

            return {
                "payment_method_id": payment_method_id,
                "type": payment_method.type.value,
                "provider": payment_method.provider,
                "total_payments": payment_method.total_payments,
                "total_amount": payment_method.total_amount,
                "average_amount": payment_method.total_amount / max(payment_method.total_payments, 1),
                "last_used_at": payment_method.last_used_at.isoformat() if payment_method.last_used_at else None,
                "fraud_score": payment_method.fraud_score,
                "is_verified": payment_method.is_verified,
                "created_at": payment_method.created_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting payment method statistics {payment_method_id}: {e}")
            return None

    @staticmethod
    async def _encrypt_sensitive_data(payment_method_data: PaymentMethodCreate) -> Optional[str]:
        """Шифрование чувствительных данных"""
        try:
            import json
            from cryptography.fernet import Fernet

            # Получение ключа шифрования
            key = settings.encryption_key
            if not key:
                logger.warning("Encryption key not set, sensitive data will not be encrypted")
                return None

            fernet = Fernet(key.encode())

            sensitive_data = {}

            if payment_method_data.card_number:
                sensitive_data["card_number"] = payment_method_data.card_number
            if payment_method_data.expiry_date:
                sensitive_data["expiry_date"] = payment_method_data.expiry_date
            if payment_method_data.cvv:
                sensitive_data["cvv"] = payment_method_data.cvv
            if payment_method_data.wallet_id:
                sensitive_data["wallet_id"] = payment_method_data.wallet_id

            if sensitive_data:
                data_str = json.dumps(sensitive_data)
                encrypted_data = fernet.encrypt(data_str.encode())
                return encrypted_data.decode()

            return None

        except Exception as e:
            logger.error(f"Error encrypting sensitive data: {e}")
            return None

    @staticmethod
    async def _generate_masked_number(payment_method_data: PaymentMethodCreate) -> Optional[str]:
        """Генерация маскированного номера"""
        try:
            if payment_method_data.card_number:
                # Маскировка номера карты
                card_number = payment_method_data.card_number.replace(" ", "").replace("-", "")
                if len(card_number) >= 4:
                    return f"**** **** **** {card_number[-4:]}"

            elif payment_method_data.wallet_id:
                # Маскировка ID кошелька
                wallet_id = payment_method_data.wallet_id
                if len(wallet_id) >= 4:
                    return f"****{wallet_id[-4:]}"

            return None

        except Exception as e:
            logger.error(f"Error generating masked number: {e}")
            return None

    @staticmethod
    async def _generate_name(payment_method_data: PaymentMethodCreate) -> str:
        """Генерация имени способа оплаты"""
        try:
            if payment_method_data.type == PaymentMethodType.BANK_CARD:
                return "Банковская карта"
            elif payment_method_data.type == PaymentMethodType.ELECTRONIC_WALLET:
                return "Электронный кошелек"
            elif payment_method_data.type == PaymentMethodType.BANK_ACCOUNT:
                return "Банковский счет"
            elif payment_method_data.type == PaymentMethodType.SBP:
                return "СБП"
            else:
                return "Способ оплаты"

        except Exception as e:
            logger.error(f"Error generating payment method name: {e}")
            return "Способ оплаты"

    @staticmethod
    async def _should_be_default(
        db: AsyncSession,
        user_id: str,
        requested_default: bool
    ) -> bool:
        """Определение, должен ли метод быть по умолчанию"""
        try:
            if not requested_default:
                # Проверка, есть ли уже метод по умолчанию
                query = select(PaymentMethod).where(
                    PaymentMethod.user_id == user_id,
                    PaymentMethod.is_default == True,
                    PaymentMethod.is_active == True
                )
                result = await db.execute(query)
                existing_default = result.scalar_one_or_none()

                # Если нет метода по умолчанию, делаем этот по умолчанию
                return existing_default is None

            return True

        except Exception as e:
            logger.error(f"Error determining default payment method: {e}")
            return False

    @staticmethod
    def payment_method_to_response(payment_method: PaymentMethod) -> PaymentMethodResponse:
        """Преобразование модели PaymentMethod в схему PaymentMethodResponse"""
        return PaymentMethodResponse(
            id=payment_method.id,
            user_id=payment_method.user_id,
            type=payment_method.type,
            provider=payment_method.provider,
            name=payment_method.name,
            title=payment_method.title,
            masked_number=payment_method.masked_number,
            masked_email=payment_method.masked_email,
            is_active=payment_method.is_active,
            is_default=payment_method.is_default,
            is_verified=payment_method.is_verified,
            daily_limit=payment_method.daily_limit,
            monthly_limit=payment_method.monthly_limit,
            total_payments=payment_method.total_payments,
            total_amount=payment_method.total_amount,
            last_used_at=payment_method.last_used_at,
            created_at=payment_method.created_at,
            expires_at=payment_method.expires_at,
            is_expired=payment_method.is_expired,
            is_bank_card=payment_method.is_bank_card,
            is_wallet=payment_method.is_wallet,
            usage_rate=payment_method.usage_rate
        )

    @staticmethod
    def payment_method_to_dict(payment_method: PaymentMethod) -> Dict[str, Any]:
        """Преобразование модели PaymentMethod в словарь для кэширования"""
        return {
            "id": payment_method.id,
            "user_id": payment_method.user_id,
            "type": payment_method.type.value,
            "provider": payment_method.provider,
            "name": payment_method.name,
            "title": payment_method.title,
            "masked_number": payment_method.masked_number,
            "masked_email": payment_method.masked_email,
            "is_active": payment_method.is_active,
            "is_default": payment_method.is_default,
            "is_verified": payment_method.is_verified,
            "daily_limit": payment_method.daily_limit,
            "monthly_limit": payment_method.monthly_limit,
            "total_payments": payment_method.total_payments,
            "total_amount": payment_method.total_amount,
            "last_used_at": payment_method.last_used_at.isoformat() if payment_method.last_used_at else None,
            "expires_at": payment_method.expires_at.isoformat() if payment_method.expires_at else None,
            "fraud_score": payment_method.fraud_score,
            "created_at": payment_method.created_at.isoformat(),
            "updated_at": payment_method.updated_at.isoformat()
        }
