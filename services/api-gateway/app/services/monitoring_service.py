"""
Сервис мониторинга API Gateway
"""

import asyncio
import logging
import psutil
import time
from datetime import datetime
from typing import Dict, Any, List

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class MonitoringService:
    """Сервис мониторинга"""

    def __init__(self):
        self.service_health_status = {}
        self.gateway_metrics = {
            "start_time": time.time(),
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "rate_limited_requests": 0,
            "average_response_time": 0,
            "uptime_seconds": 0
        }

    async def start_health_checks(self):
        """Запуск проверки здоровья сервисов"""
        try:
            logger.info("Starting health checks")

            while True:
                try:
                    await self._perform_health_checks()
                    await asyncio.sleep(settings.health_check_interval)
                except Exception as e:
                    logger.error(f"Error in health check cycle: {e}")
                    await asyncio.sleep(10)

        except Exception as e:
            logger.error(f"Error starting health checks: {e}")

    async def _perform_health_checks(self):
        """Выполнение проверки здоровья всех сервисов"""
        try:
            for service_name, service_config in settings.services.items():
                if service_config.enabled:
                    await self._check_service_health(service_name, service_config)

        except Exception as e:
            logger.error(f"Error performing health checks: {e}")

    async def _check_service_health(self, service_name: str, service_config):
        """Проверка здоровья конкретного сервиса"""
        try:
            health_url = f"{service_config.url}{service_config.health_check}"

            start_time = time.time()
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(health_url)

                response_time = time.time() - start_time

                if response.status_code == 200:
                    status = "healthy"
                elif response.status_code >= 500:
                    status = "unhealthy"
                else:
                    status = "degraded"

                # Обновление статуса сервиса
                self.service_health_status[service_name] = {
                    "status": status,
                    "response_time": response_time,
                    "last_check": datetime.utcnow(),
                    "error_message": None
                }

                logger.debug(f"Service {service_name} health check: {status} ({response_time:.2f}s)")

        except httpx.TimeoutException:
            self._update_service_status(service_name, "unhealthy", "Timeout")
        except httpx.ConnectError:
            self._update_service_status(service_name, "down", "Connection failed")
        except Exception as e:
            self._update_service_status(service_name, "unhealthy", str(e))

    def _update_service_status(self, service_name: str, status: str, error_message: str):
        """Обновление статуса сервиса"""
        try:
            self.service_health_status[service_name] = {
                "status": status,
                "response_time": None,
                "last_check": datetime.utcnow(),
                "error_message": error_message
            }

            logger.warning(f"Service {service_name} status: {status} - {error_message}")

        except Exception as e:
            logger.error(f"Error updating service status: {e}")

    async def get_gateway_stats(self) -> Dict[str, Any]:
        """Получение статистики API Gateway"""
        try:
            current_time = time.time()
            uptime_seconds = current_time - self.gateway_metrics["start_time"]

            # Обновление uptime
            self.gateway_metrics["uptime_seconds"] = uptime_seconds

            # Получение системных метрик
            system_metrics = self._get_system_metrics()

            # Получение статуса сервисов
            services_status = {}
            for service_name, health_data in self.service_health_status.items():
                services_status[service_name] = health_data["status"]

            return {
                **self.gateway_metrics,
                **system_metrics,
                "services_status": services_status,
                "period_start": datetime.fromtimestamp(self.gateway_metrics["start_time"]),
                "period_end": datetime.utcnow()
            }

        except Exception as e:
            logger.error(f"Error getting gateway stats: {e}")
            return {}

    def _get_system_metrics(self) -> Dict[str, Any]:
        """Получение системных метрик"""
        try:
            return {
                "memory_usage_mb": psutil.virtual_memory().used / 1024 / 1024,
                "cpu_usage_percent": psutil.cpu_percent(interval=1),
                "disk_usage_percent": psutil.disk_usage('/').percent,
                "active_connections": len(psutil.net_connections()),
                "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            }

        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}

    def increment_request_count(self, successful: bool = True):
        """Увеличение счетчика запросов"""
        try:
            self.gateway_metrics["total_requests"] += 1

            if successful:
                self.gateway_metrics["successful_requests"] += 1
            else:
                self.gateway_metrics["failed_requests"] += 1

        except Exception as e:
            logger.error(f"Error incrementing request count: {e}")

    def increment_rate_limited_count(self):
        """Увеличение счетчика ограниченных запросов"""
        try:
            self.gateway_metrics["rate_limited_requests"] += 1

        except Exception as e:
            logger.error(f"Error incrementing rate limited count: {e}")

    def update_response_time(self, response_time: float):
        """Обновление среднего времени ответа"""
        try:
            if self.gateway_metrics["average_response_time"] == 0:
                self.gateway_metrics["average_response_time"] = response_time
            else:
                total_requests = self.gateway_metrics["total_requests"]
                self.gateway_metrics["average_response_time"] = (
                    self.gateway_metrics["average_response_time"] * (total_requests - 1) + response_time
                ) / total_requests

        except Exception as e:
            logger.error(f"Error updating response time: {e}")

    async def get_service_health_status(self, service_name: str = None) -> Dict[str, Any]:
        """Получение статуса здоровья сервисов"""
        try:
            if service_name:
                return self.service_health_status.get(service_name, {})

            return self.service_health_status

        except Exception as e:
            logger.error(f"Error getting service health status: {e}")
            return {}

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Получение метрик производительности"""
        try:
            return {
                "gateway_metrics": self.gateway_metrics,
                "system_metrics": self._get_system_metrics(),
                "services_health": self.service_health_status,
                "timestamp": datetime.utcnow()
            }

        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {}

    async def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        response_time: float,
        user_id: str = None,
        ip_address: str = None
    ):
        """Логирование запроса"""
        try:
            if not settings.log_requests:
                return

            log_data = {
                "timestamp": datetime.utcnow(),
                "method": method,
                "path": path,
                "status_code": status_code,
                "response_time": response_time,
                "user_id": user_id,
                "ip_address": ip_address,
                "user_agent": None  # Можно добавить из request
            }

            # Здесь можно отправить логи в систему логирования
            logger.info(f"Request: {method} {path} - {status_code} ({response_time:.2f}s)")

        except Exception as e:
            logger.error(f"Error logging request: {e}")

    async def log_error(
        self,
        error: str,
        method: str = None,
        path: str = None,
        user_id: str = None,
        details: Dict[str, Any] = None
    ):
        """Логирование ошибки"""
        try:
            if not settings.log_errors:
                return

            log_data = {
                "timestamp": datetime.utcnow(),
                "error": error,
                "method": method,
                "path": path,
                "user_id": user_id,
                "details": details or {}
            }

            # Здесь можно отправить логи в систему логирования
            logger.error(f"Gateway Error: {error}", extra=log_data)

        except Exception as e:
            logger.error(f"Error logging error: {e}")

    async def send_alert(self, alert_type: str, message: str, details: Dict[str, Any] = None):
        """Отправка алерта"""
        try:
            alert_data = {
                "type": alert_type,
                "message": message,
                "details": details or {},
                "timestamp": datetime.utcnow(),
                "service": "api-gateway"
            }

            # Здесь можно реализовать отправку алертов в Slack, Email, SMS
            logger.warning(f"ALERT: {alert_type} - {message}")

        except Exception as e:
            logger.error(f"Error sending alert: {e}")

    async def check_thresholds(self):
        """Проверка пороговых значений"""
        try:
            # Проверка высокого уровня ошибок
            if self.gateway_metrics["total_requests"] > 100:
                error_rate = self.gateway_metrics["failed_requests"] / self.gateway_metrics["total_requests"]
                if error_rate > 0.1:  # 10% ошибок
                    await self.send_alert(
                        "high_error_rate",
                        f"High error rate detected: {error_rate:.2%}",
                        {"error_rate": error_rate}
                    )

            # Проверка высокой нагрузки
            if self._get_system_metrics().get("cpu_usage_percent", 0) > 90:
                await self.send_alert(
                    "high_cpu_usage",
                    "High CPU usage detected",
                    {"cpu_usage": self._get_system_metrics().get("cpu_usage_percent")}
                )

            # Проверка недоступности сервисов
            for service_name, health_data in self.service_health_status.items():
                if health_data["status"] in ["down", "unhealthy"]:
                    await self.send_alert(
                        "service_down",
                        f"Service {service_name} is {health_data['status']}",
                        {"service": service_name, "status": health_data["status"]}
                    )

        except Exception as e:
            logger.error(f"Error checking thresholds: {e}")

    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Получение сводки метрик"""
        try:
            return {
                "gateway": {
                    "total_requests": self.gateway_metrics["total_requests"],
                    "success_rate": (
                        self.gateway_metrics["successful_requests"] /
                        max(self.gateway_metrics["total_requests"], 1) * 100
                    ),
                    "average_response_time": self.gateway_metrics["average_response_time"],
                    "uptime_hours": self.gateway_metrics["uptime_seconds"] / 3600
                },
                "services": {
                    "total_services": len(settings.services),
                    "healthy_services": sum(
                        1 for health in self.service_health_status.values()
                        if health["status"] == "healthy"
                    ),
                    "unhealthy_services": sum(
                        1 for health in self.service_health_status.values()
                        if health["status"] in ["unhealthy", "down"]
                    )
                },
                "system": self._get_system_metrics(),
                "timestamp": datetime.utcnow()
            }

        except Exception as e:
            logger.error(f"Error getting metrics summary: {e}")
            return {}
