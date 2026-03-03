"""Tests for cursor-based pagination, content preview truncation, and DB-level search.

These tests are written TDD-style — they describe the target behaviour of the
new server-side pagination introduced in the Option-E performance refactor.
"""

import pytest
from fastapi.testclient import TestClient


LONG_CONTENT = "X" * 600  # 600 chars — well above the 300-char preview limit


class TestCursorPagination:
    """Keyset (cursor-based) pagination via GET /prompts?cursor=..."""

    def _make_prompts(self, client: TestClient, count: int) -> list[dict]:
        """Create ``count`` distinct prompts and return their response bodies."""
        created = []
        for i in range(count):
            r = client.post(
                "/prompts",
                json={"title": f"Prompt {i:03d}", "content": f"Content for prompt {i}"},
            )
            assert r.status_code == 201, r.text
            created.append(r.json())
        return created

    def test_first_page_has_next_cursor_when_more_pages_exist(self, client: TestClient):
        """A first page of size < total must return a non-null next_cursor."""
        self._make_prompts(client, 5)

        resp = client.get("/prompts?limit=2")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["prompts"]) == 2
        assert data["next_cursor"] is not None

    def test_last_page_has_no_next_cursor(self, client: TestClient):
        """When the result fits in a single page next_cursor must be null."""
        self._make_prompts(client, 3)

        resp = client.get("/prompts?limit=10")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["prompts"]) == 3
        assert data["next_cursor"] is None

    def test_traversing_all_pages_yields_every_prompt_exactly_once(
        self, client: TestClient
    ):
        """Iterating through pages with the returned cursor covers the full set."""
        self._make_prompts(client, 7)

        seen_ids: list[str] = []
        cursor = None

        for _ in range(10):  # safety limit
            url = "/prompts?limit=3" + (f"&cursor={cursor}" if cursor else "")
            resp = client.get(url)
            assert resp.status_code == 200
            data = resp.json()
            page_ids = [p["id"] for p in data["prompts"]]
            assert len(set(page_ids) & set(seen_ids)) == 0, "Duplicate prompt returned"
            seen_ids.extend(page_ids)
            cursor = data["next_cursor"]
            if cursor is None:
                break

        assert len(seen_ids) == 7

    def test_total_reflects_full_result_set_not_current_page(self, client: TestClient):
        """``total`` must equal the number of prompts matching filters regardless of page size."""
        self._make_prompts(client, 10)

        resp = client.get("/prompts?limit=3")
        data = resp.json()
        assert len(data["prompts"]) == 3
        assert data["total"] == 10

    def test_cursor_pagination_with_collection_filter(self, client: TestClient):
        """Pagination is stable when filtered to a specific collection."""
        coll = client.post("/collections", json={"name": "Paged Collection"}).json()
        cid = coll["id"]

        for i in range(6):
            client.post(
                "/prompts",
                json={"title": f"Col Prompt {i}", "content": f"Content {i}", "collection_id": cid},
            )
        # Two prompts outside the collection
        client.post("/prompts", json={"title": "Outsider", "content": "No collection"})
        client.post("/prompts", json={"title": "Outsider 2", "content": "No collection 2"})

        seen_ids: list[str] = []
        cursor = None
        for _ in range(10):
            url = f"/prompts?limit=2&collection_id={cid}" + (f"&cursor={cursor}" if cursor else "")
            resp = client.get(url)
            assert resp.status_code == 200
            data = resp.json()
            for p in data["prompts"]:
                assert p["collection_id"] == cid, "Non-collection prompt leaked through"
            seen_ids.extend(p["id"] for p in data["prompts"])
            cursor = data["next_cursor"]
            if cursor is None:
                break

        assert len(seen_ids) == 6
        assert data["total"] == 6

    def test_cursor_pagination_with_search(self, client: TestClient):
        """Search + cursor pagination together yield only matching prompts."""
        for i in range(5):
            client.post(
                "/prompts",
                json={"title": f"Python prompt {i}", "content": f"Python content {i}"},
            )
        for i in range(3):
            client.post(
                "/prompts",
                json={"title": f"JavaScript prompt {i}", "content": f"JS content {i}"},
            )

        seen_ids: list[str] = []
        cursor = None
        for _ in range(10):
            url = "/prompts?limit=2&search=Python&filter=title" + (f"&cursor={cursor}" if cursor else "")
            resp = client.get(url)
            assert resp.status_code == 200
            data = resp.json()
            for p in data["prompts"]:
                assert "Python" in p["title"]
            seen_ids.extend(p["id"] for p in data["prompts"])
            cursor = data["next_cursor"]
            if cursor is None:
                break

        assert len(seen_ids) == 5
        assert data["total"] == 5

    def test_cursor_with_zero_limit_returns_empty_with_correct_total(
        self, client: TestClient
    ):
        """limit=0 must return an empty prompts list but the correct total."""
        self._make_prompts(client, 4)

        resp = client.get("/prompts?limit=0")
        assert resp.status_code == 200
        data = resp.json()
        assert data["prompts"] == []
        assert data["total"] == 4

    def test_invalid_cursor_returns_400(self, client: TestClient):
        """A garbage cursor string must be rejected with HTTP 400."""
        resp = client.get("/prompts?cursor=not-a-valid-cursor")
        assert resp.status_code == 400

    def test_response_includes_next_cursor_field(self, client: TestClient):
        """The ``next_cursor`` key must always be present in the response, even when null."""
        resp = client.get("/prompts")
        assert resp.status_code == 200
        data = resp.json()
        assert "next_cursor" in data


