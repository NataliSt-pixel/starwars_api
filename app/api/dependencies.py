from aiohttp import web
from typing import Optional
import json
from app.security import get_current_user_from_token
from app.schemas import PaginationParams, AdvertisementFilterParams


async def validate_json(request: web.Request) -> dict:
    """Валидация JSON тела запроса"""
    try:
        data = await request.json()
        return data
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON")
    except Exception:
        raise ValueError("Failed to parse request body")


def get_pagination_params(request: web.Request) -> PaginationParams:
    """Получение параметров пагинации из запроса"""
    try:
        page = int(request.query.get('page', 1))
        size = int(request.query.get('size', 10))

        if page < 1:
            page = 1
        if size < 1:
            size = 1
        elif size > 100:
            size = 100

        return PaginationParams(page=page, size=size)

    except ValueError:
        return PaginationParams()


def get_filter_params(request: web.Request) -> AdvertisementFilterParams:
    """Получение параметров фильтрации из запроса"""
    user_id = request.query.get('user_id')
    search = request.query.get('search')

    if user_id:
        try:
            user_id = int(user_id)
        except ValueError:
            user_id = None

    return AdvertisementFilterParams(user_id=user_id, search=search)


def get_current_user(request: web.Request) -> Optional[dict]:
    """Получение текущего пользователя из заголовка Authorization"""
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return None

    try:
        scheme, token = auth_header.split()
        if scheme.lower() != 'bearer':
            return None
    except ValueError:
        return None

    return get_current_user_from_token(token)