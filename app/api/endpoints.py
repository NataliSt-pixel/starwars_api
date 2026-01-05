from aiohttp import web
import logging
from typing import Optional

from app.crud import UserCRUD, AdvertisementCRUD
from app.schemas import (
    UserCreate, UserResponse, UserUpdate,
    AdvertisementCreate, AdvertisementResponse, AdvertisementUpdate, AdvertisementListResponse,
    LoginRequest, Token, ErrorResponse
)
from app.api.dependencies import (
    validate_json, get_pagination_params, get_filter_params, get_current_user
)
from app.security import create_access_token

logger = logging.getLogger(__name__)


async def register(request: web.Request) -> web.Response:
    """Регистрация нового пользователя"""
    try:
        data = await validate_json(request)
        user_data = UserCreate(**data)

        existing_user = await UserCRUD.get_by_username(user_data.username)
        if existing_user:
            return web.json_response(
                ErrorResponse(error="Username already exists").dict(),
                status=400
            )

        existing_email = await UserCRUD.get_by_email(user_data.email)
        if existing_email:
            return web.json_response(
                ErrorResponse(error="Email already exists").dict(),
                status=400
            )

        user = await UserCRUD.create(user_data.dict())

        return web.json_response(
            UserResponse(**user.to_dict()).dict(),
            status=201
        )

    except ValueError as e:
        return web.json_response(
            ErrorResponse(error="Invalid request data", detail=str(e)).dict(),
            status=400
        )
    except Exception as e:
        logger.error(f"Error in register: {e}")
        return web.json_response(
            ErrorResponse(error="Internal server error", detail=str(e)).dict(),
            status=500
        )


async def login(request: web.Request) -> web.Response:
    """Вход пользователя"""
    try:
        data = await validate_json(request)
        login_data = LoginRequest(**data)

        user = await UserCRUD.authenticate(
            login_data.username,
            login_data.password
        )

        if not user:
            return web.json_response(
                ErrorResponse(error="Invalid username or password").dict(),
                status=401
            )

        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id}
        )

        return web.json_response(
            Token(access_token=access_token).dict()
        )

    except ValueError as e:
        return web.json_response(
            ErrorResponse(error="Invalid request data", detail=str(e)).dict(),
            status=400
        )
    except Exception as e:
        logger.error(f"Error in login: {e}")
        return web.json_response(
            ErrorResponse(error="Internal server error", detail=str(e)).dict(),
            status=500
        )


async def get_current_user_info(request: web.Request) -> web.Response:
    """Получить информацию о текущем пользователе"""
    user_info = get_current_user(request)

    if not user_info:
        return web.json_response(
            ErrorResponse(error="Not authenticated").dict(),
            status=401
        )

    user = await UserCRUD.get_by_id(user_info["user_id"])
    if not user:
        return web.json_response(
            ErrorResponse(error="User not found").dict(),
            status=404
        )

    return web.json_response(
        UserResponse(**user.to_dict()).dict()
    )


async def update_current_user(request: web.Request) -> web.Response:
    """Обновить текущего пользователя"""
    user_info = get_current_user(request)

    if not user_info:
        return web.json_response(
            ErrorResponse(error="Not authenticated").dict(),
            status=401
        )

    try:
        data = await validate_json(request)
        update_data = UserUpdate(**data)

        if update_data.username:
            existing_user = await UserCRUD.get_by_username(update_data.username)
            if existing_user and existing_user.id != user_info["user_id"]:
                return web.json_response(
                    ErrorResponse(error="Username already exists").dict(),
                    status=400
                )

        if update_data.email:
            existing_email = await UserCRUD.get_by_email(update_data.email)
            if existing_email and existing_email.id != user_info["user_id"]:
                return web.json_response(
                    ErrorResponse(error="Email already exists").dict(),
                    status=400
                )

        user = await UserCRUD.update(user_info["user_id"], update_data.dict(exclude_unset=True))

        if not user:
            return web.json_response(
                ErrorResponse(error="User not found").dict(),
                status=404
            )

        return web.json_response(
            UserResponse(**user.to_dict()).dict()
        )

    except ValueError as e:
        return web.json_response(
            ErrorResponse(error="Invalid request data", detail=str(e)).dict(),
            status=400
        )
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        return web.json_response(
            ErrorResponse(error="Internal server error", detail=str(e)).dict(),
            status=500
        )


