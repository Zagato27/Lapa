"""
API роуты для WebSocket соединений
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Request, WebSocket
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.websocket_manager import WebSocketManager

router = APIRouter()
security = HTTPBearer(auto_error=False)

logger = logging.getLogger(__name__)


async def get_current_user(
    request: Request,
    credentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Зависимость для получения текущего пользователя"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Токен не предоставлен")

    # Здесь должна быть валидация токена через API Gateway
    # Пока что просто возвращаем данные из request
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Неверный токен")

    return {"user_id": user_id}


@router.websocket("/orders/{order_id}")
async def order_websocket(
    websocket: WebSocket,
    order_id: str,
    user_type: str = Query(..., description="Тип пользователя: client или walker"),
    token: str = Query(..., description="JWT токен для аутентификации")
):
    """WebSocket соединение для реального времени данных заказа"""
    try:
        # Получение менеджера WebSocket из состояния приложения
        websocket_manager: WebSocketManager = websocket.app.state.websocket_manager

        # Валидация токена (упрощенная версия)
        # В реальном приложении здесь должна быть полная валидация JWT
        if not token:
            await websocket.close(code=1008, reason="Токен не предоставлен")
            return

        # Извлечение user_id из токена (упрощенная версия)
        # В реальном приложении здесь должна быть декодировка JWT
        try:
            import jwt
            from app.config import settings
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            user_id = payload.get("user_id")
            if not user_id:
                await websocket.close(code=1008, reason="Неверный токен")
                return
        except:
            await websocket.close(code=1008, reason="Ошибка валидации токена")
            return

        # Проверка типа пользователя
        if user_type not in ["client", "walker"]:
            await websocket.close(code=1008, reason="Неверный тип пользователя")
            return

        # Подключение к WebSocket
        await websocket_manager.connect(websocket, order_id, user_id, user_type)

        try:
            while True:
                # Ожидание сообщений от клиента
                data = await websocket.receive_json()

                # Обработка сообщений от клиента
                message_type = data.get("type")

                if message_type == "ping":
                    # Ответ на пинг
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })

                elif message_type == "location_update":
                    # Обновление геолокации
                    location_data = data.get("data", {})
                    if location_data:
                        # Отправка обновления всем подключенным клиентам
                        await websocket_manager.send_location_update(order_id, location_data)

                elif message_type == "status_request":
                    # Запрос статуса
                    from app.database.session import get_session
                    redis_session = await get_session()
                    tracking_status = await redis_session.get_tracking_status(order_id)

                    await websocket.send_json({
                        "type": "status_response",
                        "data": tracking_status or {"is_active": False}
                    })

                else:
                    # Неизвестный тип сообщения
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Неизвестный тип сообщения: {message_type}"
                    })

        except Exception as e:
            logger.error(f"WebSocket error for order {order_id}: {e}")
        finally:
            # Отключение WebSocket
            await websocket_manager.disconnect(websocket)

    except Exception as e:
        logger.error(f"WebSocket connection error for order {order_id}: {e}")
        try:
            await websocket.close(code=1011, reason="Внутренняя ошибка сервера")
        except:
            pass


@router.get("/connections/{order_id}", summary="Получение соединений заказа")
async def get_order_connections(
    order_id: str,
    current_user: Dict = Depends(get_current_user),
    request: Request = None
):
    """Получение информации о WebSocket соединениях для заказа"""
    try:
        # Проверка прав доступа к заказу
        from app.database import get_db
        db = await get_db().__aenter__()

        from app.models.order import Order
        order_query = db.execute(
            select(Order).where(
                Order.id == order_id,
                (Order.client_id == current_user["user_id"]) | (Order.walker_id == current_user["user_id"])
            )
        )
        order_result = await order_query
        order = order_result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=403, detail="Нет доступа к этому заказу")

        # Получение менеджера WebSocket
        websocket_manager: WebSocketManager = request.app.state.websocket_manager
        connections = websocket_manager.get_order_connections(order_id)

        return {
            "order_id": order_id,
            "connections": connections,
            "total_connections": len(connections)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting connections for order {order_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения соединений")


@router.get("/stats", summary="Получение статистики WebSocket")
async def get_websocket_stats(request: Request = None):
    """Получение статистики WebSocket соединений"""
    try:
        websocket_manager: WebSocketManager = request.app.state.websocket_manager

        return {
            "total_connections": websocket_manager.get_connection_count(),
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting WebSocket stats: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения статистики")
