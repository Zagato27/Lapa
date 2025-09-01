# Lapa Order Service

Сервис заказов платформы Lapa. Отвечает за создание и управление заказами, ценообразование, геопоиск ближайших исполнителей и сопутствующую бизнес-логику.

## Ключевые возможности
- CRUD операций над заказами
- Ценообразование (модуль `pricing_service`)
- Матчинг с исполнителями по геолокации (модуль `matching_service` + PostGIS)
- Кэширование списков заказов в Redis (составные ключи, консистентная инвалидация)
- Структурированное логирование и метрики Prometheus

## Технологии
- FastAPI (ASGI)
- SQLAlchemy 2.x (Async) + asyncpg
- PostgreSQL (+ PostGIS для географии)
- Redis (кэш, списки и выборки)
- Pydantic v2 для схем
- structlog для логирования
- Prometheus client (/metrics)

## Структура каталогов
```
app/
  api/v1/          # Роуты API
  config/          # Настройки приложения
  database/        # Подключение и сессии БД, Redis
  models/          # Модели ORM: order, order_location, order_review
  schemas/         # Pydantic-схемы запросов/ответов
  services/        # Бизнес-логика: order_service, pricing_service, matching_service
  utils/           # Утилиты
main.py            # Точка входа FastAPI
```

## Конфигурация (переменные окружения)
См. `app/config.py` для полного списка. Основное:
- POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
- REDIS_HOST, REDIS_PORT, REDIS_PASSWORD (опционально)
- HOST, PORT — HTTP-сервер
- CORS_ORIGINS, ALLOWED_HOSTS

## Запуск локально
```
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Docker
Сервис интегрирован в общий `docker-compose.yml`. Локально:
```
docker build -t lapa-order-service .
```

## База данных и миграции
- Единый `Base` для всех моделей (см. `app/models/base.py`).
- Геооперации выполняются через PostGIS (например `ST_DWithin`).
- Миграции (если используются) — через Alembic в корне сервиса.

## Кэширование
- Списки заказов кэшируются в Redis по составным ключам (пейджинг, фильтры).
- Инвалидация выполняется консистентно при CRUD-операциях в `order_service`.

## Безопасность и аутентификация
- В проде авторизация/аутентификация обычно обеспечивается API Gateway.
- В сервисе ожидаются заголовки с идентификатором пользователя, полученные от Gateway.

## Метрики и логирование
- `/metrics` — метрики Prometheus
- structlog — JSON-логирование для удобной агрегации

## Тестирование
```
pytest -q
```

## Точки интеграции
- User Service — данные пользователей
- Payment Service — статусы оплат
- Location Service — геопоиск исполнителей
- Notification Service — уведомления о статусе заказа

## Диагностика
- `/health` — состояние сервиса
- Логи ошибок и бизнес-событий — в stdout (структурировано)
