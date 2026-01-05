"""
Упрощенный запуск Advertisements API с SQLite
"""
import asyncio
import aiosqlite
from aiohttp import web
import logging
import json
import hashlib
import secrets
from datetime import datetime, timedelta
import jwt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "advertisements.db"
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"

async def init_db():
    """Инициализация SQLite базы данных"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        await db.execute('''
        CREATE TABLE IF NOT EXISTS advertisements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        ''')

        await db.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
        await db.execute('CREATE INDEX IF NOT EXISTS idx_ads_user_id ON advertisements(user_id)')

        await db.commit()
        logger.info(f"SQLite database initialized: {DB_PATH}")

def hash_password(password: str) -> str:
    """Простое хеширование пароля"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Проверка пароля"""
    return hash_password(password) == hashed


def create_token(user_id: int, username: str) -> str:
    """Создание JWT токена"""
    payload = {
        "user_id": user_id,
        "sub": username,
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str):
    """Проверка JWT токена"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

async def health_check(request):
    """Проверка здоровья"""
    return web.json_response({
        "status": "ok",
        "service": "Advertisements API",
        "version": "1.0.0"
    })


async def register(request):
    """Регистрация"""
    try:
        data = await request.json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()

        if not username or not email or not password:
            return web.json_response(
                {"error": "All fields are required"},
                status=400
            )

        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT id FROM users WHERE username = ?",
                (username,)
            )
            existing = await cursor.fetchone()
            if existing:
                return web.json_response(
                    {"error": "Username already exists"},
                    status=400
                )

            password_hash = hash_password(password)
            cursor = await db.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, password_hash)
            )
            await db.commit()

            user_id = cursor.lastrowid

            return web.json_response({
                "id": user_id,
                "username": username,
                "email": email
            }, status=201)

    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def login(request):
    """Вход"""
    try:
        data = await request.json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            )
            user = await cursor.fetchone()

            if not user or not verify_password(password, user['password_hash']):
                return web.json_response(
                    {"error": "Invalid credentials"},
                    status=401
                )

            token = create_token(user['id'], user['username'])

            return web.json_response({
                "access_token": token,
                "token_type": "bearer"
            })

    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Login error: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def get_ads(request):
    """Получить объявления"""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row

            page = int(request.query.get('page', 1))
            limit = int(request.query.get('limit', 10))
            offset = (page - 1) * limit
            cursor = await db.execute('''
                SELECT a.*, u.username 
                FROM advertisements a
                LEFT JOIN users u ON a.user_id = u.id
                ORDER BY a.created_at DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))

            rows = await cursor.fetchall()
            ads = [dict(row) for row in rows]
            cursor = await db.execute("SELECT COUNT(*) FROM advertisements")
            total = (await cursor.fetchone())[0]

            return web.json_response({
                "items": ads,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit if limit > 0 else 0
            })

    except Exception as e:
        logger.error(f"Error getting ads: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def create_ad(request):
    """Создать объявление"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return web.json_response({"error": "Authentication required"}, status=401)

        token = auth_header.replace('Bearer ', '').strip()
        payload = verify_token(token)
        if not payload:
            return web.json_response({"error": "Invalid token"}, status=401)

        user_id = payload.get('user_id')

        data = await request.json()
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()

        if not title or not description:
            return web.json_response({"error": "Title and description are required"}, status=400)

        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "INSERT INTO advertisements (title, description, user_id) VALUES (?, ?, ?)",
                (title, description, user_id)
            )
            await db.commit()

            ad_id = cursor.lastrowid
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT a.*, u.username 
                FROM advertisements a
                LEFT JOIN users u ON a.user_id = u.id
                WHERE a.id = ?
            ''', (ad_id,))

            ad = await cursor.fetchone()

            return web.json_response(dict(ad), status=201)

    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Error creating ad: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


def create_app():
    """Создание приложения"""
    app = web.Application()
    app.router.add_get('/api/health', health_check)
    app.router.add_get('/api/ads', get_ads)
    app.router.add_post('/api/register', register)
    app.router.add_post('/api/login', login)
    app.router.add_post('/api/ads', create_ad)

    @web.middleware
    async def cors_middleware(request, handler):
        response = await handler(request)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    app.middlewares.append(cors_middleware)

    return app


async def main():
    """Основная функция"""
    await init_db()

    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, '0.0.0.0', 8000)

    logger.info(" Advertisements API запущен!")
    logger.info(" Адрес: http://localhost:8000")
    logger.info(" Эндпоинты:")
    logger.info("   GET  /api/health   - Проверка здоровья")
    logger.info("   POST /api/register - Регистрация")
    logger.info("   POST /api/login    - Вход")
    logger.info("   GET  /api/ads      - Получить объявления")
    logger.info("   POST /api/ads      - Создать объявление (требуется токен)")

    await site.start()

    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Сервер остановлен")
    finally:
        await runner.cleanup()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Сервер остановлен пользователем")