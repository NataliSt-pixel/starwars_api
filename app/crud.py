"""
CRUD операции для пользователей и объявлений
"""
import logging
from typing import Optional, List
from app.database import Database
from app.models import User, Advertisement
from app.security import get_password_hash, verify_password

logger = logging.getLogger(__name__)


class UserCRUD:
    """CRUD операции для пользователей"""

    @staticmethod
    async def get_by_id(user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        row = await Database.fetchrow(
            "SELECT * FROM users WHERE id = $1",
            user_id
        )
        return User.from_dict(row) if row else None

    @staticmethod
    async def get_by_username(username: str) -> Optional[User]:
        """Получить пользователя по имени"""
        row = await Database.fetchrow(
            "SELECT * FROM users WHERE username = $1",
            username
        )
        return User.from_dict(row) if row else None

    @staticmethod
    async def get_by_email(email: str) -> Optional[User]:
        """Получить пользователя по email"""
        row = await Database.fetchrow(
            "SELECT * FROM users WHERE email = $1",
            email
        )
        return User.from_dict(row) if row else None

    @staticmethod
    async def create(user_data: dict) -> User:
        """Создать нового пользователя"""
        password_hash = get_password_hash(user_data["password"])

        row = await Database.fetchrow(
            """
            INSERT INTO users (username, email, password_hash)
            VALUES ($1, $2, $3)
            RETURNING *
            """,
            user_data["username"],
            user_data["email"],
            password_hash
        )

        return User.from_dict(row)

    @staticmethod
    async def update(user_id: int, user_data: dict) -> Optional[User]:
        """Обновить пользователя"""
        update_fields = []
        values = []
        i = 1

        if "username" in user_data:
            update_fields.append(f"username = ${i}")
            values.append(user_data["username"])
            i += 1

        if "email" in user_data:
            update_fields.append(f"email = ${i}")
            values.append(user_data["email"])
            i += 1

        if "password" in user_data:
            update_fields.append(f"password_hash = ${i}")
            values.append(get_password_hash(user_data["password"]))
            i += 1

        if not update_fields:
            return await UserCRUD.get_by_id(user_id)

        update_fields.append(f"updated_at = CURRENT_TIMESTAMP")
        values.append(user_id)

        query = f"""
        UPDATE users 
        SET {', '.join(update_fields)}
        WHERE id = ${i}
        RETURNING *
        """

        row = await Database.fetchrow(query, *values)
        return User.from_dict(row) if row else None

    @staticmethod
    async def authenticate(username: str, password: str) -> Optional[User]:
        """Аутентификация пользователя"""
        user = await UserCRUD.get_by_username(username)
        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user

    @staticmethod
    async def get_all(limit: int = 100, offset: int = 0) -> List[User]:
        """Получить всех пользователей (для админки)"""
        rows = await Database.fetch(
            "SELECT * FROM users ORDER BY id LIMIT $1 OFFSET $2",
            limit, offset
        )
        return [User.from_dict(row) for row in rows]

    @staticmethod
    async def count() -> int:
        """Посчитать количество пользователей"""
        count = await Database.fetchval("SELECT COUNT(*) FROM users")
        return count if count else 0


class AdvertisementCRUD:
    """CRUD операции для объявлений"""

    @staticmethod
    async def get_all(
            skip: int = 0,
            limit: int = 100,
            user_id: Optional[int] = None,
            search: Optional[str] = None
    ) -> List[Advertisement]:
        """Получить все объявления"""
        query = """
        SELECT a.*, u.id as u_id, u.username, u.email, u.created_at as u_created_at, u.updated_at as u_updated_at
        FROM advertisements a
        LEFT JOIN users u ON a.user_id = u.id
        WHERE 1=1
        """

        params = []
        i = 1

        if user_id:
            query += f" AND a.user_id = ${i}"
            params.append(user_id)
            i += 1

        if search:
            query += f" AND (a.title ILIKE ${i} OR a.description ILIKE ${i})"
            params.append(f"%{search}%")
            i += 1

        query += f" ORDER BY a.created_at DESC LIMIT ${i} OFFSET ${i + 1}"
        params.extend([limit, skip])

        rows = await Database.fetch(query, *params)

        advertisements = []
        for row in rows:
            user_data = {
                'id': row['u_id'],
                'username': row['username'],
                'email': row['email'],
                'created_at': row['u_created_at'],
                'updated_at': row['u_updated_at']
            } if row['u_id'] else None

            ad_data = dict(row)
            ad_data['user'] = user_data
            advertisements.append(Advertisement.from_dict(ad_data))

        return advertisements

    @staticmethod
    async def get_by_id(ad_id: int) -> Optional[Advertisement]:
        """Получить объявление по ID"""
        row = await Database.fetchrow(
            """
            SELECT a.*, u.id as u_id, u.username, u.email, u.created_at as u_created_at, u.updated_at as u_updated_at
            FROM advertisements a
            LEFT JOIN users u ON a.user_id = u.id
            WHERE a.id = $1
            """,
            ad_id
        )

        if not row:
            return None

        user_data = {
            'id': row['u_id'],
            'username': row['username'],
            'email': row['email'],
            'created_at': row['u_created_at'],
            'updated_at': row['u_updated_at']
        } if row['u_id'] else None

        ad_data = dict(row)
        ad_data['user'] = user_data

        return Advertisement.from_dict(ad_data)

    @staticmethod
    async def create(ad_data: dict, user_id: int) -> Advertisement:
        """Создать новое объявление"""
        row = await Database.fetchrow(
            """
            INSERT INTO advertisements (title, description, user_id)
            VALUES ($1, $2, $3)
            RETURNING *
            """,
            ad_data["title"],
            ad_data["description"],
            user_id
        )

        return await AdvertisementCRUD.get_by_id(row['id'])

    @staticmethod
    async def update(ad_id: int, ad_data: dict, user_id: int) -> Optional[Advertisement]:
        """Обновить объявление (только автор)"""
        ad = await AdvertisementCRUD.get_by_id(ad_id)
        if not ad or ad.user_id != user_id:
            return None

        update_fields = []
        values = []
        i = 1

        if "title" in ad_data:
            update_fields.append(f"title = ${i}")
            values.append(ad_data["title"])
            i += 1

        if "description" in ad_data:
            update_fields.append(f"description = ${i}")
            values.append(ad_data["description"])
            i += 1

        if not update_fields:
            return ad

        update_fields.append(f"updated_at = CURRENT_TIMESTAMP")

        values.extend([ad_id, user_id])

        query = f"""
        UPDATE advertisements 
        SET {', '.join(update_fields)}
        WHERE id = ${i} AND user_id = ${i + 1}
        RETURNING *
        """

        row = await Database.fetchrow(query, *values)
        if row:
            return await AdvertisementCRUD.get_by_id(ad_id)

        return None

    @staticmethod
    async def delete(ad_id: int, user_id: int) -> bool:
        """Удалить объявление (только автор)"""
        result = await Database.execute(
            "DELETE FROM advertisements WHERE id = $1 AND user_id = $2",
            ad_id, user_id
        )
        return "DELETE 1" in result

    @staticmethod
    async def count(
            user_id: Optional[int] = None,
            search: Optional[str] = None
    ) -> int:
        """Посчитать количество объявлений"""
        query = "SELECT COUNT(*) FROM advertisements WHERE 1=1"
        params = []
        i = 1

        if user_id:
            query += f" AND user_id = ${i}"
            params.append(user_id)
            i += 1

        if search:
            query += f" AND (title ILIKE ${i} OR description ILIKE ${i})"
            params.append(f"%{search}%")

        count = await Database.fetchval(query, *params)
        return count if count else 0