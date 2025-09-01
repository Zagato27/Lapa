"""
Pydantic схемы для шаблонов уведомлений
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, validator
import enum


class TemplateType(str, enum.Enum):
    """Типы шаблонов"""
    PUSH = "push"
    EMAIL = "email"
    SMS = "sms"
    TELEGRAM = "telegram"


class TemplateStatus(str, enum.Enum):
    """Статусы шаблонов"""
    ACTIVE = "active"
    DRAFT = "draft"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class NotificationTemplateCreate(BaseModel):
    """Создание шаблона уведомления"""
    name: str
    description: Optional[str] = None
    template_type: TemplateType
    subject_template: Optional[str] = None
    content_template: str
    html_template: Optional[str] = None
    language: str = "ru"
    is_default: bool = False
    variables: Optional[Dict[str, str]] = None
    required_variables: Optional[List[str]] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None

    @validator('name')
    def validate_name(cls, v):
        if len(v) > 100:
            raise ValueError('Template name too long')
        return v

    @validator('content_template')
    def validate_content_template(cls, v):
        if len(v) > 10000:
            raise ValueError('Content template too long')
        return v


class NotificationTemplateUpdate(BaseModel):
    """Обновление шаблона уведомления"""
    name: Optional[str] = None
    description: Optional[str] = None
    subject_template: Optional[str] = None
    content_template: Optional[str] = None
    html_template: Optional[str] = None
    variables: Optional[Dict[str, str]] = None
    required_variables: Optional[List[str]] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None


class NotificationTemplateResponse(BaseModel):
    """Ответ с данными шаблона"""
    id: str
    name: str
    description: Optional[str]
    template_type: TemplateType
    status: TemplateStatus
    subject_template: Optional[str]
    content_template: str
    html_template: Optional[str]
    language: str
    is_default: bool
    variables: Optional[Dict[str, str]]
    required_variables: Optional[List[str]]
    category: Optional[str]
    tags: Optional[List[str]]
    creator_id: str
    usage_count: int
    success_rate: Optional[float]
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime]


class TemplateRenderRequest(BaseModel):
    """Запрос на рендеринг шаблона"""
    template_id: str
    variables: Dict[str, Any]
    language: Optional[str] = None


class TemplateRenderResponse(BaseModel):
    """Ответ с результатом рендеринга"""
    template_id: str
    subject: Optional[str]
    content: str
    html_content: Optional[str]
    language: str
    rendered_at: datetime


class TemplateValidationRequest(BaseModel):
    """Запрос на валидацию шаблона"""
    template_id: str
    variables: Optional[Dict[str, Any]] = None


class TemplateValidationResponse(BaseModel):
    """Ответ с результатом валидации"""
    template_id: str
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    validated_at: datetime


class TemplateListResponse(BaseModel):
    """Ответ со списком шаблонов"""
    templates: List[NotificationTemplateResponse]
    total: int
    page: int
    limit: int
    pages: int


class TemplateSearchRequest(BaseModel):
    """Запрос на поиск шаблонов"""
    query: str
    template_type: Optional[TemplateType] = None
    status: Optional[TemplateStatus] = None
    category: Optional[str] = None
    language: Optional[str] = None
    limit: int = 50


class TemplateCloneRequest(BaseModel):
    """Запрос на клонирование шаблона"""
    template_id: str
    new_name: str
    new_description: Optional[str] = None


class TemplateExportRequest(BaseModel):
    """Запрос на экспорт шаблона"""
    template_id: str
    format: str = "json"  # json, yaml, xml


class TemplateImportRequest(BaseModel):
    """Запрос на импорт шаблона"""
    name: str
    template_data: Dict[str, Any]
    template_type: TemplateType


class TemplateCategoryResponse(BaseModel):
    """Ответ с категориями шаблонов"""
    categories: List[Dict[str, Any]]
    total_templates: int


class TemplateStatisticsResponse(BaseModel):
    """Ответ со статистикой шаблонов"""
    total_templates: int
    active_templates: int
    draft_templates: int
    templates_by_type: Dict[str, int]
    templates_by_category: Dict[str, int]
    most_used_templates: List[Dict[str, Any]]
    period_start: datetime
    period_end: datetime
