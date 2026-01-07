import sqlite3
import aiosqlite
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)
_db = None


async def init_db(app=None):
    """Initialize database connection and create tables"""
    global _db

    try:
        _db = await aiosqlite.connect("ads.db")
        await _db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                username TEXT NOT NULL,
                hashed_password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await _db.execute("""
            CREATE TABLE IF NOT EXISTS ads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                owner_id INTEGER NOT NULL,
                FOREIGN KEY (owner_id) REFERENCES users (id)
            )
        """)

        await _db.execute("CREATE INDEX IF NOT EXISTS idx_ads_owner ON ads(owner_id)")
        await _db.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")

        await _db.commit()
        logger.info("<Database initialized successfully>")
        await create_test_user()

    except Exception as e:
        logger.error(f"<Database initialization failed: {e}>")
        raise


async def create_test_user():
    """Create a test user if doesn't exist (for testing)"""
    try:
        from .security import get_password_hash

        test_email = "test@example.com"
        existing_user = await get_user_by_email(test_email)

        if not existing_user:
            user_data = {
                'email': test_email,
                'username': 'testuser',
                'hashed_password': get_password_hash('testpassword'),
                'created_at': datetime.utcnow()
            }

            cursor = await _db.execute(
                """INSERT INTO users (email, username, hashed_password, created_at) 
                   VALUES (?, ?, ?, ?)""",
                (user_data['email'], user_data['username'],
                 user_data['hashed_password'], user_data['created_at'])
            )
            await _db.commit()
            user_id = cursor.lastrowid
            await cursor.close()

            logger.info(f"<Test user created with ID: {user_id}>")
            ad_data = {
                'title': 'Test Ad',
                'description': 'This is a test advertisement',
                'owner_id': user_id,
                'created_at': datetime.utcnow()
            }

            await create_ad(ad_data)
            logger.info("<Test ad created>")

    except Exception as e:
        logger.warning(f"<Could not create test user: {e}>")


async def close_db(app=None):
    """Close database connection"""
    global _db
    if _db:
        await _db.close()
        _db = None
        logger.info("<Database connection closed>")

async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email"""
    if not _db:
        raise RuntimeError("Database not initialized")

    cursor = await _db.execute(
        "SELECT id, email, username, hashed_password, created_at FROM users WHERE email = ?",
        (email,)
    )
    row = await cursor.fetchone()
    await cursor.close()

    if row:
        return {
            "id": row[0],
            "email": row[1],
            "username": row[2],
            "hashed_password": row[3],
            "created_at": row[4]
        }
    return None


async def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user by ID"""
    if not _db:
        raise RuntimeError("Database not initialized")

    cursor = await _db.execute(
        "SELECT id, email, username, hashed_password, created_at FROM users WHERE id = ?",
        (user_id,)
    )
    row = await cursor.fetchone()
    await cursor.close()

    if row:
        return {
            "id": row[0],
            "email": row[1],
            "username": row[2],
            "hashed_password": row[3],
            "created_at": row[4]
        }
    return None


async def create_user(user_data: Dict[str, Any]) -> int:
    """Create a new user"""
    if not _db:
        raise RuntimeError("Database not initialized")

    cursor = await _db.execute(
        """INSERT INTO users (email, username, hashed_password, created_at) 
           VALUES (?, ?, ?, ?)""",
        (user_data['email'], user_data['username'],
         user_data['hashed_password'], user_data.get('created_at', datetime.utcnow()))
    )
    await _db.commit()
    user_id = cursor.lastrowid
    await cursor.close()

    return user_id

async def create_ad(ad_data: Dict[str, Any]) -> int:
    """Create a new ad"""
    if not _db:
        raise RuntimeError("Database not initialized")

    cursor = await _db.execute(
        """INSERT INTO ads (title, description, created_at, owner_id) 
           VALUES (?, ?, ?, ?)""",
        (ad_data['title'], ad_data.get('description', ''),
         ad_data.get('created_at', datetime.utcnow()), ad_data['owner_id'])
    )
    await _db.commit()
    ad_id = cursor.lastrowid
    await cursor.close()

    return ad_id


async def get_ad(ad_id: int) -> Optional[Dict[str, Any]]:
    """Get ad by ID"""
    if not _db:
        raise RuntimeError("Database not initialized")

    cursor = await _db.execute(
        "SELECT id, title, description, created_at, owner_id FROM ads WHERE id = ?",
        (ad_id,)
    )
    row = await cursor.fetchone()
    await cursor.close()

    if row:
        return {
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "created_at": row[3],
            "owner_id": row[4]
        }
    return None


async def get_all_ads() -> List[Dict[str, Any]]:
    """Get all ads"""
    if not _db:
        raise RuntimeError("Database not initialized")

    cursor = await _db.execute(
        "SELECT id, title, description, created_at, owner_id FROM ads ORDER BY created_at DESC"
    )
    rows = await cursor.fetchall()
    await cursor.close()

    return [
        {
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "created_at": row[3],
            "owner_id": row[4]
        }
        for row in rows
    ]


async def update_ad(ad_id: int, update_data: Dict[str, Any]) -> None:
    """Update ad"""
    if not _db:
        raise RuntimeError("Database not initialized")

    set_clauses = []
    params = []

    for key, value in update_data.items():
        set_clauses.append(f"{key} = ?")
        params.append(value)

    params.append(ad_id)

    query = f"UPDATE ads SET {', '.join(set_clauses)} WHERE id = ?"
    await _db.execute(query, params)
    await _db.commit()


async def delete_ad(ad_id: int) -> None:
    """Delete ad"""
    if not _db:
        raise RuntimeError("Database not initialized")

    await _db.execute("DELETE FROM ads WHERE id = ?", (ad_id,))
    await _db.commit()