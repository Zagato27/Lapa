"""
Основной сервис для управления медиафайлами
"""

import logging
import uuid
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, desc
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database.session import get_session
from app.models.media_file import MediaFile, MediaType, MediaStatus, StorageBackend
from app.models.media_album import MediaAlbum, AlbumType, AlbumStatus
from app.models.media_access import MediaAccess, AccessType, AccessLevel, AccessStatus
from app.models.media_metadata import MediaMetadata
from app.models.media_variant import MediaVariant, VariantType, VariantStatus
from app.schemas.media_file import (
    MediaFileCreate,
    MediaFileUpdate,
    MediaFileResponse,
    MediaFilesListResponse
)
from app.schemas.media_album import (
    MediaAlbumCreate,
    MediaAlbumUpdate,
    MediaAlbumResponse
)

logger = logging.getLogger(__name__)


class MediaService:
    """Сервис для работы с медиафайлами"""

    @staticmethod
    async def create_media_file(
        db: AsyncSession,
        owner_id: str,
        file_data: bytes,
        filename: str,
        media_type: MediaType,
        album_id: Optional[str] = None,
        title: Optional[str] = None
    ) -> MediaFile:
        """Создание медиафайла.

        - Валидирует размер и тип файла согласно `settings`
        - Применяет rate-limit через Redis
        - Сохраняет файл через `StorageManager`
        - Создаёт запись `MediaFile` и при необходимости обновляет статистику альбома
        - Кэширует файл и планирует асинхронную обработку
        Используется эндпоинтом `POST /api/v1/files/upload`.
        """
        try:
            # Проверка размера файла
            file_size = len(file_data)
            if media_type == MediaType.IMAGE and file_size > settings.max_image_size_mb * 1024 * 1024:
                raise ValueError(f"Image file size exceeds limit of {settings.max_image_size_mb}MB")
            elif media_type == MediaType.VIDEO and file_size > settings.max_video_size_mb * 1024 * 1024:
                raise ValueError(f"Video file size exceeds limit of {settings.max_video_size_mb}MB")
            elif file_size > settings.max_file_size_mb * 1024 * 1024:
                raise ValueError(f"File size exceeds limit of {settings.max_file_size_mb}MB")

            # Проверка типа файла
            if not MediaService._validate_file_type(filename, media_type):
                raise ValueError(f"Invalid file type for {media_type.value}")

            # Проверка rate limiting
            redis_session = await get_session()
            if not await redis_session.check_rate_limit(owner_id, "upload"):
                raise ValueError("Upload rate limit exceeded")

            # Генерация ID файла
            file_id = str(uuid.uuid4())

            # Сохранение файла
            from app.services.storage_manager import StorageManager
            storage_manager = StorageManager()
            file_path, file_url = await storage_manager.save_file(file_data, filename, file_id, owner_id)

            # Создание записи файла
            media_file = MediaFile(
                id=file_id,
                filename=filename,
                file_path=file_path,
                file_url=file_url,
                media_type=media_type,
                storage_backend=settings.storage_backend,
                owner_id=owner_id,
                album_id=album_id,
                file_size=file_size,
                title=title
            )

            db.add(media_file)

            # Добавление файла в альбом
            if album_id:
                album = await MediaService._get_album(db, album_id)
                if album:
                    album.add_file(file_size, media_type.value)

            # Обновление статистики хранилища
            await redis_session.increment_storage_usage(owner_id, file_size)

            await db.commit()
            await db.refresh(media_file)

            # Кэширование файла
            file_data_dict = MediaService.media_file_to_dict(media_file)
            await redis_session.cache_media_file(file_id, file_data_dict)

            # Асинхронная обработка файла
            await MediaService._schedule_processing(media_file)

            logger.info(f"Media file created: {file_id} by user {owner_id}")
            return media_file

        except Exception as e:
            logger.error(f"Media file creation failed: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def get_media_file_by_id(
        db: AsyncSession,
        file_id: str,
        user_id: Optional[str] = None
    ) -> Optional[MediaFile]:
        """Получение медиафайла по ID с проверкой доступа.

        Сначала проверяется кэш в Redis. Если запись найдена, она
        преобразуется обратно в модель с корректными Enum типами.
        Затем выполняется проверка прав доступа пользователя.
        Используется многими файловыми эндпоинтами.
        """
        try:
            # Проверка кэша
            redis_session = await get_session()
            cached_file = await redis_session.get_cached_media_file(file_id)

            if cached_file:
                media_file = MediaService._media_file_from_cache_dict(cached_file)
                # Проверка доступа
                if await MediaService._user_has_access_to_file(db, user_id, file_id):
                    return media_file

            # Получение из базы данных
            query = select(MediaFile).where(MediaFile.id == file_id)
            result = await db.execute(query)
            media_file = result.scalar_one_or_none()

            if media_file and await MediaService._user_has_access_to_file(db, user_id, file_id):
                # Кэширование
                file_data = MediaService.media_file_to_dict(media_file)
                await redis_session.cache_media_file(file_id, file_data)
                return media_file

            return None

        except Exception as e:
            logger.error(f"Error getting media file {file_id}: {e}")
            return None

    @staticmethod
    async def get_user_media_files(
        db: AsyncSession,
        user_id: str,
        page: int = 1,
        limit: int = 20,
        media_type: Optional[MediaType] = None,
        album_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> MediaFilesListResponse:
        """Получение медиафайлов пользователя с пагинацией и фильтрами.

        Фильтры по типу и статусу безопасно приводятся к Enum.
        Результат не кэшируется напрямую здесь, но файлы кэшируются поштучно.
        Используется эндпоинтом `GET /api/v1/files`.
        """
        try:
            offset = (page - 1) * limit

            # Построение запроса
            query = select(MediaFile).where(MediaFile.owner_id == user_id)

            if media_type:
                query = query.where(MediaFile.media_type == (
                    media_type if isinstance(media_type, MediaType) else MediaType(media_type)
                ))
            if album_id:
                query = query.where(MediaFile.album_id == album_id)
            if status:
                safe_status = status
                try:
                    safe_status = MediaStatus(status)  # приведение к Enum при необходимости
                except Exception:
                    pass
                query = query.where(MediaFile.status == safe_status)

            # Подсчет общего количества
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await db.execute(count_query)
            total = total_result.scalar()

            # Получение файлов с пагинацией
            query = query.order_by(desc(MediaFile.created_at)).offset(offset).limit(limit)
            result = await db.execute(query)
            files = result.scalars().all()

            pages = (total + limit - 1) // limit

            return MediaFilesListResponse(
                files=[MediaService.media_file_to_response(file, user_id) for file in files],
                total=total,
                page=page,
                limit=limit,
                pages=pages
            )

        except Exception as e:
            logger.error(f"Error getting user media files for {user_id}: {e}")
            return MediaFilesListResponse(files=[], total=0, page=page, limit=limit, pages=0)

    @staticmethod
    async def update_media_file(
        db: AsyncSession,
        file_id: str,
        user_id: str,
        file_data: MediaFileUpdate
    ) -> Optional[MediaFile]:
        """Обновление медиафайла"""
        try:
            media_file = await MediaService.get_media_file_by_id(db, file_id, user_id)
            if not media_file:
                return None

            # Проверка прав на обновление
            if media_file.owner_id != user_id:
                raise ValueError("Cannot update other user's files")

            update_data = file_data.dict(exclude_unset=True)

            if not update_data:
                return media_file

            stmt = (
                update(MediaFile)
                .where(MediaFile.id == file_id)
                .values(**update_data, updated_at=datetime.utcnow())
            )

            result = await db.execute(stmt)
            await db.commit()

            if result.rowcount > 0:
                # Получение обновленного файла
                updated_file = await MediaService.get_media_file_by_id(db, file_id, user_id)

                # Инвалидация кэша
                redis_session = await get_session()
                await redis_session.invalidate_media_file_cache(file_id)

                return updated_file

            return media_file

        except Exception as e:
            logger.error(f"Media file update failed for {file_id}: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def delete_media_file(
        db: AsyncSession,
        file_id: str,
        user_id: str
    ) -> bool:
        """Удаление медиафайла"""
        try:
            media_file = await MediaService.get_media_file_by_id(db, file_id, user_id)
            if not media_file:
                return False

            # Проверка прав на удаление
            if media_file.owner_id != user_id:
                raise ValueError("Cannot delete other user's files")

            # Удаление файла из хранилища
            storage_manager = StorageManager()
            await storage_manager.delete_file(media_file.file_path)

            # Обновление статистики хранилища
            redis_session = await get_session()
            await redis_session.decrement_storage_usage(user_id, media_file.file_size)

            # Удаление из альбома
            if media_file.album_id:
                album = await MediaService._get_album(db, media_file.album_id)
                if album:
                    album.remove_file(media_file.file_size, media_file.media_type.value)

            # Удаление файла
            await db.delete(media_file)
            await db.commit()

            # Инвалидация кэша
            await redis_session.invalidate_media_file_cache(file_id)

            logger.info(f"Media file {file_id} deleted by user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Media file deletion failed for {file_id}: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def create_album(
        db: AsyncSession,
        owner_id: str,
        album_data: MediaAlbumCreate
    ) -> MediaAlbum:
        """Создание альбома"""
        try:
            album_id = str(uuid.uuid4())

            album = MediaAlbum(
                id=album_id,
                name=album_data.name,
                album_type=album_data.album_type,
                owner_id=owner_id,
                description=album_data.description,
                pet_id=album_data.pet_id,
                order_id=album_data.order_id,
                is_public=album_data.is_public,
                is_shared=album_data.is_shared,
                max_files=album_data.max_files,
                max_file_size_mb=album_data.max_file_size_mb
            )

            if album_data.allowed_types:
                album.allowed_types = album_data.allowed_types

            db.add(album)
            await db.commit()
            await db.refresh(album)

            logger.info(f"Album created: {album_id} by user {owner_id}")
            return album

        except Exception as e:
            logger.error(f"Album creation failed: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def get_album_by_id(
        db: AsyncSession,
        album_id: str,
        user_id: Optional[str] = None
    ) -> Optional[MediaAlbum]:
        """Получение альбома по ID"""
        try:
            query = select(MediaAlbum).where(MediaAlbum.id == album_id)
            result = await db.execute(query)
            album = result.scalar_one_or_none()

            if album:
                # Проверка доступа
                if album.is_public or album.owner_id == user_id:
                    return album

            return None

        except Exception as e:
            logger.error(f"Error getting album {album_id}: {e}")
            return None

    @staticmethod
    async def add_file_to_album(
        db: AsyncSession,
        file_id: str,
        album_id: str,
        user_id: str
    ) -> bool:
        """Добавление файла в альбом"""
        try:
            media_file = await MediaService.get_media_file_by_id(db, file_id, user_id)
            album = await MediaService.get_album_by_id(db, album_id, user_id)

            if not media_file or not album:
                return False

            # Проверка прав
            if media_file.owner_id != user_id or album.owner_id != user_id:
                raise ValueError("Cannot modify other user's files or albums")

            # Проверка места в альбоме
            if not album.can_upload:
                raise ValueError("Album is full or does not allow uploads")

            # Обновление файла
            media_file.album_id = album_id
            await db.commit()

            # Обновление статистики альбома
            album.add_file(media_file.file_size, media_file.media_type.value)

            # Инвалидация кэша
            redis_session = await get_session()
            await redis_session.invalidate_album_files_cache(album_id)

            return True

        except Exception as e:
            logger.error(f"Error adding file {file_id} to album {album_id}: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def remove_file_from_album(
        db: AsyncSession,
        file_id: str,
        user_id: str
    ) -> bool:
        """Удаление файла из альбома"""
        try:
            media_file = await MediaService.get_media_file_by_id(db, file_id, user_id)
            if not media_file or not media_file.album_id:
                return False

            previous_album_id = media_file.album_id
            album = await MediaService._get_album(db, previous_album_id)
            if album:
                album.remove_file(media_file.file_size, media_file.media_type.value)

            media_file.album_id = None
            await db.commit()

            # Инвалидация кэша
            redis_session = await get_session()
            if previous_album_id:
                await redis_session.invalidate_album_files_cache(previous_album_id)

            return True

        except Exception as e:
            logger.error(f"Error removing file {file_id} from album: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def _validate_file_type(filename: str, media_type: MediaType) -> bool:
        """Проверка типа файла"""
        file_extension = Path(filename).suffix.lower()

        if media_type == MediaType.IMAGE:
            return file_extension in settings.allowed_image_types
        elif media_type == MediaType.VIDEO:
            return file_extension in settings.allowed_video_types
        elif media_type == MediaType.AUDIO:
            return file_extension in settings.allowed_audio_types

        return False

    @staticmethod
    async def _user_has_access_to_file(
        db: AsyncSession,
        user_id: Optional[str],
        file_id: str
    ) -> bool:
        """Проверка доступа пользователя к файлу"""
        try:
            if not user_id:
                # Проверка публичного доступа
                media_file = await MediaService._get_media_file(db, file_id)
                return media_file and media_file.is_public

            # Проверка прав владельца
            media_file = await MediaService._get_media_file(db, file_id)
            if media_file and media_file.owner_id == user_id:
                return True

            # Проверка специального доступа
            access = await MediaService._get_file_access(db, file_id, user_id)
            return access and access.can_view

        except Exception:
            return False

    @staticmethod
    async def _get_media_file(db: AsyncSession, file_id: str) -> Optional[MediaFile]:
        """Получение медиафайла без проверки доступа"""
        try:
            query = select(MediaFile).where(MediaFile.id == file_id)
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except Exception:
            return None

    @staticmethod
    async def _get_album(db: AsyncSession, album_id: str) -> Optional[MediaAlbum]:
        """Получение альбома"""
        try:
            query = select(MediaAlbum).where(MediaAlbum.id == album_id)
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except Exception:
            return None

    @staticmethod
    async def _get_file_access(db: AsyncSession, file_id: str, user_id: str) -> Optional[MediaAccess]:
        """Получение доступа к файлу"""
        try:
            query = select(MediaAccess).where(
                and_(
                    MediaAccess.media_file_id == file_id,
                    or_(
                        MediaAccess.user_id == user_id,
                        MediaAccess.granted_by == user_id
                    ),
                    MediaAccess.status == AccessStatus.ACTIVE
                )
            )
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except Exception:
            return None

    @staticmethod
    async def _schedule_processing(media_file: MediaFile):
        """Планирование обработки файла"""
        try:
            # Установка статуса обработки
            redis_session = await get_session()
            processing_status = {
                "status": "queued",
                "progress": 0,
                "message": "File queued for processing",
                "started_at": datetime.utcnow().isoformat()
            }
            await redis_session.set_processing_status(media_file.id, processing_status)

            # Здесь можно добавить задачу в очередь обработки
            # (например, через Celery или другую систему очередей)

        except Exception as e:
            logger.error(f"Error scheduling processing for file {media_file.id}: {e}")

    @staticmethod
    def media_file_to_response(media_file: MediaFile, user_id: str) -> MediaFileResponse:
        """Преобразование модели MediaFile в схему MediaFileResponse"""
        return MediaFileResponse(
            id=media_file.id,
            filename=media_file.filename,
            file_path=media_file.file_path,
            file_url=media_file.file_url,
            public_url=media_file.public_url,
            media_type=media_file.media_type,
            status=media_file.status,
            storage_backend=media_file.storage_backend,
            owner_id=media_file.owner_id,
            is_public=media_file.is_public,
            album_id=media_file.album_id,
            file_size=media_file.file_size,
            mime_type=media_file.mime_type,
            width=media_file.width,
            height=media_file.height,
            duration=media_file.duration,
            processed_at=media_file.processed_at,
            thumbnail_path=media_file.thumbnail_path,
            thumbnail_url=media_file.thumbnail_url,
            optimized_path=media_file.optimized_path,
            optimized_url=media_file.optimized_url,
            file_hash=media_file.file_hash,
            title=media_file.title,
            description=media_file.description,
            tags=media_file.tags,
            colors=media_file.colors,
            location=media_file.location,
            view_count=media_file.view_count,
            download_count=media_file.download_count,
            created_at=media_file.created_at,
            expires_at=media_file.expires_at,
            last_accessed_at=media_file.last_accessed_at,
            is_image=media_file.is_image,
            is_video=media_file.is_video,
            is_audio=media_file.is_audio,
            is_ready=media_file.is_ready,
            is_expired=media_file.is_expired,
            file_size_mb=media_file.file_size_mb,
            compression_ratio=media_file.compression_ratio,
            aspect_ratio=media_file.aspect_ratio,
            has_thumbnail=media_file.has_thumbnail
        )

    @staticmethod
    def media_file_to_dict(media_file: MediaFile) -> Dict[str, Any]:
        """Преобразование модели MediaFile в словарь для кэширования"""
        return {
            "id": media_file.id,
            "filename": media_file.filename,
            "file_path": media_file.file_path,
            "file_url": media_file.file_url,
            "public_url": media_file.public_url,
            "media_type": media_file.media_type.value,
            "status": media_file.status.value,
            "storage_backend": media_file.storage_backend.value,
            "owner_id": media_file.owner_id,
            "is_public": media_file.is_public,
            "album_id": media_file.album_id,
            "file_size": media_file.file_size,
            "mime_type": media_file.mime_type,
            "width": media_file.width,
            "height": media_file.height,
            "duration": media_file.duration,
            "processed_at": media_file.processed_at.isoformat() if media_file.processed_at else None,
            "thumbnail_path": media_file.thumbnail_path,
            "thumbnail_url": media_file.thumbnail_url,
            "optimized_path": media_file.optimized_path,
            "optimized_url": media_file.optimized_url,
            "file_hash": media_file.file_hash,
            "title": media_file.title,
            "description": media_file.description,
            "tags": media_file.tags,
            "colors": media_file.colors,
            "location": media_file.location,
            "view_count": media_file.view_count,
            "download_count": media_file.download_count,
            "created_at": media_file.created_at.isoformat(),
            "expires_at": media_file.expires_at.isoformat() if media_file.expires_at else None,
            "last_accessed_at": media_file.last_accessed_at.isoformat() if media_file.last_accessed_at else None
        }

    @staticmethod
    def _media_file_from_cache_dict(data: Dict[str, Any]) -> MediaFile:
        """Восстанавливает объект `MediaFile` из словаря кэша.

        Приводит строковые значения к Enum типам, заполняет опциональные поля.
        Предназначено только для чтения/отдачи в ответы, объект не прикреплён к сессии.
        """
        mf = MediaFile(
            id=data.get("id"),
            filename=data.get("filename"),
            file_path=data.get("file_path"),
            file_url=data.get("file_url"),
            public_url=data.get("public_url"),
            media_type=MediaType(data.get("media_type")) if data.get("media_type") else None,
            status=MediaStatus(data.get("status")) if data.get("status") else None,
            storage_backend=StorageBackend(data.get("storage_backend")) if data.get("storage_backend") else None,
            owner_id=data.get("owner_id"),
            is_public=data.get("is_public", False),
            album_id=data.get("album_id"),
            file_size=data.get("file_size", 0),
            mime_type=data.get("mime_type"),
            width=data.get("width"),
            height=data.get("height"),
            duration=data.get("duration"),
            processed_at=None,
            thumbnail_path=data.get("thumbnail_path"),
            thumbnail_url=data.get("thumbnail_url"),
            optimized_path=data.get("optimized_path"),
            optimized_url=data.get("optimized_url"),
            file_hash=data.get("file_hash"),
            title=data.get("title"),
            description=data.get("description"),
            tags=data.get("tags"),
            colors=data.get("colors"),
            location=data.get("location"),
            view_count=data.get("view_count", 0),
            download_count=data.get("download_count", 0),
        )
        # Дополнительные метки времени
        try:
            from datetime import datetime
            if data.get("created_at"):
                mf.created_at = datetime.fromisoformat(data["created_at"])  # type: ignore[attr-defined]
            if data.get("expires_at"):
                mf.expires_at = datetime.fromisoformat(data["expires_at"])  # type: ignore[attr-defined]
            if data.get("last_accessed_at"):
                mf.last_accessed_at = datetime.fromisoformat(data["last_accessed_at"])  # type: ignore[attr-defined]
        except Exception:
            pass
        return mf

    @staticmethod
    def album_to_response(album) -> Dict[str, Any]:
        """Преобразование модели MediaAlbum в схему ответа"""
        return {
            "id": album.id,
            "name": album.name,
            "description": album.description,
            "album_type": album.album_type.value,
            "status": album.status.value,
            "owner_id": album.owner_id,
            "pet_id": album.pet_id,
            "order_id": album.order_id,
            "is_public": album.is_public,
            "is_shared": album.is_shared,
            "allow_upload": album.allow_upload,
            "allow_download": album.allow_download,
            "max_files": album.max_files,
            "max_file_size_mb": album.max_file_size_mb,
            "allowed_types": album.allowed_types,
            "cover_file_id": album.cover_file_id,
            "total_files": album.total_files,
            "total_size": album.total_size,
            "image_count": album.image_count,
            "video_count": album.video_count,
            "audio_count": album.audio_count,
            "tags": album.tags,
            "created_at": album.created_at.isoformat(),
            "updated_at": album.updated_at.isoformat(),
            "last_activity_at": album.last_activity_at.isoformat() if album.last_activity_at else None,
            "is_active": album.is_active,
            "is_archived": album.is_archived,
            "is_deleted": album.is_deleted,
            "total_size_mb": album.total_size_mb,
            "total_size_gb": album.total_size_gb,
            "can_upload": album.can_upload,
            "can_download": album.can_download,
            "has_space": album.has_space
        }
