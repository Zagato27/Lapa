# Lapa Chat Service

Сервис чатов и сообщений: личные чаты, сообщения, вложения, настройки, WebSocket-трансляции.

## Ключевые возможности
- Создание/подписка на чаты
- Отправка/получение сообщений
- Вложения к сообщениям (files)
- WebSocket-уведомления участникам

## Технологии
- FastAPI, WebSocket
- SQLAlchemy (Async) + PostgreSQL
- Pydantic v2
- structlog, Prometheus

## Структура
```
app/
  api/v1/
  config/
  database/
  models/        # chat, message, chat_participant, message_attachment, chat_settings, base
  schemas/
  services/      # chat_service, websocket_manager, message_service, file_manager
main.py
```

## Конфигурация
- POSTGRES_*, HOST, PORT

## Запуск
```
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## WebSocket
- Менеджер соединений передаёт сообщения всем участникам чата

## Безопасность
- Проверка участников чата перед отправкой/чтением сообщений
