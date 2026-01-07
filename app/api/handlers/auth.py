import jwt
from datetime import datetime, timedelta
from aiohttp import web
import json
from ...database import get_user_by_email, create_user as db_create_user
from ...security import verify_password, get_password_hash
from ...config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def register(request):
    """Register new user"""
    try:
        data = await request.json()
        required_fields = ['email', 'password', 'username']
        for field in required_fields:
            if field not in data:
                raise web.HTTPBadRequest(reason=f"Missing required field: {field}")
        existing_user = await get_user_by_email(data['email'])
        if existing_user:
            raise web.HTTPBadRequest(reason="Email already registered")
        hashed_password = get_password_hash(data['password'])

        user_data = {
            'email': data['email'],
            'username': data['username'],
            'hashed_password': hashed_password,
            'created_at': datetime.utcnow()
        }

        user_id = await db_create_user(user_data)

        return web.json_response(
            {
                'id': user_id,
                'email': data['email'],
                'username': data['username'],
                'message': 'User registered successfully'
            },
            status=201,
            dumps=lambda x: json.dumps(x, cls=DateTimeEncoder)
        )

    except json.JSONDecodeError:
        raise web.HTTPBadRequest(reason="Invalid JSON")
    except Exception as e:
        raise web.HTTPInternalServerError(reason=str(e))


async def login(request):
    """Login user and return access token"""
    try:
        data = await request.json()
        required_fields = ['email', 'password']
        for field in required_fields:
            if field not in data:
                raise web.HTTPBadRequest(reason=f"Missing required field: {field}")
        user = await get_user_by_email(data['email'])
        if not user or not verify_password(data['password'], user['hashed_password']):
            raise web.HTTPUnauthorized(reason="Incorrect email or password")

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user['email'], "user_id": user['id']},
            expires_delta=access_token_expires
        )

        return web.json_response({
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user['id'],
            "email": user['email'],
            "username": user['username']
        })

    except json.JSONDecodeError:
        raise web.HTTPBadRequest(reason="Invalid JSON")
    except Exception as e:
        raise web.HTTPInternalServerError(reason=str(e))