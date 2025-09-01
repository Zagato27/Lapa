"""
Pydantic-схемы (v2) для чатов.

Используются роутами `app.api.v1.chats` и сервисом `ChatService`.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_validator
import enum


class ChatType(str, enum.Enum):
    """Типы чатов"""
    ORDER = "order"
    SUPPORT = "support"
    GROUP = "group"
    PRIVATE = "private"


class ChatStatus(str, enum.Enum):
    """Статусы чатов"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    FROZEN = "frozen"


class ParticipantRole(str, enum.Enum):
    """Роли участников"""
    OWNER = "owner"
    ADMIN = "admin"
    MODERATOR = "moderator"
    MEMBER = "member"
    GUEST = "guest"


class ParticipantStatus(str, enum.Enum):
    """Статусы участников"""
    ACTIVE = "active"
    INVITED = "invited"
    BANNED = "banned"
    LEFT = "left"
    MUTED = "muted"


class ChatCreate(BaseModel):
    """Создание чата"""
    order_id: Optional[str] = None
    chat_type: ChatType = ChatType.PRIVATE
    title: Optional[str] = None
    description: Optional[str] = None
    participant_ids: Optional[List[str]] = None  # ID пользователей для добавления
    is_private: bool = False
    allow_guests: bool = False
    max_participants: Optional[int] = None

    @field_validator('participant_ids')
    def validate_participants(cls, v):
        from app.config import settings
        if v and len(v) > settings.max_chat_participants:
            raise ValueError(f'Too many participants. Maximum is {settings.max_chat_participants}')
        return v

    @field_validator('max_participants')
    def validate_max_participants(cls, v):
        from app.config import settings
        if v and v > settings.max_chat_participants:
            raise ValueError(f'Max participants cannot exceed {settings.max_chat_participants}')
        return v


class ChatUpdate(BaseModel):
    """Обновление чата"""
    title: Optional[str] = None
    description: Optional[str] = None
    allow_guests: Optional[bool] = None
    max_participants: Optional[int] = None


class ChatResponse(BaseModel):
    """Ответ с данными чата"""
    id: str
    order_id: Optional[str]
    creator_id: str
    chat_type: ChatType
    status: ChatStatus
    title: Optional[str]
    description: Optional[str]
    is_private: bool
    is_encrypted: bool
    allow_guests: bool
    allow_files: bool
    max_participants: Optional[int]
    total_messages: int
    total_participants: int
    last_message_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    # Вычисляемые поля
    can_send_messages: Optional[bool] = None
    is_active: Optional[bool] = None
    is_archived: Optional[bool] = None
    participants_count: Optional[int] = None


class ChatsListResponse(BaseModel):
    """Ответ со списком чатов"""
    chats: List[ChatResponse]
    total: int
    page: int
    limit: int
    pages: int


class ChatParticipantAdd(BaseModel):
    """Добавление участника в чат"""
    user_id: str
    role: ParticipantRole = ParticipantRole.MEMBER
    nickname: Optional[str] = None


class ChatParticipantUpdate(BaseModel):
    """Обновление участника чата"""
    role: Optional[ParticipantRole] = None
    can_send_messages: Optional[bool] = None
    can_send_files: Optional[bool] = None
    can_invite_users: Optional[bool] = None
    can_delete_messages: Optional[bool] = None
    can_pin_messages: Optional[bool] = None
    can_manage_participants: Optional[bool] = None
    notifications_enabled: Optional[bool] = None
    nickname: Optional[str] = None


class ChatParticipantResponse(BaseModel):
    """Ответ с данными участника чата"""
    id: str
    chat_id: str
    user_id: str
    role: ParticipantRole
    status: ParticipantStatus
    can_send_messages: bool
    can_send_files: bool
    can_invite_users: bool
    can_delete_messages: bool
    can_pin_messages: bool
    can_manage_participants: bool
    notifications_enabled: bool
    messages_sent: int
    last_seen_at: Optional[datetime]
    joined_at: datetime
    muted_until: Optional[datetime]
    banned_until: Optional[datetime]
    invited_by: Optional[str]
    invited_at: Optional[datetime]
    nickname: Optional[str]

    # Вычисляемые поля
    is_owner: Optional[bool] = None
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None
    is_banned: Optional[bool] = None
    is_muted: Optional[bool] = None
    can_participate: Optional[bool] = None


