"""
Сервис для управления геофенсингом
"""

import logging
import uuid
from typing import List, Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, text

from app.config import settings
from app.database.session import get_session
from app.models.geofence import Geofence
from app.schemas.location import GeofenceCreate, GeofenceUpdate, GeofenceResponse

logger = logging.getLogger(__name__)


class GeofenceService:
    """Сервис для работы с геофенсингом"""

    @staticmethod
    async def create_geofence(db: AsyncSession, geofence_data: GeofenceCreate, user_id: str) -> Geofence:
        """Создание геофенса"""
        try:
            geofence_id = str(uuid.uuid4())

            # Создание геометрии для PostGIS
            from geoalchemy2 import WKTElement
            center_geom = WKTElement(f'POINT({geofence_data.center_longitude} {geofence_data.center_latitude})', srid=4326)

            geofence = Geofence(
                id=geofence_id,
                order_id=geofence_data.order_id,
                user_id=user_id,
                center_location=center_geom,
                center_latitude=geofence_data.center_latitude,
                center_longitude=geofence_data.center_longitude,
                radius_meters=geofence_data.radius_meters,
                geofence_type=geofence_data.geofence_type,
                name=geofence_data.name,
                description=geofence_data.description,
                alert_on_enter=geofence_data.alert_on_enter,
                alert_on_exit=geofence_data.alert_on_exit,
                alert_distance=geofence_data.alert_distance,
                active_from_time=geofence_data.active_from_time,
                active_until_time=geofence_data.active_until_time
            )

            db.add(geofence)
            await db.commit()
            await db.refresh(geofence)

            # Инвалидация кэша
            redis_session = await get_session()
            await redis_session.invalidate_order_locations_cache(geofence_data.order_id)

            logger.info(f"Geofence created: {geofence.id} for order {geofence_data.order_id}")
            return geofence

        except Exception as e:
            logger.error(f"Geofence creation failed: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def get_geofence_by_id(db: AsyncSession, geofence_id: str, user_id: str) -> Optional[Geofence]:
        """Получение геофенса по ID"""
        try:
            query = select(Geofence).where(
                Geofence.id == geofence_id,
                Geofence.user_id == user_id
            )
            result = await db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Error getting geofence {geofence_id}: {e}")
            return None

    @staticmethod
    async def get_order_geofences(db: AsyncSession, order_id: str, user_id: str) -> List[Geofence]:
        """Получение геофенсов для заказа"""
        try:
            # Проверка кэша
            redis_session = await get_session()
            cached_geofences = await redis_session.get_cached_order_geofences(order_id)

            if cached_geofences:
                return [Geofence(**gf) for gf in cached_geofences]

            # Получение из базы данных
            query = select(Geofence).where(
                Geofence.order_id == order_id,
                Geofence.user_id == user_id
            )
            result = await db.execute(query)
            geofences = result.scalars().all()

            # Кэширование результатов
            geofences_data = [GeofenceService.geofence_to_dict(gf) for gf in geofences]
            await redis_session.cache_order_geofences(order_id, geofences_data)

            return geofences

        except Exception as e:
            logger.error(f"Error getting geofences for order {order_id}: {e}")
            return []

    @staticmethod
    async def update_geofence(db: AsyncSession, geofence_id: str, user_id: str, geofence_data: GeofenceUpdate) -> Optional[Geofence]:
        """Обновление геофенса"""
        try:
            update_data = geofence_data.dict(exclude_unset=True)

            if not update_data:
                return await GeofenceService.get_geofence_by_id(db, geofence_id, user_id)

            # Обновление центра геофенса, если переданы координаты
            if 'center_latitude' in update_data and 'center_longitude' in update_data:
                from geoalchemy2 import WKTElement
                center_geom = WKTElement(f'POINT({update_data["center_longitude"]} {update_data["center_latitude"]})', srid=4326)
                update_data['center_location'] = center_geom

            stmt = (
                update(Geofence)
                .where(Geofence.id == geofence_id, Geofence.user_id == user_id)
                .values(**update_data, updated_at=datetime.utcnow())
            )

            result = await db.execute(stmt)
            await db.commit()

            if result.rowcount == 0:
                return None

            # Получение обновленного геофенса
            geofence = await GeofenceService.get_geofence_by_id(db, geofence_id, user_id)

            # Инвалидация кэша
            if geofence:
                redis_session = await get_session()
                await redis_session.invalidate_order_locations_cache(geofence.order_id)

            return geofence

        except Exception as e:
            logger.error(f"Geofence update failed for {geofence_id}: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def delete_geofence(db: AsyncSession, geofence_id: str, user_id: str) -> bool:
        """Удаление геофенса"""
        try:
            # Получение геофенса для проверки доступа
            geofence = await GeofenceService.get_geofence_by_id(db, geofence_id, user_id)
            if not geofence:
                return False

            # Удаление геофенса
            stmt = select(Geofence).where(Geofence.id == geofence_id)
            result = await db.execute(stmt)
            geofence_to_delete = result.scalar_one_or_none()

            if geofence_to_delete:
                await db.delete(geofence_to_delete)
                await db.commit()

                # Инвалидация кэша
                redis_session = await get_session()
                await redis_session.invalidate_order_locations_cache(geofence.order_id)

                logger.info(f"Geofence {geofence_id} deleted successfully")
                return True

            return False

        except Exception as e:
            logger.error(f"Geofence deletion failed for {geofence_id}: {e}")
            await db.rollback()
            return False

    @staticmethod
    async def toggle_geofence(db: AsyncSession, geofence_id: str, user_id: str, is_active: bool) -> bool:
        """Включение/отключение геофенса"""
        try:
            stmt = (
                update(Geofence)
                .where(Geofence.id == geofence_id, Geofence.user_id == user_id)
                .values(is_active=is_active, updated_at=datetime.utcnow())
            )

            result = await db.execute(stmt)
            await db.commit()

            if result.rowcount > 0:
                # Получение геофенса для инвалидации кэша
                geofence = await GeofenceService.get_geofence_by_id(db, geofence_id, user_id)
                if geofence:
                    redis_session = await get_session()
                    await redis_session.invalidate_order_locations_cache(geofence.order_id)

                logger.info(f"Geofence {geofence_id} {'enabled' if is_active else 'disabled'}")
                return True

            return False

        except Exception as e:
            logger.error(f"Geofence toggle failed for {geofence_id}: {e}")
            await db.rollback()
            return False

    @staticmethod
    async def get_geofence_statistics(db: AsyncSession, geofence_id: str, user_id: str) -> Dict[str, Any]:
        """Получение статистики геофенса"""
        try:
            geofence = await GeofenceService.get_geofence_by_id(db, geofence_id, user_id)
            if not geofence:
                return {}

            return {
                "geofence_id": geofence_id,
                "name": geofence.name,
                "enter_count": geofence.enter_count,
                "exit_count": geofence.exit_count,
                "violation_count": geofence.violation_count,
                "is_violated": geofence.is_violated,
                "last_violation_at": geofence.last_violation_at.isoformat() if geofence.last_violation_at else None,
                "created_at": geofence.created_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting geofence statistics {geofence_id}: {e}")
            return {}

    @staticmethod
    async def find_geofences_containing_point(db: AsyncSession, latitude: float, longitude: float) -> List[Geofence]:
        """Поиск геофенсов, содержащих указанную точку"""
        try:
            # Безопасный параметризованный запрос с PostGIS
            query = text(
                """
                SELECT * FROM geofences
                WHERE ST_DWithin(
                    center_location::geography,
                    ST_GeogFromText(:point_wkt),
                    radius_meters
                )
                AND is_active = true
                """
            )

            point_wkt = f"POINT({longitude} {latitude})"
            result = await db.execute(query, {"point_wkt": point_wkt})
            rows = result.mappings().all()
            return [Geofence(**dict(row)) for row in rows]

        except Exception as e:
            logger.error(f"Error finding geofences containing point ({latitude}, {longitude}): {e}")
            return []

    @staticmethod
    def geofence_to_response(geofence: Geofence) -> GeofenceResponse:
        """Преобразование модели Geofence в схему GeofenceResponse"""
        return GeofenceResponse(
            id=geofence.id,
            order_id=geofence.order_id,
            user_id=geofence.user_id,
            center_latitude=geofence.center_latitude,
            center_longitude=geofence.center_longitude,
            radius_meters=geofence.radius_meters,
            geofence_type=geofence.geofence_type,
            name=geofence.name,
            description=geofence.description,
            alert_on_enter=geofence.alert_on_enter,
            alert_on_exit=geofence.alert_on_exit,
            alert_distance=geofence.alert_distance,
            active_from_time=geofence.active_from_time,
            active_until_time=geofence.active_until_time,
            is_active=geofence.is_active,
            is_violated=geofence.is_violated,
            enter_count=geofence.enter_count,
            exit_count=geofence.exit_count,
            violation_count=geofence.violation_count,
            created_at=geofence.created_at,
            updated_at=geofence.updated_at,
            last_violation_at=geofence.last_violation_at,
            center_coordinates=geofence.center_coordinates,
            is_safe_zone=geofence.is_safe_zone,
            is_danger_zone=geofence.is_danger_zone,
            area_square_meters=geofence.area_square_meters
        )

    @staticmethod
    def geofence_to_dict(geofence: Geofence) -> Dict[str, Any]:
        """Преобразование модели Geofence в словарь для кэширования"""
        return {
            "id": geofence.id,
            "order_id": geofence.order_id,
            "user_id": geofence.user_id,
            "center_latitude": geofence.center_latitude,
            "center_longitude": geofence.center_longitude,
            "radius_meters": geofence.radius_meters,
            "geofence_type": geofence.geofence_type,
            "name": geofence.name,
            "description": geofence.description,
            "alert_on_enter": geofence.alert_on_enter,
            "alert_on_exit": geofence.alert_on_exit,
            "alert_distance": geofence.alert_distance,
            "active_from_time": geofence.active_from_time,
            "active_until_time": geofence.active_until_time,
            "is_active": geofence.is_active,
            "is_violated": geofence.is_violated,
            "enter_count": geofence.enter_count,
            "exit_count": geofence.exit_count,
            "violation_count": geofence.violation_count,
            "created_at": geofence.created_at.isoformat(),
            "updated_at": geofence.updated_at.isoformat(),
            "last_violation_at": geofence.last_violation_at.isoformat() if geofence.last_violation_at else None
        }
