"""
API роуты для обработки медиафайлов
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.processing import (
    ImageProcessingRequest,
    VideoProcessingRequest,
    ProcessingStatusResponse
)
from app.services.media_processor import MediaProcessor

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


@router.post("/images", summary="Обработка изображения")
async def process_image(
    request: ImageProcessingRequest,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обработка изображения"""
    try:
        processor = MediaProcessor()

        # Здесь должна быть валидация прав доступа к файлу
        # Получение пути к файлу из базы данных
        from app.services.media_service import MediaService
        media_file = await MediaService.get_media_file_by_id(db, request.media_file_id, current_user["user_id"])

        if not media_file:
            raise HTTPException(status_code=404, detail="Файл не найден")

        # Обработка изображения
        result = await processor.process_image(media_file.file_path, request.dict())

        return {
            "message": "Обработка изображения запущена",
            "file_id": request.media_file_id,
            "result": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing image {request.media_file_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обработки изображения")


@router.post("/videos", summary="Обработка видео")
async def process_video(
    request: VideoProcessingRequest,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обработка видео"""
    try:
        processor = MediaProcessor()

        # Здесь должна быть валидация прав доступа к файлу
        from app.services.media_service import MediaService
        media_file = await MediaService.get_media_file_by_id(db, request.media_file_id, current_user["user_id"])

        if not media_file:
            raise HTTPException(status_code=404, detail="Файл не найден")

        # Обработка видео
        result = await processor.process_video(media_file.file_path, request.dict())

        return {
            "message": "Обработка видео запущена",
            "file_id": request.media_file_id,
            "result": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing video {request.media_file_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обработки видео")


@router.get("/status/{file_id}", response_model=ProcessingStatusResponse, summary="Статус обработки")
async def get_processing_status(
    file_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение статуса обработки файла"""
    try:
        from app.database.session import get_session
        redis_session = await get_session()
        status = await redis_session.get_processing_status(file_id)

        if not status:
            raise HTTPException(status_code=404, detail="Статус обработки не найден")

        return ProcessingStatusResponse(**status)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting processing status for {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения статуса обработки")


@router.post("/colors/{file_id}", summary="Извлечение цветов")
async def extract_colors(
    file_id: str,
    num_colors: int = Query(5, description="Количество цветов"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Извлечение основных цветов изображения"""
    try:
        processor = MediaProcessor()

        # Получение файла
        from app.services.media_service import MediaService
        media_file = await MediaService.get_media_file_by_id(db, file_id, current_user["user_id"])

        if not media_file:
            raise HTTPException(status_code=404, detail="Файл не найден")

        if not media_file.is_image:
            raise HTTPException(status_code=400, detail="Файл должен быть изображением")

        # Извлечение цветов
        colors = await processor.extract_colors(media_file.file_path, num_colors)

        return {
            "file_id": file_id,
            "colors": colors
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting colors from {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка извлечения цветов")


@router.post("/optimize/{file_id}", summary="Оптимизация файла")
async def optimize_file(
    file_id: str,
    quality: int = Query(80, description="Качество оптимизации"),
    max_width: int = Query(None, description="Максимальная ширина"),
    max_height: int = Query(None, description="Максимальная высота"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Оптимизация медиафайла"""
    try:
        processor = MediaProcessor()

        # Получение файла
        from app.services.media_service import MediaService
        media_file = await MediaService.get_media_file_by_id(db, file_id, current_user["user_id"])

        if not media_file:
            raise HTTPException(status_code=404, detail="Файл не найден")

        # Параметры оптимизации
        options = {
            "quality": quality,
            "max_width": max_width,
            "max_height": max_height
        }

        # Оптимизация файла
        if media_file.is_image:
            result = await processor.process_image(media_file.file_path, {"optimize": True, **options})
        elif media_file.is_video:
            result = await processor.process_video(media_file.file_path, {"convert": True, **options})
        else:
            raise HTTPException(status_code=400, detail="Оптимизация не поддерживается для этого типа файла")

        return {
            "message": "Оптимизация запущена",
            "file_id": file_id,
            "result": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error optimizing file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка оптимизации файла")


@router.post("/thumbnail/{file_id}", summary="Генерация миниатюры")
async def generate_thumbnail(
    file_id: str,
    size: str = Query("300x300", description="Размер миниатюры"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Генерация миниатюры для медиафайла"""
    try:
        processor = MediaProcessor()

        # Получение файла
        from app.services.media_service import MediaService
        media_file = await MediaService.get_media_file_by_id(db, file_id, current_user["user_id"])

        if not media_file:
            raise HTTPException(status_code=404, detail="Файл не найден")

        # Парсинг размера
        try:
            width, height = map(int, size.split('x'))
        except:
            raise HTTPException(status_code=400, detail="Неверный формат размера")

        # Генерация миниатюры
        if media_file.is_image:
            thumbnail_path = await processor._generate_thumbnail(media_file.file_path, {"thumbnail_size": (width, height)})
        elif media_file.is_video:
            thumbnail_path = await processor._generate_video_thumbnail(media_file.file_path, {"thumbnail_size": (width, height)})
        else:
            raise HTTPException(status_code=400, detail="Генерация миниатюры не поддерживается для этого типа файла")

        return {
            "message": "Миниатюра сгенерирована",
            "file_id": file_id,
            "thumbnail_path": thumbnail_path
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating thumbnail for {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка генерации миниатюры")


@router.post("/convert/{file_id}", summary="Конвертация файла")
async def convert_file(
    file_id: str,
    target_format: str = Query(..., description="Целевой формат"),
    quality: int = Query(80, description="Качество"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Конвертация медиафайла в другой формат"""
    try:
        processor = MediaProcessor()

        # Получение файла
        from app.services.media_service import MediaService
        media_file = await MediaService.get_media_file_by_id(db, file_id, current_user["user_id"])

        if not media_file:
            raise HTTPException(status_code=404, detail="Файл не найден")

        # Параметры конвертации
        options = {
            "target_format": target_format,
            "quality": quality
        }

        # Конвертация файла
        if media_file.is_image:
            result = await processor.process_image(media_file.file_path, {"convert": True, **options})
        elif media_file.is_video:
            result = await processor.process_video(media_file.file_path, {"convert": True, **options})
        else:
            raise HTTPException(status_code=400, detail="Конвертация не поддерживается для этого типа файла")

        return {
            "message": "Конвертация запущена",
            "file_id": file_id,
            "target_format": target_format,
            "result": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error converting file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка конвертации файла")


@router.get("/queue", summary="Очередь обработки")
async def get_processing_queue():
    """Получение информации об очереди обработки"""
    try:
        # Здесь должна быть логика получения информации об очереди
        return {
            "queue_length": 0,
            "processing_jobs": [],
            "completed_today": 0,
            "failed_today": 0
        }

    except Exception as e:
        logger.error(f"Error getting processing queue: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения очереди обработки")
