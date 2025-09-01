"""
API роуты для управления доступом к медиафайлам
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.media_access import (
    MediaAccessCreate,
    MediaAccessUpdate,
    MediaAccessResponse,
    MediaAccessGrantRequest
)

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


@router.post("/grant", response_model=MediaAccessResponse, summary="Предоставление доступа")
async def grant_access(
    access_data: MediaAccessGrantRequest,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Предоставление доступа к медиафайлу"""
    try:
        from app.services.media_service import MediaService
        from app.models.media_access import MediaAccess, AccessType, AccessLevel

        # Проверка, что файл существует и принадлежит пользователю
        media_file = await MediaService.get_media_file_by_id(db, access_data.media_file_id, current_user["user_id"])

        if not media_file:
            raise HTTPException(status_code=404, detail="Файл не найден")

        # Создание доступа
        if access_data.recipient_type == "user" and access_data.recipient_id:
            # Доступ для конкретного пользователя
            access = MediaAccess(
                media_file_id=access_data.media_file_id,
                access_type=access_data.access_type,
                access_level=access_data.access_level,
                user_id=access_data.recipient_id,
                granted_by=current_user["user_id"],
                max_views=access_data.max_views,
                max_downloads=access_data.max_downloads,
                expires_at=access_data.expires_at,
                description=access_data.description
            )
        else:
            # Публичный доступ
            access = MediaAccess(
                media_file_id=access_data.media_file_id,
                access_type=access_data.access_type,
                access_level=access_data.access_level,
                granted_by=current_user["user_id"],
                max_views=access_data.max_views,
                max_downloads=access_data.max_downloads,
                expires_at=access_data.expires_at,
                description=access_data.description
            )
            access.generate_token()

        db.add(access)
        await db.commit()
        await db.refresh(access)

        return MediaAccessResponse(
            id=access.id,
            media_file_id=access.media_file_id,
            access_type=access.access_type,
            access_level=access.access_level,
            status=access.status,
            user_id=access.user_id,
            group_id=access.group_id,
            token=access.token,
            max_views=access.max_views,
            max_downloads=access.max_downloads,
            expires_at=access.expires_at,
            view_count=access.view_count,
            download_count=access.download_count,
            last_access_at=access.last_access_at,
            granted_by=access.granted_by,
            granted_at=access.granted_at,
            description=access.description,
            is_active=access.is_active,
            is_expired=access.is_expired,
            is_revoked=access.is_revoked,
            is_pending=access.is_pending,
            can_view=access.can_view,
            can_download=access.can_download,
            can_edit=access.can_edit,
            can_delete=access.can_delete,
            can_share=access.can_share,
            is_public_link=access.is_public_link,
            has_password=access.has_password,
            views_left=access.views_left,
            downloads_left=access.downloads_left
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error granting access to file {access_data.media_file_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка предоставления доступа")


@router.put("/{access_id}", response_model=MediaAccessResponse, summary="Обновление доступа")
async def update_access(
    access_id: str,
    access_data: MediaAccessUpdate,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновление прав доступа"""
    try:
        from app.models.media_access import MediaAccess
        from sqlalchemy import select

        # Получение доступа
        query = select(MediaAccess).where(MediaAccess.id == access_id)
        result = await db.execute(query)
        access = result.scalar_one_or_none()

        if not access:
            raise HTTPException(status_code=404, detail="Доступ не найден")

        # Проверка прав на обновление
        if access.granted_by != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Нет прав на обновление доступа")

        # Обновление полей
        update_data = access_data.dict(exclude_unset=True)

        for field, value in update_data.items():
            setattr(access, field, value)

        await db.commit()
        await db.refresh(access)

        return MediaAccessResponse(
            id=access.id,
            media_file_id=access.media_file_id,
            access_type=access.access_type,
            access_level=access.access_level,
            status=access.status,
            user_id=access.user_id,
            group_id=access.group_id,
            token=access.token,
            max_views=access.max_views,
            max_downloads=access.max_downloads,
            expires_at=access.expires_at,
            view_count=access.view_count,
            download_count=access.download_count,
            last_access_at=access.last_access_at,
            granted_by=access.granted_by,
            granted_at=access.granted_at,
            description=access.description,
            is_active=access.is_active,
            is_expired=access.is_expired,
            is_revoked=access.is_revoked,
            is_pending=access.is_pending,
            can_view=access.can_view,
            can_download=access.can_download,
            can_edit=access.can_edit,
            can_delete=access.can_delete,
            can_share=access.can_share,
            is_public_link=access.is_public_link,
            has_password=access.has_password,
            views_left=access.views_left,
            downloads_left=access.downloads_left
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating access {access_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления доступа")


@router.delete("/{access_id}", summary="Отзыв доступа")
async def revoke_access(
    access_id: str,
    reason: str = Query(None, description="Причина отзыва"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Отзыв доступа к файлу"""
    try:
        from app.models.media_access import MediaAccess
        from sqlalchemy import select

        # Получение доступа
        query = select(MediaAccess).where(MediaAccess.id == access_id)
        result = await db.execute(query)
        access = result.scalar_one_or_none()

        if not access:
            raise HTTPException(status_code=404, detail="Доступ не найден")

        # Проверка прав на отзыв
        if access.granted_by != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Нет прав на отзыв доступа")

        access.revoke()
        await db.commit()

        return {"message": "Доступ успешно отозван"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking access {access_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка отзыва доступа")


@router.get("/file/{file_id}", summary="Получение списка доступов к файлу")
async def get_file_access_list(
    file_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка всех доступов к файлу"""
    try:
        from app.services.media_service import MediaService
        from app.models.media_access import MediaAccess
        from sqlalchemy import select

        # Проверка, что файл существует и принадлежит пользователю
        media_file = await MediaService.get_media_file_by_id(db, file_id, current_user["user_id"])

        if not media_file:
            raise HTTPException(status_code=404, detail="Файл не найден")

        # Получение списка доступов
        query = select(MediaAccess).where(MediaAccess.media_file_id == file_id)
        result = await db.execute(query)
        accesses = result.scalars().all()

        return {
            "file_id": file_id,
            "accesses": [MediaAccessResponse(
                id=access.id,
                media_file_id=access.media_file_id,
                access_type=access.access_type,
                access_level=access.access_level,
                status=access.status,
                user_id=access.user_id,
                group_id=access.group_id,
                token=access.token,
                max_views=access.max_views,
                max_downloads=access.max_downloads,
                expires_at=access.expires_at,
                view_count=access.view_count,
                download_count=access.download_count,
                last_access_at=access.last_access_at,
                granted_by=access.granted_by,
                granted_at=access.granted_at,
                description=access.description,
                is_active=access.is_active,
                is_expired=access.is_expired,
                is_revoked=access.is_revoked,
                is_pending=access.is_pending,
                can_view=access.can_view,
                can_download=access.can_download,
                can_edit=access.can_edit,
                can_delete=access.can_delete,
                can_share=access.can_share,
                is_public_link=access.is_public_link,
                has_password=access.has_password,
                views_left=access.views_left,
                downloads_left=access.downloads_left
            ) for access in accesses],
            "total": len(accesses)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file access list for {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения списка доступов")


@router.post("/public/{file_id}", summary="Создание публичной ссылки")
async def create_public_link(
    file_id: str,
    expires_in_days: int = Query(7, description="Срок действия в днях"),
    max_views: int = Query(None, description="Максимум просмотров"),
    password: str = Query(None, description="Пароль для доступа"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание публичной ссылки на файл"""
    try:
        from app.services.media_service import MediaService
        from app.models.media_access import MediaAccess, AccessType, AccessLevel
        from datetime import datetime, timedelta

        # Проверка, что файл существует и принадлежит пользователю
        media_file = await MediaService.get_media_file_by_id(db, file_id, current_user["user_id"])

        if not media_file:
            raise HTTPException(status_code=404, detail="Файл не найден")

        # Создание публичного доступа
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        access = MediaAccess(
            media_file_id=file_id,
            access_type=AccessType.VIEW,
            access_level=AccessLevel.READ,
            granted_by=current_user["user_id"],
            expires_at=expires_at,
            max_views=max_views
        )

        if password:
            access.password_hash = password  # Здесь должна быть хэширование

        access.generate_token()

        db.add(access)
        await db.commit()
        await db.refresh(access)

        # Сохранение токена в Redis
        from app.database.session import get_session
        redis_session = await get_session()
        access_data = {
            "access_id": access.id,
            "file_id": file_id,
            "user_id": current_user["user_id"],
            "expires_at": expires_at.isoformat()
        }
        await redis_session.set_access_token(access.token, access_data)

        return {
            "message": "Публичная ссылка создана",
            "public_url": f"/media/public/{access.token}",
            "token": access.token,
            "expires_at": expires_at.isoformat(),
            "max_views": max_views
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating public link for {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания публичной ссылки")


@router.get("/stats/{file_id}", summary="Статистика доступа к файлу")
async def get_file_access_stats(
    file_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение статистики доступа к файлу"""
    try:
        from app.services.media_service import MediaService
        from app.models.media_access import MediaAccess
        from sqlalchemy import select, func

        # Проверка, что файл существует и принадлежит пользователю
        media_file = await MediaService.get_media_file_by_id(db, file_id, current_user["user_id"])

        if not media_file:
            raise HTTPException(status_code=404, detail="Файл не найден")

        # Получение статистики
        query = select(
            func.count(MediaAccess.id).label('total_access'),
            func.sum(MediaAccess.view_count).label('total_views'),
            func.sum(MediaAccess.download_count).label('total_downloads')
        ).where(MediaAccess.media_file_id == file_id)

        result = await db.execute(query)
        stats = result.first()

        return {
            "file_id": file_id,
            "total_access_rules": stats.total_access or 0,
            "total_views": stats.total_views or 0,
            "total_downloads": stats.total_downloads or 0
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file access stats for {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения статистики доступа")
