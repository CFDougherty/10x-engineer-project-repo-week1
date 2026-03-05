"""Async PostgreSQL storage for PromptLab using SQLAlchemy.

In a production environment with multiple replicas this module should be
replaced with proper connection pooling (e.g. PgBouncer). For single-instance
use the built-in SQLAlchemy pool is sufficient.
"""

import asyncio
import base64
import json
import logging
from datetime import datetime, timezone
from typing import Callable, List, Optional, Tuple

from sqlalchemy import func as sa_func, select, delete, update, or_, and_, text, Float
from sqlalchemy.exc import SQLAlchemyError

from app.database import AsyncSessionLocal
from app.models import Prompt, Collection, PromptVersion
from app.models_db import PromptDB, CollectionDB, PromptVersionDB, PromptMetaDB


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONTENT_PREVIEW_LEN = 300

# Cosine distance cutoff for semantic search (pgvector <=> operator, range 0–2).
SEMANTIC_DISTANCE_THRESHOLD = 0.82


# ---------------------------------------------------------------------------
# Cursor helpers (keyset pagination)
# ---------------------------------------------------------------------------

def _encode_cursor(created_at: datetime, prompt_id: str) -> str:
    """Encode a (created_at, id) pair into a URL-safe base64 cursor string."""
    payload = {"t": created_at.isoformat(), "id": prompt_id}
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()


def _decode_cursor(cursor: str) -> Tuple[datetime, str]:
    """Decode a cursor string back to (created_at, id).

    Raises ValueError on malformed input so callers can return HTTP 400.
    """
    try:
        payload = json.loads(base64.urlsafe_b64decode(cursor.encode()))
        return datetime.fromisoformat(payload["t"]), payload["id"]
    except Exception as exc:
        raise ValueError(f"Invalid pagination cursor: {exc}") from exc


# ---------------------------------------------------------------------------
# Search condition builder
# ---------------------------------------------------------------------------

def _build_search_conditions(query: str, search_field: str, fuzzy: bool):
    """Return a SQLAlchemy WHERE expression for text search using pg_trgm.

    For fuzzy=True the condition combines an ILIKE substring match with a
    pg_trgm similarity threshold so that near-matches are also caught.
    For fuzzy=False only the ILIKE match is used.

    The ``collection`` field is intentionally not handled here — callers that
    need collection-name search must add a JOIN and filter on CollectionDB.name
    before calling get_prompts_page.
    """
    q_ilike = f"%{query}%"
    trgm_threshold = 0.1

    def title_cond():
        base = PromptDB.title.ilike(q_ilike)
        if fuzzy:
            return or_(base, sa_func.similarity(PromptDB.title, query) > trgm_threshold)
        return base

    def desc_cond():
        base = PromptDB.description.ilike(q_ilike)
        if fuzzy:
            return or_(base, sa_func.similarity(PromptDB.description, query) > trgm_threshold)
        return base

    def content_cond():
        # Content is too long for an effective trigram similarity; ILIKE is sufficient.
        return PromptDB.content.ilike(q_ilike)

    def tags_cond():
        return sa_func.array_to_string(PromptDB.tags, " ").ilike(q_ilike)

    field_map = {
        "title": title_cond,
        "description": desc_cond,
        "content": content_cond,
        "tags": tags_cond,
    }
    if search_field in field_map:
        return field_map[search_field]()
    # "all" or unrecognised — search every text field
    return or_(title_cond(), desc_cond(), content_cond(), tags_cond())


# ---------------------------------------------------------------------------
# ORM → Pydantic converters
# ---------------------------------------------------------------------------

