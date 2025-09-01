"""
Сервис для управления медицинской информацией питомцев
"""

import logging
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database.session import get_session
from app.models.pet import Pet
from app.models.pet_medical import PetMedical
from app.schemas.pet import PetMedicalCreate, PetMedicalUpdate, PetMedicalResponse

logger = logging.getLogger(__name__)


class MedicalService:
    """Сервис для работы с медицинской информацией питомцев"""

    @staticmethod
    async def create_medical_record(
        db: AsyncSession,
        pet_id: str,
        user_id: str,
        medical_data: PetMedicalCreate
    ) -> Optional[PetMedical]:
        """Создание медицинской записи"""
        try:
            # Проверка существования питомца
            pet = await MedicalService._get_pet_by_id(db, pet_id, user_id)
            if not pet:
                logger.error(f"Pet {pet_id} not found or access denied for user {user_id}")
                return None

            medical_id = str(uuid.uuid4())

            medical_record = PetMedical(
                id=medical_id,
                pet_id=pet_id,
                record_type=medical_data.record_type,
                title=medical_data.title,
                description=medical_data.description,
                medication_name=medical_data.medication_name,
                medication_dosage=medical_data.medication_dosage,
                medication_frequency=medical_data.medication_frequency,
                veterinarian_name=medical_data.veterinarian_name,
                veterinarian_phone=medical_data.veterinarian_phone,
                clinic_name=medical_data.clinic_name,
                clinic_address=medical_data.clinic_address,
                event_date=medical_data.event_date,
                next_visit_date=medical_data.next_visit_date,
                vaccination_due_date=medical_data.vaccination_due_date,
                cost=medical_data.cost,
                results=medical_data.results,
                recommendations=medical_data.recommendations,
                is_completed=medical_data.is_completed if hasattr(medical_data, 'is_completed') else True,
                requires_follow_up=medical_data.requires_follow_up if hasattr(medical_data, 'requires_follow_up') else False,
                created_by=user_id
            )

            db.add(medical_record)
            await db.commit()
            await db.refresh(medical_record)

            # Инвалидация кэша
            redis_session = await get_session()
            await redis_session.invalidate_pet_cache(pet_id)
            await redis_session.invalidate_user_pets_cache(user_id)

            logger.info(f"Medical record created successfully: {medical_record.title} for pet {pet_id}")
            return medical_record

        except Exception as e:
            logger.error(f"Medical record creation failed: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def get_medical_records(
        db: AsyncSession,
        pet_id: str,
        user_id: str,
        record_type: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Получение медицинских записей питомца"""
        try:
            # Проверка доступа к питомцу
            pet = await MedicalService._get_pet_by_id(db, pet_id, user_id)
            if not pet:
                return {"records": [], "total": 0, "page": page, "limit": limit, "pages": 0}

            offset = (page - 1) * limit

            query = select(PetMedical).where(PetMedical.pet_id == pet_id)

            if record_type:
                query = query.where(PetMedical.record_type == record_type)

            # Подсчет общего количества
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await db.execute(count_query)
            total = total_result.scalar()

            # Получение записей с пагинацией, отсортированных по дате события
            query = query.order_by(PetMedical.event_date.desc()).offset(offset).limit(limit)
            result = await db.execute(query)
            records = result.scalars().all()

            pages = (total + limit - 1) // limit

            return {
                "records": [MedicalService.medical_to_response(record) for record in records],
                "total": total,
                "page": page,
                "limit": limit,
                "pages": pages
            }

        except Exception as e:
            logger.error(f"Error getting medical records for pet {pet_id}: {e}")
            return {"records": [], "total": 0, "page": page, "limit": limit, "pages": 0}

    @staticmethod
    async def get_medical_record_by_id(
        db: AsyncSession,
        record_id: str,
        user_id: str
    ) -> Optional[PetMedical]:
        """Получение медицинской записи по ID с проверкой доступа"""
        try:
            # Получаем запись вместе с информацией о питомце для проверки доступа
            query = select(PetMedical).join(Pet).where(
                PetMedical.id == record_id,
                Pet.user_id == user_id
            )
            result = await db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Error getting medical record {record_id}: {e}")
            return None

    @staticmethod
    async def update_medical_record(
        db: AsyncSession,
        record_id: str,
        user_id: str,
        medical_data: PetMedicalUpdate
    ) -> Optional[PetMedical]:
        """Обновление медицинской записи"""
        try:
            update_data = medical_data.dict(exclude_unset=True)

            if not update_data:
                return await MedicalService.get_medical_record_by_id(db, record_id, user_id)

            # Получаем текущую запись для проверки доступа
            current_record = await MedicalService.get_medical_record_by_id(db, record_id, user_id)
            if not current_record:
                return None

            stmt = (
                update(PetMedical)
                .where(PetMedical.id == record_id)
                .values(**update_data, updated_at=datetime.utcnow())
            )

            result = await db.execute(stmt)
            await db.commit()

            if result.rowcount == 0:
                return None

            # Инвалидация кэша
            redis_session = await get_session()
            await redis_session.invalidate_pet_cache(current_record.pet_id)
            await redis_session.invalidate_user_pets_cache(user_id)

            # Возвращаем обновленную запись
            return await MedicalService.get_medical_record_by_id(db, record_id, user_id)

        except Exception as e:
            logger.error(f"Medical record update failed for {record_id}: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def delete_medical_record(db: AsyncSession, record_id: str, user_id: str) -> bool:
        """Удаление медицинской записи"""
        try:
            # Получаем запись для проверки доступа
            record = await MedicalService.get_medical_record_by_id(db, record_id, user_id)
            if not record:
                return False

            # Удаление записи
            stmt = select(PetMedical).where(PetMedical.id == record_id)
            result = await db.execute(stmt)
            record_to_delete = result.scalar_one_or_none()

            if record_to_delete:
                await db.delete(record_to_delete)
                await db.commit()

                # Инвалидация кэша
                redis_session = await get_session()
                await redis_session.invalidate_pet_cache(record.pet_id)
                await redis_session.invalidate_user_pets_cache(user_id)

                logger.info(f"Medical record {record_id} deleted successfully")
                return True

            return False

        except Exception as e:
            logger.error(f"Medical record deletion failed for {record_id}: {e}")
            await db.rollback()
            return False

    @staticmethod
    async def get_upcoming_events(
        db: AsyncSession,
        user_id: str,
        days_ahead: int = 30
    ) -> List[Dict[str, Any]]:
        """Получение предстоящих медицинских событий"""
        try:
            from datetime import timedelta

            cutoff_date = datetime.utcnow() + timedelta(days=days_ahead)

            # Получаем все питомцы пользователя
            from app.models.pet import Pet
            pets_query = select(Pet.id, Pet.name).where(
                Pet.user_id == user_id,
                Pet.is_active == True
            )
            pets_result = await db.execute(pets_query)
            pets = {pet_id: name for pet_id, name in pets_result.fetchall()}

            if not pets:
                return []

            # Получаем предстоящие события
            events_query = select(PetMedical).where(
                PetMedical.pet_id.in_(pets.keys()),
                PetMedical.is_completed == False
            ).where(
                (PetMedical.next_visit_date <= cutoff_date) |
                (PetMedical.vaccination_due_date <= cutoff_date)
            ).order_by(PetMedical.next_visit_date, PetMedical.vaccination_due_date)

            result = await db.execute(events_query)
            records = result.scalars().all()

            events = []
            for record in records:
                pet_name = pets.get(record.pet_id, "Неизвестный питомец")

                if record.next_visit_date:
                    days_until = (record.next_visit_date - datetime.utcnow()).days
                    if days_until >= 0:
                        events.append({
                            "id": record.id,
                            "pet_id": record.pet_id,
                            "pet_name": pet_name,
                            "type": "next_visit",
                            "title": f"Следующий визит: {record.title}",
                            "event_date": record.next_visit_date,
                            "days_until": days_until
                        })

                if record.vaccination_due_date:
                    days_until = (record.vaccination_due_date - datetime.utcnow()).days
                    if days_until >= 0:
                        events.append({
                            "id": record.id,
                            "pet_id": record.pet_id,
                            "pet_name": pet_name,
                            "type": "vaccination",
                            "title": f"Вакцинация: {record.title}",
                            "event_date": record.vaccination_due_date,
                            "days_until": days_until
                        })

            # Сортировка по дате
            events.sort(key=lambda x: x["event_date"])
            return events[:10]  # Возвращаем только первые 10 событий

        except Exception as e:
            logger.error(f"Error getting upcoming events for user {user_id}: {e}")
            return []

    @staticmethod
    async def _get_pet_by_id(db: AsyncSession, pet_id: str, user_id: str) -> Optional[Pet]:
        """Получение питомца с проверкой доступа"""
        query = select(Pet).where(
            Pet.id == pet_id,
            Pet.user_id == user_id,
            Pet.is_active == True
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    def medical_to_response(medical: PetMedical) -> PetMedicalResponse:
        """Преобразование модели PetMedical в схему PetMedicalResponse"""
        return PetMedicalResponse(
            id=medical.id,
            pet_id=medical.pet_id,
            record_type=medical.record_type,
            title=medical.title,
            description=medical.description,
            medication_name=medical.medication_name,
            medication_dosage=medical.medication_dosage,
            medication_frequency=medical.medication_frequency,
            veterinarian_name=medical.veterinarian_name,
            veterinarian_phone=medical.veterinarian_phone,
            clinic_name=medical.clinic_name,
            clinic_address=medical.clinic_address,
            event_date=medical.event_date,
            next_visit_date=medical.next_visit_date,
            vaccination_due_date=medical.vaccination_due_date,
            cost=medical.cost,
            results=medical.results,
            recommendations=medical.recommendations,
            is_completed=medical.is_completed,
            requires_follow_up=medical.requires_follow_up,
            created_by=medical.created_by,
            created_at=medical.created_at,
            updated_at=medical.updated_at,
            is_vaccination=medical.is_vaccination,
            is_medication=medical.is_medication,
            is_past_due=medical.is_past_due,
            days_until_next_visit=medical.days_until_next_visit,
            days_until_vaccination=medical.days_until_vaccination
        )
