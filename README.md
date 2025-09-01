# Lapa Platform

Много-сервисная платформа (microservices) на FastAPI. Репозиторий содержит набор независимых сервисов и API Gateway, объединённых общей инфраструктурой (Docker Compose / Kubernetes), едиными практиками логирования, метрик и валидации данных.

## Архитектура
Сервисы (каждый — самостоятельное приложение FastAPI):
- api-gateway: единая точка входа, маршрутизация к сервисам, аутентификация (JWT), безопасность, мониторинг
- user-service: пользователи, аутентификация, роли/права, профили, верификация выгульщиков
- pet-service: питомцы, фото, медицинские записи
- order-service: заказы, ценообразование, матчинг исполнителей (геопоиск)
- payment-service: кошельки, платежи/возвраты, payout, интеграции с провайдерами (моки)
- notification-service: шаблоны/каналы/подписки, отправка и трекинг уведомлений
- media-service: загрузка/хранение медиа, альбомы, варианты (thumbnails/preview)
- location-service: трекинг, геофенсы, маршруты, алерты (PostGIS), WebSocket
- chat-service: чаты, сообщения, вложения, WS-трансляции
- analytics-service: события, метрики, KPI, отчёты, дашборды, сегментация

Общие принципы:
- Pydantic v2 для схем, SQLAlchemy 2.x (Async) + asyncpg
- PostgreSQL (+ PostGIS для `location-service`), Redis (кэш/блокировки/лимиты)
- Структурированное логирование (structlog) и метрики Prometheus (`/metrics` у каждого сервиса)

## Структура репозитория
```
./
  docker/                 # шаблоны Dockerfile и инфраструктурные образы
  infrastructure/
    k8s/base/             # манифесты для Kubernetes (namespace, secrets, services и т.д.)
  services/
    api-gateway/
    user-service/
    pet-service/
    order-service/
    payment-service/
    notification-service/
    media-service/
    location-service/
    chat-service/
    analytics-service/
  docker-compose.yml
  README.md (этот файл)
```

## Быстрый старт (Docker Compose)
1) Подготовьте .env в корне (см. примеры переменных ниже)
2) Запустите всё одной командой:
```bash
docker compose up -d --build
```
3) Откройте API Gateway: `http://localhost:8080/` (Swagger: `/docs`)

Стандартные порты (по умолчанию):
- API Gateway: 8080
- Сервисы: 8000 (каждый в своём контейнере)

## Пример .env (корень репозитория)
```env
# Общие
HOST=0.0.0.0
PORT=8000
DEBUG=false
ALLOWED_HOSTS=*

# Postgres
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=lapa_user
POSTGRES_PASSWORD=lapa_password
POSTGRES_DB=lapa

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=

# JWT (используется gateway и user-service)
JWT_SECRET_KEY=change-me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# URL сервисов для gateway/analytics
USER_SERVICE_URL=http://user-service:8000
PET_SERVICE_URL=http://pet-service:8000
ORDER_SERVICE_URL=http://order-service:8000
LOCATION_SERVICE_URL=http://location-service:8000
PAYMENT_SERVICE_URL=http://payment-service:8000
CHAT_SERVICE_URL=http://chat-service:8000
MEDIA_SERVICE_URL=http://media-service:8000
NOTIFICATION_SERVICE_URL=http://notification-service:8000
ANALYTICS_SERVICE_URL=http://analytics-service:8000
```

## Запуск сервисов локально (без Docker)
Для любого сервиса:
```bash
cd services/<service-name>
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
Требуется PostgreSQL/Redis, настройки — в `app/config.py` соответствующего сервиса.

## API Gateway
- Swagger: `http://localhost:8080/docs`
- Проксирование: `/{service}/{path}` → соответствующий сервис
- Auth: `AuthMiddleware` валидирует JWT и прокладывает `request.state.user_id`
- Служебные эндпоинты: `/api/v1/gateway/stats`, `/api/v1/gateway/services`, `/health`, `/metrics`

## База данных и миграции
- Каждый сервис использует единый `Base` для своих моделей (`app/models/base.py`)
- PostGIS требуется для `location-service` (геооперации `ST_DWithin`, `ST_GeogFromText`)
- Для миграций используйте Alembic (если предусмотрен в сервисе)

## Мониторинг и логирование
- Метрики Prometheus доступны на `/metrics` каждого сервиса и gateway
- Логи — JSON (structlog), выводятся в stdout (готовы для агрегации)

## Тестирование и качество
- Тесты: `pytest`
- В некоторых сервисах присутствуют dev-зависимости `flake8`, `black`, `isort`

## Развёртывание (Kubernetes)
Манифесты в `infrastructure/k8s/base/` (namespace, базы данных, redis, gateway и т.д.). Пример:
```bash
kubectl apply -f infrastructure/k8s/base/namespace.yaml
kubectl apply -f infrastructure/k8s/base/postgres.yaml
kubectl apply -f infrastructure/k8s/base/redis.yaml
kubectl apply -f infrastructure/k8s/base/services.yaml
kubectl apply -f infrastructure/k8s/base/api-gateway.yaml
```
Секреты/конфиги — см. `infrastructure/k8s/base/secrets.yaml` и соответствующие файлы.

## Полезные ссылки по сервисам
- services/api-gateway/README.md — маршруты, middleware и интеграции
- services/user-service/README.md — аутентификация, профили
- services/pet-service/README.md — питомцы и медиа
- services/order-service/README.md — заказы, ценообразование, геопоиск
- services/payment-service/README.md — платежи и кошельки
- services/notification-service/README.md — уведомления, шаблоны, кампании
- services/media-service/README.md — медиа, варианты, альбомы
- services/location-service/README.md — геолокация, геофенсы, WebSocket
- services/chat-service/README.md — чаты и сообщения
- services/analytics-service/README.md — события, метрики, KPI

## Troubleshooting
- Проверьте доступность Postgres/Redis контейнеров (`docker compose ps`, `logs`)
- PostGIS: убедитесь, что расширение установлено для базы `lapa` (для `location-service`)
- JWT: одинаковые секрет/алгоритм в gateway и user-service
- CORS/TrustedHost: скорректируйте `CORS_ORIGINS` и `ALLOWED_HOSTS` при работе из браузера

---
Подробности по каждому сервису — в соответствующих README внутри `services/`.