"""
Модуль аутентификации
"""
from aiohttp import web
from app.security import get_current_user_from_token
from app.crud import UserCRUD


async def get_current_user(request: web.Request):
    """Получение текущего пользователя"""
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return None

    try:
        scheme, token = auth_header.split()
        if scheme.lower() != 'bearer':
            return None
    except ValueError:
        return None

    user_info = get_current_user_from_token(token)
    if not user_info:
        return None

    return await UserCRUD.get_by_id(user_info["user_id"])


async def auth_required(handler):
    """Декоратор для требующих аутентификации эндпоинтов"""

    async def middleware(request):
        user = await get_current_user(request)
        if not user:
            return web.json_response(
                {"error": "Authentication required"},
                status=401
            )
        request.user = user
        return await handler(request)

    return middleware


async def owner_required(handler):
    """Декоратор для требующих владения ресурсом эндпоинтов"""

    async def middleware(request):
        user = await get_current_user(request)
        if not user:
            return web.json_response(
                {"error": "Authentication required"},
                status=401
            )

        if 'id' in request.match_info:
            from app.crud import AdvertisementCRUD
            ad_id = int(request.match_info['id'])
            ad = await AdvertisementCRUD.get_by_id(ad_id)

            if not ad:
                return web.json_response(
                    {"error": "Advertisement not found"},
                    status=404
                )

            if ad.user_id != user.id:
                return web.json_response(
                    {"error": "Not authorized to modify this advertisement"},
                    status=403
                )

            request.ad = ad

        request.user = user
        return await handler(request)

    return middleware