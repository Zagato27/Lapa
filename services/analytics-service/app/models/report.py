"""
Модель отчетов аналитики
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, JSON, ForeignKey, Float, Enum
from sqlalchemy.sql import func
import enum
import uuid

from .base import Base


class ReportType(str, enum.Enum):
    """Типы отчетов"""
    SCHEDULED = "scheduled"                  # Запланированный
    ON_DEMAND = "on_demand"                  # По требованию
    AUTOMATED = "automated"                  # Автоматизированный
    COMPLIANCE = "compliance"                # Соответствие требованиям


class ReportFormat(str, enum.Enum):
    """Форматы отчетов"""
    PDF = "pdf"                              # PDF
    EXCEL = "excel"                           # Excel
    CSV = "csv"                              # CSV
    HTML = "html"                            # HTML
    JSON = "json"                            # JSON
    POWERPOINT = "powerpoint"                 # PowerPoint


class ReportStatus(str, enum.Enum):
    """Статусы отчетов"""
    PENDING = "pending"                      # Ожидает
    PROCESSING = "processing"                # Обрабатывается
    COMPLETED = "completed"                  # Завершен
    FAILED = "failed"                        # Ошибка
    CANCELLED = "cancelled"                  # Отменен


class ReportFrequency(str, enum.Enum):
    """Частота генерации отчетов"""
    DAILY = "daily"                          # Ежедневно
    WEEKLY = "weekly"                        # Еженедельно
    MONTHLY = "monthly"                      # Ежемесячно
    QUARTERLY = "quarterly"                  # Ежеквартально
    YEARLY = "yearly"                        # Ежегодно
    ONCE = "once"                            # Однократно


class Report(Base):
    """Модель отчета аналитики"""
    __tablename__ = "analytics_reports"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)                    # Название отчета
    description = Column(Text, nullable=True)                 # Описание

    # Тип и формат
    report_type = Column(Enum(ReportType), nullable=False)
    format = Column(Enum(ReportFormat), nullable=False, default=ReportFormat.PDF)

    # Статус и прогресс
    status = Column(Enum(ReportStatus), nullable=False, default=ReportStatus.PENDING)
    progress_percentage = Column(Float, default=0)            # Процент выполнения

    # Параметры генерации
    template_id = Column(String, nullable=True)               # ID шаблона
    parameters = Column(JSON, nullable=True)                  # Параметры отчета
    filters = Column(JSON, nullable=True)                     # Фильтры данных

    # Расписание
    frequency = Column(Enum(ReportFrequency), nullable=True)
    next_run_at = Column(DateTime, nullable=True)             # Следующий запуск
    last_run_at = Column(DateTime, nullable=True)             # Последний запуск

    # Период данных
    date_from = Column(DateTime, nullable=True)               # Дата начала
    date_to = Column(DateTime, nullable=True)                 # Дата окончания
    timezone = Column(String, default="Europe/Moscow")        # Часовой пояс

    # Результаты
    file_path = Column(String, nullable=True)                 # Путь к файлу
    file_size = Column(Integer, nullable=True)                # Размер файла
    generation_time = Column(Float, nullable=True)            # Время генерации
    error_message = Column(Text, nullable=True)               # Сообщение об ошибке

    # Доставка
    delivery_method = Column(String, nullable=True)           # Метод доставки
    delivery_recipients = Column(JSON, nullable=True)         # Получатели
    delivery_status = Column(String, nullable=True)           # Статус доставки

    # Создал и настройки
    # Межсервисная ссылка на пользователя-автора
    created_by = Column(String, nullable=False, index=True)
    is_template = Column(Boolean, default=False)              # Является ли шаблоном
    is_public = Column(Boolean, default=False)                # Публичный доступ

    # Статистика
    download_count = Column(Integer, default=0)               # Количество скачиваний
    view_count = Column(Integer, default=0)                   # Количество просмотров
    last_accessed_at = Column(DateTime, nullable=True)        # Последний доступ

    # Метаданные
    tags = Column(JSON, nullable=True)                        # Теги
    metadata = Column(JSON, nullable=True)                    # Дополнительные метаданные

    # Временные метки
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Report(id={self.id}, name={self.name}, type={self.report_type.value}, status={self.status.value})>"

    @property
    def is_pending(self) -> bool:
        """Проверка, ожидает ли выполнения"""
        return self.status == ReportStatus.PENDING

    @property
    def is_processing(self) -> bool:
        """Проверка, выполняется ли"""
        return self.status == ReportStatus.PROCESSING

    @property
    def is_completed(self) -> bool:
        """Проверка, завершен ли"""
        return self.status == ReportStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Проверка, произошла ли ошибка"""
        return self.status == ReportStatus.FAILED

    @property
    def duration_days(self) -> Optional[int]:
        """Длительность периода в днях"""
        if self.date_from and self.date_to:
            return (self.date_to - self.date_from).days
        return None

    @property
    def is_overdue(self) -> bool:
        """Проверка, просрочен ли отчет"""
        if not self.next_run_at:
            return False
        return datetime.utcnow() > self.next_run_at

    @property
    def file_exists(self) -> bool:
        """Проверка существования файла"""
        if not self.file_path:
            return False
        # Здесь должна быть проверка существования файла
        return True

    def start_processing(self):
        """Начало обработки отчета"""
        self.status = ReportStatus.PROCESSING
        self.progress_percentage = 0
        self.updated_at = datetime.utcnow()

    def update_progress(self, percentage: float):
        """Обновление прогресса"""
        self.progress_percentage = max(0, min(100, percentage))
        self.updated_at = datetime.utcnow()

    def complete_successfully(self, file_path: str, file_size: int, generation_time: float):
        """Успешное завершение генерации"""
        self.status = ReportStatus.COMPLETED
        self.file_path = file_path
        self.file_size = file_size
        self.generation_time = generation_time
        self.completed_at = datetime.utcnow()
        self.progress_percentage = 100
        self.updated_at = datetime.utcnow()

    def fail(self, error_message: str):
        """Отметить как неудачный"""
        self.status = ReportStatus.FAILED
        self.error_message = error_message
        self.updated_at = datetime.utcnow()

    def cancel(self):
        """Отмена отчета"""
        self.status = ReportStatus.CANCELLED
        self.updated_at = datetime.utcnow()

    def schedule_next_run(self):
        """Планирование следующего запуска"""
        if not self.frequency or self.frequency == ReportFrequency.ONCE:
            self.next_run_at = None
            return

        now = datetime.utcnow()

        if self.frequency == ReportFrequency.DAILY:
            self.next_run_at = now + timedelta(days=1)
        elif self.frequency == ReportFrequency.WEEKLY:
            self.next_run_at = now + timedelta(weeks=1)
        elif self.frequency == ReportFrequency.MONTHLY:
            next_month = now.month + 1 if now.month < 12 else 1
            next_year = now.year + 1 if now.month == 12 else now.year
            self.next_run_at = now.replace(year=next_year, month=next_month, day=1)
        elif self.frequency == ReportFrequency.QUARTERLY:
            next_quarter = ((now.month - 1) // 3 + 1) % 4 + 1
            next_month = (next_quarter - 1) * 3 + 1
            next_year = now.year + 1 if next_quarter == 1 and now.month > 9 else now.year
            self.next_run_at = now.replace(year=next_year, month=next_month, day=1)
        elif self.frequency == ReportFrequency.YEARLY:
            self.next_run_at = now.replace(year=now.year + 1, month=1, day=1)

    def increment_download_count(self):
        """Увеличение счетчика скачиваний"""
        self.download_count += 1
        self.last_accessed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def increment_view_count(self):
        """Увеличение счетчика просмотров"""
        self.view_count += 1
        self.last_accessed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "report_type": self.report_type.value,
            "format": self.format.value,
            "status": self.status.value,
            "progress_percentage": self.progress_percentage,
            "template_id": self.template_id,
            "parameters": self.parameters,
            "filters": self.filters,
            "frequency": self.frequency.value if self.frequency else None,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "date_from": self.date_from.isoformat() if self.date_from else None,
            "date_to": self.date_to.isoformat() if self.date_to else None,
            "timezone": self.timezone,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "generation_time": self.generation_time,
            "error_message": self.error_message,
            "delivery_method": self.delivery_method,
            "delivery_recipients": self.delivery_recipients,
            "delivery_status": self.delivery_status,
            "created_by": self.created_by,
            "is_template": self.is_template,
            "is_public": self.is_public,
            "download_count": self.download_count,
            "view_count": self.view_count,
            "last_accessed_at": self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

    @staticmethod
    def create_scheduled_report(
        name: str,
        report_type: ReportType,
        format: ReportFormat,
        frequency: ReportFrequency,
        created_by: str,
        parameters: Optional[dict] = None
    ) -> 'Report':
        """Создание запланированного отчета"""
        report = Report(
            id=str(uuid.uuid4()),
            name=name,
            report_type=report_type,
            format=format,
            frequency=frequency,
            created_by=created_by,
            parameters=parameters or {}
        )
        report.schedule_next_run()
        return report

    @staticmethod
    def create_on_demand_report(
        name: str,
        format: ReportFormat,
        created_by: str,
        parameters: Optional[dict] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> 'Report':
        """Создание отчета по требованию"""
        report = Report(
            id=str(uuid.uuid4()),
            name=name,
            report_type=ReportType.ON_DEMAND,
            format=format,
            created_by=created_by,
            parameters=parameters or {},
            date_from=date_from,
            date_to=date_to or datetime.utcnow()
        )
        return report
