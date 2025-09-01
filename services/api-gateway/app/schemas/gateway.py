"""
Pydantic схемы для основных функций API Gateway
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_validator
import enum


class ServiceStatus(str, enum.Enum):
    """Статусы сервисов"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    DOWN = "down"


class RouteStatus(str, enum.Enum):
    """Статусы маршрутов"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class ServiceRouteRequest(BaseModel):
    """Запрос на маршрутизацию к сервису"""
    service_name: str
    path: str
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    query_params: Optional[Dict[str, Any]] = None
    body: Optional[Dict[str, Any]] = None
    timeout: Optional[int] = None

    @field_validator('service_name')
    def validate_service_name(cls, v: str) -> str:
        if not v:
            raise ValueError('Service name is required')
        return v

    @field_validator('path')
    def validate_path(cls, v: str) -> str:
        if not v.startswith('/'):
            raise ValueError('Path must start with /')
        return v


class ServiceRouteResponse(BaseModel):
    """Ответ от сервиса"""
    service_name: str
    path: str
    method: str
    status_code: int
    headers: Dict[str, str]
    body: Any
    response_time: float
    timestamp: datetime


class GatewayStatsResponse(BaseModel):
    """Ответ со статистикой API Gateway"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    rate_limited_requests: int
    average_response_time: float
    uptime_seconds: int
    memory_usage_mb: float
    cpu_usage_percent: float
    active_connections: int
    services_status: Dict[str, ServiceStatus]
    routes_stats: Dict[str, Dict[str, Any]]
    period_start: datetime
    period_end: datetime


class ServiceHealthResponse(BaseModel):
    """Ответ о здоровье сервиса"""
    service_name: str
    status: ServiceStatus
    response_time: Optional[float]
    last_check: datetime
    error_message: Optional[str]
    version: Optional[str]
    uptime: Optional[int]


class RouteConfigRequest(BaseModel):
    """Запрос на настройку маршрута"""
    path: str
    service: str
    methods: List[str] = ["GET", "POST", "PUT", "DELETE"]
    auth_required: bool = True
    rate_limit: Optional[int] = None
    cache_ttl: Optional[int] = None
    transform_request: bool = False
    transform_response: bool = False
    enabled: bool = True


class RouteConfigResponse(BaseModel):
    """Ответ с конфигурацией маршрута"""
    id: str
    path: str
    service: str
    methods: List[str]
    auth_required: bool
    rate_limit: Optional[int]
    cache_ttl: Optional[int]
    transform_request: bool
    transform_response: bool
    status: RouteStatus
    created_at: datetime
    updated_at: datetime


class ServiceRegistryResponse(BaseModel):
    """Ответ со списком сервисов"""
    services: List[Dict[str, Any]]
    total_services: int
    healthy_services: int
    unhealthy_services: int


class GatewayConfigRequest(BaseModel):
    """Запрос на обновление конфигурации шлюза"""
    cors_origins: Optional[List[str]] = None
    enable_rate_limiting: Optional[bool] = None
    enable_caching: Optional[bool] = None
    enable_auth: Optional[bool] = None
    log_requests: Optional[bool] = None
    log_responses: Optional[bool] = None


class GatewayConfigResponse(BaseModel):
    """Ответ с конфигурацией шлюза"""
    cors_origins: List[str]
    enable_rate_limiting: bool
    enable_caching: bool
    enable_auth: bool
    log_requests: bool
    log_responses: bool
    updated_at: datetime


class CircuitBreakerStatus(BaseModel):
    """Статус circuit breaker"""
    service_name: str
    state: str  # closed, open, half_open
    failure_count: int
    last_failure_time: Optional[datetime]
    next_attempt_time: Optional[datetime]


class LoadBalancerStats(BaseModel):
    """Статистика балансировки нагрузки"""
    service_name: str
    total_requests: int
    requests_per_instance: Dict[str, int]
    average_response_time_per_instance: Dict[str, float]
    error_rate_per_instance: Dict[str, float]


class CacheStats(BaseModel):
    """Статистика кэширования"""
    total_entries: int
    hit_rate: float
    miss_rate: float
    eviction_count: int
    memory_usage_mb: float
    uptime_seconds: int


class SecurityStats(BaseModel):
    """Статистика безопасности"""
    blocked_requests: int
    suspicious_requests: int
    rate_limited_requests: int
    auth_failures: int
    cors_violations: int
    sql_injection_attempts: int
    xss_attempts: int
    period_start: datetime
    period_end: datetime


class WebSocketConnection(BaseModel):
    """WebSocket соединение"""
    connection_id: str
    service_name: str
    user_id: Optional[str]
    connected_at: datetime
    last_activity: datetime
    message_count: int


class WebSocketStats(BaseModel):
    """Статистика WebSocket"""
    active_connections: int
    total_connections_today: int
    messages_sent_today: int
    messages_received_today: int
    connections_by_service: Dict[str, int]


class APICompositionRequest(BaseModel):
    """Запрос на композицию API"""
    requests: List[ServiceRouteRequest]
    composition_type: str = "parallel"  # parallel, sequential, conditional
    timeout: int = 30


class APICompositionResponse(BaseModel):
    """Ответ композиции API"""
    composition_id: str
    results: List[Dict[str, Any]]
    total_time: float
    successful_requests: int
    failed_requests: int
    timestamp: datetime