class ChatSettingsUpdate(BaseModel):
    """Обновление настроек чата"""
    allow_guests: Optional[bool] = None
    allow_files: Optional[bool] = None
    allow_images: Optional[bool] = None
    allow_videos: Optional[bool] = None
    allow_voice_messages: Optional[bool] = None
    enable_moderation: Optional[bool] = None
    auto_moderation: Optional[bool] = None
    banned_words_filter: Optional[bool] = None
    enable_push_notifications: Optional[bool] = None
    enable_email_notifications: Optional[bool] = None
    enable_sms_notifications: Optional[bool] = None
    notification_sound: Optional[bool] = None
    encryption_enabled: Optional[bool] = None
    self_destruct_messages: Optional[bool] = None
    self_destruct_timer: Optional[int] = None
    max_message_length: Optional[int] = None
    max_file_size_mb: Optional[int] = None
    rate_limit_messages: Optional[int] = None
    slow_mode_seconds: Optional[int] = None
    theme: Optional[str] = None
    language: Optional[str] = None
    webhook_enabled: Optional[bool] = None
    webhook_url: Optional[str] = None
    bot_enabled: Optional[bool] = None
    auto_archive_days: Optional[int] = None
    archive_inactive_chats: Optional[bool] = None
    enable_logging: Optional[bool] = None
    custom_emoji_enabled: Optional[bool] = None
    message_reactions_enabled: Optional[bool] = None
    message_replies_enabled: Optional[bool] = None
    message_editing_enabled: Optional[bool] = None
    message_deletion_enabled: Optional[bool] = None


class ChatSettingsResponse(BaseModel):
    """Ответ с настройками чата"""
    id: str
    chat_id: str
    allow_guests: bool
    allow_files: bool
    allow_images: bool
    allow_videos: bool
    allow_voice_messages: bool
    enable_moderation: bool
    auto_moderation: bool
    banned_words_filter: bool
    enable_push_notifications: bool
    enable_email_notifications: bool
    enable_sms_notifications: bool
    notification_sound: bool
    encryption_enabled: bool
    self_destruct_messages: bool
    self_destruct_timer: Optional[int]
    max_message_length: int
    max_file_size_mb: int
    rate_limit_messages: int
    slow_mode_seconds: int
    theme: str
    language: str
    webhook_enabled: bool
    webhook_url: Optional[str]
    bot_enabled: bool
    auto_archive_days: Optional[int]
    archive_inactive_chats: bool
    enable_logging: bool
    custom_emoji_enabled: bool
    message_reactions_enabled: bool
    message_replies_enabled: bool
    message_editing_enabled: bool
    message_deletion_enabled: bool
    created_at: datetime


class ChatActionRequest(BaseModel):
    """Запрос на действие с чатом"""
    action: str  # archive, delete, freeze, unfreeze
    reason: Optional[str] = None


class ChatInviteRequest(BaseModel):
    """Запрос на приглашение в чат"""
    user_ids: List[str]
    message: Optional[str] = None


class ChatStatisticsResponse(BaseModel):
    """Ответ со статистикой чата"""
    chat_id: str
    total_messages: int
    total_participants: int
    active_participants: int
    messages_today: int
    messages_this_week: int
    messages_this_month: int
    average_messages_per_day: float
    top_participants: List[Dict[str, Any]]
    created_at: datetime


class ChatArchiveRequest(BaseModel):
    """Запрос на архивацию чата"""
    archive_type: str = "manual"  # manual, auto, system
    reason: Optional[str] = None


class ChatExportRequest(BaseModel):
    """Запрос на экспорт чата"""
    format: str = "json"  # json, html, pdf
    include_attachments: bool = False
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
