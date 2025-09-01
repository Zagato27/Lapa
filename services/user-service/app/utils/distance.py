"""
Утилиты для работы с геолокацией и расчетом расстояний
"""

import math
from typing import Tuple


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Расчет расстояния между двумя точками на Земле по формуле Хаверсина
    Возвращает расстояние в километрах
    """
    # Радиус Земли в километрах
    R = 6371.0

    # Перевод в радианы
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Разницы координат
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Формула Хаверсина
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance


def calculate_distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """
    Расчет расстояния между двумя точками
    point1 и point2 - кортежи (latitude, longitude)
    Возвращает расстояние в километрах
    """
    lat1, lon1 = point1
    lat2, lon2 = point2

    return haversine_distance(lat1, lon1, lat2, lon2)


def meters_to_degrees(meters: float) -> float:
    """
    Перевод расстояния из метров в градусы
    (для работы с PostGIS)
    """
    # Примерное расстояние одного градуса широты в метрах
    METERS_PER_DEGREE = 111000
    return meters / METERS_PER_DEGREE


def degrees_to_meters(degrees: float) -> float:
    """
    Перевод расстояния из градусов в метры
    """
    METERS_PER_DEGREE = 111000
    return degrees * METERS_PER_DEGREE
