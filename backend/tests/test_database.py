"""Tests for app/database.py — engine, session factory, and settings.

Tests exercise the lazy-init paths that are bypassed by conftest.py
(which pre-sets _engine to avoid connection-pool issues in pytest).
"""

from __future__ import annotations

import os
import pytest
from unittest.mock import patch, MagicMock
import app.database as db_module
from app.database import Settings, get_settings, AsyncSessionLocal


@pytest.fixture(autouse=True)
def reset_db_globals():
    """Save and restore the module-level engine/factory globals around each test."""
    orig_engine = db_module._engine
    orig_factory = db_module._session_factory
    yield
    db_module._engine = orig_engine
    db_module._session_factory = orig_factory


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Clear lru_cache on get_settings so env vars take effect."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


class TestSettings:
    def test_default_database_url(self):
        """Settings must have a sensible default database URL."""
        s = Settings()
        assert "postgresql" in s.database_url
        assert "promptlab" in s.database_url

    def test_default_api_key_is_empty(self):
        """API key defaults to empty string (auth disabled by default)."""
        s = Settings()
        assert s.api_key == ""

    def test_default_test_database_url_is_empty(self):
        """test_database_url defaults to empty string."""
        env = os.environ.copy()
        env.pop("TEST_DATABASE_URL", None)
        with patch.dict(os.environ, env, clear=True):
            s = Settings()
            assert s.test_database_url == ""


class TestGetSettings:
    def test_returns_settings_instance(self):
        """get_settings() must return a Settings instance."""
        result = get_settings()
        assert isinstance(result, Settings)

    def test_cached_returns_same_object(self):
        """get_settings() must return the same object on repeated calls (lru_cache)."""
        first = get_settings()
        second = get_settings()
        assert first is second


class TestGetEngine:
    def test_creates_engine_when_none(self):
        """get_engine() must create and cache an engine when _engine is None."""
        db_module._engine = None
        db_module._session_factory = None  # reset dependent factory too

        mock_engine = MagicMock()
        with patch("app.database.create_async_engine", return_value=mock_engine) as mock_create:
            result = db_module.get_engine()
            assert result is mock_engine
            mock_create.assert_called_once()
            # Verify key settings were passed
            kwargs = mock_create.call_args[1]
            assert kwargs.get("pool_pre_ping") is True

    def test_cached_on_second_call(self):
        """get_engine() must return the same engine on repeated calls."""
        db_module._engine = None
        db_module._session_factory = None

        mock_engine = MagicMock()
        with patch("app.database.create_async_engine", return_value=mock_engine) as mock_create:
            first = db_module.get_engine()
            second = db_module.get_engine()
            assert first is second
            mock_create.assert_called_once()

    def test_returns_existing_engine(self):
        """get_engine() must return the pre-set engine without calling create_async_engine."""
        existing = MagicMock()
        db_module._engine = existing

        with patch("app.database.create_async_engine") as mock_create:
            result = db_module.get_engine()
            mock_create.assert_not_called()
        assert result is existing


class TestGetSessionFactory:
    def test_creates_factory_when_none(self):
        """get_session_factory() must create and cache a session factory when None."""
        db_module._session_factory = None

        mock_factory = MagicMock()
        with patch("app.database.async_sessionmaker", return_value=mock_factory) as mock_maker:
            result = db_module.get_session_factory()
            assert result is mock_factory
            mock_maker.assert_called_once()
            kwargs = mock_maker.call_args[1]
            assert kwargs.get("expire_on_commit") is False

    def test_cached_on_second_call(self):
        """get_session_factory() must return the same factory on repeated calls."""
        db_module._session_factory = None

        mock_factory = MagicMock()
        with patch("app.database.async_sessionmaker", return_value=mock_factory) as mock_maker:
            first = db_module.get_session_factory()
            second = db_module.get_session_factory()
            assert first is second
            mock_maker.assert_called_once()

    def test_returns_existing_factory(self):
        """get_session_factory() must return the pre-set factory without recreating it."""
        existing = MagicMock()
        db_module._session_factory = existing

        with patch("app.database.async_sessionmaker") as mock_maker:
            result = db_module.get_session_factory()
            mock_maker.assert_not_called()
        assert result is existing


class TestAsyncSessionLocal:
    def test_returns_session_object(self):
        """AsyncSessionLocal() must call the session factory and return a session."""
        mock_session = MagicMock()
        mock_factory = MagicMock(return_value=mock_session)
        db_module._session_factory = mock_factory

        result = AsyncSessionLocal()
        mock_factory.assert_called_once()
        assert result is mock_session


class TestInitDb:
    async def test_init_db_runs_idempotently(self):
        """init_db() creates tables and indexes; idempotent due to IF NOT EXISTS guards."""
        from app.database import init_db
        # Runs against the test DB (already set up by conftest); IF NOT EXISTS makes it safe
        await init_db()  # should complete without error
