"""Async PostgreSQL storage for PromptLab using SQLAlchemy.

In a production environment with multiple replicas this module should be
replaced with proper connection pooling (e.g. PgBouncer). For single-instance
use the built-in SQLAlchemy pool is sufficient.
"""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select, delete

from app.database import AsyncSessionLocal
from app.models import Prompt, Collection, PromptVersion
from app.models_db import PromptDB, CollectionDB, PromptVersionDB, PromptMetaDB


# ---------------------------------------------------------------------------
# ORM → Pydantic converters
# ---------------------------------------------------------------------------

def _to_prompt(row: PromptDB) -> Prompt:
    return Prompt(
        id=row.id,
        title=row.title,
        content=row.content,
        description=row.description,
        collection_id=row.collection_id,
        tags=row.tags,
        created_at=row.created_at,
        updated_at=row.updated_at,
        version=row.version,
    )


def _to_collection(row: CollectionDB) -> Collection:
    return Collection(
        id=row.id,
        name=row.name,
        description=row.description,
        created_at=row.created_at,
    )


def _to_prompt_version(row: PromptVersionDB) -> PromptVersion:
    return PromptVersion(
        prompt_id=row.prompt_id,
        version=row.version,
        title=row.title,
        content=row.content,
        description=row.description,
        collection_id=row.collection_id,
        tags=row.tags,
        created_at=row.created_at,
    )


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ---------------------------------------------------------------------------
# Storage class
# ---------------------------------------------------------------------------

