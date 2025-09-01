"""
Менеджер хранилища для медиафайлов
"""

import logging
import os
import uuid
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)


class StorageManager:
    """Менеджер для работы с различными типами хранилищ"""

    def __init__(self):
        self.storage_backend = settings.storage_backend
        self.upload_path = Path(settings.upload_path)
        self.upload_path.mkdir(parents=True, exist_ok=True)

    async def save_file(
        self,
        file_data: bytes,
        filename: str,
        file_id: str,
        user_id: str
    ) -> Tuple[str, str]:
        """Сохранение файла в хранилище"""
        try:
            if self.storage_backend == "local":
                return await self._save_local_file(file_data, filename, file_id, user_id)
            elif self.storage_backend == "s3":
                return await self._save_s3_file(file_data, filename, file_id, user_id)
            elif self.storage_backend == "cloudinary":
                return await self._save_cloudinary_file(file_data, filename, file_id, user_id)
            else:
                raise ValueError(f"Unsupported storage backend: {self.storage_backend}")

        except Exception as e:
            logger.error(f"Error saving file {filename}: {e}")
            raise

    async def delete_file(self, file_path: str) -> bool:
        """Удаление файла из хранилища"""
        try:
            if self.storage_backend == "local":
                return await self._delete_local_file(file_path)
            elif self.storage_backend == "s3":
                return await self._delete_s3_file(file_path)
            elif self.storage_backend == "cloudinary":
                return await self._delete_cloudinary_file(file_path)
            else:
                raise ValueError(f"Unsupported storage backend: {self.storage_backend}")

        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False

    async def get_file_url(self, file_path: str, expires: int = 3600) -> str:
        """Получение URL файла"""
        try:
            if self.storage_backend == "local":
                return self._get_local_file_url(file_path)
            elif self.storage_backend == "s3":
                return await self._get_s3_file_url(file_path, expires)
            elif self.storage_backend == "cloudinary":
                return await self._get_cloudinary_file_url(file_path, expires)
            else:
                raise ValueError(f"Unsupported storage backend: {self.storage_backend}")

        except Exception as e:
            logger.error(f"Error getting file URL for {file_path}: {e}")
            raise

    async def get_file_size(self, file_path: str) -> int:
        """Получение размера файла"""
        try:
            if self.storage_backend == "local":
                return self._get_local_file_size(file_path)
            elif self.storage_backend == "s3":
                return await self._get_s3_file_size(file_path)
            elif self.storage_backend == "cloudinary":
                return await self._get_cloudinary_file_size(file_path)
            else:
                raise ValueError(f"Unsupported storage backend: {self.storage_backend}")

        except Exception as e:
            logger.error(f"Error getting file size for {file_path}: {e}")
            return 0

    async def _save_local_file(
        self,
        file_data: bytes,
        filename: str,
        file_id: str,
        user_id: str
    ) -> Tuple[str, str]:
        """Сохранение файла локально"""
        # Создание директории пользователя
        user_dir = self.upload_path / user_id
        user_dir.mkdir(exist_ok=True)

        # Создание поддиректории по дате
        date_dir = user_dir / datetime.utcnow().strftime("%Y/%m/%d")
        date_dir.mkdir(parents=True, exist_ok=True)

        # Полное имя файла
        file_extension = Path(filename).suffix
        full_filename = f"{file_id}{file_extension}"
        file_path = date_dir / full_filename

        # Сохранение файла
        with open(file_path, 'wb') as f:
            f.write(file_data)

        # Формирование URL
        file_url = f"/media/{user_id}/{datetime.utcnow().strftime('%Y/%m/%d')}/{full_filename}"

        return str(file_path), file_url

    async def _save_s3_file(
        self,
        file_data: bytes,
        filename: str,
        file_id: str,
        user_id: str
    ) -> Tuple[str, str]:
        """Сохранение файла в Amazon S3"""
        try:
            import boto3
            from botocore.exceptions import NoCredentialsError

            if not settings.aws_access_key_id or not settings.aws_secret_access_key:
                raise ValueError("AWS credentials not configured")

            s3 = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region
            )

            # Ключ файла в S3
            file_extension = Path(filename).suffix
            s3_key = f"media/{user_id}/{datetime.utcnow().strftime('%Y/%m/%d')}/{file_id}{file_extension}"

            # Загрузка файла
            s3.put_object(
                Bucket=settings.s3_bucket_name,
                Key=s3_key,
                Body=file_data,
                ContentType=self._get_content_type(filename),
                ACL='public-read' if settings.s3_public_read else 'private'
            )

            # Формирование URL
            if settings.s3_public_read:
                file_url = f"https://{settings.s3_bucket_name}.s3.amazonaws.com/{s3_key}"
            else:
                file_url = f"s3://{settings.s3_bucket_name}/{s3_key}"

            return s3_key, file_url

        except Exception as e:
            logger.error(f"Error saving file to S3: {e}")
            raise

    async def _save_cloudinary_file(
        self,
        file_data: bytes,
        filename: str,
        file_id: str,
        user_id: str
    ) -> Tuple[str, str]:
        """Сохранение файла в Cloudinary"""
        try:
            import cloudinary
            import cloudinary.uploader

            if not settings.cloudinary_cloud_name or not settings.cloudinary_api_key:
                raise ValueError("Cloudinary credentials not configured")

            cloudinary.config(
                cloud_name=settings.cloudinary_cloud_name,
                api_key=settings.cloudinary_api_key,
                api_secret=settings.cloudinary_api_secret
            )

            # Загрузка файла
            upload_result = cloudinary.uploader.upload(
                file_data,
                public_id=file_id,
                folder=f"media/{user_id}",
                resource_type="auto"
            )

            file_path = upload_result['public_id']
            file_url = upload_result['secure_url']

            return file_path, file_url

        except Exception as e:
            logger.error(f"Error saving file to Cloudinary: {e}")
            raise

    async def _delete_local_file(self, file_path: str) -> bool:
        """Удаление локального файла"""
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting local file {file_path}: {e}")
            return False

    async def _delete_s3_file(self, file_path: str) -> bool:
        """Удаление файла из S3"""
        try:
            import boto3

            s3 = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region
            )

            s3.delete_object(Bucket=settings.s3_bucket_name, Key=file_path)
            return True

        except Exception as e:
            logger.error(f"Error deleting S3 file {file_path}: {e}")
            return False

    async def _delete_cloudinary_file(self, file_path: str) -> bool:
        """Удаление файла из Cloudinary"""
        try:
            import cloudinary
            import cloudinary.uploader

            cloudinary.uploader.destroy(file_path)
            return True

        except Exception as e:
            logger.error(f"Error deleting Cloudinary file {file_path}: {e}")
            return False

    def _get_local_file_url(self, file_path: str) -> str:
        """Получение URL локального файла"""
        # Преобразование пути в URL
        path_parts = Path(file_path).parts
        upload_index = None

        for i, part in enumerate(path_parts):
            if part == "media_uploads":
                upload_index = i
                break

        if upload_index is not None:
            url_parts = path_parts[upload_index + 1:]
            return "/media/" + "/".join(url_parts)

        return file_path

    async def _get_s3_file_url(self, file_path: str, expires: int) -> str:
        """Получение URL файла из S3"""
        try:
            import boto3

            s3 = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region
            )

            if settings.s3_public_read:
                return f"https://{settings.s3_bucket_name}.s3.amazonaws.com/{file_path}"
            else:
                # Генерация подписанного URL
                url = s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': settings.s3_bucket_name, 'Key': file_path},
                    ExpiresIn=expires
                )
                return url

        except Exception as e:
            logger.error(f"Error getting S3 file URL for {file_path}: {e}")
            raise

    async def _get_cloudinary_file_url(self, file_path: str, expires: int) -> str:
        """Получение URL файла из Cloudinary"""
        # Cloudinary URLs уже содержат подпись и срок действия
        return f"https://res.cloudinary.com/{settings.cloudinary_cloud_name}/image/upload/{file_path}"

    def _get_local_file_size(self, file_path: str) -> int:
        """Получение размера локального файла"""
        try:
            return Path(file_path).stat().st_size
        except Exception:
            return 0

    async def _get_s3_file_size(self, file_path: str) -> int:
        """Получение размера файла из S3"""
        try:
            import boto3

            s3 = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region
            )

            response = s3.head_object(Bucket=settings.s3_bucket_name, Key=file_path)
            return response['ContentLength']

        except Exception:
            return 0

    async def _get_cloudinary_file_size(self, file_path: str) -> int:
        """Получение размера файла из Cloudinary"""
        # Для Cloudinary размер файла нужно получать отдельно
        # Это упрощенная версия
        return 0

    def _get_content_type(self, filename: str) -> str:
        """Определение типа контента по имени файла"""
        import mimetypes
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or "application/octet-stream"

    async def get_storage_stats(self) -> Dict[str, Any]:
        """Получение статистики хранилища"""
        try:
            if self.storage_backend == "local":
                return self._get_local_storage_stats()
            elif self.storage_backend == "s3":
                return await self._get_s3_storage_stats()
            elif self.storage_backend == "cloudinary":
                return await self._get_cloudinary_storage_stats()
            else:
                return {}

        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {}

    def _get_local_storage_stats(self) -> Dict[str, Any]:
        """Получение статистики локального хранилища"""
        try:
            total_files = 0
            total_size = 0

            for file_path in self.upload_path.rglob('*'):
                if file_path.is_file():
                    total_files += 1
                    total_size += file_path.stat().st_size

            return {
                "backend": "local",
                "total_files": total_files,
                "total_size": total_size,
                "total_size_mb": total_size / (1024 * 1024),
                "upload_path": str(self.upload_path)
            }

        except Exception as e:
            logger.error(f"Error getting local storage stats: {e}")
            return {}

    async def _get_s3_storage_stats(self) -> Dict[str, Any]:
        """Получение статистики S3 хранилища"""
        try:
            import boto3

            s3 = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region
            )

            # Получение списка объектов
            paginator = s3.get_paginator('list_objects_v2')
            total_files = 0
            total_size = 0

            for page in paginator.paginate(Bucket=settings.s3_bucket_name, Prefix='media/'):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        total_files += 1
                        total_size += obj['Size']

            return {
                "backend": "s3",
                "bucket": settings.s3_bucket_name,
                "total_files": total_files,
                "total_size": total_size,
                "total_size_mb": total_size / (1024 * 1024)
            }

        except Exception as e:
            logger.error(f"Error getting S3 storage stats: {e}")
            return {}

    async def _get_cloudinary_storage_stats(self) -> Dict[str, Any]:
        """Получение статистики Cloudinary хранилища"""
        try:
            import cloudinary
            import cloudinary.api

            cloudinary.config(
                cloud_name=settings.cloudinary_cloud_name,
                api_key=settings.cloudinary_api_key,
                api_secret=settings.cloudinary_api_secret
            )

            # Получение статистики использования
            usage = cloudinary.api.usage()

            return {
                "backend": "cloudinary",
                "total_files": usage.get('resources', 0),
                "total_size": usage.get('storage', {}).get('used', 0),
                "total_size_mb": usage.get('storage', {}).get('used', 0) / (1024 * 1024)
            }

        except Exception as e:
            logger.error(f"Error getting Cloudinary storage stats: {e}")
            return {}
