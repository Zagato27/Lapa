"""
Модели базы данных для Analytics Service
"""

from .base import Base
from .event import Event
from .metric import Metric
from .kpi import KPI
from .dashboard import Dashboard
from .report import Report
from .segment import Segment
__all__ = [
    "Base",
    "Event",
    "Metric",
    "KPI",
    "Dashboard",
    "Report",
    "Segment"
]
