"""
API роуты для управления файлами
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File
from fastapi.security import HTTPBearer
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path

from app.database import get_db
from app.schemas.message import MessageAttachmentCreate, MessageAttachmentResponse
from app.services.message_service import MessageService
from app.services.file_manager import FileManager

router = APIRouter()
security = HTTPBearer(auto_error=False)

logger = logging.getLogger(__name__)


async def get_current_user(
    request: Request,
    credentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Зависимость для получения текущего пользователя"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Токен не предоставлен")

    # Здесь должна быть валидация токена через API Gateway
    # Пока что просто возвращаем данные из request
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Неверный токен")

    return {"user_id": user_id}


@router.post("/upload", response_model=MessageAttachmentResponse, summary="Загрузка файла")
async def upload_file(
    chat_id: str = Query(..., description="ID чата"),
    file: UploadFile = File(...),
    caption: str = Query(None, description="Подпись к файлу"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Загрузка файла в чат"""
    try:
        # Инициализация менеджера файлов
        file_manager = FileManager()

        # Проверка типа файла
        if not file_manager.validate_file_type(file.filename):
            raise HTTPException(status_code=400, detail="Недопустимый тип файла")

        # Загрузка файла
        file_info = await file_manager.save_upload_file(file, chat_id, current_user["user_id"])

        # Создание вложения в сообщении
        attachment_data = MessageAttachmentCreate(
            attachment_type=file_info.get("attachment_type", "document"),
            file=file,
            caption=caption
        )

        attachment = await MessageService.create_attachment(db, chat_id, current_user["user_id"], attachment_data)

        # Обновление информации о файле
        attachment.file_path = file_info["file_path"]
        attachment.file_url = file_info["file_url"]
        attachment.thumbnail_path = file_info.get("thumbnail_path")
        attachment.thumbnail_url = file_info.get("thumbnail_url")
        attachment.file_size = file_info["file_size"]
        attachment.mime_type = file_info.get("mime_type")
        attachment.width = file_info.get("width")
        attachment.height = file_info.get("height")

        await db.commit()
        await db.refresh(attachment)

        return MessageService.attachment_to_response(attachment)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file to chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка загрузки файла")


@router.get("/download/{attachment_id}", summary="Скачивание файла")
async def download_file(
    attachment_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Скачивание файла по ID вложения"""
    try:
        # Получение вложения
        from app.models.message_attachment import MessageAttachment
        attachment_query = db.execute(
            select(MessageAttachment).where(MessageAttachment.id == attachment_id)
        )
        attachment_result = await attachment_query
        attachment = attachment_result.scalar_one_or_none()

        if not attachment:
            raise HTTPException(status_code=404, detail="Файл не найден")

        # Проверка прав доступа к файлу
        message = await MessageService.get_message_by_id(db, attachment.message_id, current_user["user_id"])
        if not message:
            raise HTTPException(status_code=403, detail="Нет доступа к файлу")

        # Проверка существования файла
        file_manager = FileManager()
        file_info = await file_manager.get_file_info(attachment.file_path)

        if not file_info or not file_info["exists"]:
            raise HTTPException(status_code=404, detail="Файл не найден на сервере")

        # Возврат файла
        return FileResponse(
            path=attachment.file_path,
            filename=attachment.original_filename,
            media_type=attachment.mime_type
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file {attachment_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка скачивания файла")


@router.get("/thumbnail/{attachment_id}", summary="Получение миниатюры")
async def get_thumbnail(
    attachment_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение миниатюры изображения"""
    try:
        # Получение вложения
        from app.models.message_attachment import MessageAttachment
        attachment_query = db.execute(
            select(MessageAttachment).where(MessageAttachment.id == attachment_id)
        )
        attachment_result = await attachment_query
        attachment = attachment_result.scalar_one_or_none()

        if not attachment:
            raise HTTPException(status_code=404, detail="Файл не найден")

        # Проверка, что это изображение
        if not attachment.thumbnail_path:
            raise HTTPException(status_code=400, detail="Миниатюра недоступна")

        # Проверка прав доступа
        message = await MessageService.get_message_by_id(db, attachment.message_id, current_user["user_id"])
        if not message:
            raise HTTPException(status_code=403, detail="Нет доступа к файлу")

        # Проверка существования миниатюры
        file_manager = FileManager()
        thumbnail_info = await file_manager.get_file_info(attachment.thumbnail_path)

        if not thumbnail_info or not thumbnail_info["exists"]:
            raise HTTPException(status_code=404, detail="Миниатюра не найдена")

        # Возврат миниатюры
        return FileResponse(
            path=attachment.thumbnail_path,
            filename=f"thumb_{attachment.original_filename}",
            media_type="image/jpeg"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting thumbnail for {attachment_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения миниатюры")


@router.delete("/{attachment_id}", summary="Удаление файла")
async def delete_file(
    attachment_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удаление файла и вложения"""
    try:
        # Получение вложения
        from app.models.message_attachment import MessageAttachment
        attachment_query = db.execute(
            select(MessageAttachment).where(MessageAttachment.id == attachment_id)
        )
        attachment_result = await attachment_query
        attachment = attachment_result.scalar_one_or_none()

        if not attachment:
            raise HTTPException(status_code=404, detail="Файл не найден")

        # Проверка прав доступа
        message = await MessageService.get_message_by_id(db, attachment.message_id, current_user["user_id"])
        if not message:
            raise HTTPException(status_code=403, detail="Нет доступа к файлу")

        # Удаление файлов
        file_manager = FileManager()
        if attachment.file_path:
            await file_manager.delete_file(attachment.file_path)
        if attachment.thumbnail_path:
            await file_manager.delete_file(attachment.thumbnail_path)

        # Удаление записи из базы данных
        await db.delete(attachment)
        await db.commit()

        return {"message": "Файл успешно удален"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file {attachment_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления файла")


@router.get("/stats", summary="Статистика файлов")
async def get_file_stats():
    """Получение статистики загрузки файлов"""
    try:
        file_manager = FileManager()
        stats = file_manager.get_upload_stats()

        return stats

    except Exception as e:
        logger.error(f"Error getting file stats: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения статистики")
