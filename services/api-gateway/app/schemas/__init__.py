"""
Pydantic схемы для API Gateway Service
"""

from .gateway import (
    ServiceRouteRequest,
    ServiceRouteResponse,
    GatewayStatsResponse,
    ServiceHealthResponse,
    RouteConfigRequest,
    RouteConfigResponse
)
# Упрощённый набор экспортируемых схем (auth/monitoring могут отсутствовать)

__all__ = [
    "ServiceRouteRequest",
    "ServiceRouteResponse",
    "GatewayStatsResponse",
    "ServiceHealthResponse",
    "RouteConfigRequest",
    "RouteConfigResponse",
    "TokenRequest",
    "TokenResponse",
    "UserInfo",
    "LoginRequest",
    "RegisterRequest",
    "RequestLog",
    "ErrorLog",
    "PerformanceMetrics",
    "HealthCheckResponse"
]
