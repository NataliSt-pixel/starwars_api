from typing import Optional, List, Dict, Any
from datetime import datetime
from app.database import Database
from app.models import Character
from app.schemas import CharacterCreate, CharacterUpdate
import logging

logger = logging.getLogger(__name__)


class CharacterCRUD:
    """CRUD операции для персонажей"""

    @staticmethod
    async def get_all(
            skip: int = 0,
            limit: int = 100,
            filters: Optional[Dict[str, Any]] = None
    ) -> List[Character]:
        """Получить всех персонажей с пагинацией и фильтрацией"""
        query = "SELECT * FROM characters WHERE 1=1"
        params = []

        if filters:
            if filters.get('name'):
                query += " AND name ILIKE $1"
                params.append(f"%{filters['name']}%")
            if filters.get('gender'):
                query += " AND gender = $2"
                params.append(filters['gender'])
            if filters.get('homeworld'):
                query += " AND homeworld LIKE $3"
                params.append(f"%{filters['homeworld']}%")

        query += " ORDER BY id LIMIT $4 OFFSET $5"
        params.extend([limit, skip])

        rows = await Database.fetch(query, *params)
        return [Character.from_dict(dict(row)) for row in rows]

    @staticmethod
    async def get_by_id(character_id: int) -> Optional[Character]:
        """Получить персонажа по ID"""
        row = await Database.fetchrow(
            "SELECT * FROM characters WHERE id = $1",
            character_id
        )
        return Character.from_dict(dict(row)) if row else None

    @staticmethod
    async def get_by_uid(uid: int) -> Optional[Character]:
        """Получить персонажа по UID (из SWAPI)"""
        row = await Database.fetchrow(
            "SELECT * FROM characters WHERE uid = $1",
            uid
        )
        return Character.from_dict(dict(row)) if row else None

    @staticmethod
    async def create(character: CharacterCreate) -> Character:
        """Создать нового персонажа"""
        now = datetime.utcnow()
        query = """
        INSERT INTO characters 
        (uid, name, birth_year, eye_color, gender, hair_color, homeworld, mass, skin_color, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        RETURNING *
        """

        row = await Database.fetchrow(
            query,
            character.uid,
            character.name,
            character.birth_year,
            character.eye_color,
            character.gender,
            character.hair_color,
            character.homeworld,
            character.mass,
            character.skin_color,
            now
        )

        return Character.from_dict(dict(row))

    @staticmethod
    async def update(character_id: int, character: CharacterUpdate) -> Optional[Character]:
        """Обновить существующего персонажа"""
        current = await CharacterCRUD.get_by_id(character_id)
        if not current:
            return None

        update_data = character.dict(exclude_unset=True)
        if not update_data:
            return current

        update_data['updated_at'] = datetime.utcnow()

        set_clause = ", ".join([f"{key} = ${i + 2}" for i, key in enumerate(update_data.keys())])
        query = f"UPDATE characters SET {set_clause}, updated_at = ${len(update_data) + 2} WHERE id = $1 RETURNING *"

        params = [character_id] + list(update_data.values()) + [update_data['updated_at']]
        row = await Database.fetchrow(query, *params)

        return Character.from_dict(dict(row)) if row else None

    @staticmethod
    async def delete(character_id: int) -> bool:
        """Удалить персонажа"""
        result = await Database.execute(
            "DELETE FROM characters WHERE id = $1",
            character_id
        )
        return "DELETE 1" in result

    @staticmethod
    async def count(filters: Optional[Dict[str, Any]] = None) -> int:
        """Посчитать общее количество персонажей"""
        query = "SELECT COUNT(*) FROM characters WHERE 1=1"
        params = []

        if filters:
            if filters.get('name'):
                query += " AND name ILIKE $1"
                params.append(f"%{filters['name']}%")
            if filters.get('gender'):
                query += " AND gender = $2"
                params.append(filters['gender'])

        count = await Database.fetchval(query, *params)
        return count if count else 0

    @staticmethod
    async def get_statistics() -> Dict[str, Any]:
        """Получить статистику по персонажам"""
        stats = {}

        stats['total'] = await CharacterCRUD.count()

        gender_stats = await Database.fetch("""
            SELECT gender, COUNT(*) as count 
            FROM characters 
            GROUP BY gender 
            ORDER BY count DESC
        """)
        stats['by_gender'] = {row['gender'] or 'unknown': row['count'] for row in gender_stats}
        planet_stats = await Database.fetch("""
            SELECT 
                CASE 
                    WHEN homeworld LIKE '%planets/%' THEN 
                        SUBSTRING(homeworld FROM 'planets/(\d+)')
                    ELSE 'unknown'
                END as planet_id,
                COUNT(*) as count
            FROM characters 
            GROUP BY planet_id 
            ORDER BY count DESC 
            LIMIT 5
        """)
        stats['top_planets'] = {row['planet_id']: row['count'] for row in planet_stats}

        return stats