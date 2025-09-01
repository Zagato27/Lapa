"""
Pydantic-схемы (v2) для обработки медиафайлов.

Используются роутами `app.api.v1.processing` и `MediaProcessor`.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_validator


class ImageProcessingRequest(BaseModel):
    """Запрос на обработку изображения"""
    media_file_id: str
    operations: List[Dict[str, Any]]

    # Базовые операции
    resize: Optional[Dict[str, Any]] = None  # {"width": 800, "height": 600, "maintain_aspect": true}
    crop: Optional[Dict[str, Any]] = None    # {"x": 100, "y": 100, "width": 200, "height": 200}
    rotate: Optional[int] = None             # Угол поворота в градусах
    flip: Optional[str] = None               # "horizontal", "vertical"

    # Коррекция цвета
    brightness: Optional[float] = None       # -100 to 100
    contrast: Optional[float] = None         # -100 to 100
    saturation: Optional[float] = None       # -100 to 100
    hue: Optional[float] = None              # -180 to 180

    # Фильтры
    blur: Optional[Dict[str, Any]] = None    # {"radius": 5}
    sharpen: Optional[Dict[str, Any]] = None # {"amount": 1.0}
    filters: Optional[List[str]] = None      # ["grayscale", "sepia", "vintage"]

    # Формат и качество
    output_format: Optional[str] = None      # "jpg", "png", "webp"
    quality: Optional[int] = None            # 1-100 для JPEG
    compression: Optional[int] = None        # 0-9 для PNG

    # Водяной знак
    watermark: Optional[Dict[str, Any]] = None

    @field_validator('operations')
    def validate_operations(cls, v):
        if not v:
            return v
        valid_operations = [
            "resize", "crop", "rotate", "flip", "brightness", "contrast",
            "saturation", "hue", "blur", "sharpen", "filter", "watermark"
        ]
        for op in v:
            if 'type' not in op or op['type'] not in valid_operations:
                raise ValueError(f'Invalid operation type: {op.get("type")}')
        return v


class VideoProcessingRequest(BaseModel):
    """Запрос на обработку видео"""
    media_file_id: str

    # Базовые операции
    trim: Optional[Dict[str, Any]] = None    # {"start": "00:00:10", "end": "00:00:30"}
    resize: Optional[Dict[str, Any]] = None  # {"width": 1280, "height": 720}
    crop: Optional[Dict[str, Any]] = None    # {"x": 100, "y": 100, "width": 800, "height": 600}

    # Качество и формат
    output_format: Optional[str] = None      # "mp4", "webm", "avi"
    video_codec: Optional[str] = None        # "h264", "h265", "vp9"
    audio_codec: Optional[str] = None        # "aac", "mp3", "opus"
    bitrate: Optional[int] = None            # Битрейт в kbps
    frame_rate: Optional[float] = None       # Частота кадров

    # Аудио
    audio_volume: Optional[float] = None     # Громкость (0.0-2.0)
    audio_normalize: Optional[bool] = None   # Нормализация громкости

    # Эффекты
    speed: Optional[float] = None            # Скорость воспроизведения
    reverse: Optional[bool] = None           # Реверс видео

    # Миниатюра
    generate_thumbnail: bool = True
    thumbnail_time: str = "00:00:05"         # Время для кадра миниатюры


class ProcessingStatusResponse(BaseModel):
    """Ответ со статусом обработки"""
    media_file_id: str
    status: str
    progress: Optional[float]
    message: Optional[str]
    estimated_time: Optional[int]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    errors: Optional[List[str]]


class BatchProcessingRequest(BaseModel):
    """Запрос на пакетную обработку"""
    media_file_ids: List[str]
    processing_type: str  # "image", "video"
    parameters: Dict[str, Any]

    @field_validator('media_file_ids')
    def validate_file_ids(cls, v):
        if not v:
            raise ValueError('At least one media file ID required')
        if len(v) > 100:
            raise ValueError('Too many files for batch processing')
        return v


class BatchProcessingResponse(BaseModel):
    """Ответ на пакетную обработку"""
    total_files: int
    processed_files: int
    failed_files: int
    results: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]


class MediaConversionRequest(BaseModel):
    """Запрос на конвертацию медиафайла"""
    media_file_id: str
    target_format: str
    quality: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    bitrate: Optional[int] = None


class MediaOptimizationRequest(BaseModel):
    """Запрос на оптимизацию медиафайла"""
    media_file_ids: List[str]
    optimization_level: str = "medium"  # "low", "medium", "high", "extreme"
    target_formats: Optional[List[str]] = None
    max_width: Optional[int] = None
    max_height: Optional[int] = None
    quality: Optional[int] = None


class MediaThumbnailRequest(BaseModel):
    """Запрос на генерацию миниатюр"""
    media_file_ids: List[str]
    sizes: List[str] = ["150x150", "300x300", "600x600"]
    format: str = "jpg"
    quality: int = 80
    time_offset: Optional[str] = None  # Для видео: "00:00:05"


class MediaMetadataRequest(BaseModel):
    """Запрос на извлечение метаданных"""
    media_file_ids: List[str]
    extract_gps: bool = False
    extract_colors: bool = True
    extract_faces: bool = False


class ProcessingQueueResponse(BaseModel):
    """Ответ с очередью обработки"""
    queue_length: int
    processing_jobs: List[Dict[str, Any]]
    completed_today: int
    failed_today: int
    average_processing_time: float


class ProcessingStatisticsResponse(BaseModel):
    """Ответ со статистикой обработки"""
    total_processed: int
    success_rate: float
    average_file_size: float
    average_processing_time: float
    most_used_formats: List[Dict[str, Any]]
    processing_by_type: Dict[str, int]
    period_start: datetime
    period_end: datetime
