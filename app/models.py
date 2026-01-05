from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """Модель пользователя"""
    id: Optional[int] = None
    username: str = ""
    email: str = ""
    password_hash: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict):
        """Создание из словаря"""
        return cls(
            id=data.get('id'),
            username=data.get('username', ''),
            email=data.get('email', ''),
            password_hash=data.get('password_hash', ''),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

    def to_dict(self):
        """Преобразование в словарь"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class Advertisement:
    """Модель объявления"""
    id: Optional[int] = None
    title: str = ""
    description: str = ""
    user_id: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    user: Optional[User] = None  # Для join

    @classmethod
    def from_dict(cls, data: dict):
        """Создание из словаря"""
        user_data = data.get('user')
        user = User.from_dict(user_data) if user_data else None

        return cls(
            id=data.get('id'),
            title=data.get('title', ''),
            description=data.get('description', ''),
            user_id=data.get('user_id', 0),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            user=user
        )

    def to_dict(self):
        """Преобразование в словарь"""
        result = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if self.user:
            result['user'] = self.user.to_dict()

        return result