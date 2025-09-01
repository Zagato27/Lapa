"""
Модели API Gateway

Содержит модель `RouteStats`. Шлюз не использует БД напрямую, но модель
оставлена для возможной интеграции со сторонним хранилищем.
"""

from .route_stats import RouteStats

__all__ = ["RouteStats"]

"""
Модели базы данных для API Gateway Service
"""

from .route_stats import RouteStats
from .service_health import ServiceHealth
from .rate_limit import RateLimit
from .api_key import APIKey

__all__ = [
    "RouteStats",
    "ServiceHealth",
    "RateLimit",
    "APIKey"
]