async def get_advertisements(request: web.Request) -> web.Response:
    """Получить список объявлений (публичный доступ)"""
    try:
        pagination = get_pagination_params(request)
        filters = get_filter_params(request)

        ads = await AdvertisementCRUD.get_all(
            skip=(pagination.page - 1) * pagination.size,
            limit=pagination.size,
            user_id=filters.user_id,
            search=filters.search
        )

        total = await AdvertisementCRUD.count(
            user_id=filters.user_id,
            search=filters.search
        )

        pages = (total + pagination.size - 1) // pagination.size if pagination.size > 0 else 0

        response_data = AdvertisementListResponse(
            items=[AdvertisementResponse(**ad.to_dict()) for ad in ads],
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=pages
        )

        return web.json_response(response_data.dict())

    except Exception as e:
        logger.error(f"Error getting advertisements: {e}")
        return web.json_response(
            ErrorResponse(error="Internal server error", detail=str(e)).dict(),
            status=500
        )


async def get_advertisement(request: web.Request) -> web.Response:
    """Получить объявление по ID (публичный доступ)"""
    try:
        ad_id = int(request.match_info['id'])
        ad = await AdvertisementCRUD.get_by_id(ad_id)

        if not ad:
            return web.json_response(
                ErrorResponse(error="Advertisement not found").dict(),
                status=404
            )

        return web.json_response(
            AdvertisementResponse(**ad.to_dict()).dict()
        )

    except ValueError:
        return web.json_response(
            ErrorResponse(error="Invalid advertisement ID").dict(),
            status=400
        )
    except Exception as e:
        logger.error(f"Error getting advertisement: {e}")
        return web.json_response(
            ErrorResponse(error="Internal server error", detail=str(e)).dict(),
            status=500
        )


async def get_user_advertisements(request: web.Request) -> web.Response:
    """Получить объявления конкретного пользователя (публичный доступ)"""
    try:
        user_id = int(request.match_info['user_id'])

        pagination = get_pagination_params(request)

        ads = await AdvertisementCRUD.get_all(
            skip=(pagination.page - 1) * pagination.size,
            limit=pagination.size,
            user_id=user_id
        )

        total = await AdvertisementCRUD.count(user_id=user_id)
        pages = (total + pagination.size - 1) // pagination.size if pagination.size > 0 else 0

        response_data = AdvertisementListResponse(
            items=[AdvertisementResponse(**ad.to_dict()) for ad in ads],
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=pages
        )

        return web.json_response(response_data.dict())

    except ValueError:
        return web.json_response(
            ErrorResponse(error="Invalid user ID").dict(),
            status=400
        )
    except Exception as e:
        logger.error(f"Error getting user advertisements: {e}")
        return web.json_response(
            ErrorResponse(error="Internal server error", detail=str(e)).dict(),
            status=500
        )


async def create_advertisement(request: web.Request) -> web.Response:
    """Создать новое объявление (только аутентифицированные)"""
    user_info = get_current_user(request)

    if not user_info:
        return web.json_response(
            ErrorResponse(error="Not authenticated").dict(),
            status=401
        )

    try:
        data = await validate_json(request)
        ad_data = AdvertisementCreate(**data)

        ad = await AdvertisementCRUD.create(
            ad_data.dict(),
            user_info["user_id"]
        )

        return web.json_response(
            AdvertisementResponse(**ad.to_dict()).dict(),
            status=201
        )

    except ValueError as e:
        return web.json_response(
            ErrorResponse(error="Invalid request data", detail=str(e)).dict(),
            status=400
        )
    except Exception as e:
        logger.error(f"Error creating advertisement: {e}")
        return web.json_response(
            ErrorResponse(error="Internal server error", detail=str(e)).dict(),
            status=500
        )


