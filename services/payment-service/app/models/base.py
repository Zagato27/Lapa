"""
Единый Declarative Base для всех моделей Payment Service.

Используется модулем `app.database.connection` для создания таблиц и
должен импортироваться всеми моделями (`payment`, `wallet`, `transaction`, `payment_method`, `payout`).
"""

from sqlalchemy.orm import declarative_base


Base = declarative_base()


