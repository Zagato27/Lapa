"""
Единый базовый класс SQLAlchemy для всех моделей Location Service.

Используется всеми моделями, чтобы разделять одно `MetaData` и корректно
создавать/мигрировать таблицы (`Base.metadata.create_all`).
"""

from sqlalchemy.orm import declarative_base


Base = declarative_base()


