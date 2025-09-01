"""
Модель верификации выгульщиков.

Используется `WalkerService` для управления жизненным циклом верификаций.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, JSON, ForeignKey
from sqlalchemy.sql import func

from .base import Base


class WalkerVerification(Base):
    """Модель верификации выгульщика"""
    __tablename__ = "walker_verifications"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Данные паспорта
    passport_number = Column(String, nullable=False)
    passport_series = Column(String, nullable=False)
    passport_issued_by = Column(Text, nullable=False)
    passport_issued_date = Column(DateTime, nullable=False)
    passport_expiry_date = Column(DateTime, nullable=False)

    # Опыт работы
    experience_years = Column(Integer, nullable=False)

    # Услуги и график работы
    services_offered = Column(JSON, nullable=False)  # JSON array of services
    work_schedule = Column(JSON, nullable=False)    # JSON object with schedule

    # Статус верификации
    status = Column(String, default="pending")  # pending, approved, rejected
    admin_notes = Column(Text, nullable=True)
    verified_by = Column(String, nullable=True)  # ID администратора
    verified_at = Column(DateTime, nullable=True)

    # Документы
    passport_photo_front_url = Column(String, nullable=True)
    passport_photo_back_url = Column(String, nullable=True)
    additional_documents_urls = Column(JSON, nullable=True)  # JSON array of URLs

    # Метаданные
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<WalkerVerification(id={self.id}, user_id={self.user_id}, status={self.status})>"

    @property
    def is_pending(self) -> bool:
        """Проверка статуса ожидания"""
        return self.status == "pending"

    @property
    def is_approved(self) -> bool:
        """Проверка статуса одобрения"""
        return self.status == "approved"

    @property
    def is_rejected(self) -> bool:
        """Проверка статуса отклонения"""
        return self.status == "rejected"

    def approve(self, admin_id: str, notes: Optional[str] = None):
        """Одобрение верификации"""
        self.status = "approved"
        self.verified_by = admin_id
        self.verified_at = datetime.utcnow()
        if notes:
            self.admin_notes = notes

    def reject(self, admin_id: str, notes: str):
        """Отклонение верификации"""
        self.status = "rejected"
        self.verified_by = admin_id
        self.verified_at = datetime.utcnow()
        self.admin_notes = notes
