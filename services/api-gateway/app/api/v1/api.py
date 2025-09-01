"""
Основной API роутер для API Gateway Service
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from app.services.gateway_service import GatewayService
from app.config import settings
from app.services.auth_service import AuthService
from app.services.monitoring_service import MonitoringService
from app.schemas.gateway import GatewayStatsResponse, ServiceHealthResponse
from app.routes import auth_router, users_router, pets_router

# Создаем главный роутер для API Gateway
api_router = APIRouter()
# Подключаем пользовательские роуты верхнего уровня
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(pets_router, prefix="/pets", tags=["pets"])

# Получение сервисов
def get_gateway_service(request: Request) -> GatewayService:
    return request.app.state.gateway_service

def get_auth_service(request: Request) -> AuthService:
    return request.app.state.auth_service

def get_monitoring_service(request: Request) -> MonitoringService:
    return request.app.state.monitoring_service

# Gateway management endpoints
@api_router.get("/gateway/stats", response_model=GatewayStatsResponse, summary="Статистика API Gateway")
async def get_gateway_stats(
    gateway_service: GatewayService = Depends(get_gateway_service),
    monitoring_service: MonitoringService = Depends(get_monitoring_service)
):
    """Получение статистики API Gateway"""
    try:
        gateway_stats = await gateway_service.get_gateway_stats()
        monitoring_stats = await monitoring_service.get_gateway_stats()

        return GatewayStatsResponse(**{**gateway_stats, **monitoring_stats})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting gateway stats: {str(e)}")


@api_router.get("/gateway/services", summary="Список сервисов")
async def get_services(
    gateway_service: GatewayService = Depends(get_gateway_service)
):
    """Получение списка зарегистрированных сервисов"""
    try:
        services = await gateway_service.get_service_registry()
        return {"services": services}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting services: {str(e)}")


@api_router.get("/gateway/routes", summary="Список маршрутов")
async def get_routes(
    gateway_service: GatewayService = Depends(get_gateway_service)
):
    """Получение списка маршрутов"""
    try:
        routes = await gateway_service.get_route_registry()
        return {"routes": routes}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting routes: {str(e)}")


@api_router.put("/gateway/services/{service_name}/enable", summary="Включение сервиса")
async def enable_service(
    service_name: str,
    gateway_service: GatewayService = Depends(get_gateway_service)
):
    """Включение сервиса"""
    try:
        success = await gateway_service.enable_service(service_name)
        if not success:
            raise HTTPException(status_code=404, detail="Service not found")

        return {"message": f"Service {service_name} enabled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error enabling service: {str(e)}")


@api_router.put("/gateway/services/{service_name}/disable", summary="Отключение сервиса")
async def disable_service(
    service_name: str,
    gateway_service: GatewayService = Depends(get_gateway_service)
):
    """Отключение сервиса"""
    try:
        success = await gateway_service.disable_service(service_name)
        if not success:
            raise HTTPException(status_code=404, detail="Service not found")

        return {"message": f"Service {service_name} disabled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error disabling service: {str(e)}")


@api_router.get("/gateway/services/{service_name}/health", summary="Здоровье сервиса")
async def get_service_health(
    service_name: str,
    gateway_service: GatewayService = Depends(get_gateway_service)
):
    """Получение статуса здоровья сервиса"""
    try:
        health = await gateway_service.get_service_health(service_name)
        return health

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting service health: {str(e)}")


@api_router.put("/gateway/services/{service_name}/circuit-breaker/close", summary="Закрытие circuit breaker")
async def close_circuit_breaker(
    service_name: str,
    gateway_service: GatewayService = Depends(get_gateway_service)
):
    """Закрытие circuit breaker для сервиса"""
    try:
        await gateway_service.close_circuit_breaker(service_name)
        return {"message": f"Circuit breaker closed for service {service_name}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error closing circuit breaker: {str(e)}")


@api_router.post("/gateway/reload-config", summary="Перезагрузка конфигурации")
async def reload_configuration(
    gateway_service: GatewayService = Depends(get_gateway_service)
):
    """Перезагрузка конфигурации API Gateway"""
    try:
        await gateway_service.reload_configuration()
        return {"message": "Configuration reloaded successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reloading configuration: {str(e)}")


@api_router.get("/gateway/performance", summary="Метрики производительности")
async def get_performance_metrics(
    monitoring_service: MonitoringService = Depends(get_monitoring_service)
):
    """Получение метрик производительности"""
    try:
        metrics = await monitoring_service.get_performance_metrics()
        return metrics

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting performance metrics: {str(e)}")


# Authentication endpoints (proxy to User Service)
@api_router.post("/auth/login", summary="Вход в систему")
async def login(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Аутентификация пользователя"""
    try:
        request_data = await request.json()
        result = await auth_service.authenticate_user(
            request_data.get("username"),
            request_data.get("password")
        )
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")


@api_router.post("/auth/register", summary="Регистрация пользователя")
async def register(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Регистрация нового пользователя"""
    try:
        request_data = await request.json()
        result = await auth_service.register_user(request_data)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration error: {str(e)}")


@api_router.post("/auth/refresh", summary="Обновление токена")
async def refresh_token(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Обновление токена доступа"""
    try:
        request_data = await request.json()
        result = await auth_service.refresh_token(request_data.get("refresh_token"))
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token refresh error: {str(e)}")


@api_router.post("/auth/logout", summary="Выход из системы")
async def logout(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Выход пользователя из системы"""
    try:
        request_data = await request.json()
        success = await auth_service.logout_user(request_data.get("token"))
        return {"success": success}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logout error: {str(e)}")


# Generic routing endpoint
@api_router.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def route_to_service(
    service: str,
    path: str,
    request: Request,
    gateway_service: GatewayService = Depends(get_gateway_service)
):
    """Маршрутизация запросов к микросервисам"""
    try:
        # Полная маршрутизация через GatewayService (добавляем версию API целевого сервиса)
        full_path = f"/api/{settings.api_version}/{path}"

        # Проставим идентификатор пользователя в заголовки для доверенных внутренних сервисов
        # Это упростит аутентификацию downstream без повторной валидации JWT
        if hasattr(request.state, 'user_id') and request.state.user_id:
            request.headers.__dict__.setdefault('_list', [])
            # Невозможно мутировать Headers напрямую в FastAPI, поэтому прокинем через state
            # и учтём это в GatewayService.route_request
            request.state.inject_user_headers = {
                'X-User-Id': str(request.state.user_id),
                'X-User-Role': str(getattr(request.state, 'user_role', '') or '')
            }

        result = await gateway_service.route_request(
            request,
            service,
            full_path,
            request.method
        )

        # Проксируем статус и тело ответа downstream сервиса
        status_code = result.get("status_code", 200)
        body_text = result.get("body", "")
        headers = result.get("headers", {})
        media_type = headers.get("content-type")

        return Response(content=body_text, status_code=status_code, media_type=media_type)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Routing error: {str(e)}")
