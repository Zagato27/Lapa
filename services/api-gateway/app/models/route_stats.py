"""
Модель статистики маршрутов API Gateway
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, JSON, ForeignKey, Float
from sqlalchemy.orm import declarative_base
import uuid
from sqlalchemy.sql import func

Base = declarative_base()


class RouteStats(Base):
    """Модель статистики маршрутов"""
    __tablename__ = "gateway_route_stats"

    id = Column(String, primary_key=True, index=True)
    route_path = Column(String, nullable=False, index=True)          # Путь маршрута
    service_name = Column(String, nullable=False, index=True)       # Название сервиса
    method = Column(String, nullable=False)                        # HTTP метод

    # Статистика запросов
    total_requests = Column(Integer, default=0)                     # Всего запросов
    successful_requests = Column(Integer, default=0)                # Успешных запросов
    failed_requests = Column(Integer, default=0)                    # Неудачных запросов
    rate_limited_requests = Column(Integer, default=0)              # Ограниченных запросов

    # Временные метрики
    average_response_time = Column(Float, nullable=True)            # Среднее время ответа
    min_response_time = Column(Float, nullable=True)                # Минимальное время ответа
    max_response_time = Column(Float, nullable=True)                # Максимальное время ответа
    percentile_95_response_time = Column(Float, nullable=True)      # 95-й процентиль

    # Статистика ошибок
    error_4xx_count = Column(Integer, default=0)                    # Ошибки 4xx
    error_5xx_count = Column(Integer, default=0)                    # Ошибки 5xx
    timeout_count = Column(Integer, default=0)                      # Таймауты

    # Статистика по статусам
    status_codes = Column(JSON, nullable=True)                      # Распределение кодов состояния

    # География запросов
    top_countries = Column(JSON, nullable=True)                     # Топ стран
    top_cities = Column(JSON, nullable=True)                        # Топ городов

    # Устройства и браузеры
    top_devices = Column(JSON, nullable=True)                       # Топ устройств
    top_browsers = Column(JSON, nullable=True)                      # Топ браузеров

    # Период статистики
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False, index=True)
    granularity = Column(String, default="hour")                    # Гранулярность (hour, day, week, month)

    # Метаданные
    metadata = Column(JSON, nullable=True)                          # Дополнительные метаданные

    # Временные метки
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<RouteStats(route={self.route_path}, service={self.service_name}, requests={self.total_requests})>"

    @property
    def success_rate(self) -> Optional[float]:
        """Расчет процента успешных запросов"""
        if self.total_requests == 0:
            return None
        return (self.successful_requests / self.total_requests) * 100

    @property
    def error_rate(self) -> Optional[float]:
        """Расчет процента ошибок"""
        if self.total_requests == 0:
            return None
        return (self.failed_requests / self.total_requests) * 100

    @property
    def rate_limit_rate(self) -> Optional[float]:
        """Расчет процента ограниченных запросов"""
        if self.total_requests == 0:
            return None
        return (self.rate_limited_requests / self.total_requests) * 100

    def increment_request(self, response_time: float, status_code: int):
        """Увеличение счетчика запросов"""
        self.total_requests += 1

        # Обновление временных метрик
        if self.average_response_time is None:
            self.average_response_time = response_time
            self.min_response_time = response_time
            self.max_response_time = response_time
        else:
            # Пересчет среднего времени
            self.average_response_time = (
                (self.average_response_time * (self.total_requests - 1)) + response_time
            ) / self.total_requests
            self.min_response_time = min(self.min_response_time, response_time)
            self.max_response_time = max(self.max_response_time, response_time)

        # Обновление статистики по статусам
        if self.status_codes is None:
            self.status_codes = {}
        status_str = str(status_code)
        self.status_codes[status_str] = self.status_codes.get(status_str, 0) + 1

        # Классификация запроса
        if 200 <= status_code < 400:
            self.successful_requests += 1
        elif 400 <= status_code < 500:
            self.failed_requests += 1
            self.error_4xx_count += 1
        elif 500 <= status_code < 600:
            self.failed_requests += 1
            self.error_5xx_count += 1

        self.updated_at = datetime.utcnow()

    def increment_rate_limit(self):
        """Увеличение счетчика ограниченных запросов"""
        self.rate_limited_requests += 1
        self.updated_at = datetime.utcnow()

    def increment_timeout(self):
        """Увеличение счетчика таймаутов"""
        self.timeout_count += 1
        self.failed_requests += 1
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "route_path": self.route_path,
            "service_name": self.service_name,
            "method": self.method,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "rate_limited_requests": self.rate_limited_requests,
            "average_response_time": self.average_response_time,
            "min_response_time": self.min_response_time,
            "max_response_time": self.max_response_time,
            "percentile_95_response_time": self.percentile_95_response_time,
            "error_4xx_count": self.error_4xx_count,
            "error_5xx_count": self.error_5xx_count,
            "timeout_count": self.timeout_count,
            "status_codes": self.status_codes,
            "top_countries": self.top_countries,
            "top_cities": self.top_cities,
            "top_devices": self.top_devices,
            "top_browsers": self.top_browsers,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "granularity": self.granularity,
            "success_rate": self.success_rate,
            "error_rate": self.error_rate,
            "rate_limit_rate": self.rate_limit_rate,
            "created_at": self.created_at.isoformat()
        }

    @staticmethod
    def create_route_stats(
        route_path: str,
        service_name: str,
        method: str,
        period_start: datetime,
        period_end: datetime,
        granularity: str = "hour"
    ) -> 'RouteStats':
        """Создание записи статистики маршрута"""
        route_stats = RouteStats(
            id=str(uuid.uuid4()),
            route_path=route_path,
            service_name=service_name,
            method=method,
            period_start=period_start,
            period_end=period_end,
            granularity=granularity
        )
        return route_stats
