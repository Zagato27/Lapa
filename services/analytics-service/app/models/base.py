"""
Единый базовый класс SQLAlchemy для всех моделей Analytics Service.

Важно использовать один общий `Base`, чтобы все модели разделяли одно `MetaData`.
Это необходимо для корректного создания схемы БД (`Base.metadata.create_all`) и миграций.
"""

from sqlalchemy.orm import declarative_base


Base = declarative_base()


