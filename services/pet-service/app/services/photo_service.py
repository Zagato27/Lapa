"""
Сервис для управления фотографиями питомцев
"""

import logging
import uuid
import os
import aiofiles
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from PIL import Image

from app.config import settings
from app.database.session import get_session
from app.models.pet import Pet
from app.models.pet_photo import PetPhoto
from app.schemas.pet import PetPhotoCreate, PetPhotoResponse

logger = logging.getLogger(__name__)


class PhotoService:
    """Сервис для работы с фотографиями питомцев"""

    UPLOAD_DIR = Path("uploads/pet_photos")
    THUMBNAIL_SIZE = (200, 200)

    @staticmethod
    async def create_upload_dir():
        """Создание директории для загрузок"""
        PhotoService.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    async def save_uploaded_file(file, filename: str) -> str:
        """Сохранение загруженного файла"""
        await PhotoService.create_upload_dir()

        file_path = PhotoService.UPLOAD_DIR / filename
        async with aiofiles.open(file_path, 'wb') as buffer:
            content = await file.read()
            await buffer.write(content)

        return str(file_path)

    @staticmethod
    async def create_thumbnail(image_path: str) -> str:
        """Создание миниатюры изображения"""
        try:
            with Image.open(image_path) as img:
                img.thumbnail(PhotoService.THUMBNAIL_SIZE)
                thumbnail_path = f"{image_path}_thumb.jpg"

                if img.mode != 'RGB':
                    img = img.convert('RGB')

                img.save(thumbnail_path, 'JPEG', quality=85)
                return thumbnail_path

        except Exception as e:
            logger.error(f"Error creating thumbnail for {image_path}: {e}")
            return ""

    @staticmethod
    async def get_image_dimensions(image_path: str) -> tuple[int, int]:
        """Получение размеров изображения"""
        try:
            with Image.open(image_path) as img:
                return img.size
        except Exception as e:
            logger.error(f"Error getting image dimensions for {image_path}: {e}")
            return (0, 0)

    @staticmethod
    async def create_photo(
        db: AsyncSession,
        pet_id: str,
        user_id: str,
        file,
        photo_data: PetPhotoCreate
    ) -> Optional[PetPhoto]:
        """Создание фотографии питомца"""
        try:
            # Проверка существования питомца
            pet = await PhotoService._get_pet_by_id(db, pet_id, user_id)
            if not pet:
                logger.error(f"Pet {pet_id} not found or access denied for user {user_id}")
                return None

            # Проверка лимита фотографий
            photos_count = await PhotoService._count_pet_photos(db, pet_id)
            if photos_count >= settings.max_photos_per_pet:
                logger.error(f"Maximum photos limit reached for pet {pet_id}")
                return None

            # Генерация имени файла
            file_extension = Path(file.filename).suffix.lower()
            filename = f"{uuid.uuid4()}{file_extension}"

            # Сохранение файла
            file_path = await PhotoService.save_uploaded_file(file, filename)

            # Получение размеров изображения
            width, height = await PhotoService.get_image_dimensions(file_path)

            # Создание миниатюры
            thumbnail_path = await PhotoService.create_thumbnail(file_path)

            # Создание записи в БД
            photo_id = str(uuid.uuid4())

            photo = PetPhoto(
                id=photo_id,
                pet_id=pet_id,
                filename=filename,
                original_filename=file.filename,
                file_path=file_path,
                file_url=f"/uploads/pet_photos/{filename}",
                file_size=os.path.getsize(file_path),
                mime_type=file.content_type or "image/jpeg",
                width=width,
                height=height,
                thumbnail_path=thumbnail_path,
                thumbnail_url=f"/uploads/pet_photos/{Path(thumbnail_path).name}" if thumbnail_path else None,
                photo_type=photo_data.photo_type,
                description=photo_data.description,
                tags=photo_data.tags,
                uploaded_by=user_id
            )

            db.add(photo)

            # Обновление количества фотографий у питомца
            if photo.photo_type == "avatar":
                await PhotoService._set_pet_avatar(db, pet_id, photo.file_url)

            await db.commit()
            await db.refresh(photo)

            # Инвалидация кэша
            redis_session = await get_session()
            await redis_session.invalidate_pet_cache(pet_id)
            await redis_session.invalidate_user_pets_cache(user_id)

            logger.info(f"Photo created successfully: {photo.filename} for pet {pet_id}")
            return photo

        except Exception as e:
            logger.error(f"Photo creation failed: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def get_pet_photos(
        db: AsyncSession,
        pet_id: str,
        user_id: str,
        photo_type: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Получение фотографий питомца"""
        try:
            # Проверка доступа к питомцу
            pet = await PhotoService._get_pet_by_id(db, pet_id, user_id)
            if not pet:
                return {"photos": [], "total": 0, "page": page, "limit": limit, "pages": 0}

            offset = (page - 1) * limit

            query = select(PetPhoto).where(
                PetPhoto.pet_id == pet_id,
                PetPhoto.is_active == True
            )

            if photo_type:
                query = query.where(PetPhoto.photo_type == photo_type)

            # Подсчет общего количества
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await db.execute(count_query)
            total = total_result.scalar()

            # Получение фотографий с пагинацией
            query = query.offset(offset).limit(limit)
            result = await db.execute(query)
            photos = result.scalars().all()

            pages = (total + limit - 1) // limit

            return {
                "photos": [PhotoService.photo_to_response(photo) for photo in photos],
                "total": total,
                "page": page,
                "limit": limit,
                "pages": pages
            }

        except Exception as e:
            logger.error(f"Error getting pet photos for {pet_id}: {e}")
            return {"photos": [], "total": 0, "page": page, "limit": limit, "pages": 0}

    @staticmethod
    async def delete_photo(db: AsyncSession, photo_id: str, user_id: str) -> bool:
        """Удаление фотографии"""
        try:
            # Получение фотографии
            photo = await PhotoService._get_photo_by_id(db, photo_id)
            if not photo:
                return False

            # Проверка доступа через питомца
            pet = await PhotoService._get_pet_by_id(db, photo.pet_id, user_id)
            if not pet:
                return False

            # Удаление файлов
            try:
                if os.path.exists(photo.file_path):
                    os.remove(photo.file_path)
                if photo.thumbnail_path and os.path.exists(photo.thumbnail_path):
                    os.remove(photo.thumbnail_path)
            except Exception as e:
                logger.warning(f"Error deleting files for photo {photo_id}: {e}")

            # Мягкое удаление из БД
            stmt = (
                update(PetPhoto)
                .where(PetPhoto.id == photo_id)
                .values(is_active=False, updated_at=datetime.utcnow())
            )

            result = await db.execute(stmt)
            await db.commit()

            if result.rowcount > 0:
                # Инвалидация кэша
                redis_session = await get_session()
                await redis_session.invalidate_pet_cache(photo.pet_id)
                await redis_session.invalidate_user_pets_cache(user_id)

                logger.info(f"Photo {photo_id} deleted successfully")
                return True

            return False

        except Exception as e:
            logger.error(f"Photo deletion failed for {photo_id}: {e}")
            await db.rollback()
            return False

    @staticmethod
    async def set_as_avatar(db: AsyncSession, photo_id: str, user_id: str) -> bool:
        """Установка фотографии как аватара питомца"""
        try:
            # Получение фотографии
            photo = await PhotoService._get_photo_by_id(db, photo_id)
            if not photo:
                return False

            # Проверка доступа через питомца
            pet = await PhotoService._get_pet_by_id(db, photo.pet_id, user_id)
            if not pet:
                return False

            # Установка как аватара
            return await PhotoService._set_pet_avatar(db, photo.pet_id, photo.file_url)

        except Exception as e:
            logger.error(f"Error setting photo as avatar {photo_id}: {e}")
            await db.rollback()
            return False

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
    async def _get_photo_by_id(db: AsyncSession, photo_id: str) -> Optional[PetPhoto]:
        """Получение фотографии по ID"""
        query = select(PetPhoto).where(
            PetPhoto.id == photo_id,
            PetPhoto.is_active == True
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def _count_pet_photos(db: AsyncSession, pet_id: str) -> int:
        """Подсчет количества фотографий питомца"""
        query = select(func.count()).where(
            PetPhoto.pet_id == pet_id,
            PetPhoto.is_active == True
        )
        result = await db.execute(query)
        return result.scalar()

    @staticmethod
    async def _set_pet_avatar(db: AsyncSession, pet_id: str, avatar_url: str) -> bool:
        """Установка аватара питомца"""
        try:
            stmt = (
                update(Pet)
                .where(Pet.id == pet_id)
                .values(avatar_url=avatar_url, updated_at=datetime.utcnow())
            )

            result = await db.execute(stmt)
            await db.commit()

            return result.rowcount > 0

        except Exception as e:
            logger.error(f"Error setting pet avatar {pet_id}: {e}")
            await db.rollback()
            return False

    @staticmethod
    def photo_to_response(photo: PetPhoto) -> PetPhotoResponse:
        """Преобразование модели PetPhoto в схему PetPhotoResponse"""
        return PetPhotoResponse(
            id=photo.id,
            pet_id=photo.pet_id,
            filename=photo.filename,
            original_filename=photo.original_filename,
            file_url=photo.file_url,
            file_size=photo.file_size,
            mime_type=photo.mime_type,
            width=photo.width,
            height=photo.height,
            thumbnail_url=photo.thumbnail_url,
            photo_type=photo.photo_type,
            description=photo.description,
            tags=photo.tags,
            uploaded_by=photo.uploaded_by,
            created_at=photo.created_at,
            updated_at=photo.updated_at,
            file_size_mb=photo.file_size_mb,
            is_image=photo.is_image,
            is_avatar=photo.is_avatar
        )
