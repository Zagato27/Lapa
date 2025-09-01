"""
Основной сервис для управления питомцами
"""

import logging
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database.session import get_session
from app.models.pet import Pet
from app.models.pet_photo import PetPhoto
from app.schemas.pet import (
    PetCreate,
    PetUpdate,
    PetProfile,
    PetsListResponse
)

logger = logging.getLogger(__name__)


class PetService:
    """Сервис для работы с питомцами"""

    @staticmethod
    async def create_pet(db: AsyncSession, user_id: str, pet_data: PetCreate) -> Pet:
        """Создание нового питомца"""
        try:
            pet_id = str(uuid.uuid4())

            pet = Pet(
                id=pet_id,
                user_id=user_id,
                name=pet_data.name,
                breed=pet_data.breed,
                date_of_birth=pet_data.date_of_birth,
                age_years=pet_data.age_years,
                age_months=pet_data.age_months,
                gender=pet_data.gender,
                color=pet_data.color,
                weight_kg=pet_data.weight_kg,
                size=pet_data.size,
                energy_level=pet_data.energy_level,
                friendliness=pet_data.friendliness,
                is_vaccinated=pet_data.is_vaccinated,
                is_neutered=pet_data.is_neutered,
                has_allergies=pet_data.has_allergies,
                allergies_description=pet_data.allergies_description,
                special_needs=pet_data.special_needs,
                medications=pet_data.medications,
                medical_conditions=pet_data.medical_conditions,
                is_friendly_with_dogs=pet_data.is_friendly_with_dogs,
                is_friendly_with_cats=pet_data.is_friendly_with_cats,
                is_friendly_with_children=pet_data.is_friendly_with_children,
                behavioral_notes=pet_data.behavioral_notes,
                walking_frequency=pet_data.walking_frequency,
                walking_duration_minutes=pet_data.walking_duration_minutes,
                feeding_schedule=pet_data.feeding_schedule,
                favorite_activities=pet_data.favorite_activities,
                walking_notes=pet_data.walking_notes,
                emergency_contact_name=pet_data.emergency_contact_name,
                emergency_contact_phone=pet_data.emergency_contact_phone,
                veterinarian_name=pet_data.veterinarian_name,
                veterinarian_phone=pet_data.veterinarian_phone,
                veterinarian_address=pet_data.veterinarian_address
            )

            # Расчет возраста, если указана дата рождения
            if pet.date_of_birth:
                pet.calculate_age()

            db.add(pet)
            await db.commit()
            await db.refresh(pet)

            # Инвалидация кэша
            redis_session = await get_session()
            await redis_session.invalidate_user_pets_cache(user_id)

            logger.info(f"Pet created successfully: {pet.name} for user {user_id}")
            return pet

        except Exception as e:
            logger.error(f"Pet creation failed: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def get_pet_by_id(db: AsyncSession, pet_id: str, user_id: Optional[str] = None) -> Optional[Pet]:
        """Получение питомца по ID"""
        try:
            query = select(Pet).where(Pet.id == pet_id, Pet.is_active == True)

            if user_id:
                query = query.where(Pet.user_id == user_id)

            result = await db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Error getting pet {pet_id}: {e}")
            return None

    @staticmethod
    async def update_pet(db: AsyncSession, pet_id: str, user_id: str, pet_data: PetUpdate) -> Optional[Pet]:
        """Обновление данных питомца"""
        try:
            update_data = pet_data.dict(exclude_unset=True)

            if not update_data:
                return await PetService.get_pet_by_id(db, pet_id, user_id)

            # Расчет возраста, если обновлена дата рождения
            if 'date_of_birth' in update_data and update_data['date_of_birth']:
                # Здесь можно добавить логику пересчета возраста
                pass

            stmt = (
                update(Pet)
                .where(Pet.id == pet_id, Pet.user_id == user_id)
                .values(**update_data, updated_at=datetime.utcnow())
            )

            result = await db.execute(stmt)
            await db.commit()

            if result.rowcount == 0:
                return None

            # Инвалидация кэша
            redis_session = await get_session()
            await redis_session.invalidate_pet_cache(pet_id)
            await redis_session.invalidate_user_pets_cache(user_id)

            return await PetService.get_pet_by_id(db, pet_id, user_id)

        except Exception as e:
            logger.error(f"Pet update failed for {pet_id}: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def delete_pet(db: AsyncSession, pet_id: str, user_id: str) -> bool:
        """Удаление питомца (мягкое удаление)"""
        try:
            stmt = (
                update(Pet)
                .where(Pet.id == pet_id, Pet.user_id == user_id)
                .values(is_active=False, updated_at=datetime.utcnow())
            )

            result = await db.execute(stmt)
            await db.commit()

            if result.rowcount > 0:
                # Инвалидация кэша
                redis_session = await get_session()
                await redis_session.invalidate_pet_cache(pet_id)
                await redis_session.invalidate_user_pets_cache(user_id)

                logger.info(f"Pet {pet_id} deleted successfully")
                return True

            return False

        except Exception as e:
            logger.error(f"Pet deletion failed for {pet_id}: {e}")
            await db.rollback()
            return False

    @staticmethod
    async def get_user_pets(
        db: AsyncSession,
        user_id: str,
        page: int = 1,
        limit: int = 20
    ) -> PetsListResponse:
        """Получение списка питомцев пользователя"""
        try:
            offset = (page - 1) * limit

            # Проверка кэша
            redis_session = await get_session()
            cached_pets = await redis_session.get_cached_user_pets(user_id)

            if cached_pets:
                total = len(cached_pets)
                start = offset
                end = start + limit
                pets_page = cached_pets[start:end]
                pages = (total + limit - 1) // limit

                return PetsListResponse(
                    pets=[PetService.pet_to_profile(Pet(**pet)) for pet in pets_page],
                    total=total,
                    page=page,
                    limit=limit,
                    pages=pages
                )

            # Подсчет общего количества
            count_query = select(func.count()).where(Pet.user_id == user_id, Pet.is_active == True)
            total_result = await db.execute(count_query)
            total = total_result.scalar()

            # Получение питомцев с пагинацией
            query = (
                select(Pet)
                .where(Pet.user_id == user_id, Pet.is_active == True)
                .offset(offset)
                .limit(limit)
            )
            result = await db.execute(query)
            pets = result.scalars().all()

            # Кэширование результатов
            if page == 1 and len(pets) < 50:  # Кэшируем только первую страницу и если не слишком много
                pets_data = [PetService.pet_to_dict(pet) for pet in pets]
                await redis_session.cache_user_pets(user_id, pets_data)

            pages = (total + limit - 1) // limit

            return PetsListResponse(
                pets=[PetService.pet_to_profile(pet) for pet in pets],
                total=total,
                page=page,
                limit=limit,
                pages=pages
            )

        except Exception as e:
            logger.error(f"Error getting user pets for {user_id}: {e}")
            return PetsListResponse(pets=[], total=0, page=page, limit=limit, pages=0)

    @staticmethod
    async def set_pet_avatar(db: AsyncSession, pet_id: str, user_id: str, photo_id: str) -> bool:
        """Установка аватара питомца"""
        try:
            # Получение фотографии
            from app.models.pet_photo import PetPhoto
            photo_query = select(PetPhoto).where(
                PetPhoto.id == photo_id,
                PetPhoto.pet_id == pet_id
            )
            photo_result = await db.execute(photo_query)
            photo = photo_result.scalar_one_or_none()

            if not photo:
                return False

            # Обновление аватара питомца
            stmt = (
                update(Pet)
                .where(Pet.id == pet_id, Pet.user_id == user_id)
                .values(avatar_url=photo.file_url, updated_at=datetime.utcnow())
            )

            result = await db.execute(stmt)
            await db.commit()

            if result.rowcount > 0:
                # Инвалидация кэша
                redis_session = await get_session()
                await redis_session.invalidate_pet_cache(pet_id)
                await redis_session.invalidate_user_pets_cache(user_id)

                logger.info(f"Avatar set for pet {pet_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error setting pet avatar {pet_id}: {e}")
            await db.rollback()
            return False

    @staticmethod
    async def get_pet_stats(db: AsyncSession, user_id: str) -> Dict[str, Any]:
        """Получение статистики питомцев пользователя"""
        try:
            # Общее количество питомцев
            total_query = select(func.count()).where(Pet.user_id == user_id, Pet.is_active == True)
            total_result = await db.execute(total_query)
            total_pets = total_result.scalar()

            # Количество по породам
            breed_query = (
                select(Pet.breed, func.count(Pet.id))
                .where(Pet.user_id == user_id, Pet.is_active == True)
                .group_by(Pet.breed)
            )
            breed_result = await db.execute(breed_query)
            breeds = dict(breed_result.fetchall())

            # Количество по полу
            gender_query = (
                select(Pet.gender, func.count(Pet.id))
                .where(Pet.user_id == user_id, Pet.is_active == True)
                .group_by(Pet.gender)
            )
            gender_result = await db.execute(gender_query)
            genders = dict(gender_result.fetchall())

            return {
                "total_pets": total_pets,
                "breeds": breeds,
                "genders": genders
            }

        except Exception as e:
            logger.error(f"Error getting pet stats for {user_id}: {e}")
            return {"total_pets": 0, "breeds": {}, "genders": {}}

    @staticmethod
    def pet_to_profile(pet: Pet) -> PetProfile:
        """Преобразование модели Pet в схему PetProfile"""
        return PetProfile(
            id=pet.id,
            user_id=pet.user_id,
            name=pet.name,
            breed=pet.breed,
            date_of_birth=pet.date_of_birth,
            age_years=pet.age_years,
            age_months=pet.age_months,
            gender=pet.gender,
            color=pet.color,
            weight_kg=pet.weight_kg,
            size=pet.size,
            energy_level=pet.energy_level,
            friendliness=pet.friendliness,
            is_vaccinated=pet.is_vaccinated,
            is_neutered=pet.is_neutered,
            has_allergies=pet.has_allergies,
            allergies_description=pet.allergies_description,
            special_needs=pet.special_needs,
            medications=pet.medications,
            medical_conditions=pet.medical_conditions,
            is_friendly_with_dogs=pet.is_friendly_with_dogs,
            is_friendly_with_cats=pet.is_friendly_with_cats,
            is_friendly_with_children=pet.is_friendly_with_children,
            behavioral_notes=pet.behavioral_notes,
            walking_frequency=pet.walking_frequency,
            walking_duration_minutes=pet.walking_duration_minutes,
            feeding_schedule=pet.feeding_schedule,
            favorite_activities=pet.favorite_activities,
            walking_notes=pet.walking_notes,
            emergency_contact_name=pet.emergency_contact_name,
            emergency_contact_phone=pet.emergency_contact_phone,
            veterinarian_name=pet.veterinarian_name,
            veterinarian_phone=pet.veterinarian_phone,
            veterinarian_address=pet.veterinarian_address,
            avatar_url=pet.avatar_url,
            photos_count=pet.photos_count,
            created_at=pet.created_at,
            updated_at=pet.updated_at,
            age_string=pet.age_string,
            size_category=pet.size_category
        )

    @staticmethod
    def pet_to_dict(pet: Pet) -> Dict[str, Any]:
        """Преобразование модели Pet в словарь для кэширования"""
        return {
            "id": pet.id,
            "user_id": pet.user_id,
            "name": pet.name,
            "breed": pet.breed,
            "date_of_birth": pet.date_of_birth.isoformat() if pet.date_of_birth else None,
            "age_years": pet.age_years,
            "age_months": pet.age_months,
            "gender": pet.gender,
            "color": pet.color,
            "weight_kg": pet.weight_kg,
            "size": pet.size,
            "energy_level": pet.energy_level,
            "friendliness": pet.friendliness,
            "is_vaccinated": pet.is_vaccinated,
            "is_neutered": pet.is_neutered,
            "has_allergies": pet.has_allergies,
            "allergies_description": pet.allergies_description,
            "special_needs": pet.special_needs,
            "medications": pet.medications,
            "medical_conditions": pet.medical_conditions,
            "is_friendly_with_dogs": pet.is_friendly_with_dogs,
            "is_friendly_with_cats": pet.is_friendly_with_cats,
            "is_friendly_with_children": pet.is_friendly_with_children,
            "behavioral_notes": pet.behavioral_notes,
            "walking_frequency": pet.walking_frequency,
            "walking_duration_minutes": pet.walking_duration_minutes,
            "feeding_schedule": pet.feeding_schedule,
            "favorite_activities": pet.favorite_activities,
            "walking_notes": pet.walking_notes,
            "emergency_contact_name": pet.emergency_contact_name,
            "emergency_contact_phone": pet.emergency_contact_phone,
            "veterinarian_name": pet.veterinarian_name,
            "veterinarian_phone": pet.veterinarian_phone,
            "veterinarian_address": pet.veterinarian_address,
            "avatar_url": pet.avatar_url,
            "photos_count": pet.photos_count,
            "created_at": pet.created_at.isoformat(),
            "updated_at": pet.updated_at.isoformat(),
            "age_string": pet.age_string,
            "size_category": pet.size_category
        }
