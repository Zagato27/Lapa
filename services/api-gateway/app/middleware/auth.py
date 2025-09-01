"""
Middleware аутентификации для API Gateway
"""

import logging
from typing import Optional

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware для аутентификации"""

    def __init__(self, app):
        super().__init__(app)
        self.auth_service = AuthService()
        self.public_paths = {
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/metrics"
        }

    async def dispatch(self, request: Request, call_next):
        """Обработка запроса"""
        try:
            # Пропускаем публичные пути
            if request.url.path in self.public_paths:
                return await call_next(request)

            # Пропускаем пути аутентификации (login/register/refresh/logout)
            if request.url.path.startswith("/api/v1/auth"):
                return await call_next(request)

            # Проверка необходимости аутентификации для данного маршрута
            if not self._requires_authentication(request.url.path):
                return await call_next(request)

            # Извлечение токена
            token = self._extract_token(request)
            if not token:
                return JSONResponse(
                    status_code=401,
                    content={"error": "Missing authentication token"}
                )

            # Проверка токена
            try:
                payload = await self.auth_service.verify_token(token)

                # Добавление информации о пользователе в request
                request.state.user_id = payload.get("user_id") or payload.get("sub")
                request.state.user_role = payload.get("role") or payload.get("roles", [None])[0]
                request.state.user_roles = payload.get("roles", [])
                request.state.token_payload = payload

                return await call_next(request)

            except HTTPException as e:
                return JSONResponse(
                    status_code=e.status_code,
                    content={"error": e.detail}
                )
            except Exception as e:
                logger.error(f"Token verification error: {e}")
                return JSONResponse(
                    status_code=401,
                    content={"error": "Invalid authentication token"}
                )

        except Exception as e:
            logger.error(f"Auth middleware error: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Authentication service error"}
            )

    def _requires_authentication(self, path: str) -> bool:
        """Проверка необходимости аутентификации для пути"""
        try:
            # Проверка настроек маршрутов
            for route_path, route_config in settings.routes.items():
                if path.startswith(route_path):
                    return route_config.auth_required

            # По умолчанию требуется аутентификация для API
            if path.startswith("/api/v1"):
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking authentication requirement: {e}")
            return True

    def _extract_token(self, request: Request) -> Optional[str]:
        """Извлечение токена из запроса"""
        try:
            # Проверка Authorization header
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                return auth_header[7:]  # Удаляем "Bearer " префикс

            # Проверка токена в query параметрах
            token = request.query_params.get("token")
            if token:
                return token

            # Проверка токена в cookies
            token = request.cookies.get("access_token")
            if token:
                return token

            return None

        except Exception as e:
            logger.error(f"Error extracting token: {e}")
            return None