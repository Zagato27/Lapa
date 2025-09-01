"""
Менеджер файлов для чата
"""

import logging
import os
import uuid
import aiofiles
from pathlib import Path
from typing import Optional, Dict, Any
import hashlib
from PIL import Image
import mimetypes

from app.config import settings

logger = logging.getLogger(__name__)


class FileManager:
    """Менеджер для работы с файлами в чате"""

    def __init__(self):
        self.upload_dir = Path(settings.upload_path)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save_upload_file(self, file, chat_id: str, user_id: str) -> Dict[str, Any]:
        """Сохранение загруженного файла"""
        try:
            # Генерация уникального имени файла
            file_extension = Path(file.filename).suffix.lower()
            file_id = str(uuid.uuid4())
            file_name = f"{file_id}{file_extension}"

            # Создание директории для чата
            chat_dir = self.upload_dir / chat_id
            chat_dir.mkdir(exist_ok=True)

            # Полный путь к файлу
            file_path = chat_dir / file_name

            # Сохранение файла
            async with aiofiles.open(file_path, 'wb') as buffer:
                content = await file.read()
                await buffer.write(content)

            # Получение информации о файле
            file_size = len(content)
            mime_type = self._get_mime_type(file.filename)

            # Вычисление хэша файла
            file_hash = hashlib.sha256(content).hexdigest()

            # Обработка изображений
            dimensions = None
            thumbnail_path = None

            if mime_type and mime_type.startswith('image/'):
                dimensions = await self._process_image(file_path)
                thumbnail_path = await self._create_thumbnail(file_path, chat_id, file_id)

            return {
                "file_id": file_id,
                "file_name": file_name,
                "original_filename": file.filename,
                "file_path": str(file_path),
                "file_url": f"/uploads/{chat_id}/{file_name}",
                "thumbnail_path": str(thumbnail_path) if thumbnail_path else None,
                "thumbnail_url": f"/uploads/{chat_id}/thumbnails/{file_id}.jpg" if thumbnail_path else None,
                "file_size": file_size,
                "mime_type": mime_type,
                "file_hash": file_hash,
                "width": dimensions[0] if dimensions else None,
                "height": dimensions[1] if dimensions else None
            }

        except Exception as e:
            logger.error(f"Error saving upload file: {e}")
            raise

    async def delete_file(self, file_path: str) -> bool:
        """Удаление файла"""
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                return True
            return False

        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False

    async def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Получение информации о файле"""
        try:
            path = Path(file_path)
            if not path.exists():
                return None

            stat = path.stat()

            return {
                "file_path": str(path),
                "file_size": stat.st_size,
                "created_at": stat.st_ctime,
                "modified_at": stat.st_mtime,
                "exists": True
            }

        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return None

    async def _process_image(self, file_path: Path) -> tuple[int, int]:
        """Обработка изображения и получение размеров"""
        try:
            with Image.open(file_path) as img:
                width, height = img.size

                # Проверка и изменение размера если необходимо
                if width > settings.image_max_width or height > settings.image_max_height:
                    img.thumbnail((settings.image_max_width, settings.image_max_height))
                    img.save(file_path, quality=85)
                    width, height = img.size

                return width, height

        except Exception as e:
            logger.error(f"Error processing image {file_path}: {e}")
            return 0, 0

    async def _create_thumbnail(self, file_path: Path, chat_id: str, file_id: str) -> Optional[Path]:
        """Создание миниатюры для изображения"""
        try:
            with Image.open(file_path) as img:
                # Создание миниатюры
                img.thumbnail((settings.thumbnail_size, settings.thumbnail_size))

                # Создание директории для миниатюр
                thumbnails_dir = self.upload_dir / chat_id / "thumbnails"
                thumbnails_dir.mkdir(exist_ok=True)

                # Сохранение миниатюры
                thumbnail_path = thumbnails_dir / f"{file_id}.jpg"
                img.convert('RGB').save(thumbnail_path, 'JPEG', quality=80)

                return thumbnail_path

        except Exception as e:
            logger.error(f"Error creating thumbnail for {file_path}: {e}")
            return None

    def _get_mime_type(self, filename: str) -> Optional[str]:
        """Определение MIME-типа файла"""
        try:
            mime_type, _ = mimetypes.guess_type(filename)
            return mime_type

        except Exception:
            return None

    def validate_file_type(self, filename: str) -> bool:
        """Проверка допустимости типа файла"""
        try:
            file_extension = Path(filename).suffix.lower()
            return file_extension in settings.allowed_file_types

        except Exception:
            return False

    def validate_file_size(self, file_size: int) -> bool:
        """Проверка размера файла"""
        try:
            max_size = settings.max_file_size_mb * 1024 * 1024
            return file_size <= max_size

        except Exception:
            return False

    async def cleanup_old_files(self, days: int = 30) -> int:
        """Очистка старых файлов"""
        try:
            import time
            from datetime import datetime, timedelta

            cutoff_time = time.time() - (days * 24 * 60 * 60)
            deleted_count = 0

            for file_path in self.upload_dir.rglob('*'):
                if file_path.is_file():
                    if file_path.stat().st_mtime < cutoff_time:
                        file_path.unlink()
                        deleted_count += 1

            logger.info(f"Cleaned up {deleted_count} old files")
            return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up old files: {e}")
            return 0

    def get_upload_stats(self) -> Dict[str, Any]:
        """Получение статистики загрузок"""
        try:
            total_files = 0
            total_size = 0

            for file_path in self.upload_dir.rglob('*'):
                if file_path.is_file():
                    total_files += 1
                    total_size += file_path.stat().st_size

            return {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024),
                "upload_dir": str(self.upload_dir)
            }

        except Exception as e:
            logger.error(f"Error getting upload stats: {e}")
            return {
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0,
                "upload_dir": str(self.upload_dir)
            }
