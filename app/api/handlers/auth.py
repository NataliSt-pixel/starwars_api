import jwt
from datetime import datetime, timedelta
from aiohttp import web
import json
from ...database import get_user_by_email, create_user
from ...security import verify_password, get_password_hash
from ...config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from ...validators import validate_user_registration, validate_login, ValidationError


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
        errors = validate_user_registration(data)
        if errors:
            return web.json_response(
                {"errors": errors},
                status=400
            )

        existing_user = await get_user_by_email(data['email'])
        if existing_user:
            return web.json_response(
                {"error": "Email already registered"},
                status=400
            )

        hashed_password = get_password_hash(data['password'])

        user_data = {
            'email': data['email'],
            'username': data['username'],
            'hashed_password': hashed_password,
            'created_at': datetime.utcnow()
        }

        user_id = await create_user(user_data)

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
        return web.json_response(
            {"error": "Invalid JSON"},
            status=400
        )
    except Exception as e:
        return web.json_response(
            {"error": "Internal server error"},
            status=500
        )


async def login(request):
    """Login user and return access token"""
    try:
        data = await request.json()
        errors = validate_login(data)
        if errors:
            return web.json_response(
                {"errors": errors},
                status=400
            )

        user = await get_user_by_email(data['email'])
        if not user or not verify_password(data['password'], user['hashed_password']):
            return web.json_response(
                {"error": "Incorrect email or password"},
                status=401
            )

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
        return web.json_response(
            {"error": "Invalid JSON"},
            status=400
        )
    except Exception as e:
        return web.json_response(
            {"error": "Internal server error"},
            status=500
        )