# Lapa Notification Service

Сервис уведомлений: события, шаблоны, каналы, подписки, доставка, кампании.

## Ключевые возможности
- Создание и планирование отправок
- Шаблоны (email/SMS/push) и каналы
- Подписки пользователей
- Статистика доставок

## Технологии
- FastAPI, SQLAlchemy (Async), PostgreSQL
- Pydantic v2
- Redis (очереди/кэш — опционально)
- structlog, Prometheus

## Структура
```
app/
  api/v1/
  config/
  database/
  models/     # notification, template, channel, subscription, delivery, campaign, base
  schemas/
  services/
main.py
```

## Конфигурация
- POSTGRES_*, REDIS_*, HOST, PORT

## Запуск
```
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Интеграции
- Почтовые/СМС провайдеры подключаются в `services`

## Метрики/логи
- `/metrics`, structlog