def _to_prompt(row: PromptDB) -> Prompt:
    # Use model_construct to bypass __init__ sanitization — data from DB is already sanitized
    return Prompt.model_construct(
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


def _to_prompt_summary(row: PromptDB) -> Prompt:
    """Like _to_prompt but truncates content to CONTENT_PREVIEW_LEN for list views."""
    content = row.content
    if len(content) > CONTENT_PREVIEW_LEN:
        content = content[:CONTENT_PREVIEW_LEN]
    return Prompt.model_construct(
        id=row.id,
        title=row.title,
        content=content,
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
            try:
                from app.embeddings import agenerate_embedding
                row.embedding = await agenerate_embedding(prompt.title, prompt.content, prompt.description)
            except Exception as exc:
                logging.getLogger(__name__).warning("Embedding failed for prompt %s: %s", prompt.id, exc)
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

    async def get_prompts_page(
        self,
        limit: int = 20,
        cursor: Optional[str] = None,
        offset: Optional[int] = None,
        collection_id: Optional[str] = None,
        search: Optional[str] = None,
        fuzzy: bool = True,
        search_field: str = "all",
    ) -> Tuple[List[Prompt], Optional[str], int]:
        """Paginated prompt list with DB-level filtering and search.

        Supports two pagination modes:
        - **Keyset** (preferred): pass ``cursor`` from a previous response.
          Stable under concurrent inserts/deletes; returns a ``next_cursor``
          for the following page.
        - **Offset** (backward-compat): pass ``offset``.  Uses SQL LIMIT/OFFSET.

        Returns ``(prompts_with_preview, next_cursor, total)`` where:
        - ``prompts_with_preview`` has content truncated to CONTENT_PREVIEW_LEN.
        - ``next_cursor`` is None on the last page (or when using offset mode).
        - ``total`` is the full matching count, ignoring pagination.
        """
        async with AsyncSessionLocal() as session:
            # --- Build base filter conditions (no cursor / offset) -----------
            base_conditions = []
            needs_collection_join = False

            if collection_id:
                base_conditions.append(PromptDB.collection_id == collection_id)

            if search and search.strip():
                if search_field == "collection":
                    needs_collection_join = True
                    base_conditions.append(
                        CollectionDB.name.ilike(f"%{search}%")
                    )
                else:
                    base_conditions.append(
                        _build_search_conditions(search, search_field, fuzzy)
                    )

            # --- Total count (no pagination) ---------------------------------
            count_stmt = select(sa_func.count()).select_from(PromptDB)
            if needs_collection_join:
                count_stmt = count_stmt.join(
                    CollectionDB,
                    PromptDB.collection_id == CollectionDB.id,
                )
            if base_conditions:
                count_stmt = count_stmt.where(*base_conditions)
            total: int = (await session.execute(count_stmt)).scalar_one()

            # --- Fetch statement ----------------------------------------------
            stmt = (
                select(PromptDB)
                .order_by(PromptDB.created_at.desc(), PromptDB.id.desc())
            )
            if needs_collection_join:
                stmt = stmt.join(
                    CollectionDB,
                    PromptDB.collection_id == CollectionDB.id,
                )
            if base_conditions:
                stmt = stmt.where(*base_conditions)

            # --- Pagination ---------------------------------------------------
            next_cursor: Optional[str] = None

            if cursor is not None:
                # Keyset pagination — decode cursor and add boundary condition
                cursor_created_at, cursor_id = _decode_cursor(cursor)
                stmt = stmt.where(
                    or_(
                        PromptDB.created_at < cursor_created_at,
                        and_(
                            PromptDB.created_at == cursor_created_at,
                            PromptDB.id < cursor_id,
                        ),
                    )
                )
                # Fetch one extra row to detect whether a next page exists
                stmt = stmt.limit(limit + 1)
                rows = (await session.execute(stmt)).scalars().all()

                has_next = len(rows) > limit
                if has_next:
                    rows = rows[:limit]
                if has_next and rows:
                    last = rows[-1]
                    next_cursor = _encode_cursor(last.created_at, last.id)

            elif offset is not None and offset > 0:
                # SQL offset pagination (backward-compat with existing tests/clients)
                stmt = stmt.offset(offset).limit(limit)
                rows = (await session.execute(stmt)).scalars().all()

            else:
                # First page — no cursor, no offset
                # Still emit a next_cursor so callers can page forward
                stmt = stmt.limit(limit + 1)
                rows = (await session.execute(stmt)).scalars().all()

                has_next = len(rows) > limit
                if has_next:
                    rows = rows[:limit]
                if has_next and rows:
                    last = rows[-1]
                    next_cursor = _encode_cursor(last.created_at, last.id)

            return [_to_prompt_summary(r) for r in rows], next_cursor, total

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
            try:
                from app.embeddings import agenerate_embedding
                row.embedding = await agenerate_embedding(prompt.title, prompt.content, prompt.description)
            except Exception as exc:
                logging.getLogger(__name__).warning("Embedding failed for prompt %s: %s", prompt_id, exc)
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

    # ============== Semantic Search ==============

    async def semantic_search(
        self,
        query_embedding: List[float],
        limit: int = 20,
        offset: int = 0,
        collection_id: Optional[str] = None,
        threshold: float = SEMANTIC_DISTANCE_THRESHOLD,
    ) -> List[Prompt]:
        """Return prompts ordered by cosine similarity to query_embedding.

        Only prompts with a non-NULL embedding and cosine distance strictly less
        than ``threshold`` are returned. The <=> operator is pgvector cosine
        distance; ascending = most similar first.
        """
        async with AsyncSessionLocal() as session:
            stmt = (
                select(PromptDB)
                .where(PromptDB.embedding.isnot(None))
                .where(PromptDB.embedding.op("<=>", return_type=Float)(query_embedding) < threshold)
                .order_by(PromptDB.embedding.op("<=>", return_type=Float)(query_embedding))
            )
            if collection_id:
                stmt = stmt.where(PromptDB.collection_id == collection_id)
            stmt = stmt.offset(offset).limit(limit)
            result = await session.execute(stmt)
            return [_to_prompt(r) for r in result.scalars().all()]

    async def count_semantic_results(
        self,
        query_embedding: List[float],
        collection_id: Optional[str] = None,
        threshold: float = SEMANTIC_DISTANCE_THRESHOLD,
    ) -> int:
        """Count prompts whose cosine distance to query_embedding is below threshold."""
        async with AsyncSessionLocal() as session:
            stmt = (
                select(sa_func.count())
                .select_from(PromptDB)
                .where(PromptDB.embedding.isnot(None))
                .where(PromptDB.embedding.op("<=>", return_type=Float)(query_embedding) < threshold)
            )
            if collection_id:
                stmt = stmt.where(PromptDB.collection_id == collection_id)
            result = await session.execute(stmt)
            return result.scalar_one()

    async def count_embedded_prompts(
        self,
        collection_id: Optional[str] = None,
    ) -> int:
        """Count prompts with a non-NULL embedding. Used by /admin/embedding-status."""
        async with AsyncSessionLocal() as session:
            stmt = (
                select(sa_func.count())
                .select_from(PromptDB)
                .where(PromptDB.embedding.isnot(None))
            )
            if collection_id:
                stmt = stmt.where(PromptDB.collection_id == collection_id)
            result = await session.execute(stmt)
            return result.scalar_one()

    async def batch_create_prompts(self, prompts: List[Prompt]) -> None:
        """Insert all prompts in a single transaction without generating embeddings."""
        if not prompts:
            return
        async with AsyncSessionLocal() as session:
            rows = [
                PromptDB(
                    id=p.id,
                    title=p.title,
                    content=p.content,
                    description=p.description,
                    tags=p.tags,
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                    version=p.version,
                )
                for p in prompts
            ]
            session.add_all(rows)
            await session.commit()

    async def batch_update_collection_ids(self, assignments: list[tuple[str, str]]) -> None:
        """Set collection_id for a batch of (prompt_id, collection_id) pairs in one transaction.

        No embedding generation — use backfill_embeddings() after this if needed.
        """
        if not assignments:
            return
        async with AsyncSessionLocal() as session:
            for prompt_id, collection_id in assignments:
                await session.execute(
                    update(PromptDB)
                    .where(PromptDB.id == prompt_id)
                    .values(collection_id=collection_id)
                )
            await session.commit()

    async def batch_set_embeddings(self, updates: List[Tuple[str, List[float]]]) -> None:
        """Bulk-update embeddings for a list of (prompt_id, embedding) pairs in one transaction."""
        if not updates:
            return
        async with AsyncSessionLocal() as session:
            for prompt_id, embedding in updates:
                await session.execute(
                    update(PromptDB)
                    .where(PromptDB.id == prompt_id)
                    .values(embedding=embedding)
                )
            await session.commit()

    async def backfill_embeddings(self, generate_fn: Callable, chunk_size: int = 50) -> int:
        """Generate embeddings for all prompts where embedding IS NULL.

        generate_fn: sync callable (title, content, description) -> List[float].
        Returns count of prompts updated. Idempotent — skips already-embedded prompts.
        Processes in paginated chunks of chunk_size and commits after each chunk so
        that the /admin/embedding-status endpoint reflects live progress.
        Uses small batch sizes to keep memory usage low on constrained systems.
        """
        loop = asyncio.get_event_loop()
        total_updated = 0
        offset = 0

        while True:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(PromptDB)
                    .where(PromptDB.embedding.is_(None))
                    .order_by(PromptDB.id)
                    .limit(chunk_size)
                    .offset(offset)
                )
                rows = result.scalars().all()

            if not rows:
                break

            items = [(r.title, r.content, r.description) for r in rows]

            try:
                from app.embeddings import generate_embeddings_batch
                vecs: list = await loop.run_in_executor(
                    None, generate_embeddings_batch, items, 16,
                )
                good = list(zip([r.id for r in rows], vecs))
            except Exception as exc:
                # Fall back to per-item if batch function unavailable
                logging.getLogger(__name__).warning("Batch embed failed (%s); falling back to per-item", exc)
                good = []
                for row, item in zip(rows, items):
                    try:
                        vec = await loop.run_in_executor(None, generate_fn, *item)
                        good.append((row.id, vec))
                    except Exception as e:
                        logging.getLogger(__name__).warning("Backfill failed for %s: %s", row.id, e)

            await self.batch_set_embeddings(good)  # commits to DB; status endpoint sees updated count
            total_updated += len(good)

            # If all rows in this page got embeddings, the next page starts at offset 0
            # because the WHERE clause filters out already-embedded rows.
            # If some failed, advance offset to skip them.
            if len(good) == len(rows):
                offset = 0
            else:
                offset += chunk_size

        return total_updated

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
