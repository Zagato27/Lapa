"""
Единый Declarative Base для всех моделей Pet Service.

Используется модулем `app.database.connection` для создания таблиц
и импортируется всеми моделями (`pet`, `pet_photo`, `pet_medical`).
"""

from sqlalchemy.orm import declarative_base


Base = declarative_base()


