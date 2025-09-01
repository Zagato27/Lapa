"""
Основной сервис API Gateway - маршрутизация и координация
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

import httpx
from fastapi import Request, Response

from app.config import settings
from app.database import redis_client

logger = logging.getLogger(__name__)


class GatewayService:
    """Основной сервис API Gateway"""

    def __init__(self):
        self.service_registry = {}
        self.route_registry = {}
        self.circuit_breakers = {}
        self.load_balancers = {}
        self._initialize_registries()

    def _initialize_registries(self):
        """Инициализация реестров сервисов и маршрутов"""
        self.service_registry = {
            name: {
                "config": config,
                "status": "unknown",
                "last_health_check": None,
                "failure_count": 0,
                "circuit_breaker_state": "closed"
            }
            for name, config in settings.services.items()
        }

        self.route_registry = {
            path: config for path, config in settings.routes.items()
        }

    async def route_request(
        self,
        request: Request,
        service_name: str,
        path: str,
        method: str = None
    ) -> Dict[str, Any]:
        """Маршрутизация запроса к сервису"""
        try:
            method = method or request.method

            # Получение конфигурации сервиса
            service_config = self.service_registry.get(service_name)
            if not service_config:
                raise ValueError(f"Service {service_name} not found")

            if not service_config["config"].enabled:
                raise ValueError(f"Service {service_name} is disabled")

            # Проверка circuit breaker
            if self._is_circuit_breaker_open(service_name):
                raise ValueError(f"Circuit breaker is open for service {service_name}")

            # Формирование URL сервиса
            service_url = service_config["config"].url
            full_url = f"{service_url}{path}"

            # Подготовка заголовков
            headers = dict(request.headers)
            headers.pop("host", None)  # Удаляем оригинальный host

            # Подготовка тела запроса
            body = None
            if method in ["POST", "PUT", "PATCH"]:
                body = await request.body()

            # Выполнение запроса
            start_time = time.time()

            async with httpx.AsyncClient(timeout=service_config["config"].timeout) as client:
                response = await client.request(
                    method=method,
                    url=full_url,
                    headers=headers,
                    params=request.query_params,
                    content=body
                )

                response_time = time.time() - start_time

                # Обновление статистики
                await self._update_route_stats(
                    path, service_name, method, response.status_code, response_time
                )

                return {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response.text,
                    "response_time": response_time
                }

        except httpx.TimeoutException:
            await self._handle_service_failure(service_name, "timeout")
            raise ValueError(f"Service {service_name} timeout")

        except httpx.ConnectError:
            await self._handle_service_failure(service_name, "connection_error")
            raise ValueError(f"Service {service_name} connection error")

        except Exception as e:
            logger.error(f"Error routing request to {service_name}: {e}")
            await self._handle_service_failure(service_name, "error")
            raise

    async def get_service_registry(self) -> Dict[str, Any]:
        """Получение реестра сервисов"""
        try:
            registry = {}
            for name, service_data in self.service_registry.items():
                registry[name] = {
                    "name": service_data["config"].name,
                    "url": service_data["config"].url,
                    "enabled": service_data["config"].enabled,
                    "status": service_data["status"],
                    "last_health_check": service_data["last_health_check"],
                    "circuit_breaker_state": service_data["circuit_breaker_state"],
                    "failure_count": service_data["failure_count"]
                }
            return registry

        except Exception as e:
            logger.error(f"Error getting service registry: {e}")
            return {}

    async def get_route_registry(self) -> Dict[str, Any]:
        """Получение реестра маршрутов"""
        try:
            return {
                path: {
                    "path": config.path,
                    "service": config.service,
                    "methods": config.methods,
                    "auth_required": config.auth_required,
                    "rate_limit": config.rate_limit,
                    "cache_ttl": config.cache_ttl
                }
                for path, config in self.route_registry.items()
            }

        except Exception as e:
            logger.error(f"Error getting route registry: {e}")
            return {}

    async def start_route_updates(self):
        """Запуск обновления конфигурации маршрутов"""
        try:
            while True:
                try:
                    await self._update_route_configurations()
                    await asyncio.sleep(300)  # Обновление каждые 5 минут
                except Exception as e:
                    logger.error(f"Error updating route configurations: {e}")
                    await asyncio.sleep(60)

        except Exception as e:
            logger.error(f"Error in route update loop: {e}")

    async def _update_route_configurations(self):
        """Обновление конфигураций маршрутов"""
        try:
            # Здесь можно реализовать динамическую загрузку конфигурации
            # из внешних источников (Consul, etcd, database, etc.)
            logger.debug("Route configurations updated")

        except Exception as e:
            logger.error(f"Error updating route configurations: {e}")

    async def _update_route_stats(
        self,
        path: str,
        service_name: str,
        method: str,
        status_code: int,
        response_time: float
    ):
        """Обновление статистики маршрутов (в Redis, если доступен)"""
        try:
            if not redis_client:
                return

            # Ключ для статистики
            stats_key = f"route_stats:{path}:{service_name}:{method}"

            # Получение текущей статистики
            current_stats = await redis_client.get(stats_key)
            if current_stats:
                stats = json.loads(current_stats)
            else:
                stats = {
                    "total_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                    "average_response_time": 0,
                    "min_response_time": float('inf'),
                    "max_response_time": 0,
                    "status_codes": {}
                }

            # Обновление статистики
            stats["total_requests"] += 1

            if 200 <= status_code < 400:
                stats["successful_requests"] += 1
            else:
                stats["failed_requests"] += 1

            # Обновление временных метрик
            if stats["average_response_time"] == 0:
                stats["average_response_time"] = response_time
            else:
                stats["average_response_time"] = (
                    stats["average_response_time"] * (stats["total_requests"] - 1) + response_time
                ) / stats["total_requests"]

            stats["min_response_time"] = min(stats["min_response_time"], response_time)
            stats["max_response_time"] = max(stats["max_response_time"], response_time)

            # Обновление статистики по статусам
            status_str = str(status_code)
            stats["status_codes"][status_str] = stats["status_codes"].get(status_str, 0) + 1

            # Сохранение обновленной статистики
            await redis_client.setex(stats_key, 86400, json.dumps(stats))  # 24 часа

        except Exception as e:
            logger.error(f"Error updating route stats: {e}")

    async def _handle_service_failure(self, service_name: str, failure_type: str):
        """Обработка отказа сервиса"""
        try:
            service_data = self.service_registry.get(service_name)
            if not service_data:
                return

            service_data["failure_count"] += 1
            service_data["status"] = "unhealthy"

            # Проверка необходимости открытия circuit breaker
            if service_data["failure_count"] >= settings.circuit_breaker_failure_threshold:
                service_data["circuit_breaker_state"] = "open"
                service_data["last_circuit_breaker_open"] = datetime.utcnow()
                logger.warning(f"Circuit breaker opened for service {service_name}")

        except Exception as e:
            logger.error(f"Error handling service failure: {e}")

    def _is_circuit_breaker_open(self, service_name: str) -> bool:
        """Проверка состояния circuit breaker"""
        try:
            service_data = self.service_registry.get(service_name)
            if not service_data:
                return False

            if service_data["circuit_breaker_state"] == "open":
                # Проверка возможности закрытия circuit breaker
                last_open = service_data.get("last_circuit_breaker_open")
                if last_open:
                    elapsed = (datetime.utcnow() - last_open).total_seconds()
                    if elapsed >= settings.circuit_breaker_recovery_timeout:
                        service_data["circuit_breaker_state"] = "half_open"
                        logger.info(f"Circuit breaker half-open for service {service_name}")

                return service_data["circuit_breaker_state"] == "open"

            return False

        except Exception as e:
            logger.error(f"Error checking circuit breaker: {e}")
            return False

    async def close_circuit_breaker(self, service_name: str):
        """Закрытие circuit breaker"""
        try:
            service_data = self.service_registry.get(service_name)
            if service_data:
                service_data["circuit_breaker_state"] = "closed"
                service_data["failure_count"] = 0
                logger.info(f"Circuit breaker closed for service {service_name}")

        except Exception as e:
            logger.error(f"Error closing circuit breaker: {e}")

    async def get_gateway_stats(self) -> Dict[str, Any]:
        """Получение статистики API Gateway"""
        try:
            stats = {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "average_response_time": 0,
                "services_status": {},
                "routes_stats": {}
            }

            # Чтение данных из Redis, если доступен
            if redis_client:
                try:
                    keys = await redis_client.keys("route_stats:*")
                    for key in keys:
                        route_stats = await redis_client.get(key)
                        if not route_stats:
                            continue
                        route_data = json.loads(route_stats)
                        stats["total_requests"] += route_data.get("total_requests", 0)
                        stats["successful_requests"] += route_data.get("successful_requests", 0)
                        stats["failed_requests"] += route_data.get("failed_requests", 0)
                        stats["routes_stats"][key] = route_data
                except Exception as e:
                    logger.error(f"Error reading route stats from redis: {e}")

            # Статус сервисов
            for name, service_data in self.service_registry.items():
                stats["services_status"][name] = service_data["status"]

            return stats

        except Exception as e:
            logger.error(f"Error getting gateway stats: {e}")
            return {}

    async def enable_service(self, service_name: str) -> bool:
        """Включение сервиса"""
        try:
            service_data = self.service_registry.get(service_name)
            if service_data:
                service_data["config"].enabled = True
                service_data["status"] = "healthy"
                logger.info(f"Service {service_name} enabled")
                return True
            return False

        except Exception as e:
            logger.error(f"Error enabling service {service_name}: {e}")
            return False

    async def disable_service(self, service_name: str) -> bool:
        """Отключение сервиса"""
        try:
            service_data = self.service_registry.get(service_name)
            if service_data:
                service_data["config"].enabled = False
                service_data["status"] = "disabled"
                logger.info(f"Service {service_name} disabled")
                return True
            return False

        except Exception as e:
            logger.error(f"Error disabling service {service_name}: {e}")
            return False

    async def reload_configuration(self):
        """Перезагрузка конфигурации"""
        try:
            logger.info("Reloading gateway configuration")
            self._initialize_registries()
            logger.info("Gateway configuration reloaded")

        except Exception as e:
            logger.error(f"Error reloading configuration: {e}")

    async def get_service_health(self, service_name: str) -> Dict[str, Any]:
        """Получение здоровья сервиса"""
        try:
            service_data = self.service_registry.get(service_name)
            if not service_data:
                return {"status": "not_found"}

            return {
                "service_name": service_name,
                "status": service_data["status"],
                "last_health_check": service_data["last_health_check"],
                "failure_count": service_data["failure_count"],
                "circuit_breaker_state": service_data["circuit_breaker_state"],
                "enabled": service_data["config"].enabled
            }

        except Exception as e:
            logger.error(f"Error getting service health: {e}")
            return {"status": "error", "error": str(e)}
