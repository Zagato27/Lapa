"""
Pydantic-схемы (v2) для геолокации.

Используются роутами `app.api.v1.locations`, `app.api.v1.geofences`, `app.api.v1.tracking`.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_validator


class LocationTrackCreate(BaseModel):
    """Создание точки отслеживания"""
    order_id: str
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    altitude: Optional[float] = None
    speed: Optional[float] = None
    heading: Optional[float] = None
    track_type: str = "current"
    battery_level: Optional[float] = None
    network_type: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None

    @field_validator('latitude')
    def validate_latitude(cls, v: float):
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @field_validator('longitude')
    def validate_longitude(cls, v: float):
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v

    @field_validator('track_type')
    def validate_track_type(cls, v: str):
        valid_types = ['current', 'walking', 'start', 'end', 'emergency']
        if v not in valid_types:
            raise ValueError(f'Track type must be one of: {", ".join(valid_types)}')
        return v

    @field_validator('accuracy')
    def validate_accuracy(cls, v: float | None):
        if v is not None and v < 0:
            raise ValueError('Accuracy must be positive')
        return v

    @field_validator('battery_level')
    def validate_battery_level(cls, v: float | None):
        if v is not None and not 0 <= v <= 100:
            raise ValueError('Battery level must be between 0 and 100')
        return v


class LocationTrackResponse(BaseModel):
    """Ответ с точкой отслеживания"""
    id: str
    order_id: str
    user_id: str
    latitude: float
    longitude: float
    accuracy: Optional[float]
    altitude: Optional[float]
    speed: Optional[float]
    heading: Optional[float]
    track_type: str
    battery_level: Optional[float]
    network_type: Optional[str]
    device_info: Optional[Dict[str, Any]]
    address: Optional[str]
    city: Optional[str]
    district: Optional[str]
    timestamp: datetime
    created_at: datetime

    # Вычисляемые поля
    speed_kmh: Optional[float] = None
    is_walking_point: Optional[bool] = None
    is_emergency_point: Optional[bool] = None
    has_location_data: Optional[bool] = None


class LocationTracksResponse(BaseModel):
    """Ответ со списком точек отслеживания"""
    tracks: List[LocationTrackResponse]
    total: int
    page: int
    limit: int
    pages: int


class GeofenceCreate(BaseModel):
    """Создание геофенса"""
    order_id: str
    center_latitude: float
    center_longitude: float
    radius_meters: float
    geofence_type: str = "safe_zone"
    name: Optional[str] = None
    description: Optional[str] = None
    alert_on_enter: bool = False
    alert_on_exit: bool = True
    alert_distance: Optional[float] = None
    active_from_time: Optional[str] = None
    active_until_time: Optional[str] = None

    @field_validator('center_latitude')
    def validate_center_latitude(cls, v: float):
        if not -90 <= v <= 90:
            raise ValueError('Center latitude must be between -90 and 90')
        return v

    @field_validator('center_longitude')
    def validate_center_longitude(cls, v: float):
        if not -180 <= v <= 180:
            raise ValueError('Center longitude must be between -180 and 180')
        return v

    @field_validator('radius_meters')
    def validate_radius(cls, v: float):
        if v <= 0:
            raise ValueError('Radius must be positive')
        if v > 5000:
            raise ValueError('Radius cannot exceed 5000 meters')
        return v

    @field_validator('geofence_type')
    def validate_geofence_type(cls, v: str):
        valid_types = ['safe_zone', 'danger_zone', 'walking_area']
        if v not in valid_types:
            raise ValueError(f'Geofence type must be one of: {", ".join(valid_types)}')
        return v

    @field_validator('active_from_time', 'active_until_time')
    def validate_time(cls, v: str | None):
        if v is not None:
            try:
                datetime.strptime(v, "%H:%M")
            except ValueError:
                raise ValueError('Time must be in HH:MM format')
        return v


class GeofenceUpdate(BaseModel):
    """Обновление геофенса"""
    radius_meters: Optional[float] = None
    name: Optional[str] = None
    description: Optional[str] = None
    alert_on_enter: Optional[bool] = None
    alert_on_exit: Optional[bool] = None
    alert_distance: Optional[float] = None
    active_from_time: Optional[str] = None
    active_until_time: Optional[str] = None
    is_active: Optional[bool] = None


class GeofenceResponse(BaseModel):
    """Ответ с геофенсом"""
    id: str
    order_id: str
    user_id: str
    center_latitude: float
    center_longitude: float
    radius_meters: float
    geofence_type: str
    name: Optional[str]
    description: Optional[str]
    alert_on_enter: bool
    alert_on_exit: bool
    alert_distance: Optional[float]
    active_from_time: Optional[str]
    active_until_time: Optional[str]
    is_active: bool
    is_violated: bool
    enter_count: int
    exit_count: int
    violation_count: int
    created_at: datetime
    updated_at: datetime
    last_violation_at: Optional[datetime]

    # Вычисляемые поля
    center_coordinates: Optional[tuple[float, float]] = None
    is_safe_zone: Optional[bool] = None
    is_danger_zone: Optional[bool] = None
    area_square_meters: Optional[float] = None


class RouteResponse(BaseModel):
    """Ответ с маршрутом"""
    id: str
    order_id: str
    user_id: str
    total_distance_meters: Optional[float]
    total_duration_seconds: Optional[int]
    average_speed_kmh: Optional[float]
    max_speed_kmh: Optional[float]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    is_completed: bool
    is_optimized: bool
    accuracy_score: Optional[float]
    completeness_score: Optional[float]
    weather_conditions: Optional[Dict[str, Any]]
    traffic_conditions: Optional[Dict[str, Any]]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    # Вычисляемые поля
    duration_minutes: Optional[int] = None
    duration_hours: Optional[float] = None
    distance_km: Optional[float] = None
    pace_minutes_per_km: Optional[float] = None


class LocationAlertCreate(BaseModel):
    """Создание предупреждения о геолокации"""
    order_id: str
    alert_type: str
    title: str
    message: str
    severity: str = "medium"
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @field_validator('alert_type')
    def validate_alert_type(cls, v: str):
        valid_types = ['geofence_enter', 'geofence_exit', 'geofence_violation', 'emergency', 'low_battery', 'location_lost']
        if v not in valid_types:
            raise ValueError(f'Alert type must be one of: {", ".join(valid_types)}')
        return v

    @field_validator('severity')
    def validate_severity(cls, v: str):
        valid_severities = ['low', 'medium', 'high', 'critical']
        if v not in valid_severities:
            raise ValueError(f'Severity must be one of: {", ".join(valid_severities)}')
        return v


class LocationAlertResponse(BaseModel):
    """Ответ с предупреждением о геолокации"""
    id: str
    order_id: str
    user_id: str
    alert_type: str
    title: str
    message: str
    severity: str
    latitude: Optional[float]
    longitude: Optional[float]
    geofence_id: Optional[str]
    location_track_id: Optional[str]
    metadata_json: Optional[Dict[str, Any]]
    is_read: bool
    is_processed: bool
    processed_by: Optional[str]
    processed_at: Optional[datetime]
    auto_action_taken: Optional[str]
    timestamp: datetime
    created_at: datetime

    # Вычисляемые поля
    is_critical: Optional[bool] = None
    is_high_priority: Optional[bool] = None
    is_geofence_alert: Optional[bool] = None
    is_emergency_alert: Optional[bool] = None


class TrackingStartRequest(BaseModel):
    """Запрос на начало отслеживания"""
    order_id: str
    enable_geofencing: bool = True
    enable_route_optimization: bool = True
    enable_emergency_detection: bool = True


class TrackingStopRequest(BaseModel):
    """Запрос на остановку отслеживания"""
    order_id: str
    save_route: bool = True


class RouteOptimizationRequest(BaseModel):
    """Запрос на оптимизацию маршрута"""
    order_id: str
    optimization_type: str = "simplify"  # 'simplify', 'smooth', 'complete'


class LocationSharingRequest(BaseModel):
    """Запрос на включение/отключение геолокации"""
    order_id: str
    enabled: bool = True
    share_with_emergency_contacts: bool = True


class LocationSharingResponse(BaseModel):
    """Ответ о статусе геолокации"""
    order_id: str
    is_sharing_enabled: bool
    last_location: Optional[LocationTrackResponse]
    sharing_started_at: Optional[datetime]
    emergency_contacts_notified: bool


class GeofenceCheckResponse(BaseModel):
    """Ответ проверки геофенсинга"""
    is_inside_geofence: bool
    distance_to_geofence: float
    nearest_geofence: Optional[GeofenceResponse]
    alerts_triggered: List[LocationAlertResponse]


class RouteStatisticsResponse(BaseModel):
    """Ответ со статистикой маршрута"""
    route: RouteResponse
    total_points: int
    processed_points: int
    optimization_applied: bool
    geofence_violations: int
    alerts_generated: int
    battery_levels: List[Dict[str, Any]]
    speed_profile: List[Dict[str, Any]]


class LiveTrackingResponse(BaseModel):
    """Ответ с данными реального времени"""
    order_id: str
    current_location: Optional[LocationTrackResponse]
    route_progress: Dict[str, Any]
    active_alerts: List[LocationAlertResponse]
    geofence_status: GeofenceCheckResponse
    is_tracking_active: bool
    last_update: Optional[datetime]
