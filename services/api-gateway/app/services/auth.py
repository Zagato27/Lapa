"""
Сервис аутентификации для API Gateway
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Optional

import jwt
from jwt import PyJWTError
import redis.asyncio as redis

from app.config import settings


class AuthService:
    """Сервис для работы с JWT токенами"""

    def __init__(self):
        self.redis = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            decode_responses=True
        )

    async def create_access_token(self, data: Dict, expires_delta: Optional[timedelta] = None) -> str:
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

    async def create_refresh_token(self, data: Dict) -> str:
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

        # Сохраняем refresh token в Redis
        await self._store_refresh_token(encoded_jwt, data.get("user_id"), expire)

        return encoded_jwt

    async def verify_token(self, token: str) -> Dict:
        """Проверка токена"""
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm]
            )

            user_id: str = payload.get("user_id")
            token_type: str = payload.get("type")

            if user_id is None:
                raise ValueError("Токен не содержит user_id")

            # Для refresh token проверяем в Redis
            if token_type == "refresh":
                stored_token = await self.redis.get(f"refresh_token:{user_id}")
                if not stored_token or stored_token != token:
                    raise ValueError("Refresh token недействителен")

            return payload

        except PyJWTError as e:
            raise ValueError(f"Ошибка декодирования токена: {str(e)}")
        except jwt.ExpiredSignatureError:
            raise ValueError("Токен истек")
        except jwt.InvalidTokenError:
            raise ValueError("Недействительный токен")

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """Обновление access token с помощью refresh token"""
        try:
            payload = await self.verify_token(refresh_token)

            if payload.get("type") != "refresh":
                raise ValueError("Токен не является refresh token")

            user_id = payload.get("user_id")
            role = payload.get("role", "client")

            # Создаем новый access token
            access_token_data = {"user_id": user_id, "role": role}
            new_access_token = await self.create_access_token(access_token_data)

            # Создаем новый refresh token
            refresh_token_data = {"user_id": user_id, "role": role}
            new_refresh_token = await self.create_refresh_token(refresh_token_data)

            # Удаляем старый refresh token
            await self.redis.delete(f"refresh_token:{user_id}")

            return {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer"
            }

        except Exception as e:
            raise ValueError(f"Ошибка обновления токена: {str(e)}")

    async def revoke_refresh_token(self, user_id: str) -> None:
        """Отзыв refresh token"""
        await self.redis.delete(f"refresh_token:{user_id}")

    async def _store_refresh_token(self, token: str, user_id: str, expire: datetime) -> None:
        """Сохранение refresh token в Redis"""
        ttl = int((expire - datetime.utcnow()).total_seconds())
        await self.redis.setex(f"refresh_token:{user_id}", ttl, token)
