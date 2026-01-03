from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CharacterBase(BaseModel):
    uid: int = Field(..., description="Уникальный ID из SWAPI")
    name: str = Field(..., min_length=1, max_length=100, description="Имя персонажа")
    birth_year: Optional[str] = Field(None, description="Год рождения")
    eye_color: Optional[str] = Field(None, description="Цвет глаз")
    gender: Optional[str] = Field(None, description="Пол")
    hair_color: Optional[str] = Field(None, description="Цвет волос")
    homeworld: Optional[str] = Field(None, description="Родная планета (URL)")
    mass: Optional[str] = Field(None, description="Масса")
    skin_color: Optional[str] = Field(None, description="Цвет кожи")


class CharacterCreate(CharacterBase):
    pass


class CharacterUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    birth_year: Optional[str] = None
    eye_color: Optional[str] = None
    gender: Optional[str] = None
    hair_color: Optional[str] = None
    homeworld: Optional[str] = None
    mass: Optional[str] = None
    skin_color: Optional[str] = None


class CharacterResponse(CharacterBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CharacterListResponse(BaseModel):
    items: list[CharacterResponse]
    total: int
    page: int
    size: int
    pages: int


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Номер страницы")
    size: int = Field(10, ge=1, le=100, description="Размер страницы")


class CharacterFilterParams(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    homeworld: Optional[str] = None