async def update_advertisement(request: web.Request) -> web.Response:
    """Обновить объявление (только автор)"""
    user_info = get_current_user(request)

    if not user_info:
        return web.json_response(
            ErrorResponse(error="Not authenticated").dict(),
            status=401
        )

    try:
        ad_id = int(request.match_info['id'])
        data = await validate_json(request)

        update_data = AdvertisementUpdate(**data)

        ad = await AdvertisementCRUD.update(
            ad_id,
            update_data.dict(exclude_unset=True),
            user_info["user_id"]
        )

        if not ad:
            return web.json_response(
                ErrorResponse(error="Advertisement not found or not authorized").dict(),
                status=404
            )

        return web.json_response(
            AdvertisementResponse(**ad.to_dict()).dict()
        )

    except ValueError as e:
        return web.json_response(
            ErrorResponse(error="Invalid request data", detail=str(e)).dict(),
            status=400
        )
    except Exception as e:
        logger.error(f"Error updating advertisement: {e}")
        return web.json_response(
            ErrorResponse(error="Internal server error", detail=str(e)).dict(),
            status=500
        )


async def delete_advertisement(request: web.Request) -> web.Response:
    """Удалить объявление (только автор)"""
    user_info = get_current_user(request)

    if not user_info:
        return web.json_response(
            ErrorResponse(error="Not authenticated").dict(),
            status=401
        )

    try:
        ad_id = int(request.match_info['id'])

        success = await AdvertisementCRUD.delete(ad_id, user_info["user_id"])

        if not success:
            return web.json_response(
                ErrorResponse(error="Advertisement not found or not authorized").dict(),
                status=404
            )

        return web.Response(status=204)

    except ValueError:
        return web.json_response(
            ErrorResponse(error="Invalid advertisement ID").dict(),
            status=400
        )
    except Exception as e:
        logger.error(f"Error deleting advertisement: {e}")
        return web.json_response(
            ErrorResponse(error="Internal server error", detail=str(e)).dict(),
            status=500
        )

async def health_check(request: web.Request) -> web.Response:
    """Проверка здоровья API"""
    return web.json_response({
        "status": "ok",
        "service": "Advertisements API",
        "version": "1.0.0"
    })


async def api_docs(request: web.Request) -> web.Response:
    """Документация API"""
    return web.Response(
        text='''
        <html>
            <head><title>Advertisements API Documentation</title></head>
            <body>
                <h1>Advertisements API v1.0.0</h1>

                <h2>Аутентификация</h2>
                <ul>
                    <li><strong>POST /api/register</strong> - Регистрация</li>
                    <li><strong>POST /api/login</strong> - Вход</li>
                    <li><strong>GET /api/users/me</strong> - Получить текущего пользователя</li>
                    <li><strong>PUT /api/users/me</strong> - Обновить текущего пользователя</li>
                </ul>

                <h2>Объявления (публичные)</h2>
                <ul>
                    <li><strong>GET /api/ads</strong> - Список объявлений</li>
                    <li><strong>GET /api/ads/{id}</strong> - Объявление по ID</li>
                    <li><strong>GET /api/users/{user_id}/ads</strong> - Объявления пользователя</li>
                </ul>

                <h2>Объявления (защищенные)</h2>
                <ul>
                    <li><strong>POST /api/ads</strong> - Создать объявление</li>
                    <li><strong>PUT /api/ads/{id}</strong> - Обновить объявление</li>
                    <li><strong>DELETE /api/ads/{id}</strong> - Удалить объявление</li>
                </ul>

                <h2>Системные</h2>
                <ul>
                    <li><strong>GET /api/health</strong> - Проверка здоровья</li>
                </ul>

                <h3>Заголовок авторизации</h3>
                <p>Для защищенных эндпоинтов требуется заголовок:</p>
                <pre>Authorization: Bearer &lt;ваш_jwt_токен&gt;</pre>

                <h3>Параметры запросов</h3>
                <ul>
                    <li><strong>page</strong> - номер страницы</li>
                    <li><strong>size</strong> - размер страницы (max: 100)</li>
                    <li><strong>user_id</strong> - фильтр по пользователю</li>
                    <li><strong>search</strong> - поиск по тексту</li>
                </ul>
            </body>
        </html>
        ''',
        content_type='text/html'
    )