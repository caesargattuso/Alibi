"""Migrate existing local files to MinIO storage and update database URLs."""
import asyncio
from pathlib import Path

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.models import Script, Scene, Character
from app.services.storage import get_storage
from app.core.config import settings


async def migrate():
    storage = get_storage()
    upload_dir = Path(settings.UPLOAD_DIR)

    async with AsyncSessionLocal() as db:
        # Migrate script covers
        result = await db.execute(select(Script))
        for script in result.scalars():
            if script.cover_image and script.cover_image.startswith("/uploads/"):
                local_path = upload_dir / script.cover_image[len("/uploads/"):]
                if local_path.exists():
                    content = local_path.read_bytes()
                    ext = local_path.suffix
                    new_path = f"scripts/{script.id}/cover{ext}"
                    new_url = await storage.save(new_path, content, "image/png")
                    script.cover_image = new_url
                    print(f"Cover: {script.cover_image} -> {new_url}")

            if script.banner_image and script.banner_image.startswith("/uploads/"):
                local_path = upload_dir / script.banner_image[len("/uploads/"):]
                if local_path.exists():
                    content = local_path.read_bytes()
                    ext = local_path.suffix
                    new_path = f"scripts/{script.id}/banner{ext}"
                    new_url = await storage.save(new_path, content, "image/png")
                    script.banner_image = new_url
                    print(f"Banner: {script.banner_image} -> {new_url}")

        # Migrate scene backgrounds
        result = await db.execute(select(Scene))
        for scene in result.scalars():
            if scene.background_image and scene.background_image.startswith("/uploads/"):
                local_path = upload_dir / scene.background_image[len("/uploads/"):]
                if local_path.exists():
                    content = local_path.read_bytes()
                    ext = local_path.suffix
                    new_path = f"scripts/{scene.script_id}/scenes/{scene.scene_key}/bg{ext}"
                    new_url = await storage.save(new_path, content, "image/png")
                    scene.background_image = new_url
                    print(f"Scene bg: {scene.background_image} -> {new_url}")

        # Migrate character avatars
        result = await db.execute(select(Character))
        for char in result.scalars():
            if char.avatar_url and char.avatar_url.startswith("/uploads/"):
                local_path = upload_dir / char.avatar_url[len("/uploads/"):]
                if local_path.exists():
                    content = local_path.read_bytes()
                    ext = local_path.suffix
                    new_path = f"scripts/{char.script_id}/characters/{char.character_key}/avatar{ext}"
                    new_url = await storage.save(new_path, content, "image/png")
                    char.avatar_url = new_url
                    print(f"Avatar: {char.avatar_url} -> {new_url}")

        await db.commit()
        print("Migration complete!")


if __name__ == "__main__":
    asyncio.run(migrate())