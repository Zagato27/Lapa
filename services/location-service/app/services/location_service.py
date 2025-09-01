"""
Основной сервис для управления геолокацией
"""

import logging
import uuid
import math
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, desc
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database.session import get_session
from app.models.location_track import LocationTrack
from app.models.geofence import Geofence
from app.models.location_alert import LocationAlert
from app.schemas.location import (
    LocationTrackCreate,
    LocationTrackResponse,
    LocationTracksResponse,
    TrackingStartRequest,
    TrackingStopRequest,
    GeofenceCheckResponse
)

logger = logging.getLogger(__name__)


class LocationService:
    """Сервис для работы с геолокацией"""

    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Расчет расстояния между двумя точками по формуле гаверсинуса (в метрах)"""
        R = 6371000  # Радиус Земли в метрах

        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    @staticmethod
    async def create_location_track(db: AsyncSession, track_data: LocationTrackCreate) -> LocationTrack:
        """Создание точки отслеживания"""
        try:
            track_id = str(uuid.uuid4())

            # Создание геометрии для PostGIS
            from geoalchemy2 import WKTElement
            location_geom = WKTElement(f'POINT({track_data.longitude} {track_data.latitude})', srid=4326)

            track = LocationTrack(
                id=track_id,
                order_id=track_data.order_id,
                user_id="",  # Будет заполнено из контекста
                location=location_geom,
                latitude=track_data.latitude,
                longitude=track_data.longitude,
                accuracy=track_data.accuracy,
                altitude=track_data.altitude,
                speed=track_data.speed,
                heading=track_data.heading,
                track_type=track_data.track_type,
                battery_level=track_data.battery_level,
                network_type=track_data.network_type,
                device_info=track_data.device_info,
                timestamp=datetime.utcnow()
            )

            db.add(track)
            await db.commit()
            await db.refresh(track)

            # Инвалидация кэша
            redis_session = await get_session()
            await redis_session.invalidate_order_locations_cache(track_data.order_id)

            logger.info(f"Location track created: {track.id} for order {track_data.order_id}")
            return track

        except Exception as e:
            logger.error(f"Location track creation failed: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def get_location_tracks(
        db: AsyncSession,
        order_id: str,
        page: int = 1,
        limit: int = 50,
        track_type: Optional[str] = None
    ) -> LocationTracksResponse:
        """Получение точек отслеживания для заказа"""
        try:
            offset = (page - 1) * limit

            # Проверка кэша
            redis_session = await get_session()
            cache_key = f"{order_id}:{page}:{limit}:{track_type}"
            cached_tracks = await redis_session.get_cached_order_locations(cache_key)

            if cached_tracks:
                return LocationTracksResponse(
                    tracks=[LocationService.track_to_response(LocationTrack(**track)) for track in cached_tracks],
                    total=len(cached_tracks),
                    page=page,
                    limit=limit,
                    pages=1
                )

            # Построение запроса
            query = select(LocationTrack).where(
                LocationTrack.order_id == order_id,
                LocationTrack.is_valid == True
            )

            if track_type:
                query = query.where(LocationTrack.track_type == track_type)

            # Подсчет общего количества
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await db.execute(count_query)
            total = total_result.scalar()

            # Получение точек с пагинацией
            query = query.order_by(desc(LocationTrack.timestamp)).offset(offset).limit(limit)
            result = await db.execute(query)
            tracks = result.scalars().all()

            # Кэширование результатов
            if page == 1 and len(tracks) < 100:  # Кэшируем только первую страницу и если не слишком много
                tracks_data = [LocationService.track_to_dict(track) for track in tracks]
                await redis_session.cache_order_locations(cache_key, tracks_data)

            pages = (total + limit - 1) // limit

            return LocationTracksResponse(
                tracks=[LocationService.track_to_response(track) for track in tracks],
                total=total,
                page=page,
                limit=limit,
                pages=pages
            )

        except Exception as e:
            logger.error(f"Error getting location tracks for order {order_id}: {e}")
            return LocationTracksResponse(tracks=[], total=0, page=page, limit=limit, pages=0)

    @staticmethod
    async def get_current_location(db: AsyncSession, order_id: str) -> Optional[LocationTrack]:
        """Получение текущей локации для заказа"""
        try:
            query = select(LocationTrack).where(
                LocationTrack.order_id == order_id,
                LocationTrack.is_valid == True,
                LocationTrack.track_type.in_(['current', 'walking'])
            ).order_by(desc(LocationTrack.timestamp)).limit(1)

            result = await db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Error getting current location for order {order_id}: {e}")
            return None

    @staticmethod
    async def start_tracking(db: AsyncSession, request: TrackingStartRequest, user_id: str) -> bool:
        """Начало отслеживания для заказа"""
        try:
            # Проверка существования заказа
            from app.models.order import Order
            order_query = select(Order).where(Order.id == request.order_id)
            order_result = await db.execute(order_query)
            order = order_result.scalar_one_or_none()

            if not order:
                logger.error(f"Order {request.order_id} not found")
                return False

            # Проверка прав доступа
            if order.client_id != user_id and order.walker_id != user_id:
                logger.error(f"Access denied for user {user_id} to order {request.order_id}")
                return False

            # Создание геофенсов, если запрошено
            if request.enable_geofencing:
                await LocationService._create_default_geofence(db, request.order_id, order.client_id)

            # Установка статуса отслеживания в Redis
            redis_session = await get_session()
            await redis_session.set_tracking_active(request.order_id, user_id)

            logger.info(f"Tracking started for order {request.order_id}")
            return True

        except Exception as e:
            logger.error(f"Error starting tracking for order {request.order_id}: {e}")
            return False

    @staticmethod
    async def stop_tracking(db: AsyncSession, request: TrackingStopRequest, user_id: str) -> bool:
        """Остановка отслеживания для заказа"""
        try:
            # Проверка прав доступа
            from app.models.order import Order
            order_query = select(Order).where(Order.id == request.order_id)
            order_result = await db.execute(order_query)
            order = order_result.scalar_one_or_none()

            if not order:
                logger.error(f"Order {request.order_id} not found")
                return False

            if order.client_id != user_id and order.walker_id != user_id:
                logger.error(f"Access denied for user {user_id} to order {request.order_id}")
                return False

            # Сохранение маршрута, если запрошено
            if request.save_route:
                await LocationService._save_route_from_tracks(db, request.order_id)

            # Остановка отслеживания в Redis
            redis_session = await get_session()
            await redis_session.stop_tracking(request.order_id)

            logger.info(f"Tracking stopped for order {request.order_id}")
            return True

        except Exception as e:
            logger.error(f"Error stopping tracking for order {request.order_id}: {e}")
            return False

    @staticmethod
    async def check_geofence_violations(db: AsyncSession, order_id: str, latitude: float, longitude: float) -> GeofenceCheckResponse:
        """Проверка нарушений геофенсинга"""
        try:
            # Получение активных геофенсов для заказа
            geofences_query = select(Geofence).where(
                Geofence.order_id == order_id,
                Geofence.is_active == True
            )
            result = await db.execute(geofences_query)
            geofences = result.scalars().all()

            if not geofences:
                return GeofenceCheckResponse(
                    is_inside_geofence=True,
                    distance_to_geofence=0,
                    nearest_geofence=None,
                    alerts_triggered=[]
                )

            alerts_triggered = []
            nearest_geofence = None
            min_distance = float('inf')
            is_inside_any = False

            for geofence in geofences:
                distance = LocationService.calculate_distance(
                    latitude, longitude,
                    geofence.center_latitude, geofence.center_longitude
                )

                is_inside = distance <= geofence.radius_meters

                if is_inside:
                    is_inside_any = True

                    # Проверка входа в зону
                    if geofence.alert_on_enter:
                        alert = LocationAlert.create_geofence_alert(
                            order_id, "", "geofence_enter",
                            latitude, longitude, geofence.id,
                            f"Вход в зону: {geofence.name or 'Без названия'}"
                        )
                        db.add(alert)
                        alerts_triggered.append(alert)
                        geofence.record_enter()

                else:
                    # Проверка выхода из зоны
                    if geofence.alert_on_exit and geofence.is_violated:
                        alert = LocationAlert.create_geofence_alert(
                            order_id, "", "geofence_exit",
                            latitude, longitude, geofence.id,
                            f"Выход из зоны: {geofence.name or 'Без названия'}"
                        )
                        db.add(alert)
                        alerts_triggered.append(alert)
                        geofence.record_exit()

                    # Проверка приближения к зоне
                    if geofence.alert_distance and distance <= geofence.alert_distance:
                        alert = LocationAlert.create_geofence_alert(
                            order_id, "", "geofence_violation",
                            latitude, longitude, geofence.id,
                            f"Приближение к зоне: {geofence.name or 'Без названия'}"
                        )
                        db.add(alert)
                        alerts_triggered.append(alert)
                        geofence.record_violation()

                # Поиск ближайшего геофенса
                if distance < min_distance:
                    min_distance = distance
                    nearest_geofence = geofence

            await db.commit()

            return GeofenceCheckResponse(
                is_inside_geofence=is_inside_any,
                distance_to_geofence=min_distance if nearest_geofence else 0,
                nearest_geofence=nearest_geofence,
                alerts_triggered=alerts_triggered
            )

        except Exception as e:
            logger.error(f"Error checking geofence violations for order {order_id}: {e}")
            return GeofenceCheckResponse(
                is_inside_geofence=True,
                distance_to_geofence=0,
                nearest_geofence=None,
                alerts_triggered=[]
            )

    @staticmethod
    async def process_emergency_location(db: AsyncSession, order_id: str, latitude: float, longitude: float, user_id: str):
        """Обработка экстренной геолокации"""
        try:
            # Создание экстренной точки отслеживания
            emergency_track = LocationTrack(
                id=str(uuid.uuid4()),
                order_id=order_id,
                user_id=user_id,
                latitude=latitude,
                longitude=longitude,
                track_type="emergency",
                timestamp=datetime.utcnow()
            )
            db.add(emergency_track)

            # Создание экстренного предупреждения
            emergency_alert = LocationAlert.create_emergency_alert(
                order_id, user_id, latitude, longitude,
                "Экстренное определение местоположения"
            )
            db.add(emergency_alert)

            await db.commit()

            # Отправка уведомлений экстренным контактам
            # (здесь можно добавить логику отправки SMS/email)

            logger.info(f"Emergency location processed for order {order_id}")
            return True

        except Exception as e:
            logger.error(f"Error processing emergency location for order {order_id}: {e}")
            await db.rollback()
            return False

    @staticmethod
    async def get_location_history(db: AsyncSession, order_id: str, hours: int = 24) -> List[LocationTrack]:
        """Получение истории геолокации за указанное количество часов"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            query = select(LocationTrack).where(
                LocationTrack.order_id == order_id,
                LocationTrack.timestamp >= cutoff_time,
                LocationTrack.is_valid == True
            ).order_by(LocationTrack.timestamp)

            result = await db.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error getting location history for order {order_id}: {e}")
            return []

    @staticmethod
    async def _create_default_geofence(db: AsyncSession, order_id: str, user_id: str):
        """Создание геофенса по умолчанию"""
        try:
            from app.models.order import Order
            order_query = select(Order).where(Order.id == order_id)
            order_result = await db.execute(order_query)
            order = order_result.scalar_one_or_none()

            if not order:
                return

            # Создание безопасной зоны вокруг места прогулки
            geofence = Geofence(
                id=str(uuid.uuid4()),
                order_id=order_id,
                user_id=user_id,
                center_latitude=order.latitude,
                center_longitude=order.longitude,
                radius_meters=settings.geofence_radius_meters,
                geofence_type="safe_zone",
                name="Зона прогулки",
                description="Безопасная зона для прогулки питомца",
                alert_on_enter=False,
                alert_on_exit=True,
                alert_distance=settings.geofence_alert_distance
            )

            db.add(geofence)
            await db.commit()

            logger.info(f"Default geofence created for order {order_id}")

        except Exception as e:
            logger.error(f"Error creating default geofence for order {order_id}: {e}")

    @staticmethod
    async def _save_route_from_tracks(db: AsyncSession, order_id: str):
        """Сохранение маршрута из точек отслеживания"""
        try:
            from app.models.route import Route

            # Получение точек отслеживания
            tracks = await LocationService.get_location_history(db, order_id, hours=12)

            if len(tracks) < 2:
                return

            # Создание маршрута
            route = Route(
                id=str(uuid.uuid4()),
                order_id=order_id,
                user_id=tracks[0].user_id if tracks else "",
                started_at=tracks[0].timestamp if tracks else None,
                completed_at=tracks[-1].timestamp if tracks else None,
                is_completed=True
            )

            # Расчет статистики маршрута
            route.calculate_statistics(tracks)

            db.add(route)
            await db.commit()

            logger.info(f"Route saved for order {order_id}")

        except Exception as e:
            logger.error(f"Error saving route for order {order_id}: {e}")

    @staticmethod
    def track_to_response(track: LocationTrack) -> LocationTrackResponse:
        """Преобразование модели LocationTrack в схему LocationTrackResponse"""
        return LocationTrackResponse(
            id=track.id,
            order_id=track.order_id,
            user_id=track.user_id,
            latitude=track.latitude,
            longitude=track.longitude,
            accuracy=track.accuracy,
            altitude=track.altitude,
            speed=track.speed,
            heading=track.heading,
            track_type=track.track_type,
            battery_level=track.battery_level,
            network_type=track.network_type,
            device_info=track.device_info,
            address=track.address,
            city=track.city,
            district=track.district,
            timestamp=track.timestamp,
            created_at=track.created_at,
            speed_kmh=track.speed_kmh,
            is_walking_point=track.is_walking_point,
            is_emergency_point=track.is_emergency_point,
            has_location_data=track.has_location_data
        )

    @staticmethod
    def track_to_dict(track: LocationTrack) -> Dict[str, Any]:
        """Преобразование модели LocationTrack в словарь для кэширования"""
        return {
            "id": track.id,
            "order_id": track.order_id,
            "user_id": track.user_id,
            "latitude": track.latitude,
            "longitude": track.longitude,
            "accuracy": track.accuracy,
            "altitude": track.altitude,
            "speed": track.speed,
            "heading": track.heading,
            "track_type": track.track_type,
            "battery_level": track.battery_level,
            "network_type": track.network_type,
            "device_info": track.device_info,
            "address": track.address,
            "city": track.city,
            "district": track.district,
            "timestamp": track.timestamp.isoformat(),
            "created_at": track.created_at.isoformat()
        }