class Storage:
    """Async storage layer backed by PostgreSQL via SQLAlchemy.

    Each method opens and closes its own session, so no session management
    is required by callers. The public interface matches the previous
    in-memory implementation — callers only need to add ``await``.
    """

    # ============== Prompt Operations ==============

    async def create_prompt(self, prompt: Prompt) -> Prompt:
        async with AsyncSessionLocal() as session:
            row = PromptDB(
                id=prompt.id,
                title=prompt.title,
                content=prompt.content,
                description=prompt.description,
                collection_id=prompt.collection_id,
                tags=prompt.tags,
                created_at=prompt.created_at,
                updated_at=prompt.updated_at,
                version=prompt.version,
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            return _to_prompt(row)

    async def get_prompt(self, prompt_id: str) -> Optional[Prompt]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(PromptDB).where(PromptDB.id == prompt_id)
            )
            row = result.scalar_one_or_none()
            return _to_prompt(row) if row else None

    async def get_all_prompts(self) -> List[Prompt]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(PromptDB))
            return [_to_prompt(r) for r in result.scalars().all()]

    async def update_prompt(self, prompt_id: str, prompt: Prompt) -> Optional[Prompt]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(PromptDB).where(PromptDB.id == prompt_id)
            )
            row = result.scalar_one_or_none()
            if row is None:
                return None
            # Preserve original created_at — matches previous in-memory behaviour
            row.title = prompt.title
            row.content = prompt.content
            row.description = prompt.description
            row.collection_id = prompt.collection_id
            row.tags = prompt.tags
            row.updated_at = prompt.updated_at
            row.version = prompt.version
            await session.commit()
            await session.refresh(row)
            return _to_prompt(row)

    async def patch_prompt(self, prompt_id: str, prompt: Prompt) -> Optional[Prompt]:
        # api.py builds the fully-merged Prompt before calling this, so the
        # DB operation is identical to update_prompt.
        return await self.update_prompt(prompt_id, prompt)

    async def delete_prompt(self, prompt_id: str) -> bool:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(PromptDB).where(PromptDB.id == prompt_id)
            )
            row = result.scalar_one_or_none()
            if row is None:
                return False
            await session.delete(row)
            await session.commit()
            return True

    # ============== Collection Operations ==============

    async def create_collection(self, collection: Collection) -> Collection:
        async with AsyncSessionLocal() as session:
            row = CollectionDB(
                id=collection.id,
                name=collection.name,
                description=collection.description,
                created_at=collection.created_at,
                updated_at=collection.created_at,
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            return _to_collection(row)

    async def get_collection(self, collection_id: str) -> Optional[Collection]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(CollectionDB).where(CollectionDB.id == collection_id)
            )
            row = result.scalar_one_or_none()
            return _to_collection(row) if row else None

    async def get_all_collections(self) -> List[Collection]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(CollectionDB))
            return [_to_collection(r) for r in result.scalars().all()]

    async def update_collection(self, collection_id: str, collection: Collection) -> Optional[Collection]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(CollectionDB).where(CollectionDB.id == collection_id)
            )
            row = result.scalar_one_or_none()
            if row is None:
                return None
            row.name = collection.name
            row.description = collection.description
            row.updated_at = _utcnow()
            await session.commit()
            await session.refresh(row)
            return _to_collection(row)

    async def delete_collection(self, collection_id: str) -> bool:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(CollectionDB).where(CollectionDB.id == collection_id)
            )
            row = result.scalar_one_or_none()
            if row is None:
                return False
            await session.delete(row)
            await session.commit()
            return True

    async def get_prompts_by_collection(self, collection_id: str) -> List[Prompt]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(PromptDB).where(PromptDB.collection_id == collection_id)
            )
            return [_to_prompt(r) for r in result.scalars().all()]

    async def get_prompts_by_collection_id(self, collection_id: str) -> List[Prompt]:
        return await self.get_prompts_by_collection(collection_id)

    async def delete_prompts_by_collection_id(self, collection_id: str) -> None:
        async with AsyncSessionLocal() as session:
            await session.execute(
                delete(PromptDB).where(PromptDB.collection_id == collection_id)
            )
            await session.commit()

    # ============== Versioning Operations ==============

    async def create_prompt_version(self, prompt_id: str, prompt: Prompt) -> PromptVersion:
        async with AsyncSessionLocal() as session:
            # Get or create metadata
            meta_result = await session.execute(
                select(PromptMetaDB).where(PromptMetaDB.id == prompt_id)
            )
            meta_row = meta_result.scalar_one_or_none()

            if meta_row is None:
                current_version = 1
                meta_row = PromptMetaDB(
                    id=prompt_id,
                    current_version=current_version,
                    created_at=prompt.created_at,
                )
                session.add(meta_row)
            else:
                current_version = meta_row.current_version + 1
                meta_row.current_version = current_version

            # Create immutable version snapshot
            version_row = PromptVersionDB(
                prompt_id=prompt_id,
                version=current_version,
                title=prompt.title,
                content=prompt.content,
                description=prompt.description,
                collection_id=prompt.collection_id,
                tags=prompt.tags,
                created_at=_utcnow(),
            )
            session.add(version_row)

            # Update the canonical prompt's version number
            prompt_result = await session.execute(
                select(PromptDB).where(PromptDB.id == prompt_id)
            )
            prompt_row = prompt_result.scalar_one_or_none()
            if prompt_row is not None:
                prompt_row.version = current_version

            await session.commit()
            await session.refresh(version_row)
            return _to_prompt_version(version_row)

    async def get_prompt_version(self, prompt_id: str, version: int) -> Optional[PromptVersion]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(PromptVersionDB).where(
                    PromptVersionDB.prompt_id == prompt_id,
                    PromptVersionDB.version == version,
                )
            )
            row = result.scalar_one_or_none()
            return _to_prompt_version(row) if row else None

    async def get_all_prompt_versions(self, prompt_id: str) -> List[PromptVersion]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(PromptVersionDB)
                .where(PromptVersionDB.prompt_id == prompt_id)
                .order_by(PromptVersionDB.version.desc())
            )
            return [_to_prompt_version(r) for r in result.scalars().all()]

    async def promote_prompt_version(self, prompt_id: str, version: int) -> Optional[Prompt]:
        old_version = await self.get_prompt_version(prompt_id, version)
        if not old_version:
            return None

        original_prompt = await self.get_prompt(prompt_id)
        new_prompt = Prompt(
            id=prompt_id,
            title=old_version.title,
            content=old_version.content,
            description=old_version.description,
            collection_id=old_version.collection_id,
            tags=old_version.tags,
            created_at=original_prompt.created_at,
        )

        await self.update_prompt(prompt_id, new_prompt)
        await self.create_prompt_version(prompt_id, new_prompt)
        return await self.get_prompt(prompt_id)

    # ============== Utility ==============

    async def clear(self) -> None:
        """Delete all rows from every table. Used in tests and /admin/clear-all-data."""
        async with AsyncSessionLocal() as session:
            # Delete in FK-safe order: children before parents
            await session.execute(delete(PromptMetaDB))
            await session.execute(delete(PromptVersionDB))
            await session.execute(delete(PromptDB))
            await session.execute(delete(CollectionDB))
            await session.commit()


# Global singleton — same pattern as before; callers just add await
storage = Storage()
