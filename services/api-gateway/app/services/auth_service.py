"""
Сервис аутентификации API Gateway
"""

import logging
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

import httpx
from fastapi import HTTPException

from app.config import settings

logger = logging.getLogger(__name__)


class AuthService:
    """Сервис аутентификации"""

    def __init__(self):
        self.user_service_url = settings.user_service_url

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Проверка JWT токена (верификация подписи и срока действия на стороне Gateway)."""
        try:
            # Полная проверка подписи и exp
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
                options={"require": ["exp"]},
            )
            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise HTTPException(status_code=401, detail="Token verification failed")

    async def _verify_token_with_user_service(self, token: str):
        """Проверка токена через User Service"""
        try:
            url = f"{self.user_service_url}/auth/verify"

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    url,
                    json={"token": token},
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code != 200:
                    raise HTTPException(status_code=401, detail="Token verification failed")

                return response.json()

        except httpx.ConnectError:
            logger.warning("User Service is not available, skipping token verification")
        except Exception as e:
            logger.error(f"Error verifying token with User Service: {e}")
            raise HTTPException(status_code=401, detail="Token verification failed")

    async def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """Аутентификация пользователя"""
        try:
            if not self.user_service_url:
                raise HTTPException(status_code=503, detail="Authentication service unavailable")

            url = f"{self.user_service_url}/auth/login"

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    url,
                    json={"username": username, "password": password},
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code != 200:
                    raise HTTPException(status_code=401, detail="Invalid credentials")

                return response.json()

        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Authentication service unavailable")
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(status_code=500, detail="Authentication failed")

    async def register_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Регистрация пользователя"""
        try:
            if not self.user_service_url:
                raise HTTPException(status_code=503, detail="Registration service unavailable")

            url = f"{self.user_service_url}/auth/register"

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    url,
                    json=user_data,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code != 201:
                    raise HTTPException(status_code=400, detail="Registration failed")

                return response.json()

        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Registration service unavailable")
        except Exception as e:
            logger.error(f"Registration error: {e}")
            raise HTTPException(status_code=500, detail="Registration failed")

    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Получение информации о пользователе"""
        try:
            if not self.user_service_url:
                raise HTTPException(status_code=503, detail="User service unavailable")

            url = f"{self.user_service_url}/users/{user_id}"

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url)

                if response.status_code != 200:
                    raise HTTPException(status_code=404, detail="User not found")

                return response.json()

        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="User service unavailable")
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            raise HTTPException(status_code=500, detail="Failed to get user info")

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Обновление токена"""
        try:
            if not self.user_service_url:
                raise HTTPException(status_code=503, detail="Token refresh service unavailable")

            url = f"{self.user_service_url}/auth/refresh"

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    url,
                    json={"refresh_token": refresh_token},
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code != 200:
                    raise HTTPException(status_code=401, detail="Invalid refresh token")

                return response.json()

        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Token refresh service unavailable")
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            raise HTTPException(status_code=500, detail="Token refresh failed")

    async def logout_user(self, token: str) -> bool:
        """Выход пользователя из системы"""
        try:
            if not self.user_service_url:
                return True

            url = f"{self.user_service_url}/auth/logout"

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    url,
                    json={"token": token},
                    headers={"Content-Type": "application/json"}
                )

                return response.status_code == 200

        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False

    async def validate_permissions(self, user_id: str, resource: str, action: str) -> bool:
        """Проверка прав доступа"""
        try:
            # Здесь должна быть логика проверки прав доступа
            # Можно реализовать через User Service или отдельный сервис авторизации

            # Пока что возвращаем True для всех запросов
            return True

        except Exception as e:
            logger.error(f"Permission validation error: {e}")
            return False

    async def get_user_roles(self, user_id: str) -> List[str]:
        """Получение ролей пользователя"""
        try:
            user_info = await self.get_user_info(user_id)
            return user_info.get("roles", [])

        except Exception as e:
            logger.error(f"Error getting user roles: {e}")
            return []

    async def is_admin_user(self, user_id: str) -> bool:
        """Проверка, является ли пользователь администратором"""
        try:
            roles = await self.get_user_roles(user_id)
            return "admin" in roles

        except Exception as e:
            logger.error(f"Error checking admin status: {e}")
            return False

    def create_token(self, payload: Dict[str, Any]) -> str:
        """Создание JWT токена (для внутреннего использования)"""
        try:
            expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
            payload.update({"exp": expire})

            token = jwt.encode(
                payload,
                settings.jwt_secret_key,
                algorithm=settings.jwt_algorithm
            )

            return token

        except Exception as e:
            logger.error(f"Token creation error: {e}")
            raise

    def decode_token(self, token: str) -> Dict[str, Any]:
        """Декодирование JWT токена (для внутреннего использования)"""
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm]
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            logger.error(f"Token decode error: {e}")
            raise HTTPException(status_code=401, detail="Token decode failed")

    async def hash_password(self, password: str) -> str:
        """Хэширование пароля"""
        try:
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')

        except Exception as e:
            logger.error(f"Password hashing error: {e}")
            raise

    async def verify_password(self, password: str, hashed: str) -> bool:
        """Проверка пароля"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    async def check_rate_limit(self, user_id: str, endpoint: str) -> bool:
        """Проверка лимита запросов для пользователя"""
        try:
            # Здесь должна быть логика проверки rate limit
            # Можно реализовать через Redis или отдельный сервис

            return True

        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return False
