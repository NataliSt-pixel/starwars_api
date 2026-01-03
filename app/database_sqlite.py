import aiosqlite
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class DatabaseSQLite:
    """Класс для работы с SQLite базой данных"""

    _db_path: Path = Path("starwars_api.db")
    _conn: Optional[aiosqlite.Connection] = None

    @classmethod
    async def get_connection(cls) -> aiosqlite.Connection:
        """Получить подключение к SQLite"""
        if cls._conn is None:
            cls._conn = await aiosqlite.connect(cls._db_path)
            cls._conn.row_factory = aiosqlite.Row
            logger.info(f"SQLite database connected: {cls._db_path}")
        return cls._conn

    @classmethod
    async def close_connection(cls) -> None:
        """Закрыть подключение"""
        if cls._conn:
            await cls._conn.close()
            cls._conn = None

    @classmethod
    async def execute(cls, query: str, *args) -> None:
        """Выполнить запрос"""
        conn = await cls.get_connection()
        await conn.execute(query, args)
        await conn.commit()

    @classmethod
    async def fetch(cls, query: str, *args) -> List[Dict[str, Any]]:
        """Выполнить запрос с возвратом нескольких строк"""
        conn = await cls.get_connection()
        cursor = await conn.execute(query, args)
        rows = await cursor.fetchall()
        await cursor.close()
        return [dict(row) for row in rows]

    @classmethod
    async def fetchrow(cls, query: str, *args) -> Optional[Dict[str, Any]]:
        """Выполнить запрос с возвратом одной строки"""
        conn = await cls.get_connection()
        cursor = await conn.execute(query, args)
        row = await cursor.fetchone()
        await cursor.close()
        return dict(row) if row else None

    @classmethod
    async def fetchval(cls, query: str, *args) -> Optional[Any]:
        """Выполнить запрос с возвратом одного значения"""
        conn = await cls.get_connection()
        cursor = await conn.execute(query, args)
        row = await cursor.fetchone()
        await cursor.close()
        return row[0] if row else None

Database = DatabaseSQLite