"""
Модели базы данных для Media Service
"""

from .base import Base
from .media_file import MediaFile
from .media_album import MediaAlbum
from .media_tag import MediaTag
from .media_access import MediaAccess
from .media_metadata import MediaMetadata
from .media_variant import MediaVariant

__all__ = [
    "Base",
    "MediaFile",
    "MediaAlbum",
    "MediaTag",
    "MediaAccess",
    "MediaMetadata",
    "MediaVariant"
]
