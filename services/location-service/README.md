# Lapa Location Service

Сервис геолокации: трекинг перемещений, геофенсы, маршруты, алерты и WebSocket-уведомления.

## Ключевые возможности
- Отправка координат (реалтайм/WebSocket)
- Хранение треков перемещения
- Геофенсы и алерты по входу/выходу
- Поиск ближайших объектов по радиусу

## Технологии
- FastAPI, WebSocket
- SQLAlchemy (Async) + PostgreSQL + PostGIS
- Pydantic v2
- geoalchemy2, PostGIS функции (`ST_DWithin`, `ST_GeogFromText`)
- structlog, Prometheus

## Структура
```
app/
  api/v1/
  config/
  database/
  models/          # geofence, location_track, route, location_alert, base
  schemas/
  services/        # location_service, geofence_service, location_tracker, websocket_manager
main.py
```

## Конфигурация
- POSTGRES_* (с PostGIS), HOST, PORT
- Интервалы и параметры алертов — в `app/config.py`

## Запуск
```
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## WebSocket
- Отдельный endpoint для подписки на события трекинга/алертов

## Безопасность
- Все геооперации выполняются параметризованными запросами через SQLAlchemy `text()`
