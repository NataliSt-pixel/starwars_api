from aiohttp import web
import logging
from aiohttp_cors import CorsConfig, ResourceOptions, setup as setup_cors
import asyncio
import os
from dotenv import load_dotenv

from app.database import Database
from app.api.endpoints import (
    health_check, api_docs,
    register, login, get_current_user_info, update_current_user,
    get_advertisements, get_advertisement, create_advertisement,
    update_advertisement, delete_advertisement, get_user_advertisements
)

load_dotenv()

logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger(__name__)


async def init_db():
    """Инициализация базы данных"""
    try:
        init_sql = '''
        -- Таблица пользователей
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        );

        -- Таблица объявлений
        CREATE TABLE IF NOT EXISTS advertisements (
            id SERIAL PRIMARY KEY,
            title VARCHAR(100) NOT NULL,
            description TEXT NOT NULL,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        );

        -- Индексы
        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_ads_user_id ON advertisements(user_id);
        CREATE INDEX IF NOT EXISTS idx_ads_created_at ON advertisements(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_ads_title ON advertisements(title);
        CREATE INDEX IF NOT EXISTS idx_ads_description ON advertisements(description);
        '''

        await Database.execute(init_sql)
        logger.info("Database tables created")

        user_count = await Database.fetchval("SELECT COUNT(*) FROM users")
        logger.info(f"Users in database: {user_count}")

        if user_count == 0:
            from app.security import get_password_hash

            test_password = get_password_hash("test123")
            await Database.execute(
                "INSERT INTO users (username, email, password_hash) VALUES ($1, $2, $3)",
                "testuser", "test@example.com", test_password
            )
            logger.info("Test user created: testuser / test123")

            await Database.execute(
                "INSERT INTO advertisements (title, description, user_id) VALUES ($1, $2, 1)",
                "Продам велосипед", "Отличный горный велосипед, почти новый"
            )
            await Database.execute(
                "INSERT INTO advertisements (title, description, user_id) VALUES ($1, $2, 1)",
                "Ищу работу Python разработчиком", "Опыт 2 года, ищу удаленную работу"
            )
            logger.info("Test advertisements created")

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def create_app():
    """Создание приложения"""
    app = web.Application()
    cors_config = CorsConfig(defaults={
        "*": ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        )
    })
    cors = setup_cors(app, defaults=cors_config.defaults)
    app.router.add_post('/api/register', register)
    app.router.add_post('/api/login', login)
    app.router.add_get('/api/users/me', get_current_user_info)
    app.router.add_put('/api/users/me', update_current_user)
    app.router.add_get('/api/ads', get_advertisements)
    app.router.add_get(r'/api/ads/{id:\d+}', get_advertisement)
    app.router.add_get(r'/api/users/{user_id:\d+}/ads', get_user_advertisements)
    app.router.add_post('/api/ads', create_advertisement)
    app.router.add_put(r'/api/ads/{id:\d+}', update_advertisement)
    app.router.add_delete(r'/api/ads/{id:\d+}', delete_advertisement)
    app.router.add_get('/api/health', health_check)
    app.router.add_get('/api/docs', api_docs)

    for route in list(app.router.routes()):
        cors.add(route)

    @web.middleware
    async def log_middleware(request, handler):
        logger.info(f"{request.method} {request.path}")
        try:
            response = await handler(request)
            logger.info(f"{request.method} {request.path} - {response.status}")
            return response
        except web.HTTPException as ex:
            logger.error(f"{request.method} {request.path} - {ex.status}")
            raise
        except Exception as ex:
            logger.error(f"{request.method} {request.path} - 500: {ex}")
            raise

    app.middlewares.append(log_middleware)

    @web.middleware
    async def error_middleware(request, handler):
        try:
            return await handler(request)
        except web.HTTPException as ex:
            return web.json_response({
                'error': ex.reason,
                'status': ex.status
            }, status=ex.status)
        except Exception as ex:
            logger.exception(f"Unhandled exception: {ex}")
            return web.json_response({
                'error': 'Internal server error',
                'detail': str(ex)
            }, status=500)

    app.middlewares.append(error_middleware)

    return app


async def start_app():
    """Запуск приложения"""

    await init_db()
    app = create_app()

    runner = web.AppRunner(app)
    await runner.setup()

    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8000))

    site = web.TCPSite(runner, host, port)

    logger.info(f" Advertisements API запущен!")
    logger.info(f" Адрес: http://{host}:{port}")
    logger.info(f" Документация: http://{host}:{port}/api/docs")
    logger.info("")
    logger.info("   Примеры использования:")
    logger.info("   Регистрация: POST /api/register")
    logger.info("   Вход: POST /api/login")
    logger.info("   Все объявления: GET /api/ads")
    logger.info("   Создать объявление: POST /api/ads (требуется токен)")

    await site.start()

    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Сервер остановлен пользователем")
    finally:
        await runner.cleanup()


async def shutdown():
    """Завершение работы"""
    logger.info("Завершение работы...")
    await Database.close_pool()


def main():
    """Точка входа"""
    try:
        asyncio.run(start_app())
    except KeyboardInterrupt:
        logger.info("Сервер остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка при запуске сервера: {e}")
    finally:
        asyncio.run(shutdown())


if __name__ == '__main__':
    main()