"""
Основной сервис для работы с пользователями.

Функциональность:
- CRUD профилей пользователей
- Поиск выгульщиков рядом (через PostGIS)
- Пагинация и фильтрация пользователей

Используется в эндпоинтах `app.api.v1.users` и косвенно в API Gateway.
"""

import logging
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, text
from sqlalchemy.orm import selectinload
from geoalchemy2 import WKTElement

from app.config import settings
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserProfile, NearbyWalkersResponse, NearbyWalker
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)


class UserService:
    """Сервис для работы с пользователями"""

    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        """Создание нового пользователя"""
        try:
            user_id = str(uuid.uuid4())
            hashed_password = AuthService().get_password_hash(user_data.password)

            user = User(
                id=user_id,
                email=user_data.email,
                phone=user_data.phone,
                password_hash=hashed_password,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                role=user_data.role
            )

            db.add(user)
            await db.commit()
            await db.refresh(user)

            logger.info(f"User created successfully: {user.email}")
            return user

        except Exception as e:
            logger.error(f"User creation failed: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
        """Получение пользователя по ID"""
        try:
            stmt = select(User).where(User.id == user_id)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Получение пользователя по email"""
        try:
            stmt = select(User).where(User.email == email)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None

    @staticmethod
    async def update_user(db: AsyncSession, user_id: str, user_data: UserUpdate) -> Optional[User]:
        """Обновление данных пользователя"""
        try:
            update_data = user_data.dict(exclude_unset=True)

            if not update_data:
                return await UserService.get_user_by_id(db, user_id)

            # Обновление геолокации
            if 'latitude' in update_data and 'longitude' in update_data:
                latitude = update_data.pop('latitude')
                longitude = update_data.pop('longitude')
                update_data['location'] = WKTElement(f'POINT({longitude} {latitude})', srid=4326)
                update_data['latitude'] = latitude
                update_data['longitude'] = longitude

            stmt = (
                update(User)
                .where(User.id == user_id)
                .values(**update_data, updated_at=datetime.utcnow())
            )

            await db.execute(stmt)
            await db.commit()

            return await UserService.get_user_by_id(db, user_id)

        except Exception as e:
            logger.error(f"User update failed for {user_id}: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def get_nearby_walkers(
        db: AsyncSession,
        latitude: float,
        longitude: float,
        radius: float = None,
        limit: int = None
    ) -> NearbyWalkersResponse:
        """Поиск выгульщиков рядом с указанной точкой"""
        try:
            if radius is None:
                radius = settings.walker_search_radius

            if limit is None:
                limit = settings.max_nearby_walkers

            # Параметризованный запрос с использованием geography для метров
            walkers_query = text(
                """
                SELECT
                    id, first_name, last_name, avatar_url, rating, total_orders,
                    completed_orders, latitude, longitude, hourly_rate,
                    services_offered, bio,
                    ST_Distance(location, ST_GeogFromText(:point)) as distance_meters
                FROM users
                WHERE
                    role = 'walker'
                    AND is_active = true
                    AND is_walker_verified = true
                    AND location IS NOT NULL
                    AND ST_DWithin(
                        location::geography,
                        ST_GeogFromText(:point),
                        :radius_meters
                    )
                ORDER BY distance_meters
                LIMIT :limit
                """
            )

            point_wkt = f"SRID=4326;POINT({longitude} {latitude})"
            result = await db.execute(
                walkers_query,
                {"point": point_wkt, "radius_meters": radius, "limit": limit},
            )
            rows = result.fetchall()

            walkers = []
            for row in rows:
                walker = NearbyWalker(
                    id=row.id,
                    first_name=row.first_name,
                    last_name=row.last_name,
                    avatar_url=row.avatar_url,
                    rating=row.rating,
                    total_orders=row.total_orders,
                    completed_orders=row.completed_orders,
                    latitude=row.latitude,
                    longitude=row.longitude,
                    distance=row.distance_meters,
                    hourly_rate=row.hourly_rate,
                    services_offered=row.services_offered,
                    bio=row.bio
                )
                walkers.append(walker)

            return NearbyWalkersResponse(
                walkers=walkers,
                total=len(walkers)
            )

        except Exception as e:
            logger.error(f"Error finding nearby walkers: {e}")
            return NearbyWalkersResponse(walkers=[], total=0)

    @staticmethod
    async def get_users_list(
        db: AsyncSession,
        page: int = 1,
        limit: int = 20,
        role: Optional[str] = None
    ) -> Dict[str, Any]:
        """Получение списка пользователей с пагинацией"""
        try:
            offset = (page - 1) * limit

            # Базовый запрос
            query = select(User)

            # Фильтр по роли
            if role:
                query = query.where(User.role == role)

            # Подсчет общего количества
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await db.execute(count_query)
            total = total_result.scalar()

            # Получение пользователей с пагинацией
            query = query.offset(offset).limit(limit)
            result = await db.execute(query)
            users = result.scalars().all()

            return {
                "users": users,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit
            }

        except Exception as e:
            logger.error(f"Error getting users list: {e}")
            return {
                "users": [],
                "total": 0,
                "page": page,
                "limit": limit,
                "pages": 0
            }

    @staticmethod
    async def update_user_rating(db: AsyncSession, user_id: str, new_rating: float) -> bool:
        """Обновление рейтинга пользователя"""
        try:
            user = await UserService.get_user_by_id(db, user_id)
            if not user:
                return False

            user.update_rating(new_rating)
            await db.commit()

            logger.info(f"Rating updated for user {user_id}: {user.rating}")
            return True

        except Exception as e:
            logger.error(f"Error updating rating for user {user_id}: {e}")
            await db.rollback()
            return False

    @staticmethod
    def user_to_profile(user: User) -> UserProfile:
        """Преобразование модели User в схему UserProfile"""
        return UserProfile(
            id=user.id,
            email=user.email,
            phone=user.phone,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            avatar_url=user.avatar_url,
            bio=user.bio,
            latitude=user.latitude,
            longitude=user.longitude,
            rating=user.rating,
            total_orders=user.total_orders,
            completed_orders=user.completed_orders,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_walker_verified=user.is_walker_verified,
            notifications_enabled=user.notifications_enabled,
            push_notifications=user.push_notifications,
            email_notifications=user.email_notifications,
            sms_notifications=user.sms_notifications,
            experience_years=user.experience_years,
            services_offered=user.services_offered,
            work_schedule=user.work_schedule,
            hourly_rate=user.hourly_rate,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login_at=user.last_login_at
        )
