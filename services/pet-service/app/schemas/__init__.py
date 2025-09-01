"""
Pydantic схемы для Pet Service
"""

from .pet import (
    PetCreate,
    PetUpdate,
    PetResponse,
    PetProfile,
    PetPhotoCreate,
    PetPhotoResponse,
    PetMedicalCreate,
    PetMedicalUpdate,
    PetMedicalResponse
)

__all__ = [
    "PetCreate",
    "PetUpdate",
    "PetResponse",
    "PetProfile",
    "PetPhotoCreate",
    "PetPhotoResponse",
    "PetMedicalCreate",
    "PetMedicalUpdate",
    "PetMedicalResponse"
]
