"""
Модель шаблонов уведомлений.

Используется `TemplateService` и эндпоинтами `app.api.v1.templates`.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, JSON, ForeignKey
from sqlalchemy.sql import func
import enum

from .base import Base


class TemplateType(str, enum.Enum):
    """Типы шаблонов"""
    PUSH = "push"                  # Push-уведомление
    EMAIL = "email"                # Email
    SMS = "sms"                    # SMS
    TELEGRAM = "telegram"          # Telegram


class TemplateStatus(str, enum.Enum):
    """Статусы шаблонов"""
    ACTIVE = "active"              # Активный
    DRAFT = "draft"                # Черновик
    ARCHIVED = "archived"          # Архивный
    DEPRECATED = "deprecated"      # Устаревший


class NotificationTemplate(Base):
    """Модель шаблона уведомления"""
    __tablename__ = "notification_templates"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Тип и статус
    template_type = Column(Enum(TemplateType), nullable=False)
    status = Column(Enum(TemplateStatus), nullable=False, default=TemplateStatus.DRAFT)

    # Содержимое шаблона
    subject_template = Column(Text, nullable=True)            # Шаблон темы (для email)
    content_template = Column(Text, nullable=False)           # Шаблон содержимого
    html_template = Column(Text, nullable=True)               # HTML шаблон (для email)

    # Настройки
    language = Column(String, default="ru")                   # Язык шаблона
    is_default = Column(Boolean, default=False)               # Шаблон по умолчанию

    # Переменные шаблона
    variables = Column(JSON, nullable=True)                   # Доступные переменные
    required_variables = Column(JSON, nullable=True)          # Обязательные переменные

    # Категория
    category = Column(String, nullable=True)                  # Категория шаблона
    tags = Column(JSON, nullable=True)                        # Теги шаблона

    # Создал
    creator_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Статистика использования
    usage_count = Column(Integer, default=0)                  # Количество использований
    success_rate = Column(Float, nullable=True)               # Процент успешных отправок

    # Настройки доставки
    delivery_settings = Column(JSON, nullable=True)           # Настройки доставки

    # Метаданные
    metadata = Column(JSON, nullable=True)                    # Дополнительные метаданные

    # Временные метки
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_used_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<NotificationTemplate(id={self.id}, name={self.name}, type={self.template_type.value}, status={self.status.value})>"

    @property
    def is_active(self) -> bool:
        """Проверка, активен ли шаблон"""
        return self.status == TemplateStatus.ACTIVE

    @property
    def is_draft(self) -> bool:
        """Проверка, является ли черновиком"""
        return self.status == TemplateStatus.DRAFT

    @property
    def is_archived(self) -> bool:
        """Проверка, архивный ли шаблон"""
        return self.status == TemplateStatus.ARCHIVED

    @property
    def is_deprecated(self) -> bool:
        """Проверка, устарел ли шаблон"""
        return self.status == TemplateStatus.DEPRECATED

    @property
    def has_subject_template(self) -> bool:
        """Проверка наличия шаблона темы"""
        return self.subject_template is not None

    @property
    def has_html_template(self) -> bool:
        """Проверка наличия HTML шаблона"""
        return self.html_template is not None

    @property
    def is_multilingual(self) -> bool:
        """Проверка поддержки нескольких языков"""
        # Здесь можно реализовать логику проверки многоязычности
        return False

    def activate(self):
        """Активация шаблона"""
        self.status = TemplateStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def archive(self):
        """Архивация шаблона"""
        self.status = TemplateStatus.ARCHIVED
        self.updated_at = datetime.utcnow()

    def deprecate(self):
        """Отметка как устаревший"""
        self.status = TemplateStatus.DEPRECATED
        self.updated_at = datetime.utcnow()

    def increment_usage(self):
        """Увеличение счетчика использования"""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def update_success_rate(self, success: bool):
        """Обновление процента успешности"""
        if success:
            self.success_rate = ((self.success_rate or 0) * (self.usage_count - 1) + 100) / self.usage_count
        else:
            self.success_rate = ((self.success_rate or 0) * (self.usage_count - 1)) / self.usage_count
        self.updated_at = datetime.utcnow()

    def add_variable(self, name: str, description: str, required: bool = False):
        """Добавление переменной шаблона"""
        if not self.variables:
            self.variables = {}
        if not self.required_variables:
            self.required_variables = []

        self.variables[name] = description
        if required:
            self.required_variables.append(name)
        self.updated_at = datetime.utcnow()

    def remove_variable(self, name: str):
        """Удаление переменной шаблона"""
        if self.variables and name in self.variables:
            del self.variables[name]
        if self.required_variables and name in self.required_variables:
            self.required_variables.remove(name)
        self.updated_at = datetime.utcnow()

    def validate_variables(self, variables: dict) -> list[str]:
        """Валидация переменных шаблона"""
        errors = []

        if self.required_variables:
            for required_var in self.required_variables:
                if required_var not in variables:
                    errors.append(f"Required variable '{required_var}' is missing")

        return errors

    def render_subject(self, variables: dict) -> Optional[str]:
        """Рендеринг темы сообщения"""
        if not self.subject_template:
            return None

        try:
            from jinja2 import Template
            template = Template(self.subject_template)
            return template.render(**variables)
        except Exception as e:
            logger.error(f"Error rendering subject template {self.id}: {e}")
            return None

    def render_content(self, variables: dict) -> str:
        """Рендеринг содержимого сообщения"""
        try:
            from jinja2 import Template
            template = Template(self.content_template)
            return template.render(**variables)
        except Exception as e:
            logger.error(f"Error rendering content template {self.id}: {e}")
            return self.content_template

    def render_html(self, variables: dict) -> Optional[str]:
        """Рендеринг HTML содержимого"""
        if not self.html_template:
            return None

        try:
            from jinja2 import Template
            template = Template(self.html_template)
            return template.render(**variables)
        except Exception as e:
            logger.error(f"Error rendering HTML template {self.id}: {e}")
            return None

    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "template_type": self.template_type.value,
            "status": self.status.value,
            "subject_template": self.subject_template,
            "content_template": self.content_template,
            "html_template": self.html_template,
            "language": self.language,
            "is_default": self.is_default,
            "variables": self.variables,
            "required_variables": self.required_variables,
            "category": self.category,
            "tags": self.tags,
            "creator_id": self.creator_id,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "delivery_settings": self.delivery_settings,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None
        }

    @staticmethod
    def create_push_template(
        name: str,
        content_template: str,
        creator_id: str,
        description: Optional[str] = None
    ) -> 'NotificationTemplate':
        """Создание шаблона push-уведомления"""
        template = NotificationTemplate(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            template_type=TemplateType.PUSH,
            content_template=content_template,
            creator_id=creator_id
        )
        return template

    @staticmethod
    def create_email_template(
        name: str,
        subject_template: str,
        content_template: str,
        html_template: Optional[str] = None,
        creator_id: str = None,
        description: Optional[str] = None
    ) -> 'NotificationTemplate':
        """Создание шаблона email"""
        template = NotificationTemplate(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            template_type=TemplateType.EMAIL,
            subject_template=subject_template,
            content_template=content_template,
            html_template=html_template,
            creator_id=creator_id
        )
        return template

    @staticmethod
    def create_sms_template(
        name: str,
        content_template: str,
        creator_id: str,
        description: Optional[str] = None
    ) -> 'NotificationTemplate':
        """Создание шаблона SMS"""
        template = NotificationTemplate(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            template_type=TemplateType.SMS,
            content_template=content_template,
            creator_id=creator_id
        )
        return template