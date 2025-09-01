"""
API роуты для управления медиафайлами
"""

import logging
from typing import Dict
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File, Form
from fastapi.security import HTTPBearer
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.media_file import (
    MediaFileCreate,
    MediaFileUpdate,
    MediaFileResponse,
    MediaFilesListResponse
)
from app.services.media_service import MediaService
from app.models.media_file import MediaType, MediaStatus

router = APIRouter()
security = HTTPBearer(auto_error=False)

logger = logging.getLogger(__name__)


async def get_current_user(
    request: Request,
    credentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Зависимость для получения текущего пользователя.

    Пытаемся взять user_id из request.state (если пришло через gateway-middleware),
    иначе валидируем JWT из Authorization.
    """
    # Сначала пробуем получить user_id из X-заголовка, затем из request.state
    user_id = request.headers.get('X-User-Id') or getattr(request.state, 'user_id', None)
    if user_id:
        return {"user_id": user_id}

    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Токен не предоставлен")

    # Fallback: валидация JWT локально (используем тот же jose, что и user-service)
    try:
        from jose import jwt
        from app.config import settings
        payload = jwt.decode(credentials.credentials, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Неверный токен")
        return {"user_id": user_id}
    except Exception:
        raise HTTPException(status_code=401, detail="Неверный токен")


@router.post("/upload", response_model=MediaFileResponse, summary="Загрузка файла")
async def upload_file(
    file: UploadFile = File(...),
    album_id: str = Form(None, description="ID альбома"),
    title: str = Form(None, description="Название файла"),
    description: str = Form(None, description="Описание файла"),
    is_public: bool = Form(False, description="Публичный доступ"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Загрузка медиафайла"""
    try:
        # Чтение содержимого файла
        file_data = await file.read()

        # Определение типа медиафайла по расширению
        from app.config import settings
        file_extension = Path(file.filename).suffix.lower()

        if file_extension in settings.allowed_image_types:
            media_type = MediaType.IMAGE
        elif file_extension in settings.allowed_video_types:
            media_type = MediaType.VIDEO
        elif file_extension in settings.allowed_audio_types:
            media_type = MediaType.AUDIO
        else:
            # По умолчанию считаем документом (если поддерживается отдельная логика)
            media_type = MediaType.DOCUMENT

        # Создание медиафайла
        media_file = await MediaService.create_media_file(
            db,
            current_user["user_id"],
            file_data,
            file.filename,
            media_type,
            album_id,
            title
        )

        return MediaService.media_file_to_response(media_file, current_user["user_id"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail="Ошибка загрузки файла")


@router.get("", response_model=MediaFilesListResponse, summary="Получение списка файлов")
async def get_files(
    album_id: str = Query(None, description="Фильтр по альбому"),
    media_type: str = Query(None, description="Фильтр по типу медиа"),
    status: str = Query(None, description="Фильтр по статусу"),
    page: int = Query(1, description="Номер страницы"),
    limit: int = Query(20, description="Количество файлов на странице"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка медиафайлов пользователя"""
    try:
        media_type_enum = None
        if media_type:
            try:
                media_type_enum = MediaType(media_type)
            except Exception:
                media_type_enum = None

        files_response = await MediaService.get_user_media_files(
            db,
            current_user["user_id"],
            page,
            limit,
            media_type=media_type_enum,
            album_id=album_id,
            status=status
        )

        return files_response

    except Exception as e:
        logger.error(f"Error getting files list: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения списка файлов")


@router.get("/{file_id}", response_model=MediaFileResponse, summary="Получение файла по ID")
async def get_file(
    file_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение информации о медиафайле"""
    try:
        media_file = await MediaService.get_media_file_by_id(db, file_id, current_user["user_id"])

        if not media_file:
            raise HTTPException(status_code=404, detail="Файл не найден")

        return MediaService.media_file_to_response(media_file, current_user["user_id"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения файла")


@router.put("/{file_id}", response_model=MediaFileResponse, summary="Обновление файла")
async def update_file(
    file_id: str,
    file_data: MediaFileUpdate,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновление информации о медиафайле"""
    try:
        media_file = await MediaService.update_media_file(db, file_id, current_user["user_id"], file_data)

        if not media_file:
            raise HTTPException(status_code=404, detail="Файл не найден")

        return MediaService.media_file_to_response(media_file, current_user["user_id"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления файла")


@router.delete("/{file_id}", summary="Удаление файла")
async def delete_file(
    file_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удаление медиафайла"""
    try:
        success = await MediaService.delete_media_file(db, file_id, current_user["user_id"])

        if not success:
            raise HTTPException(status_code=404, detail="Файл не найден")

        return {"message": "Файл успешно удален"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления файла")


@router.get("/{file_id}/download", summary="Скачивание файла")
async def download_file(
    file_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Скачивание медиафайла"""
    try:
        media_file = await MediaService.get_media_file_by_id(db, file_id, current_user["user_id"])

        if not media_file:
            raise HTTPException(status_code=404, detail="Файл не найден")

        from app.services.storage_manager import StorageManager
        storage_manager = StorageManager()

        # Возврат файла
        return FileResponse(
            path=media_file.file_path,
            filename=media_file.filename,
            media_type=media_file.mime_type
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка скачивания файла")


@router.get("/{file_id}/thumbnail", summary="Получение миниатюры")
async def get_thumbnail(
    file_id: str,
    size: str = Query("300x300", description="Размер миниатюры"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение миниатюры файла"""
    try:
        media_file = await MediaService.get_media_file_by_id(db, file_id, current_user["user_id"])

        if not media_file:
            raise HTTPException(status_code=404, detail="Файл не найден")

        if not media_file.has_thumbnail:
            raise HTTPException(status_code=404, detail="Миниатюра не найдена")

        return FileResponse(
            path=media_file.thumbnail_path,
            filename=f"thumb_{media_file.filename}",
            media_type="image/jpeg"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting thumbnail for file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения миниатюры")


@router.put("/{file_id}/album", summary="Добавление файла в альбом")
async def add_to_album(
    file_id: str,
    album_id: str = Query(..., description="ID альбома"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Добавление файла в альбом"""
    try:
        success = await MediaService.add_file_to_album(db, file_id, album_id, current_user["user_id"])

        if not success:
            raise HTTPException(status_code=400, detail="Не удалось добавить файл в альбом")

        return {"message": "Файл успешно добавлен в альбом"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding file {file_id} to album {album_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка добавления файла в альбом")


@router.delete("/{file_id}/album", summary="Удаление файла из альбома")
async def remove_from_album(
    file_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удаление файла из альбома"""
    try:
        success = await MediaService.remove_file_from_album(db, file_id, current_user["user_id"])

        if not success:
            raise HTTPException(status_code=400, detail="Не удалось удалить файл из альбома")

        return {"message": "Файл успешно удален из альбома"}

    except Exception as e:
        logger.error(f"Error removing file {file_id} from album: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления файла из альбома")


@router.put("/{file_id}/public", summary="Сделать файл публичным")
async def make_public(
    file_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Сделать файл публичным"""
    try:
        update_data = MediaFileUpdate(is_public=True)
        media_file = await MediaService.update_media_file(db, file_id, current_user["user_id"], update_data)

        if not media_file:
            raise HTTPException(status_code=404, detail="Файл не найден")

        return {"message": "Файл сделан публичным"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error making file {file_id} public: {e}")
        raise HTTPException(status_code=500, detail="Ошибка изменения видимости файла")


@router.put("/{file_id}/private", summary="Сделать файл приватным")
async def make_private(
    file_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Сделать файл приватным"""
    try:
        update_data = MediaFileUpdate(is_public=False)
        media_file = await MediaService.update_media_file(db, file_id, current_user["user_id"], update_data)

        if not media_file:
            raise HTTPException(status_code=404, detail="Файл не найден")

        return {"message": "Файл сделан приватным"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error making file {file_id} private: {e}")
        raise HTTPException(status_code=500, detail="Ошибка изменения видимости файла")
