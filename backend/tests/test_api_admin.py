"""Tests for admin API endpoints."""

import asyncio
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.api import app
from app.storage import storage
from app.models import Prompt, Collection
import uuid

client = TestClient(app)

async def test_populate_test_data():
    """Populate-test-data endpoint must create prompts and collections and report counts.

    Verifies the endpoint returns a success status, reports non-zero creation counts,
    and that the storage state matches the reported counts after the call.
    """
    await storage.clear()

    assert len(await storage.get_all_prompts()) == 0
    assert len(await storage.get_all_collections()) == 0

    response = client.post("/admin/populate-test-data")

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "started"
    assert data["total"] > 0

    # BackgroundTasks run synchronously in TestClient, so data is present now.
    # Poll /admin/populate-status for creation counts (not the 202 response).
    status_response = client.get("/admin/populate-status")
    assert status_response.status_code == 200
    status = status_response.json()

    prompts = await storage.get_all_prompts()
    collections = await storage.get_all_collections()
    assert len(prompts) == status["prompts_created"]
    assert len(collections) == status["collections_created"]
    assert len(prompts) > 0
    assert len(collections) > 0

async def test_clear_all_data():
    """Clear-all-data endpoint must remove all existing prompts and collections.

    Seeds storage with one prompt and one collection, calls the endpoint, and
    confirms both the reported removal counts and the resulting empty storage state.
    """
    test_prompt = Prompt(
        id=str(uuid.uuid4()),
        title="Test Prompt",
        content="Test content",
        description="Test description",
        tags=["test"]
    )
    await storage.create_prompt(test_prompt)

    test_collection = Collection(
        id=str(uuid.uuid4()),
        name="Test Collection",
        description="Test description"
    )
    await storage.create_collection(test_collection)

    assert len(await storage.get_all_prompts()) == 1
    assert len(await storage.get_all_collections()) == 1

    response = client.delete("/admin/clear-all-data")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "prompts_removed" in data
    assert "collections_removed" in data
    assert data["prompts_removed"] == 1
    assert data["collections_removed"] == 1

    assert len(await storage.get_all_prompts()) == 0
    assert len(await storage.get_all_collections()) == 0

async def test_clear_all_data_when_empty():
    """Clear-all-data endpoint must succeed and report zero removals when storage is empty.

    Confirms the endpoint is idempotent and handles an already-empty storage gracefully
    without errors.
    """
    await storage.clear()

    assert len(await storage.get_all_prompts()) == 0
    assert len(await storage.get_all_collections()) == 0

    response = client.delete("/admin/clear-all-data")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["prompts_removed"] == 0
    assert data["collections_removed"] == 0

async def test_admin_endpoints_clear_storage_between_tests():
    """Storage must be empty after an explicit clear, ensuring no state leaks between tests.

    Note:
        This test guards against inadvertent cross-test contamination by verifying that
        a manual storage.clear() leaves both prompts and collections collections empty.
    """
    await storage.clear()

    assert len(await storage.get_all_prompts()) == 0
    assert len(await storage.get_all_collections()) == 0


async def test_populate_test_data_all_prompts_have_versions():
    """Every prompt created by populate-test-data must have at least one version snapshot.

    Note:
        populate-test-data must call create_prompt_version for every prompt it creates,
        otherwise version history is unavailable for those prompts.
    """
    await storage.clear()

    response = client.post("/admin/populate-test-data")
    assert response.status_code == 202

    # BackgroundTasks run synchronously in TestClient, so data is present now
    prompts = await storage.get_all_prompts()
    assert len(prompts) > 0, "populate-test-data created no prompts"

    for prompt in prompts:
        versions = await storage.get_all_prompt_versions(prompt.id)
        assert len(versions) >= 1, (
            f"Prompt {prompt.id!r} ({prompt.title!r}) has no version snapshots. "
            "populate-test-data must call create_prompt_version for every prompt it creates."
        )


