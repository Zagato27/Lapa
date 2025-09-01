"""
Pydantic схемы для Analytics Service
"""

from .event import (
    EventCreate,
    EventResponse,
    EventSearchRequest,
    EventStatisticsResponse
)
from .metric import (
    MetricCreate,
    MetricResponse,
    MetricSearchRequest,
    MetricStatisticsResponse
)
from .kpi import (
    KPICreate,
    KPIResponse,
    KPIUpdate,
    KPITargetUpdate
)
from .dashboard import (
    DashboardCreate,
    DashboardResponse,
    DashboardUpdate,
    WidgetCreate,
    WidgetUpdate
)
from .report import (
    ReportCreate,
    ReportResponse,
    ReportUpdate,
    ReportScheduleCreate
)
from .segment import (
    SegmentCreate,
    SegmentResponse,
    SegmentUpdate,
    SegmentCriteria
)

__all__ = [
    "EventCreate",
    "EventResponse",
    "EventSearchRequest",
    "EventStatisticsResponse",
    "MetricCreate",
    "MetricResponse",
    "MetricSearchRequest",
    "MetricStatisticsResponse",
    "KPICreate",
    "KPIResponse",
    "KPIUpdate",
    "KPITargetUpdate",
    "DashboardCreate",
    "DashboardResponse",
    "DashboardUpdate",
    "WidgetCreate",
    "WidgetUpdate",
    "ReportCreate",
    "ReportResponse",
    "ReportUpdate",
    "ReportScheduleCreate",
    "SegmentCreate",
    "SegmentResponse",
    "SegmentUpdate",
    "SegmentCriteria"
]
