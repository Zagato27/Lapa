"""
Pydantic схемы для WebSocket
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import enum


class WebSocketMessageType(str, enum.Enum):
    """Типы WebSocket сообщений"""
    CHAT_MESSAGE = "chat_message"
    SYSTEM_MESSAGE = "system_message"
    TYPING_START = "typing_start"
    TYPING_STOP = "typing_stop"
    PRESENCE_UPDATE = "presence_update"
    CHAT_UPDATE = "chat_update"
    PARTICIPANT_JOIN = "participant_join"
    PARTICIPANT_LEAVE = "participant_leave"
    MESSAGE_READ = "message_read"
    MESSAGE_DELIVERED = "message_delivered"
    FILE_UPLOAD_PROGRESS = "file_upload_progress"
    NOTIFICATION = "notification"
    ERROR = "error"


class WebSocketMessage(BaseModel):
    """WebSocket сообщение"""
    type: WebSocketMessageType
    chat_id: Optional[str] = None
    data: Dict[str, Any]
    timestamp: Optional[datetime] = None
    sender_id: Optional[str] = None
    message_id: Optional[str] = None

    class Config:
        use_enum_values = True


class WebSocketResponse(BaseModel):
    """WebSocket ответ"""
    type: str
    status: str = "success"
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: Optional[datetime] = None


class TypingIndicator(BaseModel):
    """Индикатор набора текста"""
    chat_id: str
    user_id: str
    is_typing: bool
    timestamp: Optional[datetime] = None


class PresenceUpdate(BaseModel):
    """Обновление статуса присутствия"""
    user_id: str
    status: str  # online, offline, away
    last_seen: Optional[datetime] = None
    chat_id: Optional[str] = None


class ChatMessageData(BaseModel):
    """Данные сообщения чата"""
    id: str
    chat_id: str
    sender_id: str
    content: Optional[str]
    message_type: str
    attachment_id: Optional[str]
    reply_to_message_id: Optional[str]
    created_at: datetime


class SystemMessageData(BaseModel):
    """Данные системного сообщения"""
    chat_id: str
    message: str
    message_type: str  # user_joined, user_left, chat_updated, etc.
    metadata: Optional[Dict[str, Any]] = None


class ParticipantUpdateData(BaseModel):
    """Данные обновления участника"""
    chat_id: str
    user_id: str
    action: str  # joined, left, role_changed, banned, unbanned
    role: Optional[str] = None
    reason: Optional[str] = None


class FileUploadProgressData(BaseModel):
    """Данные прогресса загрузки файла"""
    chat_id: str
    attachment_id: str
    progress: float  # 0-100
    status: str  # uploading, processing, completed, failed
    error: Optional[str] = None


class NotificationData(BaseModel):
    """Данные уведомления"""
    id: str
    type: str  # message, mention, system, etc.
    title: str
    message: str
    chat_id: Optional[str] = None
    sender_id: Optional[str] = None
    action_url: Optional[str] = None
    priority: str = "normal"  # low, normal, high


class ErrorData(BaseModel):
    """Данные ошибки"""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class WebSocketConnectionData(BaseModel):
    """Данные подключения WebSocket"""
    connection_id: str
    user_id: str
    chat_id: str
    connected_at: datetime
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None


class WebSocketPresenceData(BaseModel):
    """Данные присутствия в чате"""
    chat_id: str
    participants: List[Dict[str, Any]]
    online_count: int
    total_count: int


class WebSocketTypingData(BaseModel):
    """Данные о наборе текста"""
    chat_id: str
    typing_users: List[Dict[str, str]]  # [{"user_id": "123", "nickname": "User"}]


class MessageStatusUpdateData(BaseModel):
    """Данные обновления статуса сообщения"""
    message_id: str
    chat_id: str
    status: str  # sent, delivered, read
    user_id: str
    timestamp: datetime


class ChatUpdateData(BaseModel):
    """Данные обновления чата"""
    chat_id: str
    update_type: str  # title_changed, description_changed, participant_added, etc.
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    updated_by: str
    timestamp: datetime
