from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.models import Character


class CharacterService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_character(self, character_id: int) -> Character:
        character = await self.db.get(Character, character_id)
        if not character:
            raise NotFoundError("角色")
        return character

    async def get_character_by_key(self, script_id: int, character_key: str) -> Character:
        stmt = select(Character).where(
            Character.script_id == script_id,
            Character.character_key == character_key,
        )
        result = await self.db.execute(stmt)
        character = result.scalar_one_or_none()
        if not character:
            raise NotFoundError("角色")
        return character

    async def get_relationships(self, character_id: int) -> dict:
        character = await self.get_character(character_id)
        relationships_data = character.relationships or {}
        relationships = []

        for rel in relationships_data.get("relations", []):
            target_key = rel.get("target_key")
            if target_key:
                stmt = select(Character).where(
                    Character.script_id == character.script_id,
                    Character.character_key == target_key,
                )
                result = await self.db.execute(stmt)
                target = result.scalar_one_or_none()

                if target:
                    relationships.append({
                        "target_id": target.id,
                        "target_name": target.name,
                        "target_key": target.character_key,
                        "relation_type": rel.get("type", "neutral"),
                        "description": rel.get("description", ""),
                        "attitude": rel.get("attitude", "neutral"),
                        "intensity": rel.get("intensity", 50),
                    })

        return {
            "character_id": character.id,
            "character_name": character.name,
            "relationships": relationships,
        }

    async def list_script_characters(self, script_id: int) -> list[Character]:
        stmt = (
            select(Character)
            .where(Character.script_id == script_id)
            .order_by(Character.sort_order)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
