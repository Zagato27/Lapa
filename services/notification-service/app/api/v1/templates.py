"""
API роуты для управления шаблонами уведомлений
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.notification_template import (
    NotificationTemplateCreate,
    NotificationTemplateResponse,
    TemplateRenderRequest,
    TemplateRenderResponse
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

    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Неверный токен")

    return {"user_id": user_id}


@router.post("", response_model=NotificationTemplateResponse, summary="Создание шаблона")
async def create_template(
    template_data: NotificationTemplateCreate,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание шаблона уведомления"""
    try:
        from app.services.template_service import TemplateService

        # Здесь должна быть валидация данных и сохранение в базу
        template = {
            "id": "template_123",
            "name": template_data.name,
            "template_type": template_data.template_type,
            "content_template": template_data.content_template,
            "subject_template": template_data.subject_template,
            "language": template_data.language,
            "is_default": template_data.is_default
        }

        return NotificationTemplateResponse(**template)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания шаблона")


@router.get("", summary="Получение списка шаблонов")
async def get_templates(
    template_type: str = Query(None, description="Фильтр по типу шаблона"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка шаблонов"""
    try:
        # Здесь должна быть логика получения шаблонов из базы данных
        templates = [
            {
                "id": "template_1",
                "name": "Welcome Email",
                "template_type": "email",
                "status": "active",
                "language": "ru",
                "usage_count": 150,
                "created_at": "2023-01-01T00:00:00Z"
            }
        ]

        return {"templates": templates, "total": len(templates)}

    except Exception as e:
        logger.error(f"Error getting templates list: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения списка шаблонов")


@router.post("/render", response_model=TemplateRenderResponse, summary="Рендеринг шаблона")
async def render_template(
    render_request: TemplateRenderRequest,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Рендеринг шаблона с переменными"""
    try:
        from app.services.template_service import TemplateService

        result = await TemplateService.render_template(
            render_request.template_id,
            render_request.variables,
            render_request.language
        )

        return TemplateRenderResponse(
            template_id=render_request.template_id,
            subject=result.get("subject"),
            content=result.get("content", ""),
            html_content=result.get("html_content"),
            language=render_request.language,
            rendered_at=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rendering template {render_request.template_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка рендеринга шаблона")