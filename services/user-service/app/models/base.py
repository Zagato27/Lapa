"""
Единый Declarative Base для всех SQLAlchemy моделей User Service.

Используется в `app.database.connection` для создания таблиц и
должен импортироваться всеми моделями (`app.models.user`, `app.models.walker_verification`).
"""

from sqlalchemy.orm import declarative_base


# Общий базовый класс моделей для сервиса пользователей
Base = declarative_base()


