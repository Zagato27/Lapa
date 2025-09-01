# Lapa Media Service

Сервис медиа: загрузка файлов, альбомы, варианты (thumbnails/preview), метаданные, доступы.

## Ключевые возможности
- Загрузка/хранение/выдача медиафайлов
- Генерация вариантов (resize/crop/quality)
- Альбомы и теги
- Доступы на уровне файлов/альбомов

## Технологии
- FastAPI
- SQLAlchemy (Async) + PostgreSQL
- Pydantic v2
- Pillow, OpenCV (обработка изображений)
- Хранилище: локально/S3 (через `storage_manager`)
- structlog, Prometheus

## Структура
```
app/
  api/v1/
  config/
  database/
  models/         # media_file, media_album, media_variant, media_metadata, media_access, media_tag, base
  schemas/
  services/       # media_service, media_processor, storage_manager
main.py
```

## Конфигурация
- POSTGRES_*, HOST, PORT
- Допустимые типы файлов, размеры, пути хранилища — см. `app/config.py`

## Запуск
```
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Примечания
- Тяжёлые операции генерации делать асинхронно/в фоне
- Хранить оригинал и варианты раздельно, с метаданными в БД
