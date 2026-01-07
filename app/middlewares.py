import jwt
from aiohttp import web
from datetime import datetime
from .database import get_user_by_id
from .config import SECRET_KEY, ALGORITHM


@web.middleware
async def auth_middleware(request, handler):
    """Authentication middleware"""
    public_paths = [
        '/api/auth/register',
        '/api/auth/login',
        '/health',
        '/'
    ]

    if any(request.path.startswith(path) for path in public_paths):
        return await handler(request)

    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise web.HTTPUnauthorized(reason="Missing or invalid authorization header")

    token = auth_header.split(' ')[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")

        if not user_id:
            raise web.HTTPUnauthorized(reason="Invalid token payload")
        expire = payload.get("exp")
        if expire is None or datetime.utcnow() > datetime.fromtimestamp(expire):
            raise web.HTTPUnauthorized(reason="Token expired")
        user = await get_user_by_id(user_id)
        if not user:
            raise web.HTTPUnauthorized(reason="User not found")
        request['user'] = user
        return await handler(request)

    except jwt.ExpiredSignatureError:
        raise web.HTTPUnauthorized(reason="Token expired")
    except jwt.InvalidTokenError:
        raise web.HTTPUnauthorized(reason="Invalid token")
    except Exception as e:
        raise web.HTTPInternalServerError(reason=str(e))


@web.middleware
async def error_middleware(request, handler):
    """Global error handling middleware"""
    try:
        response = await handler(request)
        return response
    except web.HTTPException as ex:
        return web.json_response(
            {"error": ex.reason},
            status=ex.status
        )
    except Exception as ex:
        return web.json_response(
            {"error": "Internal server error"},
            status=500
        )


def setup_middlewares(app):
    """Setup all middlewares"""
    app.middlewares.append(error_middleware)
    app.middlewares.append(auth_middleware)