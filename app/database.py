import asyncpg
from typing import Optional, List, Dict, Any
import logging
import os
from dotenv import load_dotenv

load_dotenv()

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
                    host=os.getenv("DB_HOST", "localhost"),
                    port=int(os.getenv("DB_PORT", 5432)),
                    database=os.getenv("DB_NAME", "advertisements_db"),
                    user=os.getenv("DB_USER", "postgres"),
                    password=os.getenv("DB_PASSWORD", ""),
                    min_size=5,
                    max_size=20,
                    command_timeout=60
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
    async def fetch(cls, query: str, *args) -> List[Dict[str, Any]]:
        """Выполнить запрос с возвратом нескольких строк"""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]

    @classmethod
    async def fetchrow(cls, query: str, *args) -> Optional[Dict[str, Any]]:
        """Выполнить запрос с возвратом одной строки"""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None

    @classmethod
    async def fetchval(cls, query: str, *args) -> Optional[Any]:
        """Выполнить запрос с возвратом одного значения"""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            return await conn.fetchval(query, *args)