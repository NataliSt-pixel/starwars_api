from aiohttp import web
import logging
from app.database import Database
from app.api.endpoints import (
    health_check, get_characters, get_character,
    create_character, update_character, delete_character,
    get_statistics, search_characters
)
from config import config
import asyncio

logging.basicConfig(
    level=getattr(logging, config.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger(__name__)


def create_app() -> web.Application:
    """Создание приложения aiohttp без CORS"""
    app = web.Application()

    app.router.add_get('/api/health', health_check)
    app.router.add_get('/api/characters', get_characters)
    app.router.add_get(r'/api/characters/{id:\d+}', get_character)
    app.router.add_post('/api/characters', create_character)
    app.router.add_put(r'/api/characters/{id:\d+}', update_character)
    app.router.add_delete(r'/api/characters/{id:\d+}', delete_character)
    app.router.add_get('/api/characters/search', search_characters)
    app.router.add_get('/api/statistics', get_statistics)

    @web.middleware
    async def cors_middleware(request, handler):
        response = await handler(request)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    app.middlewares.append(cors_middleware)

    @web.middleware
    async def log_middleware(request, handler):
        logger.info(f"{request.method} {request.path}")
        try:
            response = await handler(request)
            logger.info(f"{request.method} {request.path} - {response.status}")
            return response
        except Exception as e:
            logger.error(f"Error: {e}")
            raise

    app.middlewares.append(log_middleware)

    async def options_handler(request):
        return web.Response(headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        })

    for route in app.router.routes():
        if route.method == 'POST' or route.method == 'PUT' or route.method == 'DELETE':
            app.router.add_route('OPTIONS', route.path, options_handler)

    return app


async def init_db():
    """Инициализация базы данных"""
    try:
        init_sql = '''
        CREATE TABLE IF NOT EXISTS characters (
            id SERIAL PRIMARY KEY,
            uid INTEGER UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            birth_year VARCHAR(20),
            eye_color VARCHAR(50),
            gender VARCHAR(50),
            hair_color VARCHAR(50),
            homeworld VARCHAR(255),
            mass VARCHAR(20),
            skin_color VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_characters_name ON characters(name);
        CREATE INDEX IF NOT EXISTS idx_characters_gender ON characters(gender);
        CREATE INDEX IF NOT EXISTS idx_characters_homeworld ON characters(homeworld);
        CREATE INDEX IF NOT EXISTS idx_characters_uid ON characters(uid);
        '''

        await Database.execute(init_sql)
        logger.info("Database initialized")

        count = await Database.fetchval("SELECT COUNT(*) FROM characters")
        if count == 0:
            logger.info("Adding sample data...")
            sample_data = [
                (1, "Luke Skywalker", "19BBY", "blue", "male", "blond", "https://swapi.dev/api/planets/1/", "77",
                 "fair"),
                (2, "C-3PO", "112BBY", "yellow", "n/a", "n/a", "https://swapi.dev/api/planets/1/", "75", "gold"),
                (3, "R2-D2", "33BBY", "red", "n/a", "n/a", "https://swapi.dev/api/planets/8/", "32", "white, blue"),
            ]

            for data in sample_data:
                await Database.execute(
                    "INSERT INTO characters (uid, name, birth_year, eye_color, gender, hair_color, homeworld, mass, skin_color) "
                    "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) "
                    "ON CONFLICT (uid) DO NOTHING",
                    *data
                )

    except Exception as e:
        logger.error(f"Database init error: {e}")
        raise


async def start_app():
    """Запуск приложения"""
    app = create_app()

    await init_db()

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, config.api.host, config.api.port)

    logger.info(f"Server starting on http://{config.api.host}:{config.api.port}")
    logger.info(f"API Docs: http://{config.api.host}:{config.api.port}/api/health")

    await site.start()

    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        await runner.cleanup()


async def shutdown():
    """Завершение работы"""
    logger.info("Shutting down...")
    await Database.close_pool()


def main():
    """Точка входа"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(start_app())
    except KeyboardInterrupt:
        logger.info("Stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        loop.run_until_complete(shutdown())
        loop.close()


if __name__ == '__main__':
    main()