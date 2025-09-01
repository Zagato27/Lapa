"""
Service Discovery для API Gateway
Управление маршрутизацией запросов к микросервисам
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional
from urllib.parse import urljoin

import httpx
from httpx import AsyncClient, Timeout

from app.config import settings


logger = logging.getLogger(__name__)


class ServiceDiscovery:
    """Service Discovery для маршрутизации запросов"""

    def __init__(self):
        self.services: Dict[str, Dict] = {}
        self.client = AsyncClient(timeout=Timeout(10.0))
        self._running = False

        # Сопоставление путей сервисам
        self.route_mapping = {
            "/api/v1/auth": "user-service",
            "/api/v1/users": "user-service",
            "/api/v1/pets": "pet-service",
            "/api/v1/orders": "order-service",
            "/api/v1/location": "location-service",
            "/api/v1/payments": "payment-service",
            "/api/v1/chat": "chat-service",
            "/api/v1/notifications": "notification-service",
            "/api/v1/media": "media-service",
            "/api/v1/analytics": "analytics-service",
        }

        # URL сервисов
        self.service_urls = {
            "user-service": settings.user_service_url,
            "pet-service": settings.pet_service_url,
            "order-service": settings.order_service_url,
            "location-service": settings.location_service_url,
            "payment-service": settings.payment_service_url,
            "chat-service": settings.chat_service_url,
            "notification-service": settings.notification_service_url,
            "media-service": settings.media_service_url,
            "analytics-service": settings.analytics_service_url,
        }

    async def start_discovery(self):
        """Запуск обнаружения сервисов"""
        self._running = True
        logger.info("Service Discovery запущен")

        while self._running:
            await self._discover_services()
            await asyncio.sleep(30)  # Проверка каждые 30 секунд

    async def stop_discovery(self):
        """Остановка обнаружения сервисов"""
        self._running = False
        await self.client.aclose()
        logger.info("Service Discovery остановлен")

    def get_service_url(self, service_name: str) -> Optional[str]:
        """Получение URL сервиса"""
        return self.service_urls.get(service_name)

    def get_service_for_path(self, path: str) -> Optional[str]:
        """Определение сервиса по пути запроса"""
        for route_prefix, service in self.route_mapping.items():
            if path.startswith(route_prefix):
                return service
        return None

    async def proxy_request(self, service_name: str, path: str, method: str = "GET",
                          headers: Dict = None, data: Dict = None, params: Dict = None) -> Dict:
        """Проксирование запроса к микросервису"""
        service_url = self.get_service_url(service_name)
        if not service_url:
            raise ValueError(f"Сервис {service_name} не найден")

        url = urljoin(service_url, path)

        try:
            response = await self.client.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params
            )

            if response.status_code >= 400:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {"detail": response.text}
                return {
                    "status_code": response.status_code,
                    "error": error_data
                }

            return {
                "status_code": response.status_code,
                "data": response.json() if response.headers.get('content-type') == 'application/json' else response.text
            }

        except httpx.RequestError as e:
            logger.error(f"Ошибка запроса к {service_name}: {str(e)}")
            return {
                "status_code": 503,
                "error": {"detail": f"Сервис {service_name} недоступен"}
            }
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {str(e)}")
            return {
                "status_code": 500,
                "error": {"detail": "Внутренняя ошибка сервера"}
            }

    async def health_check(self, service_name: str) -> bool:
        """Проверка здоровья сервиса"""
        service_url = self.get_service_url(service_name)
        if not service_url:
            return False

        try:
            response = await self.client.get(urljoin(service_url, "/health"))
            return response.status_code == 200
        except:
            return False

    async def _discover_services(self):
        """Обнаружение доступных сервисов"""
        for service_name in self.service_urls.keys():
            is_healthy = await self.health_check(service_name)
            self.services[service_name] = {
                "healthy": is_healthy,
                "url": self.service_urls[service_name],
                "last_check": asyncio.get_event_loop().time()
            }

            if not is_healthy:
                logger.warning(f"Сервис {service_name} недоступен")
            else:
                logger.debug(f"Сервис {service_name} доступен")

    def get_services_status(self) -> Dict:
        """Получение статуса всех сервисов"""
        return {
            service_name: {
                "healthy": info["healthy"],
                "url": info["url"]
            }
            for service_name, info in self.services.items()
        }
