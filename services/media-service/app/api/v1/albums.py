"""
API роуты для управления альбомами
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.media_album import (
    MediaAlbumCreate,
    MediaAlbumUpdate,
    MediaAlbumResponse
)
from app.services.media_service import MediaService
from app.models.media_album import AlbumType

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


@router.post("", response_model=MediaAlbumResponse, summary="Создание альбома")
async def create_album(
    album_data: MediaAlbumCreate,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание нового альбома"""
    try:
        album = await MediaService.create_album(db, current_user["user_id"], album_data)

        return album

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating album: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания альбома")


@router.get("", summary="Получение списка альбомов")
async def get_albums(
    album_type: str = Query(None, description="Фильтр по типу альбома"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка альбомов пользователя"""
    try:
        # Получение альбомов пользователя
        from app.models.media_album import MediaAlbum
        from sqlalchemy import select

        query = select(MediaAlbum).where(MediaAlbum.owner_id == current_user["user_id"])

        if album_type:
            try:
                album_type_enum = AlbumType(album_type)
                query = query.where(MediaAlbum.album_type == album_type_enum)
            except Exception:
                pass

        result = await db.execute(query)
        albums = result.scalars().all()

        return {
            "albums": [MediaService.album_to_response(album) for album in albums],
            "total": len(albums)
        }

    except Exception as e:
        logger.error(f"Error getting albums list: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения списка альбомов")


@router.get("/{album_id}", response_model=MediaAlbumResponse, summary="Получение альбома по ID")
async def get_album(
    album_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение информации об альбоме"""
    try:
        album = await MediaService.get_album_by_id(db, album_id, current_user["user_id"])

        if not album:
            raise HTTPException(status_code=404, detail="Альбом не найден")

        return album

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting album {album_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения альбома")


@router.put("/{album_id}", response_model=MediaAlbumResponse, summary="Обновление альбома")
async def update_album(
    album_id: str,
    album_data: MediaAlbumUpdate,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновление информации об альбоме"""
    try:
        album = await MediaService.get_album_by_id(db, album_id, current_user["user_id"])

        if not album:
            raise HTTPException(status_code=404, detail="Альбом не найден")

        # Проверка прав на обновление
        if album.owner_id != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Нет прав на обновление альбома")

        # Обновление полей
        update_data = album_data.dict(exclude_unset=True)

        for field, value in update_data.items():
            setattr(album, field, value)

        await db.commit()
        await db.refresh(album)

        return album

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating album {album_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления альбома")


@router.delete("/{album_id}", summary="Удаление альбома")
async def delete_album(
    album_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удаление альбома"""
    try:
        album = await MediaService.get_album_by_id(db, album_id, current_user["user_id"])

        if not album:
            raise HTTPException(status_code=404, detail="Альбом не найден")

        # Проверка прав на удаление
        if album.owner_id != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Нет прав на удаление альбома")

        # Удаление альбома
        await db.delete(album)
        await db.commit()

        return {"message": "Альбом успешно удален"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting album {album_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления альбома")


@router.get("/{album_id}/files", summary="Получение файлов альбома")
async def get_album_files(
    album_id: str,
    page: int = Query(1, description="Номер страницы"),
    limit: int = Query(20, description="Количество файлов на странице"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка файлов альбома"""
    try:
        album = await MediaService.get_album_by_id(db, album_id, current_user["user_id"])

        if not album:
            raise HTTPException(status_code=404, detail="Альбом не найден")

        # Получение файлов альбома
        files_response = await MediaService.get_user_media_files(
            db, current_user["user_id"], page, limit, album_id=album_id
        )

        return files_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting album files for {album_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения файлов альбома")


@router.put("/{album_id}/archive", summary="Архивация альбома")
async def archive_album(
    album_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Архивация альбома"""
    try:
        album = await MediaService.get_album_by_id(db, album_id, current_user["user_id"])

        if not album:
            raise HTTPException(status_code=404, detail="Альбом не найден")

        # Проверка прав
        if album.owner_id != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Нет прав на архивацию альбома")

        album.archive()
        await db.commit()

        return {"message": "Альбом успешно архивирован"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error archiving album {album_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка архивации альбома")


@router.put("/{album_id}/public", summary="Сделать альбом публичным")
async def make_album_public(
    album_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Сделать альбом публичным"""
    try:
        album = await MediaService.get_album_by_id(db, album_id, current_user["user_id"])

        if not album:
            raise HTTPException(status_code=404, detail="Альбом не найден")

        # Проверка прав
        if album.owner_id != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Нет прав на изменение альбома")

        album.make_public()
        await db.commit()

        return {"message": "Альбом сделан публичным"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error making album {album_id} public: {e}")
        raise HTTPException(status_code=500, detail="Ошибка изменения видимости альбома")


@router.put("/{album_id}/private", summary="Сделать альбом приватным")
async def make_album_private(
    album_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Сделать альбом приватным"""
    try:
        album = await MediaService.get_album_by_id(db, album_id, current_user["user_id"])

        if not album:
            raise HTTPException(status_code=404, detail="Альбом не найден")

        # Проверка прав
        if album.owner_id != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Нет прав на изменение альбома")

        album.make_private()
        await db.commit()

        return {"message": "Альбом сделан приватным"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error making album {album_id} private: {e}")
        raise HTTPException(status_code=500, detail="Ошибка изменения видимости альбома")


@router.put("/{album_id}/cover/{file_id}", summary="Установка обложки альбома")
async def set_album_cover(
    album_id: str,
    file_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Установка обложки альбома"""
    try:
        album = await MediaService.get_album_by_id(db, album_id, current_user["user_id"])

        if not album:
            raise HTTPException(status_code=404, detail="Альбом не найден")

        # Проверка прав
        if album.owner_id != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Нет прав на изменение альбома")

        # Проверка, что файл принадлежит пользователю и находится в альбоме
        media_file = await MediaService.get_media_file_by_id(db, file_id, current_user["user_id"])

        if not media_file:
            raise HTTPException(status_code=404, detail="Файл не найден")

        if media_file.album_id != album_id:
            raise HTTPException(status_code=400, detail="Файл не находится в этом альбоме")

        album.set_cover(file_id)
        await db.commit()

        return {"message": "Обложка альбома установлена"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting album cover {album_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка установки обложки")
