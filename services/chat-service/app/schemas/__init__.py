"""
Pydantic схемы для Chat Service
"""

from .chat import (
    ChatCreate,
    ChatUpdate,
    ChatResponse,
    ChatsListResponse,
    ChatParticipantAdd,
    ChatParticipantUpdate,
    ChatParticipantResponse,
    ChatSettingsUpdate,
    ChatSettingsResponse
)
from .message import (
    MessageCreate,
    MessageUpdate,
    MessageResponse,
    MessagesListResponse,
    MessageAttachmentCreate,
    MessageAttachmentResponse,
    MessageReactionCreate,
    MessageReactionResponse
)
from .websocket import (
    WebSocketMessage,
    WebSocketResponse,
    TypingIndicator,
    PresenceUpdate
)

__all__ = [
    "ChatCreate",
    "ChatUpdate",
    "ChatResponse",
    "ChatsListResponse",
    "ChatParticipantAdd",
    "ChatParticipantUpdate",
    "ChatParticipantResponse",
    "ChatSettingsUpdate",
    "ChatSettingsResponse",
    "MessageCreate",
    "MessageUpdate",
    "MessageResponse",
    "MessagesListResponse",
    "MessageAttachmentCreate",
    "MessageAttachmentResponse",
    "MessageReactionCreate",
    "MessageReactionResponse",
    "WebSocketMessage",
    "WebSocketResponse",
    "TypingIndicator",
    "PresenceUpdate"
]