def test_populate_test_data_storage_exception_records_error():
    """populate-test-data must record errors in populate-status when the background task fails.

    Since the endpoint returns 202 immediately (fire-and-forget), exceptions cannot
    surface as HTTP status codes. Instead they must be written to _populate_progress["error"]
    so that polling clients (e.g. PopulateStatusBar) can surface the failure.
    TestClient executes BackgroundTasks synchronously, so the error is present
    by the time we poll /admin/populate-status after the POST.
    """
    import app.api as api_module
    api_module._populate_progress.update({"current": 0, "total": 0, "active": False, "error": None})

    with patch.object(storage, "batch_create_prompts", side_effect=RuntimeError("boom")):
        response = client.post("/admin/populate-test-data")

    assert response.status_code == 202

    status = client.get("/admin/populate-status")
    assert status.status_code == 200
    data = status.json()
    assert data["active"] is False
    assert data["error"] is not None
    assert "boom" in data["error"]


def test_populate_test_data_returns_409_when_already_running():
    """populate-test-data must return 409 Conflict if a populate is already in progress."""
    import app.api as api_module
    original = api_module._populate_progress.copy()
    api_module._populate_progress["active"] = True
    try:
        response = client.post("/admin/populate-test-data")
        assert response.status_code == 409
        assert "already in progress" in response.json()["detail"]
    finally:
        api_module._populate_progress.update(original)
        api_module._populate_progress["active"] = False


def test_clear_all_data_storage_exception_returns_500():
    """clear-all-data must return 500 when storage raises an unexpected exception.

    Uses mock to force storage.clear to raise, triggering the except block.
    """
    with patch.object(storage, "clear", side_effect=RuntimeError("boom")):
        response = client.delete("/admin/clear-all-data")
    assert response.status_code == 500
    assert "Failed to clear data" in response.json()["detail"]


async def test_clear_test_data_with_tagged_prompts():
    """DELETE /admin/clear-test-data must remove only prompts tagged 'test fill'."""
    await storage.clear()

    tagged = Prompt(id=str(uuid.uuid4()), title="Tagged", content="content", tags=["test fill"])
    untagged = Prompt(id=str(uuid.uuid4()), title="Untagged", content="content", tags=["other"])
    await storage.create_prompt(tagged)
    await storage.create_prompt(untagged)

    response = client.delete("/admin/clear-test-data")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["prompts_removed"] == 1

    remaining = await storage.get_all_prompts()
    assert len(remaining) == 1
    assert remaining[0].title == "Untagged"


async def test_clear_test_data_no_tagged_prompts():
    """DELETE /admin/clear-test-data must return 0 when no 'test fill' prompts exist."""
    await storage.clear()

    p = Prompt(id=str(uuid.uuid4()), title="Regular", content="content", tags=["other"])
    await storage.create_prompt(p)

    response = client.delete("/admin/clear-test-data")
    assert response.status_code == 200
    assert response.json()["prompts_removed"] == 0


async def test_embedding_status_empty_db():
    """GET /admin/embedding-status must report complete=True when no prompts exist."""
    await storage.clear()
    response = client.get("/admin/embedding-status")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["embedded"] == 0
    assert data["complete"] is True


async def test_embedding_status_with_unembedded_prompt():
    """GET /admin/embedding-status reports complete=False when some prompts lack embeddings."""
    await storage.clear()
    p = Prompt(id=str(uuid.uuid4()), title="No Embedding", content="content")
    with patch("app.embeddings.agenerate_embedding", side_effect=RuntimeError("disabled")):
        await storage.create_prompt(p)

    response = client.get("/admin/embedding-status")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["complete"] is False


def test_backfill_embeddings_503_on_runtime_error():
    """POST /admin/backfill-embeddings must return 503 when the model raises RuntimeError."""
    with patch.object(storage, "backfill_embeddings", side_effect=RuntimeError("model unavailable")):
        response = client.post("/admin/backfill-embeddings")
    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"].lower()


def test_backfill_embeddings_500_on_unexpected_error():
    """POST /admin/backfill-embeddings must return 500 on unexpected exceptions."""
    with patch.object(storage, "backfill_embeddings", side_effect=Exception("unexpected")):
        response = client.post("/admin/backfill-embeddings")
    assert response.status_code == 500
    assert "unexpected" in response.json()["detail"]


