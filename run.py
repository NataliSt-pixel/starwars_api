"""
Простой запуск Star Wars API
"""
import asyncio
import logging
from aiohttp import web
import aiosqlite
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8000))
DB_PATH = os.getenv('DB_PATH', 'starwars.db')


class Database:
    """Простой класс для работы с SQLite"""

    @staticmethod
    async def init_db():
        """Инициализация базы данных"""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            await db.execute('''
            CREATE TABLE IF NOT EXISTS characters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid INTEGER UNIQUE NOT NULL,
                name TEXT NOT NULL,
                birth_year TEXT,
                eye_color TEXT,
                gender TEXT,
                hair_color TEXT,
                homeworld TEXT,
                mass TEXT,
                skin_color TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            )
            ''')


            await db.execute('CREATE INDEX IF NOT EXISTS idx_name ON characters(name)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_gender ON characters(gender)')

            await db.commit()
            logger.info(f"Database initialized: {DB_PATH}")
            cursor = await db.execute('SELECT COUNT(*) FROM characters')
            count = (await cursor.fetchone())[0]

            if count == 0:
                logger.info("Adding sample data...")
                sample_data = [
                    (1, 'Luke Skywalker', '19BBY', 'blue', 'male', 'blond', 'https://swapi.dev/api/planets/1/', '77',
                     'fair'),
                    (2, 'C-3PO', '112BBY', 'yellow', 'n/a', 'n/a', 'https://swapi.dev/api/planets/1/', '75', 'gold'),
                    (3, 'R2-D2', '33BBY', 'red', 'n/a', 'n/a', 'https://swapi.dev/api/planets/8/', '32', 'white, blue'),
                    (4, 'Darth Vader', '41.9BBY', 'yellow', 'male', 'none', 'https://swapi.dev/api/planets/1/', '136',
                     'white'),
                    (5, 'Leia Organa', '19BBY', 'brown', 'female', 'brown', 'https://swapi.dev/api/planets/2/', '49',
                     'light'),
                ]

                for data in sample_data:
                    await db.execute('''
                    INSERT OR IGNORE INTO characters 
                    (uid, name, birth_year, eye_color, gender, hair_color, homeworld, mass, skin_color)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', data)

                await db.commit()
                logger.info(f"Added {len(sample_data)} sample characters")


class Character:
    """Модель персонажа"""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self):
        """Преобразование в словарь"""
        result = {}
        for key, value in self.__dict__.items():
            if not key.startswith('_'):
                if isinstance(value, bytes):
                    result[key] = value.decode('utf-8')
                else:
                    result[key] = value
        return result


class CharacterCRUD:
    """CRUD операции для персонажей"""

    @staticmethod
    async def get_all(limit: int = 10, offset: int = 0):
        """Получить всех персонажей"""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                'SELECT * FROM characters LIMIT ? OFFSET ?',
                (limit, offset)
            )
            rows = await cursor.fetchall()
            return [Character(**dict(row)) for row in rows]

    @staticmethod
    async def get_by_id(char_id: int):
        """Получить персонажа по ID"""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                'SELECT * FROM characters WHERE id = ?',
                (char_id,)
            )
            row = await cursor.fetchone()
            return Character(**dict(row)) if row else None

    @staticmethod
    async def create(character_data: dict):
        """Создать нового персонажа"""
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute('''
            INSERT INTO characters 
            (uid, name, birth_year, eye_color, gender, hair_color, homeworld, mass, skin_color)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                character_data.get('uid'),
                character_data.get('name'),
                character_data.get('birth_year'),
                character_data.get('eye_color'),
                character_data.get('gender'),
                character_data.get('hair_color'),
                character_data.get('homeworld'),
                character_data.get('mass'),
                character_data.get('skin_color')
            ))
            await db.commit()

            char_id = cursor.lastrowid
            return await CharacterCRUD.get_by_id(char_id)

    @staticmethod
    async def count():
        """Получить количество персонажей"""
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute('SELECT COUNT(*) FROM characters')
            result = await cursor.fetchone()
            return result[0] if result else 0


async def health_check(request):
    """Проверка здоровья API"""
    return web.json_response({
        'status': 'ok',
        'service': 'Star Wars API',
        'version': '1.0.0',
        'endpoints': {
            'GET /api/health': 'Health check',
            'GET /api/characters': 'List all characters',
            'GET /api/characters/{id}': 'Get character by ID',
            'POST /api/characters': 'Create new character',
            'GET /api/characters/search?q={query}': 'Search characters',
            'GET /api/statistics': 'Get statistics'
        }
    })


async def get_characters(request):
    """Получить список персонажей"""
    try:
        try:
            limit = min(int(request.query.get('limit', 10)), 100)  # Максимум 100
            page = max(int(request.query.get('page', 1)), 1)
        except ValueError:
            limit = 10
            page = 1

        offset = (page - 1) * limit

        characters = await CharacterCRUD.get_all(limit=limit, offset=offset)
        total = await CharacterCRUD.count()

        return web.json_response({
            'items': [char.to_dict() for char in characters],
            'total': total,
            'page': page,
            'limit': limit,
            'pages': (total + limit - 1) // limit if limit > 0 else 0
        })

    except Exception as e:
        logger.error(f"Error getting characters: {e}")
        return web.json_response(
            {'error': 'Internal server error', 'detail': str(e)},
            status=500
        )


