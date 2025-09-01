"""
Единый базовый класс SQLAlchemy для всех моделей Chat Service.

Важно использовать один общий `Base`, чтобы все модели разделяли одно `MetaData`.
Это необходимо для корректного создания схемы БД (`Base.metadata.create_all`).
"""

from sqlalchemy.orm import declarative_base


Base = declarative_base()


