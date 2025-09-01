"""
Пакет базы данных Analytics Service.

Экспортирует основные утилиты:
- get_db: зависимость FastAPI для выдачи `AsyncSession`
- create_tables: создание таблиц по общему `Base`
"""

from .connection import get_db, create_tables

__all__ = ["get_db", "create_tables"]


