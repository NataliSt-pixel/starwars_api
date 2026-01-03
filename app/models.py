from typing import Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Character:
    """Модель персонажа Star Wars"""
    id: int
    uid: int
    name: str
    birth_year: Optional[str] = None
    eye_color: Optional[str] = None
    gender: Optional[str] = None
    hair_color: Optional[str] = None
    homeworld: Optional[str] = None
    mass: Optional[str] = None
    skin_color: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'Character':
        """Создание экземпляра из словаря"""
        return cls(
            id=data.get('id'),
            uid=data.get('uid'),
            name=data.get('name'),
            birth_year=data.get('birth_year'),
            eye_color=data.get('eye_color'),
            gender=data.get('gender'),
            hair_color=data.get('hair_color'),
            homeworld=data.get('homeworld'),
            mass=data.get('mass'),
            skin_color=data.get('skin_color'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            'id': self.id,
            'uid': self.uid,
            'name': self.name,
            'birth_year': self.birth_year,
            'eye_color': self.eye_color,
            'gender': self.gender,
            'hair_color': self.hair_color,
            'homeworld': self.homeworld,
            'mass': self.mass,
            'skin_color': self.skin_color,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }