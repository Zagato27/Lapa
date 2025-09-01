"""
Роуты питомцев (proxy) для API Gateway
"""

from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel

from app.services.discovery import ServiceDiscovery


router = APIRouter()
security = HTTPBearer(auto_error=False)


class PetCreate(BaseModel):
    name: str
    breed: str
    gender: str
    date_of_birth: Optional[str] = None
    age_years: Optional[int] = None
    age_months: Optional[int] = None
    color: Optional[str] = None
    weight_kg: Optional[float] = None
    size: Optional[str] = None
    energy_level: Optional[str] = None
    friendliness: Optional[str] = None
    is_vaccinated: Optional[bool] = None
    is_neutered: Optional[bool] = None
    has_allergies: Optional[bool] = None
    allergies_description: Optional[str] = None
    special_needs: Optional[str] = None
    medications: Optional[list] = None
    medical_conditions: Optional[list] = None
    is_friendly_with_dogs: Optional[bool] = None
    is_friendly_with_cats: Optional[bool] = None
    is_friendly_with_children: Optional[bool] = None
    behavioral_notes: Optional[str] = None
    walking_frequency: Optional[str] = None
    walking_duration_minutes: Optional[int] = None
    feeding_schedule: Optional[dict] = None
    favorite_activities: Optional[list] = None
    walking_notes: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    veterinarian_name: Optional[str] = None
    veterinarian_phone: Optional[str] = None
    veterinarian_address: Optional[str] = None


class PetUpdate(PetCreate):
    pass


async def get_service_discovery() -> ServiceDiscovery:
    return ServiceDiscovery()


@router.get("", summary="Список питомцев пользователя")
async def list_pets(
    request: Request,
    page: int = Query(1),
    limit: int = Query(20),
    refresh: bool = Query(False),
    credentials = Depends(security),
    service_discovery: ServiceDiscovery = Depends(get_service_discovery)
):
    try:
        response = await service_discovery.proxy_request(
            service_name="pet-service",
            path="/api/v1/pets",
            method="GET",
            headers={"Authorization": f"Bearer {credentials.credentials}"},
            params={"page": page, "limit": limit, "refresh": refresh}
        )
        if response["status_code"] >= 400:
            detail = response["error"].get("detail", "Ошибка получения питомцев") if isinstance(response.get("error"), dict) else response.get("error")
            raise HTTPException(status_code=response["status_code"], detail=detail)
        return response["data"]
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сервиса: {str(e)}")


@router.post("", summary="Создание питомца")
async def create_pet(
    pet_data: PetCreate,
    request: Request,
    credentials = Depends(security),
    service_discovery: ServiceDiscovery = Depends(get_service_discovery)
):
    try:
        response = await service_discovery.proxy_request(
            service_name="pet-service",
            path="/api/v1/pets",
            method="POST",
            headers={"Authorization": f"Bearer {credentials.credentials}"},
            data=pet_data.model_dump(exclude_none=True)
        )
        if response["status_code"] >= 400:
            detail = response["error"].get("detail", "Ошибка создания питомца") if isinstance(response.get("error"), dict) else response.get("error")
            raise HTTPException(status_code=response["status_code"], detail=detail)
        return response["data"]
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сервиса: {str(e)}")


@router.get("/{pet_id}", summary="Карточка питомца")
async def get_pet(
    pet_id: str,
    request: Request,
    credentials = Depends(security),
    service_discovery: ServiceDiscovery = Depends(get_service_discovery)
):
    try:
        response = await service_discovery.proxy_request(
            service_name="pet-service",
            path=f"/api/v1/pets/{pet_id}",
            method="GET",
            headers={"Authorization": f"Bearer {credentials.credentials}"}
        )
        if response["status_code"] >= 400:
            detail = response["error"].get("detail", "Питомец не найден") if isinstance(response.get("error"), dict) else response.get("error")
            raise HTTPException(status_code=response["status_code"], detail=detail)
        return response["data"]
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сервиса: {str(e)}")


@router.put("/{pet_id}", summary="Обновление питомца")
async def update_pet(
    pet_id: str,
    pet_data: PetUpdate,
    request: Request,
    credentials = Depends(security),
    service_discovery: ServiceDiscovery = Depends(get_service_discovery)
):
    try:
        response = await service_discovery.proxy_request(
            service_name="pet-service",
            path=f"/api/v1/pets/{pet_id}",
            method="PUT",
            headers={"Authorization": f"Bearer {credentials.credentials}"},
            data=pet_data.model_dump(exclude_none=True)
        )
        if response["status_code"] >= 400:
            detail = response["error"].get("detail", "Ошибка обновления питомца") if isinstance(response.get("error"), dict) else response.get("error")
            raise HTTPException(status_code=response["status_code"], detail=detail)
        return response["data"]
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сервиса: {str(e)}")


@router.delete("/{pet_id}", summary="Удаление питомца")
async def delete_pet(
    pet_id: str,
    request: Request,
    credentials = Depends(security),
    service_discovery: ServiceDiscovery = Depends(get_service_discovery)
):
    try:
        response = await service_discovery.proxy_request(
            service_name="pet-service",
            path=f"/api/v1/pets/{pet_id}",
            method="DELETE",
            headers={"Authorization": f"Bearer {credentials.credentials}"}
        )
        if response["status_code"] >= 400:
            detail = response["error"].get("detail", "Ошибка удаления питомца") if isinstance(response.get("error"), dict) else response.get("error")
            raise HTTPException(status_code=response["status_code"], detail=detail)
        return response["data"]
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сервиса: {str(e)}")