async def test_populate_template_data_source():
    """POST /admin/populate-test-data with data_source='template' must create prompts."""
    await storage.clear()

    response = client.post("/admin/populate-test-data", json={
        "data_source": "template",
        "num_prompts": 5,
        "num_collections": 1,
        "random_seed": 42,
    })
    assert response.status_code == 202

    prompts = await storage.get_all_prompts()
    assert len(prompts) == 5


def test_query_param_api_key_allows_access():
    """GET /prompts?api_key=<key> must succeed when API key auth is enabled."""
    import os
    from app.database import get_settings

    TEST_KEY = "test-qparam-key"
    os.environ["API_KEY"] = TEST_KEY
    get_settings.cache_clear()
    try:
        resp = client.get(f"/prompts?api_key={TEST_KEY}")
        assert resp.status_code == 200
    finally:
        os.environ.pop("API_KEY", None)
        get_settings.cache_clear()


async def test_notify_sse_clients_delivers_to_queues():
    """notify_sse_clients must put the message into every registered queue."""
    import asyncio
    from app.api import notify_sse_clients, sse_client_queues

    q1: asyncio.Queue = asyncio.Queue()
    q2: asyncio.Queue = asyncio.Queue()
    sse_client_queues.clear()
    sse_client_queues.extend([q1, q2])
    try:
        await notify_sse_clients('{"event": "test"}')
        assert q1.get_nowait() == '{"event": "test"}'
        assert q2.get_nowait() == '{"event": "test"}'
    finally:
        sse_client_queues.clear()


# ── Backfill embeddings success path (api.py L1065-1072) ──


def test_backfill_embeddings_success():
    """POST /admin/backfill-embeddings success path returns updated count."""
    with (
        patch("app.embeddings.generate_embedding", return_value=[0.1] * 384),
        patch.object(storage, "backfill_embeddings", new_callable=AsyncMock, return_value=7),
    ):
        response = client.post("/admin/backfill-embeddings")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["updated"] == 7
    assert "7 prompt(s)" in data["message"]


# ── Clear test data exception path (api.py L1027-1031) ──


def test_clear_test_data_exception_returns_500():
    """DELETE /admin/clear-test-data must return 500 when storage raises."""
    with patch.object(storage, "get_all_prompts", new_callable=AsyncMock, side_effect=RuntimeError("db down")):
        response = client.delete("/admin/clear-test-data")
    assert response.status_code == 500
    assert "Failed to clear test data" in response.json()["detail"]


# ── Embedding status with complete=True when total > 0 (api.py L1049) ──


async def test_embedding_status_all_embedded():
    """GET /admin/embedding-status reports complete=True when all prompts have embeddings."""
    await storage.clear()
    p = Prompt(id=str(uuid.uuid4()), title="Embedded Prompt", content="content")
    await storage.create_prompt(p)
    vec = [1.0] + [0.0] * 383
    await storage.batch_set_embeddings([(p.id, vec)])

    response = client.get("/admin/embedding-status")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["embedded"] == 1
    assert data["complete"] is True


# ── Populate without random_seed (api.py L951-952) ──


def test_populate_without_random_seed():
    """POST /admin/populate-test-data without random_seed hits the else branch."""
    import app.api as api_module
    api_module._populate_progress.update({"current": 0, "total": 0, "active": False, "error": None})

    response = client.post("/admin/populate-test-data", json={
        "num_prompts": 2,
        "num_collections": 1,
    })
    assert response.status_code == 202
    assert response.json()["status"] == "started"


# ── Populate with append_mode=True (api.py L756) ──


async def test_populate_append_mode():
    """append_mode=True must preserve existing data instead of clearing."""
    await storage.clear()

    existing = Prompt(id=str(uuid.uuid4()), title="Pre-existing", content="should survive")
    await storage.create_prompt(existing)

    response = client.post("/admin/populate-test-data", json={
        "append_mode": True,
        "num_prompts": 2,
        "num_collections": 1,
        "random_seed": 42,
    })
    assert response.status_code == 202

    all_prompts = await storage.get_all_prompts()
    ids = [p.id for p in all_prompts]
    assert existing.id in ids
    assert len(all_prompts) >= 3  # 1 existing + 2 new


