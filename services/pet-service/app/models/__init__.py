"""
Модели базы данных для Pet Service
"""

from .base import Base
from .pet import Pet
from .pet_photo import PetPhoto
from .pet_medical import PetMedical

__all__ = ["Base", "Pet", "PetPhoto", "PetMedical"]
