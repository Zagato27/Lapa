"""
Сервис аутентификации для User Service.

Функциональность:
- Хэширование и проверка паролей (bcrypt)
- Выпуск и проверка JWT токенов (access/refresh)
- Обновление токенов и отзыв refresh token (через Redis)

Используется в `app.api.v1.auth` и сервисах `UserService` для регистрации.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import settings
from app.database.session import get_session
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Сервис для работы с аутентификацией"""

    def __init__(self):
        # Инициализация без хранения сессии Redis; получаем её по требованию
        pass

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверка пароля"""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Хэширование пароля"""
        return pwd_context.hash(password)

    def create_access_token(self, data: Dict, expires_delta: Optional[timedelta] = None) -> str:
        """Создание access token"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })

        encoded_jwt = jwt.encode(
            to_encode,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )

        return encoded_jwt

    def create_refresh_token(self, data: Dict) -> str:
        """Создание refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })

        encoded_jwt = jwt.encode(
            to_encode,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )

        return encoded_jwt

    def verify_token(self, token: str) -> Dict:
        """Проверка токена"""
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm]
            )
            return payload

        except JWTError as e:
            logger.error(f"Token verification failed: {e}")
            raise ValueError(f"Invalid token: {str(e)}")
        except Exception:
            # Библиотека jose выбрасывает JWTError на истёкшие/некорректные токены
            raise

    async def authenticate_user(self, db: AsyncSession, email: str, password: str) -> Optional[User]:
        """Аутентификация пользователя"""
        try:
            # Поиск пользователя по email
            stmt = select(User).where(User.email == email)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                return None

            if not self.verify_password(password, user.password_hash):
                return None

            # Обновление времени последнего входа безопасным выражением UPDATE
            await db.execute(
                update(User)
                .where(User.id == user.id)
                .values(last_login_at=datetime.utcnow())
            )
            await db.commit()

            return user

        except Exception as e:
            logger.error(f"Authentication failed for {email}: {e}")
            return None

    async def register_user(self, db: AsyncSession, user_data: Dict) -> User:
        """Регистрация нового пользователя"""
        try:
            # Создание нового пользователя
            user_id = str(uuid.uuid4())
            hashed_password = self.get_password_hash(user_data["password"])

            user = User(
                id=user_id,
                email=user_data["email"],
                phone=user_data["phone"],
                password_hash=hashed_password,
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                role=user_data["role"]
            )

            db.add(user)
            await db.commit()
            await db.refresh(user)

            logger.info(f"User registered successfully: {user.email}")
            return user

        except Exception as e:
            logger.error(f"User registration failed: {e}")
            await db.rollback()
            raise

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """Обновление access token с помощью refresh token"""
        try:
            payload = self.verify_token(refresh_token)

            if payload.get("type") != "refresh":
                raise ValueError("Token is not a refresh token")

            user_id = payload.get("user_id")
            role = payload.get("role", "client")

            # Создаем новый access token
            access_token_data = {"user_id": user_id, "role": role}
            new_access_token = self.create_access_token(access_token_data)

            # Создаем новый refresh token
            refresh_token_data = {"user_id": user_id, "role": role}
            new_refresh_token = self.create_refresh_token(refresh_token_data)

            # Сохранить новый refresh token в Redis (с TTL)
            redis_session = await get_session()
            ttl_seconds = settings.jwt_refresh_token_expire_days * 24 * 3600
            await redis_session.set_refresh_token(user_id, new_refresh_token, ttl_seconds)

            return {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer"
            }

        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise

    async def revoke_refresh_token(self, user_id: str) -> None:
        """Отзыв refresh token"""
        redis_session = await get_session()
        await redis_session.delete_refresh_token(user_id)
        logger.info(f"Refresh token revoked for user: {user_id}")
