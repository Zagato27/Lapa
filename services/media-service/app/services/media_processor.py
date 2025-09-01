"""
Процессор медиафайлов
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path
from PIL import Image, ExifTags
import cv2
import numpy as np

from app.config import settings
from app.database.session import get_session

logger = logging.getLogger(__name__)


class MediaProcessor:
    """Процессор для обработки медиафайлов"""

    def __init__(self):
        self.supported_image_formats = ['JPEG', 'PNG', 'GIF', 'WEBP', 'BMP', 'TIFF']
        self.supported_video_formats = ['MP4', 'MOV', 'AVI', 'MKV', 'WEBM', 'FLV']

    async def process_image(self, file_path: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Обработка изображения"""
        try:
            options = options or {}

            with Image.open(file_path) as img:
                # Получение информации об изображении
                info = await self._get_image_info(img)

                # Извлечение метаданных
                metadata = await self._extract_image_metadata(img)

                # Обработка изображения
                processed_path = None
                thumbnail_path = None

                if options.get('optimize', True):
                    processed_path = await self._optimize_image(file_path, options)

                if options.get('generate_thumbnail', True):
                    thumbnail_path = await self._generate_thumbnail(file_path, options)

                return {
                    "original_size": info["file_size"],
                    "width": info["width"],
                    "height": info["height"],
                    "format": info["format"],
                    "processed_path": processed_path,
                    "thumbnail_path": thumbnail_path,
                    "metadata": metadata
                }

        except Exception as e:
            logger.error(f"Error processing image {file_path}: {e}")
            raise

    async def process_video(self, file_path: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Обработка видео"""
        try:
            options = options or {}

            # Получение информации о видео
            info = await self._get_video_info(file_path)

            # Генерация миниатюры
            thumbnail_path = None
            if options.get('generate_thumbnail', True):
                thumbnail_path = await self._generate_video_thumbnail(file_path, options)

            # Конвертация видео
            processed_path = None
            if options.get('convert', False):
                processed_path = await self._convert_video(file_path, options)

            return {
                "original_size": info["file_size"],
                "duration": info["duration"],
                "width": info["width"],
                "height": info["height"],
                "frame_rate": info["frame_rate"],
                "bitrate": info["bitrate"],
                "processed_path": processed_path,
                "thumbnail_path": thumbnail_path
            }

        except Exception as e:
            logger.error(f"Error processing video {file_path}: {e}")
            raise

    async def extract_colors(self, file_path: str, num_colors: int = 5) -> List[Dict[str, Any]]:
        """Извлечение основных цветов изображения"""
        try:
            with Image.open(file_path) as img:
                # Преобразование в RGB
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # Изменение размера для ускорения обработки
                img = img.resize((150, 150))

                # Получение цветов
                colors = await self._extract_dominant_colors(img, num_colors)

                return colors

        except Exception as e:
            logger.error(f"Error extracting colors from {file_path}: {e}")
            return []

    async def _get_image_info(self, img: Image.Image) -> Dict[str, Any]:
        """Получение информации об изображении"""
        try:
            file_path = Path(img.filename) if img.filename else None

            return {
                "width": img.width,
                "height": img.height,
                "format": img.format,
                "mode": img.mode,
                "file_size": file_path.stat().st_size if file_path and file_path.exists() else 0
            }

        except Exception as e:
            logger.error(f"Error getting image info: {e}")
            return {}

    async def _get_video_info(self, file_path: str) -> Dict[str, Any]:
        """Получение информации о видео"""
        try:
            cap = cv2.VideoCapture(file_path)

            if not cap.isOpened():
                raise ValueError("Could not open video file")

            # Получение свойств видео
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            frame_rate = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / frame_rate if frame_rate > 0 else 0

            # Получение битрейта (примерное значение)
            file_size = Path(file_path).stat().st_size
            bitrate = int((file_size * 8) / duration) if duration > 0 else 0

            cap.release()

            return {
                "width": width,
                "height": height,
                "frame_rate": frame_rate,
                "frame_count": frame_count,
                "duration": duration,
                "bitrate": bitrate,
                "file_size": file_size
            }

        except Exception as e:
            logger.error(f"Error getting video info for {file_path}: {e}")
            return {}

    async def _extract_image_metadata(self, img: Image.Image) -> Dict[str, Any]:
        """Извлечение метаданных изображения"""
        try:
            metadata = {}

            # EXIF данные
            if hasattr(img, '_getexif') and img._getexif():
                exif_data = {}
                exif = img._getexif()

                for tag_id, value in exif.items():
                    tag = ExifTags.TAGS.get(tag_id, tag_id)
                    exif_data[tag] = str(value)

                metadata["exif"] = exif_data

                # Геолокация
                if 'GPSInfo' in exif:
                    gps_info = exif['GPSInfo']
                    latitude = self._convert_gps_coordinate(gps_info, 'latitude')
                    longitude = self._convert_gps_coordinate(gps_info, 'longitude')

                    if latitude and longitude:
                        metadata["location"] = {
                            "latitude": latitude,
                            "longitude": longitude
                        }

            return metadata

        except Exception as e:
            logger.error(f"Error extracting image metadata: {e}")
            return {}

    async def _optimize_image(self, file_path: str, options: Dict[str, Any]) -> Optional[str]:
        """Оптимизация изображения"""
        try:
            with Image.open(file_path) as img:
                # Преобразование в RGB если необходимо
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')

                # Изменение размера если указано
                if 'max_width' in options or 'max_height' in options:
                    max_width = options.get('max_width', img.width)
                    max_height = options.get('max_height', img.height)

                    if img.width > max_width or img.height > max_height:
                        img.thumbnail((max_width, max_height))

                # Оптимизация
                quality = options.get('quality', settings.image_quality)

                # Создание оптимизированного файла
                optimized_path = f"{file_path}.optimized.jpg"

                img.save(
                    optimized_path,
                    'JPEG',
                    quality=quality,
                    optimize=True,
                    progressive=True
                )

                return optimized_path

        except Exception as e:
            logger.error(f"Error optimizing image {file_path}: {e}")
            return None

    async def _generate_thumbnail(self, file_path: str, options: Dict[str, Any]) -> Optional[str]:
        """Генерация миниатюры"""
        try:
            with Image.open(file_path) as img:
                # Размер миниатюры
                size = options.get('thumbnail_size', (150, 150))

                # Создание миниатюры
                img.thumbnail(size)

                # Сохранение миниатюры
                thumbnail_path = f"{file_path}.thumbnail.jpg"

                img.save(
                    thumbnail_path,
                    'JPEG',
                    quality=settings.thumbnail_quality
                )

                return thumbnail_path

        except Exception as e:
            logger.error(f"Error generating thumbnail for {file_path}: {e}")
            return None

    async def _generate_video_thumbnail(self, file_path: str, options: Dict[str, Any]) -> Optional[str]:
        """Генерация миниатюры видео"""
        try:
            cap = cv2.VideoCapture(file_path)

            if not cap.isOpened():
                raise ValueError("Could not open video file")

            # Получение кадра (по умолчанию середина видео)
            frame_number = options.get('thumbnail_time', cap.get(cv2.CAP_PROP_FRAME_COUNT) // 2)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

            ret, frame = cap.read()
            cap.release()

            if not ret:
                raise ValueError("Could not read video frame")

            # Преобразование BGR в RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Создание изображения PIL
            img = Image.fromarray(frame_rgb)

            # Изменение размера
            img.thumbnail((300, 300))

            # Сохранение миниатюры
            thumbnail_path = f"{file_path}.thumbnail.jpg"

            img.save(
                thumbnail_path,
                'JPEG',
                quality=settings.thumbnail_quality
            )

            return thumbnail_path

        except Exception as e:
            logger.error(f"Error generating video thumbnail for {file_path}: {e}")
            return None

    async def _convert_video(self, file_path: str, options: Dict[str, Any]) -> Optional[str]:
        """Конвертация видео"""
        try:
            # Это упрощенная версия - в реальности нужна более сложная логика
            # с использованием ffmpeg или другой библиотеки для конвертации видео

            output_path = f"{file_path}.converted.mp4"

            # Пример простой конвертации с помощью OpenCV (ограниченная функциональность)
            cap = cv2.VideoCapture(file_path)

            if not cap.isOpened():
                raise ValueError("Could not open video file")

            # Получение свойств
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)

            # Создание видео-писателя
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                out.write(frame)

            cap.release()
            out.release()

            return output_path

        except Exception as e:
            logger.error(f"Error converting video {file_path}: {e}")
            return None

    async def _extract_dominant_colors(self, img: Image.Image, num_colors: int = 5) -> List[Dict[str, Any]]:
        """Извлечение основных цветов с использованием cv2.kmeans (без sklearn)."""
        try:
            img_array = np.array(img)
            pixels = img_array.reshape((-1, 3)).astype(np.float32)

            # Критерии остановки: 10 итераций или изменение < 1.0
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
            flags = cv2.KMEANS_PP_CENTERS

            compactness, labels, centers = cv2.kmeans(
                data=pixels,
                K=max(1, int(num_colors)),
                bestLabels=None,
                criteria=criteria,
                attempts=3,
                flags=flags
            )

            centers = centers.astype(int)
            labels = labels.flatten()

            total = len(labels)
            colors: List[Dict[str, Any]] = []
            for idx, center in enumerate(centers):
                percentage = float(np.sum(labels == idx) / total * 100.0)
                colors.append({
                    "rgb": [int(center[0]), int(center[1]), int(center[2])],
                    "hex": "#{:02x}{:02x}{:02x}".format(int(center[0]), int(center[1]), int(center[2])),
                    "percentage": percentage,
                })

            colors.sort(key=lambda x: x["percentage"], reverse=True)
            return colors

        except Exception as e:
            logger.error(f"Error extracting dominant colors: {e}")
            return []

    def _convert_gps_coordinate(self, gps_info: Dict, coordinate_type: str) -> Optional[float]:
        """Конвертация GPS координат из EXIF"""
        try:
            if coordinate_type == 'latitude':
                coords = gps_info.get(0x0002)  # GPSLatitude
                ref = gps_info.get(0x0001)    # GPSLatitudeRef
            else:
                coords = gps_info.get(0x0004)  # GPSLongitude
                ref = gps_info.get(0x0003)    # GPSLongitudeRef

            if not coords or not ref:
                return None

            # Конвертация DMS в десятичные градусы
            degrees = coords[0] + coords[1]/60 + coords[2]/3600

            if ref in ('S', 'W'):
                degrees = -degrees

            return degrees

        except Exception:
            return None