class TestContentPreview:
    """List endpoint returns truncated content; detail endpoint returns full content."""

    def test_list_returns_truncated_content_for_long_prompt(self, client: TestClient):
        """GET /prompts content field is truncated to at most 300 chars."""
        client.post(
            "/prompts",
            json={"title": "Long prompt", "content": LONG_CONTENT},
        )

        resp = client.get("/prompts")
        assert resp.status_code == 200
        prompt = resp.json()["prompts"][0]
        assert len(prompt["content"]) <= 300

    def test_detail_returns_full_content(self, client: TestClient):
        """GET /prompts/{id} must return the full, un-truncated content."""
        create_resp = client.post(
            "/prompts",
            json={"title": "Long prompt", "content": LONG_CONTENT},
        )
        prompt_id = create_resp.json()["id"]

        detail_resp = client.get(f"/prompts/{prompt_id}")
        assert detail_resp.status_code == 200
        assert detail_resp.json()["content"] == LONG_CONTENT

    def test_short_content_is_not_truncated(self, client: TestClient):
        """Content shorter than the preview limit is returned verbatim in list responses."""
        short = "Short content"
        client.post("/prompts", json={"title": "Short", "content": short})

        resp = client.get("/prompts")
        prompt = resp.json()["prompts"][0]
        assert prompt["content"] == short


class TestDbSearch:
    """Search is now executed at the database layer, not in Python memory."""

    def test_title_search_is_case_insensitive(self, client: TestClient):
        """Search is case-insensitive on the title field."""
        client.post("/prompts", json={"title": "CaseSensitive Title", "content": "Content"})
        client.post("/prompts", json={"title": "Unrelated", "content": "Content"})

        resp = client.get("/prompts?search=casesensitive&filter=title")
        assert resp.status_code == 200
        prompts = resp.json()["prompts"]
        assert len(prompts) == 1
        assert "CaseSensitive" in prompts[0]["title"]

    def test_search_excludes_non_matching_prompts(self, client: TestClient):
        """Only prompts matching the query are returned."""
        client.post("/prompts", json={"title": "Alpha search", "content": "Alpha"})
        client.post("/prompts", json={"title": "Beta other", "content": "Beta"})

        resp = client.get("/prompts?search=Alpha&filter=title&fuzzy=false")
        assert resp.status_code == 200
        prompts = resp.json()["prompts"]
        assert all("Alpha" in p["title"] for p in prompts)

    def test_description_search(self, client: TestClient):
        """Searching by description field finds matching prompts."""
        client.post(
            "/prompts",
            json={"title": "Title", "content": "Content", "description": "Unique descriptor here"},
        )
        client.post("/prompts", json={"title": "Other", "content": "Content"})

        resp = client.get("/prompts?search=Unique+descriptor&filter=description&fuzzy=false")
        assert resp.status_code == 200
        assert len(resp.json()["prompts"]) == 1

    def test_search_combined_with_collection_filter(self, client: TestClient):
        """search + collection_id applied together at DB level."""
        coll = client.post("/collections", json={"name": "SearchCollection"}).json()
        cid = coll["id"]

        client.post("/prompts", json={"title": "Match Inside", "content": "C", "collection_id": cid})
        client.post("/prompts", json={"title": "Match Outside", "content": "C"})
        client.post("/prompts", json={"title": "Unrelated Inside", "content": "C", "collection_id": cid})

        resp = client.get(f"/prompts?search=Match&filter=title&fuzzy=false&collection_id={cid}")
        assert resp.status_code == 200
        prompts = resp.json()["prompts"]
        assert len(prompts) == 1
        assert prompts[0]["title"] == "Match Inside"

    def test_empty_search_returns_all_prompts(self, client: TestClient):
        """An empty search string returns all prompts (no filtering)."""
        for i in range(3):
            client.post("/prompts", json={"title": f"Prompt {i}", "content": "Content"})

        resp = client.get("/prompts?search=")
        assert resp.status_code == 200
        assert resp.json()["total"] == 3
