"""
Общий базовый класс SQLAlchemy для моделей Notification Service.

Используется всеми моделями чтобы иметь единый MetaData и корректно
создавать/мигрировать таблицы в рамках сервиса.
"""

from sqlalchemy.orm import declarative_base


Base = declarative_base()


