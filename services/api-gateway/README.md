# Lapa API Gateway

Единая точка входа: маршрутизация к микросервисам, аутентификация, безопасность, мониторинг, rate limit.

## Ключевые возможности
- Проксирование запросов к сервисам (`/api/v1/{service}/...`)
- Аутентификация JWT (middleware `AuthMiddleware` + `AuthService`)
- CORS/TrustedHost/Rate limiting (slowapi)
- Мониторинг состояния сервисов и статистика шлюза
- Простейший Service Discovery (статическая конфигурация URL)

## Технологии
- FastAPI
- slowapi (лимитирование)
- httpx (проксирование)
- Redis (кэш/лимиты — опционально)
- structlog, Prometheus

## Структура
```
app/
  api/v1/              # Роуты шлюза (gateway mgmt, auth proxy, generic routing)
  config.py            # Настройки, URL сервисов и маршрутные политики
  database/__init__.py # init_cache (Redis)
  middleware/          # AuthMiddleware (+ стандартные FastAPI)
  models/              # RouteStats (на случай агрегации в БД)
  routes/              # auth, users (пример высокого уровня)
  schemas/             # Схемы ответов/запросов шлюза
  services/            # gateway_service, auth_service, monitoring_service, discovery
main.py
```

## Конфигурация
- Redis: `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`
- URL сервисов: `*_SERVICE_URL` (user, pet, order, location, payment, chat, media, notification, analytics)
- Безопасность: CORS, allowed hosts, JWT-секрет/алго
- Rate limit: глобальные и per-route

## Запуск
```
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

## Маршруты и middleware
- `AuthMiddleware` — проверка токена и прокладка `request.state.user_id`
- `api/v1/gateway/*` — служебные (статистика, список сервисов, роутов)
- `api/v1/auth/*` — прокси к user-service
- `/{service}/{path}` — общий прокси-роутинг через `GatewayService`

## Интеграции
- С сервисами платформы по HTTP через httpx
- Prometheus `/metrics`, `/health`, `/services`
