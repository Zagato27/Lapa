# Lapa User Service

Сервис пользователей и аутентификации. Управляет профилями, ролями и верификацией выгульщиков, выдает и проверяет JWT токены.

## Ключевые возможности
- Регистрация/логин/refresh/logout
- Хранение и обновление профиля
- Роли и права доступа (client/walker/admin)
- Верификация документов выгульщиков
- Геоданные пользователя (для поиска рядом)
- Кэширование и интеграция с Redis

## Технологии
- FastAPI
- SQLAlchemy 2.x (Async) + asyncpg
- PostgreSQL (опционально PostGIS для координат)
- Redis (кэш, refresh-токены)
- Pydantic v2
- `python-jose[cryptography]` — JWT
- `passlib[bcrypt]` — хэширование паролей
- structlog, Prometheus

## Структура
```
app/
  api/v1/         # Роуты: auth, users
  config/
  database/
  models/         # user, walker_verification, base
  schemas/        # user, auth
  services/       # auth_service, user_service
main.py
```

## Конфигурация (пример)
См. `app/config.py`:
- POSTGRES_*, REDIS_*
- JWT: JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
- Сетевые: HOST, PORT, ALLOWED_HOSTS, CORS_ORIGINS

## Запуск
```
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Безопасность
- Пароли — только в виде bcrypt-хэшей
- JWT — проверка подписи и сроков действия
- Refresh-токены могут храниться в Redis (ревокация/ротация)

## Метрики, логи, здоровье
- `/metrics`, `/health` — метрики и состояние
- structlog — структурированные логи

## Основные эндпоинты (сводно)
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET/PUT /api/v1/users/profile`
- `POST /api/v1/users/verify-documents`

## Тестирование
```
pytest -q
```
