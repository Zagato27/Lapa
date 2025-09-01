"""
Pydantic схемы для Location Service
"""

from .location import (
    LocationTrackCreate,
    LocationTrackResponse,
    LocationTracksResponse,
    GeofenceCreate,
    GeofenceUpdate,
    GeofenceResponse,
    RouteResponse,
    LocationAlertResponse,
    LocationAlertCreate,
    TrackingStartRequest,
    TrackingStopRequest,
    RouteOptimizationRequest,
    LocationSharingRequest
)

__all__ = [
    "LocationTrackCreate",
    "LocationTrackResponse",
    "LocationTracksResponse",
    "GeofenceCreate",
    "GeofenceUpdate",
    "GeofenceResponse",
    "RouteResponse",
    "LocationAlertResponse",
    "LocationAlertCreate",
    "TrackingStartRequest",
    "TrackingStopRequest",
    "RouteOptimizationRequest",
    "LocationSharingRequest"
]
