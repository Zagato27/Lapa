"""
Простой сервис валидации JWT для Pet Service (фолбэк, когда API Gateway недоступен).
"""

import logging
import os
from typing import Dict, Any

from jose import jwt, JWTError


logger = logging.getLogger(__name__)

# Читаем секрет и алгоритм из окружения, чтобы быть консистентными с другими сервисами
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


class AuthService:
    """Минимальный сервис для проверки JWT"""

    def verify_token(self, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except JWTError as e:
            logger.error(f"Token verification failed: {e}")
            raise