async def get_character(request):
    """Получить персонажа по ID"""
    try:
        char_id = int(request.match_info['id'])
        character = await CharacterCRUD.get_by_id(char_id)

        if not character:
            return web.json_response(
                {'error': 'Character not found'},
                status=404
            )

        return web.json_response(character.to_dict())

    except ValueError:
        return web.json_response(
            {'error': 'Invalid character ID'},
            status=400
        )
    except Exception as e:
        logger.error(f"Error getting character: {e}")
        return web.json_response(
            {'error': 'Internal server error', 'detail': str(e)},
            status=500
        )


async def create_character(request):
    """Создать нового персонажа"""
    try:
        data = await request.json()

        if not data.get('name') or not data.get('name').strip():
            return web.json_response(
                {'error': 'Name is required'},
                status=400
            )

        if not data.get('uid'):
            return web.json_response(
                {'error': 'UID is required'},
                status=400
            )

        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                'SELECT id FROM characters WHERE uid = ?',
                (data.get('uid'),)
            )
            existing = await cursor.fetchone()
            if existing:
                return web.json_response(
                    {'error': 'Character with this UID already exists'},
                    status=409
                )

        character = await CharacterCRUD.create(data)

        return web.json_response(
            character.to_dict(),
            status=201
        )

    except Exception as e:
        logger.error(f"Error creating character: {e}")
        return web.json_response(
            {'error': 'Internal server error', 'detail': str(e)},
            status=500
        )


async def search_characters(request):
    """Поиск персонажей по имени"""
    try:
        query = request.query.get('q', '').strip()
        if not query:
            return web.json_response(
                {'error': 'Search query is required'},
                status=400
            )

        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                'SELECT * FROM characters WHERE LOWER(name) LIKE ? LIMIT 20',
                (f'%{query.lower()}%',)
            )
            rows = await cursor.fetchall()
            characters = [Character(**dict(row)) for row in rows]

        return web.json_response({
            'results': [char.to_dict() for char in characters],
            'count': len(characters)
        })

    except Exception as e:
        logger.error(f"Error searching characters: {e}")
        return web.json_response(
            {'error': 'Internal server error', 'detail': str(e)},
            status=500
        )


async def get_statistics(request):
    """Получить статистику"""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT COUNT(*) FROM characters')
            total = (await cursor.fetchone())[0]

            cursor = await db.execute('''
                SELECT gender, COUNT(*) as count 
                FROM characters 
                GROUP BY gender 
                ORDER BY count DESC
            ''')

            gender_stats = {}
            rows = await cursor.fetchall()
            for row in rows:
                gender = row['gender'] if row['gender'] else 'unknown'
                gender_stats[gender] = row['count']

        return web.json_response({
            'total': total,
            'by_gender': gender_stats
        })

    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return web.json_response(
            {'error': 'Internal server error', 'detail': str(e)},
            status=500
        )


def create_app():
    """Создание приложения"""
    app = web.Application()

    app.router.add_get('/api/health', health_check)
    app.router.add_get('/api/characters', get_characters)
    app.router.add_get(r'/api/characters/{id:\d+}', get_character)
    app.router.add_post('/api/characters', create_character)
    app.router.add_get('/api/characters/search', search_characters)
    app.router.add_get('/api/statistics', get_statistics)

    @web.middleware
    async def cors_middleware(request, handler):
        if request.method == 'OPTIONS':
            response = web.Response()
        else:
            response = await handler(request)

        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    app.middlewares.append(cors_middleware)

    async def options_handler(request):
        return web.Response()

    app.router.add_route('OPTIONS', '/api/{tail:.*}', options_handler)

    @web.middleware
    async def log_middleware(request, handler):
        logger.info(f"{request.method} {request.path}")
        try:
            response = await handler(request)
            logger.info(f"{request.method} {request.path} - {response.status}")
            return response
        except Exception as e:
            logger.error(f"Error in {request.method} {request.path}: {e}")
            raise

    app.middlewares.append(log_middleware)

    return app


async def start_server():
    """Запуск сервера"""
    await Database.init_db()

    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, HOST, PORT)

    logger.info(f" Star Wars API запущен!")
    logger.info(f" Адрес: http://{HOST}:{PORT}")
    logger.info(f" Доступные эндпоинты:")
    logger.info(f"   GET  /api/health                - Проверка здоровья")
    logger.info(f"   GET  /api/characters            - Список персонажей")
    logger.info(f"   GET  /api/characters/{{id}}       - Персонаж по ID")
    logger.info(f"   POST /api/characters            - Создать персонажа")
    logger.info(f"   GET  /api/characters/search?q=  - Поиск персонажей")
    logger.info(f"   GET  /api/statistics            - Статистика")
    logger.info("")
    logger.info(" Примеры запросов:")
    logger.info("   curl http://localhost:8000/api/characters")
    logger.info("   curl http://localhost:8000/api/characters/1")
    logger.info(
        "   curl -X POST http://localhost:8000/api/characters -H 'Content-Type: application/json' -d '{\"uid\": 100, \"name\": \"Yoda\"}'")

    await site.start()

    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Сервер остановлен пользователем")
    finally:
        await runner.cleanup()


def main():
    """Точка входа"""
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        logger.info("Сервер остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка при запуске сервера: {e}")
    finally:
        logger.info("Сервер завершил работу")


if __name__ == '__main__':
    main()