from aiohttp import web
import json
from typing import Dict, Any
from app.schemas import PaginationParams


async def validate_json(request: web.Request) -> Dict[str, Any]:
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