# Lapa Payment Service

Сервис платежей и кошельков: прием платежей, возвраты, переводы между кошельками, вывод средств.

## Ключевые возможности
- Платежи, возвраты, статусы
- Пользовательские кошельки и транзакции
- Привязанные методы оплаты, Payouts
- Интеграции с провайдерами (Stripe/YooKassa/Tinkoff/SBP — моки)
- Redis: блокировки (payment lock), кэширование кошельков/лимитов

## Технологии
- FastAPI, SQLAlchemy (Async), PostgreSQL
- Redis (кэш/блокировки)
- Pydantic v2
- structlog, Prometheus

## Структура
```
app/
  api/v1/
  config/
  database/
  models/          # payment, wallet, transaction, payment_method, payout, base
  schemas/
  services/        # payment_service, wallet_service, payment_provider
main.py
```

## Конфигурация
- POSTGRES_*, REDIS_*, HOST, PORT
- Ключи провайдеров — см. `app/config.py`

## Запуск
```
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Блокировки и лимиты
- Redis lock предотвращает двойную обработку платежа
- Ежедневные лимиты/квоты — кэш в Redis

## Метрики/логи/здоровье
- `/metrics`, `/health`, structlog
