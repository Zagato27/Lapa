"""
Pydantic-схемы (v2) для сообщений.

Используются роутами `app.api.v1.messages` и сервисом сообщений.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_validator
import enum


class MessageType(str, enum.Enum):
    """Типы сообщений"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    FILE = "file"
    SYSTEM = "system"
    LOCATION = "location"
    CONTACT = "contact"
    STICKER = "sticker"
    VOICE = "voice"


class MessageStatus(str, enum.Enum):
    """Статусы сообщений"""
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    DELETED = "deleted"
    EDITED = "edited"


class AttachmentType(str, enum.Enum):
    """Типы вложений"""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    VOICE = "voice"
    LOCATION = "location"
    CONTACT = "contact"


class AttachmentStatus(str, enum.Enum):
    """Статусы вложений"""
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    DELETED = "deleted"


class MessageCreate(BaseModel):
    """Создание сообщения"""
    content: Optional[str] = None
    message_type: MessageType = MessageType.TEXT
    reply_to_message_id: Optional[str] = None
    attachment_id: Optional[str] = None

    @field_validator('content')
    def validate_content(cls, v):
        from app.config import settings
        if v and len(v) > settings.max_message_length:
            raise ValueError(f'Message content cannot exceed {settings.max_message_length} characters')
        return v


class MessageUpdate(BaseModel):
    """Обновление сообщения"""
    content: str

    @field_validator('content')
    def validate_content(cls, v):
        from app.config import settings
        if len(v) > settings.max_message_length:
            raise ValueError(f'Message content cannot exceed {settings.max_message_length} characters')
        return v


class MessageResponse(BaseModel):
    """Ответ с данными сообщения"""
    id: str
    chat_id: str
    sender_id: str
    message_type: MessageType
    status: MessageStatus
    content: Optional[str]
    metadata: Optional[Dict[str, Any]]
    attachment_id: Optional[str]
    reply_to_message_id: Optional[str]
    thread_id: Optional[str]
    is_pinned: bool
    is_edited: bool
    created_at: datetime
    updated_at: datetime
    edited_at: Optional[datetime]
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]

    # Вычисляемые поля
    is_text_message: Optional[bool] = None
    is_media_message: Optional[bool] = None
    is_system_message: Optional[bool] = None
    is_deleted: Optional[bool] = None
    has_attachment: Optional[bool] = None
    is_reply: Optional[bool] = None


class MessagesListResponse(BaseModel):
    """Ответ со списком сообщений"""
    messages: List[MessageResponse]
    total: int
    page: int
    limit: int
    pages: int
    has_more: bool


class MessageAttachmentCreate(BaseModel):
    """Создание вложения к сообщению"""
    attachment_type: AttachmentType
    file: Any  # В реальности это будет файл из FastAPI UploadFile
    caption: Optional[str] = None

    @field_validator('caption')
    def validate_caption(cls, v):
        from app.config import settings
        if v and len(v) > settings.max_message_length:
            raise ValueError(f'Caption cannot exceed {settings.max_message_length} characters')
        return v


class MessageAttachmentResponse(BaseModel):
    """Ответ с данными вложения"""
    id: str
    message_id: Optional[str]
    uploader_id: str
    attachment_type: AttachmentType
    status: AttachmentStatus
    original_filename: str
    file_path: Optional[str]
    file_url: Optional[str]
    thumbnail_path: Optional[str]
    thumbnail_url: Optional[str]
    file_size: int
    mime_type: Optional[str]
    file_hash: Optional[str]
    width: Optional[int]
    height: Optional[int]
    duration: Optional[int]
    latitude: Optional[float]
    longitude: Optional[float]
    location_name: Optional[str]
    contact_name: Optional[str]
    contact_phone: Optional[str]
    caption: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    uploaded_at: Optional[datetime]
    processed_at: Optional[datetime]

    # Вычисляемые поля
    is_image: Optional[bool] = None
    is_video: Optional[bool] = None
    is_audio: Optional[bool] = None
    is_document: Optional[bool] = None
    is_media: Optional[bool] = None
    is_ready: Optional[bool] = None
    is_failed: Optional[bool] = None
    file_size_mb: Optional[float] = None
    has_thumbnail: Optional[bool] = None


class MessageReactionCreate(BaseModel):
    """Создание реакции на сообщение"""
    emoji: str
    action: str = "add"  # add, remove

    @field_validator('emoji')
    def validate_emoji(cls, v):
        # Проверка на допустимые эмодзи
        import emoji
        if not emoji.is_emoji(v):
            raise ValueError('Invalid emoji')
        return v

    @field_validator('action')
    def validate_action(cls, v):
        if v not in ["add", "remove"]:
            raise ValueError('Action must be either "add" or "remove"')
        return v


class MessageReactionResponse(BaseModel):
    """Ответ с данными реакции"""
    id: str
    message_id: str
    user_id: str
    emoji: str
    created_at: datetime


class MessagePinRequest(BaseModel):
    """Запрос на закрепление сообщения"""
    action: str = "pin"  # pin, unpin


class MessageDeleteRequest(BaseModel):
    """Запрос на удаление сообщения"""
    delete_for_all: bool = False


class MessageSearchRequest(BaseModel):
    """Запрос на поиск сообщений"""
    query: str
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sender_id: Optional[str] = None
    message_type: Optional[MessageType] = None


class MessageSearchResponse(BaseModel):
    """Ответ с результатами поиска сообщений"""
    messages: List[MessageResponse]
    total: int
    query: str
    search_time: float


class MessageForwardRequest(BaseModel):
    """Запрос на пересылку сообщения"""
    target_chat_ids: List[str]
    message_ids: List[str]


class MessageReportRequest(BaseModel):
    """Запрос на жалобу на сообщение"""
    reason: str
    description: Optional[str] = None


class MessageStatisticsResponse(BaseModel):
    """Ответ со статистикой сообщений"""
    chat_id: str
    total_messages: int
    messages_by_type: Dict[str, int]
    messages_by_sender: Dict[str, int]
    average_message_length: float
    most_active_hour: int
    period_start: datetime
    period_end: datetime
