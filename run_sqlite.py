"""
Упрощенный запуск с SQLite для тестирования
"""
import asyncio
import aiosqlite
from aiohttp import web
import logging
import json
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "advertisements.db"


async def init_db():
    """Инициализация SQLite базы данных"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
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

        await db.commit()
        logger.info(f"SQLite database initialized: {DB_PATH}")


async def health_check(request):
    return web.json_response({"status": "ok"})


async def get_ads(request):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM advertisements LIMIT 10")
        rows = await cursor.fetchall()

        ads = [dict(row) for row in rows]
        return web.json_response({"ads": ads})


def create_app():
    app = web.Application()

    app.router.add_get('/api/health', health_check)
    app.router.add_get('/api/ads', get_ads)

    return app


async def main():
    await init_db()

    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, 'localhost', 8000)

    logger.info("Server starting on http://localhost:8000")
    await site.start()

    await asyncio.Event().wait()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped")