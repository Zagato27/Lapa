"""
Модель отзывов о заказах.

Используется:
- В `OrderService.add_order_review` для создания отзывов
- Для агрегаций рейтингов в статистике
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Float, Integer, Text, ForeignKey
from sqlalchemy.sql import func

from .base import Base


class OrderReview(Base):
    """Модель отзыва о заказе"""
    __tablename__ = "order_reviews"

    id = Column(String, primary_key=True, index=True)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False, index=True)

    # Автор отзыва
    reviewer_id = Column(String, nullable=False, index=True)
    reviewer_type = Column(String, nullable=False)  # 'client' или 'walker'

    # Получатель отзыва
    reviewee_id = Column(String, nullable=False, index=True)
    reviewee_type = Column(String, nullable=False)  # 'client' или 'walker'

    # Содержание отзыва
    rating = Column(Float, nullable=False)  # Оценка от 1 до 5
    title = Column(String, nullable=True)
    comment = Column(Text, nullable=True)

    # Категории оценки
    punctuality_rating = Column(Float, nullable=True)  # Пунктуальность
    communication_rating = Column(Float, nullable=True)  # Общение
    pet_care_rating = Column(Float, nullable=True)  # Уход за питомцем
    overall_experience = Column(Float, nullable=True)  # Общий опыт

    # Дополнительная информация
    is_public = Column(Boolean, default=True)
    is_anonymous = Column(Boolean, default=False)

    # Модерация
    is_moderated = Column(Boolean, default=False)
    moderated_by = Column(String, nullable=True)  # user_id модератора
    moderated_at = Column(DateTime, nullable=True)
    moderation_notes = Column(Text, nullable=True)

    # Метаданные
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<OrderReview(id={self.id}, order_id={self.order_id}, reviewer={self.reviewer_id}, rating={self.rating})>"

    @property
    def is_positive(self) -> bool:
        """Проверка, является ли отзыв положительным"""
        return self.rating >= 4.0

    @property
    def is_negative(self) -> bool:
        """Проверка, является ли отзыв отрицательным"""
        return self.rating <= 2.0

    @property
    def rating_category(self) -> str:
        """Категория рейтинга"""
        if self.rating >= 4.5:
            return "excellent"
        elif self.rating >= 4.0:
            return "good"
        elif self.rating >= 3.0:
            return "average"
        elif self.rating >= 2.0:
            return "poor"
        else:
            return "terrible"

    def moderate(self, moderator_id: str, approved: bool, notes: Optional[str] = None):
        """Модерация отзыва"""
        self.is_moderated = True
        self.moderated_by = moderator_id
        self.moderated_at = datetime.utcnow()
        if notes:
            self.moderation_notes = notes
