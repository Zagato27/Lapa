# Lapa Analytics Service

Сервис аналитики и бизнес-метрик: события, метрики, KPI, отчёты, дашборды, сегменты.

## Ключевые возможности
- Трекинг событий (user/system/business/error)
- Метрики и агрегирование по периодам/гранулярности
- KPI: расчёт статусов/трендов/алертов
- Отчёты и дашборды (конфигурация/статусы)
- Сегментация пользователей

## Технологии
- FastAPI
- SQLAlchemy (Async) + PostgreSQL
- Pydantic v2
- Redis (опционально — кэш статистики)
- structlog, Prometheus

## Структура
```
app/
  api/v1/
  config/
  database/           # async engine + get_db + create_tables
  models/             # event, metric, kpi, dashboard, report, segment, base
  schemas/            # event, metric, kpi
  services/           # analytics_service, data_collection_service
main.py
```

## Конфигурация
- POSTGRES_*, REDIS_*, HOST, PORT
- Внешние URL сервисов (для `DataCollectionService`) — в `app/config.py`

## Запуск
```
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Безопасность
- Межсервисные ссылки хранятся как строки без FK
- Enum-поля валидируются и фильтруются безопасно
