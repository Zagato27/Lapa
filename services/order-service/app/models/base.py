"""
Единый Declarative Base для всех SQLAlchemy моделей Order Service.

Зачем нужен:
- Обеспечивает единое `Base.metadata` для корректного создания/миграции таблиц
- Используется модулем `app.database.connection` для вызова `Base.metadata.create_all`
- Должен импортироваться всеми моделями в `app.models.*`
"""

from sqlalchemy.orm import declarative_base


# Единый базовый класс моделей для всего сервиса
Base = declarative_base()


