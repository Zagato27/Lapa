"""
Сервис для работы с выгульщиками
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.walker_verification import WalkerVerification
from app.schemas.user import WalkerVerificationRequest, WalkerVerificationResponse

logger = logging.getLogger(__name__)


class WalkerService:
    """Сервис для работы с выгульщиками"""

    @staticmethod
    async def create_verification_request(
        db: AsyncSession,
        user_id: str,
        verification_data: WalkerVerificationRequest
    ) -> WalkerVerificationResponse:
        """Создание заявки на верификацию выгульщика"""
        try:
            # Проверка, есть ли уже активная заявка
            existing_verification = await WalkerService.get_active_verification(db, user_id)
            if existing_verification:
                raise ValueError("У вас уже есть активная заявка на верификацию")

            # Создание новой заявки
            verification_id = str(uuid.uuid4())

            # Парсинг дат
            try:
                passport_issued_date = datetime.fromisoformat(verification_data.passport_issued_date)
                passport_expiry_date = datetime.fromisoformat(verification_data.passport_expiry_date)
            except ValueError:
                raise ValueError("Неверный формат даты")

            verification = WalkerVerification(
                id=verification_id,
                user_id=user_id,
                passport_number=verification_data.passport_number,
                passport_series=verification_data.passport_series,
                passport_issued_by=verification_data.passport_issued_by,
                passport_issued_date=passport_issued_date,
                passport_expiry_date=passport_expiry_date,
                experience_years=verification_data.experience_years,
                services_offered=verification_data.services_offered,
                work_schedule=verification_data.work_schedule,
                status="pending"
            )

            db.add(verification)
            await db.commit()
            await db.refresh(verification)

            logger.info(f"Verification request created for user {user_id}")

            return WalkerVerificationResponse(
                verification_id=verification_id,
                status=verification.status,
                message="Заявка на верификацию успешно создана",
                submitted_at=verification.created_at
            )

        except ValueError as e:
            await db.rollback()
            raise ValueError(str(e))
        except Exception as e:
            logger.error(f"Error creating verification request: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def get_active_verification(db: AsyncSession, user_id: str) -> Optional[WalkerVerification]:
        """Получение активной заявки на верификацию"""
        try:
            stmt = select(WalkerVerification).where(
                WalkerVerification.user_id == user_id,
                WalkerVerification.status.in_(["pending", "approved"])
            )
            result = await db.execute(stmt)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Error getting active verification for user {user_id}: {e}")
            return None

    @staticmethod
    async def get_verification_by_id(db: AsyncSession, verification_id: str) -> Optional[WalkerVerification]:
        """Получение заявки на верификацию по ID"""
        try:
            stmt = select(WalkerVerification).where(WalkerVerification.id == verification_id)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Error getting verification {verification_id}: {e}")
            return None

    @staticmethod
    async def approve_verification(
        db: AsyncSession,
        verification_id: str,
        admin_id: str,
        notes: Optional[str] = None
    ) -> bool:
        """Одобрение заявки на верификацию"""
        try:
            verification = await WalkerService.get_verification_by_id(db, verification_id)

            if not verification:
                return False

            if verification.status != "pending":
                return False

            verification.approve(admin_id, notes)

            # Обновление статуса пользователя
            from app.services.user_service import UserService
            from app.models.user import User
            from sqlalchemy import update

            stmt = (
                update(User)
                .where(User.id == verification.user_id)
                .values(is_walker_verified=True)
            )
            await db.execute(stmt)

            await db.commit()

            logger.info(f"Verification {verification_id} approved by admin {admin_id}")
            return True

        except Exception as e:
            logger.error(f"Error approving verification {verification_id}: {e}")
            await db.rollback()
            return False

    @staticmethod
    async def reject_verification(
        db: AsyncSession,
        verification_id: str,
        admin_id: str,
        notes: str
    ) -> bool:
        """Отклонение заявки на верификацию"""
        try:
            verification = await WalkerService.get_verification_by_id(db, verification_id)

            if not verification:
                return False

            if verification.status != "pending":
                return False

            verification.reject(admin_id, notes)
            await db.commit()

            logger.info(f"Verification {verification_id} rejected by admin {admin_id}")
            return True

        except Exception as e:
            logger.error(f"Error rejecting verification {verification_id}: {e}")
            await db.rollback()
            return False