# ── Populate with tag_as_test_fill=True (api.py L782-783, L845-846) ──


async def test_populate_tag_as_test_fill():
    """tag_as_test_fill=True must add 'test fill' tag to every created prompt."""
    await storage.clear()

    response = client.post("/admin/populate-test-data", json={
        "tag_as_test_fill": True,
        "num_prompts": 3,
        "num_collections": 1,
        "random_seed": 42,
    })
    assert response.status_code == 202

    all_prompts = await storage.get_all_prompts()
    assert len(all_prompts) == 3
    for p in all_prompts:
        assert "test fill" in p.tags, f"Prompt {p.id!r} missing 'test fill' tag"


# ── Populate backfill exception silently caught (api.py L921-925) ──


async def test_populate_backfill_exception_silently_caught():
    """Embedding backfill failure during populate must not set an error."""
    await storage.clear()

    with patch.object(storage, "backfill_embeddings", new_callable=AsyncMock, side_effect=RuntimeError("no model")):
        response = client.post("/admin/populate-test-data", json={
            "num_prompts": 2,
            "num_collections": 1,
            "random_seed": 42,
        })

    assert response.status_code == 202

    status = client.get("/admin/populate-status").json()
    assert status["error"] is None


# ── SSE event stream generator tests (api.py L654-691) ──


async def test_sse_connected_message():
    """SSE generator yields the connected message first."""
    from app.api import sse_endpoint, sse_client_queues

    mock_request = MagicMock()
    response = await sse_endpoint(mock_request)
    gen = response.body_iterator

    try:
        first = await gen.__anext__()
        assert '"event": "connected"' in first
        assert first.startswith("data: ")
    finally:
        await gen.aclose()
        sse_client_queues.clear()


async def test_sse_message_delivery():
    """SSE generator yields messages placed on the queue."""
    from app.api import sse_endpoint, sse_client_queues

    mock_request = MagicMock()
    response = await sse_endpoint(mock_request)
    gen = response.body_iterator

    try:
        # consume connected message
        await gen.__anext__()

        # find the queue that was registered
        queue = sse_client_queues[-1]
        await queue.put('{"event": "test_msg"}')

        msg = await gen.__anext__()
        assert msg == 'data: {"event": "test_msg"}\n\n'
    finally:
        await gen.aclose()
        sse_client_queues.clear()


async def test_sse_keepalive_on_timeout():
    """SSE generator yields keep-alive comment when queue.get times out."""
    from app.api import sse_endpoint, sse_client_queues

    mock_request = MagicMock()
    response = await sse_endpoint(mock_request)
    gen = response.body_iterator

    try:
        await gen.__anext__()  # connected message

        with patch("app.api.asyncio.wait_for", new_callable=AsyncMock, side_effect=asyncio.TimeoutError):
            keepalive = await gen.__anext__()

        assert keepalive == ": keep-alive\n\n"
    finally:
        await gen.aclose()
        sse_client_queues.clear()


async def test_sse_cleanup_on_cancel():
    """SSE generator removes queue from sse_client_queues on CancelledError."""
    from app.api import sse_endpoint, sse_client_queues

    mock_request = MagicMock()
    response = await sse_endpoint(mock_request)
    gen = response.body_iterator

    await gen.__anext__()  # connected message

    queue = sse_client_queues[-1]
    assert queue in sse_client_queues

    # Put a message so the generator advances past the first yield into the while loop,
    # then throw CancelledError which triggers the except/finally cleanup.
    await queue.put("dummy")
    await gen.__anext__()  # consume the dummy message

    try:
        await gen.athrow(asyncio.CancelledError)
    except (StopAsyncIteration, asyncio.CancelledError):
        pass

    assert queue not in sse_client_queues
