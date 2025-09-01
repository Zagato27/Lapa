"""
Pydantic схемы для Media Service
"""

from .media_file import (
    MediaFileCreate,
    MediaFileUpdate,
    MediaFileResponse,
    MediaFilesListResponse,
    MediaFileUploadResponse,
    MediaFileVariantResponse
)
from .media_album import (
    MediaAlbumCreate,
    MediaAlbumUpdate,
    MediaAlbumResponse,
    MediaAlbumsListResponse
)
from .media_access import (
    MediaAccessCreate,
    MediaAccessUpdate,
    MediaAccessResponse,
    MediaAccessGrantRequest
)
from .processing import (
    ImageProcessingRequest,
    VideoProcessingRequest,
    ProcessingStatusResponse
)

__all__ = [
    "MediaFileCreate",
    "MediaFileUpdate",
    "MediaFileResponse",
    "MediaFilesListResponse",
    "MediaFileUploadResponse",
    "MediaFileVariantResponse",
    "MediaAlbumCreate",
    "MediaAlbumUpdate",
    "MediaAlbumResponse",
    "MediaAlbumsListResponse",
    "MediaAccessCreate",
    "MediaAccessUpdate",
    "MediaAccessResponse",
    "MediaAccessGrantRequest",
    "ImageProcessingRequest",
    "VideoProcessingRequest",
    "ProcessingStatusResponse"
]
