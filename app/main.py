from aiohttp import web
import logging
from aiohttp_cors import CorsConfig, ResourceOptions, setup as setup_cors
from app.database import Database
from app.api.endpoints import (
    health_check, get_characters, get_character,
    create_character, update_character, delete_character,
    get_statistics, search_characters
)
from config import config
import asyncio
import os

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
    """Создание приложения aiohttp"""
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

    app.router.add_get('/api/health', health_check, name='health_check')

    app.router.add_get('/api/characters', get_characters, name='get_characters')
    app.router.add_get(r'/api/characters/{id:\d+}', get_character, name='get_character')
    app.router.add_post('/api/characters', create_character, name='create_character')
    app.router.add_put(r'/api/characters/{id:\d+}', update_character, name='update_character')
    app.router.add_delete(r'/api/characters/{id:\d+}', delete_character, name='delete_character')

    app.router.add_get('/api/characters/search', search_characters, name='search_characters')
    app.router.add_get('/api/statistics', get_statistics, name='get_statistics')

    app.router.add_get('/api/docs', lambda request: web.Response(
        text='''
        <html>
            <head><title>Star Wars API Documentation</title></head>
            <body>
                <h1>Star Wars API v1.0.0</h1>
                <h2>Endpoints:</h2>
                <ul>
                    <li><strong>GET /api/health</strong> - Health check</li>
                    <li><strong>GET /api/characters</strong> - Get all characters (with pagination)</li>
                    <li><strong>GET /api/characters/{id}</strong> - Get character by ID</li>
                    <li><strong>POST /api/characters</strong> - Create new character</li>
                    <li><strong>PUT /api/characters/{id}</strong> - Update character</li>
                    <li><strong>DELETE /api/characters/{id}</strong> - Delete character</li>
                    <li><strong>GET /api/characters/search?q=name</strong> - Search characters</li>
                    <li><strong>GET /api/statistics</strong> - Get statistics</li>
                </ul>
                <h2>Query Parameters:</h2>
                <ul>
                    <li><strong>page</strong> - Page number (default: 1)</li>
                    <li><strong>size</strong> - Page size (default: 10, max: 100)</li>
                    <li><strong>name</strong> - Filter by name (partial match)</li>
                    <li><strong>gender</strong> - Filter by gender</li>
                    <li><strong>homeworld</strong> - Filter by homeworld</li>
                </ul>
            </body>
        </html>
        ''',
        content_type='text/html'
    ))

    for route in list(app.router.routes()):
        cors.add(route)

    @web.middleware
    async def log_middleware(request: web.Request, handler):
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
    async def error_middleware(request: web.Request, handler):
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
        logger.info("Database initialized successfully")

        count = await Database.fetchval("SELECT COUNT(*) FROM characters")
        if count == 0:
            logger.info("Adding sample data...")
            sample_characters = [
                (1, "Luke Skywalker", "19BBY", "blue", "male", "blond", "https://www.swapi.tech/api/planets/1", "77",
                 "fair"),
                (2, "C-3PO", "112BBY", "yellow", "n/a", "n/a", "https://www.swapi.tech/api/planets/1", "75", "gold"),
                (3, "R2-D2", "33BBY", "red", "n/a", "n/a", "https://www.swapi.tech/api/planets/8", "32", "white, blue"),
                (4, "Darth Vader", "41.9BBY", "yellow", "male", "none", "https://www.swapi.tech/api/planets/1", "136",
                 "white"),
                (5, "Leia Organa", "19BBY", "brown", "female", "brown", "https://www.swapi.tech/api/planets/2", "49",
                 "light")
            ]

            for uid, name, birth_year, eye_color, gender, hair_color, homeworld, mass, skin_color in sample_characters:
                await Database.execute(
                    "INSERT INTO characters (uid, name, birth_year, eye_color, gender, hair_color, homeworld, mass, skin_color) "
                    "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) "
                    "ON CONFLICT (uid) DO NOTHING",
                    uid, name, birth_year, eye_color, gender, hair_color, homeworld, mass, skin_color
                )

            logger.info(f"Added {len(sample_characters)} sample characters")

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def start_app():
    """Запуск приложения"""
    app = create_app()

    await init_db()

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, config.api.host, config.api.port)

    logger.info(f"Starting server on http://{config.api.host}:{config.api.port}")
    logger.info(f"API Documentation: http://{config.api.host}:{config.api.port}/api/docs")

    await site.start()

    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        pass


async def shutdown():
    """Завершение работы приложения"""
    logger.info("Shutting down...")
    await Database.close_pool()
    logger.info("Shutdown complete")


def main():
    """Точка входа в приложение"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(start_app())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed: {e}")
    finally:
        loop.run_until_complete(shutdown())
        loop.close()


if __name__ == '__main__':
    main()