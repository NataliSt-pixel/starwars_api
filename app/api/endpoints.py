from aiohttp import web
import json
import logging
from typing import Dict, Any
from app.crud import CharacterCRUD
from app.schemas import (
    CharacterCreate, CharacterUpdate, CharacterResponse,
    CharacterListResponse, PaginationParams, CharacterFilterParams,
    ErrorResponse
)
from app.api.dependencies import validate_json, get_pagination_params

logger = logging.getLogger(__name__)


async def health_check(request: web.Request) -> web.Response:
    """Проверка здоровья API"""
    return web.json_response({
        "status": "ok",
        "service": "starwars_api",
        "version": "1.0.0"
    })


async def get_characters(request: web.Request) -> web.Response:
    """Получить список персонажей с пагинацией"""
    try:
        pagination = get_pagination_params(request)

        filters = {}
        if 'name' in request.query:
            filters['name'] = request.query['name']
        if 'gender' in request.query:
            filters['gender'] = request.query['gender']
        if 'homeworld' in request.query:
            filters['homeworld'] = request.query['homeworld']

        characters = await CharacterCRUD.get_all(
            skip=(pagination.page - 1) * pagination.size,
            limit=pagination.size,
            filters=filters
        )

        total = await CharacterCRUD.count(filters)
        pages = (total + pagination.size - 1) // pagination.size

        response_data = CharacterListResponse(
            items=[CharacterResponse(**char.to_dict()) for char in characters],
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=pages
        )

        return web.json_response(response_data.dict())

    except Exception as e:
        logger.error(f"Error getting characters: {e}")
        return web.json_response(
            ErrorResponse(error="Internal server error", detail=str(e)).dict(),
            status=500
        )


async def get_character(request: web.Request) -> web.Response:
    """Получить персонажа по ID"""
    try:
        char_id = int(request.match_info['id'])
        character = await CharacterCRUD.get_by_id(char_id)

        if not character:
            return web.json_response(
                ErrorResponse(error="Character not found").dict(),
                status=404
            )

        return web.json_response(
            CharacterResponse(**character.to_dict()).dict()
        )

    except ValueError:
        return web.json_response(
            ErrorResponse(error="Invalid character ID").dict(),
            status=400
        )
    except Exception as e:
        logger.error(f"Error getting character: {e}")
        return web.json_response(
            ErrorResponse(error="Internal server error", detail=str(e)).dict(),
            status=500
        )


async def create_character(request: web.Request) -> web.Response:
    """Создать нового персонажа"""
    try:
        data = await validate_json(request)
        character_data = CharacterCreate(**data)

        existing = await CharacterCRUD.get_by_uid(character_data.uid)
        if existing:
            return web.json_response(
                ErrorResponse(error="Character with this UID already exists").dict(),
                status=409
            )

        character = await CharacterCRUD.create(character_data)

        return web.json_response(
            CharacterResponse(**character.to_dict()).dict(),
            status=201
        )

    except ValueError as e:
        return web.json_response(
            ErrorResponse(error="Invalid request data", detail=str(e)).dict(),
            status=400
        )
    except Exception as e:
        logger.error(f"Error creating character: {e}")
        return web.json_response(
            ErrorResponse(error="Internal server error", detail=str(e)).dict(),
            status=500
        )


async def update_character(request: web.Request) -> web.Response:
    """Обновить существующего персонажа"""
    try:
        char_id = int(request.match_info['id'])
        data = await validate_json(request)

        existing = await CharacterCRUD.get_by_id(char_id)
        if not existing:
            return web.json_response(
                ErrorResponse(error="Character not found").dict(),
                status=404
            )

        update_data = CharacterUpdate(**data)
        updated = await CharacterCRUD.update(char_id, update_data)

        if not updated:
            return web.json_response(
                ErrorResponse(error="Failed to update character").dict(),
                status=500
            )

        return web.json_response(
            CharacterResponse(**updated.to_dict()).dict()
        )

    except ValueError as e:
        return web.json_response(
            ErrorResponse(error="Invalid request data", detail=str(e)).dict(),
            status=400
        )
    except Exception as e:
        logger.error(f"Error updating character: {e}")
        return web.json_response(
            ErrorResponse(error="Internal server error", detail=str(e)).dict(),
            status=500
        )


async def delete_character(request: web.Request) -> web.Response:
    """Удалить персонажа"""
    try:
        char_id = int(request.match_info['id'])

        existing = await CharacterCRUD.get_by_id(char_id)
        if not existing:
            return web.json_response(
                ErrorResponse(error="Character not found").dict(),
                status=404
            )

        success = await CharacterCRUD.delete(char_id)

        if not success:
            return web.json_response(
                ErrorResponse(error="Failed to delete character").dict(),
                status=500
            )

        return web.Response(status=204)

    except ValueError:
        return web.json_response(
            ErrorResponse(error="Invalid character ID").dict(),
            status=400
        )
    except Exception as e:
        logger.error(f"Error deleting character: {e}")
        return web.json_response(
            ErrorResponse(error="Internal server error", detail=str(e)).dict(),
            status=500
        )


async def get_statistics(request: web.Request) -> web.Response:
    """Получить статистику по персонажам"""
    try:
        stats = await CharacterCRUD.get_statistics()
        return web.json_response(stats)

    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return web.json_response(
            ErrorResponse(error="Internal server error", detail=str(e)).dict(),
            status=500
        )


async def search_characters(request: web.Request) -> web.Response:
    """Поиск персонажей по имени"""
    try:
        if 'q' not in request.query or not request.query['q'].strip():
            return web.json_response(
                ErrorResponse(error="Search query is required").dict(),
                status=400
            )

        search_term = request.query['q'].strip()
        filters = {'name': search_term}

        characters = await CharacterCRUD.get_all(filters=filters, limit=50)

        return web.json_response({
            'results': [CharacterResponse(**char.to_dict()).dict() for char in characters],
            'count': len(characters)
        })

    except Exception as e:
        logger.error(f"Error searching characters: {e}")
        return web.json_response(
            ErrorResponse(error="Internal server error", detail=str(e)).dict(),
            status=500
        )