"""
Модель медицинской информации питомцев.

Используется `MedicalService` и эндпоинтами `app.api.v1.medical`.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Float, Text, JSON, ForeignKey
from sqlalchemy.sql import func

from .base import Base


class PetMedical(Base):
    """Модель медицинской информации питомца"""
    __tablename__ = "pet_medical"

    id = Column(String, primary_key=True, index=True)
    pet_id = Column(String, ForeignKey("pets.id"), nullable=False, index=True)

    # Тип записи
    record_type = Column(String, nullable=False)  # vaccination, medication, illness, surgery, checkup, other

    # Основная информация
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Медицинские детали
    medication_name = Column(String, nullable=True)
    medication_dosage = Column(String, nullable=True)
    medication_frequency = Column(String, nullable=True)

    # Ветеринарная информация
    veterinarian_name = Column(String, nullable=True)
    veterinarian_phone = Column(String, nullable=True)
    clinic_name = Column(String, nullable=True)
    clinic_address = Column(Text, nullable=True)

    # Даты
    event_date = Column(DateTime, nullable=False)
    next_visit_date = Column(DateTime, nullable=True)
    vaccination_due_date = Column(DateTime, nullable=True)

    # Стоимость
    cost = Column(Float, nullable=True)

    # Результаты и рекомендации
    results = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)

    # Документы
    documents_urls = Column(JSON, nullable=True)  # JSON array of document URLs

    # Статус
    is_completed = Column(Boolean, default=True)
    requires_follow_up = Column(Boolean, default=False)

    # Метаданные
    created_by = Column(String, nullable=False)  # user_id
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<PetMedical(id={self.id}, pet_id={self.pet_id}, type={self.record_type}, title={self.title})>"

    @property
    def is_vaccination(self) -> bool:
        """Проверка, является ли запись вакцинацией"""
        return self.record_type == "vaccination"

    @property
    def is_medication(self) -> bool:
        """Проверка, является ли запись приемом лекарств"""
        return self.record_type == "medication"

    @property
    def is_past_due(self) -> bool:
        """Проверка, просрочена ли запись"""
        now = datetime.utcnow()
        if self.vaccination_due_date and self.vaccination_due_date < now:
            return True
        if self.next_visit_date and self.next_visit_date < now:
            return True
        return False

    @property
    def days_until_next_visit(self) -> Optional[int]:
        """Количество дней до следующего визита"""
        if not self.next_visit_date:
            return None

        now = datetime.utcnow()
        delta = self.next_visit_date - now
        return max(0, delta.days)

    @property
    def days_until_vaccination(self) -> Optional[int]:
        """Количество дней до следующей вакцинации"""
        if not self.vaccination_due_date:
            return None

        now = datetime.utcnow()
        delta = self.vaccination_due_date - now
        return max(0, delta.days)
