# Lapa Pet Service

Сервис питомцев: профили питомцев, фотографии, медицинские данные.

## Ключевые возможности
- CRUD питомцев
- Фото и альбомы (миниатюры/варианты)
- Медицинские записи
- Теги и метаданные (JSON)

## Технологии
- FastAPI
- SQLAlchemy (Async) + asyncpg + PostgreSQL
- Pydantic v2
- Pillow — работа с изображениями (resize, метаданные)
- Redis (опционально — кэш)
- structlog, Prometheus

## Структура
```
app/
  api/v1/
  config/
  database/
  models/          # pet, pet_photo, pet_medical, base
  schemas/
  services/        # media/фото обработка
main.py
```

## Конфигурация
- POSTGRES_*, REDIS_*, HOST, PORT
- Параметры обработки изображений — см. `app/config.py`

## Запуск
```
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Хранение медиа
- Метаданные изображений в БД
- Сами файлы — локально/S3 (в зависимости от конфигурации `storage_manager`)

## Метрики и логи
- `/metrics` — Prometheus
- structlog — JSON-логи

## Примечания
- `tags` для фото хранится как JSON в текстовом поле/JSONB в зависимости от модели
