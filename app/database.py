import asyncpg
from typing import Optional
import logging
from config import config

logger = logging.getLogger(__name__)


class Database:
    """Класс для управления подключением к базе данных"""

    _pool: Optional[asyncpg.Pool] = None

    @classmethod
    async def get_pool(cls) -> asyncpg.Pool:
        """Получаем или создаем пул подключений"""
        if cls._pool is None:
            try:
                cls._pool = await asyncpg.create_pool(
                    dsn=config.db.async_url.replace("postgresql+asyncpg://", ""),
                    min_size=5,
                    max_size=20,
                    command_timeout=60,
                    server_settings={"application_name": "starwars_api"}
                )
                logger.info("Database connection pool created")
            except Exception as e:
                logger.error(f"Failed to create database pool: {e}")
                raise
        return cls._pool

    @classmethod
    async def close_pool(cls) -> None:
        """Закрываем пул подключений"""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
            logger.info("Database connection pool closed")

    @classmethod
    async def execute(cls, query: str, *args) -> str:
        """Выполнить запрос без возврата результата"""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            return await conn.execute(query, *args)

    @classmethod
    async def fetch(cls, query: str, *args) -> list:
        """Выполнить запрос с возвратом нескольких строк"""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            return await conn.fetch(query, *args)

    @classmethod
    async def fetchrow(cls, query: str, *args) -> Optional[dict]:
        """Выполнить запрос с возвратом одной строки"""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    @classmethod
    async def fetchval(cls, query: str, *args) -> Optional[any]:
        """Выполнить запрос с возвратом одного значения"""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            return await conn.fetchval(query, *args)