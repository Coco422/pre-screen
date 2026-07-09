"""Shared SQLAlchemy engine / connection helpers."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine

from pre_screen_common.settings import AppSettings, get_settings


@lru_cache(maxsize=4)
def _engine_for(dsn: str) -> Engine:
    return create_engine(dsn, pool_pre_ping=True, future=True)


def get_engine(dsn: str | None = None, *, settings: AppSettings | None = None) -> Engine:
    if dsn is None:
        cfg = settings or get_settings()
        dsn = cfg.postgres_dsn
    return _engine_for(dsn)


def reset_engine_cache() -> None:
    """Test helper: drop cached engines."""
    _engine_for.cache_clear()


@contextmanager
def db_connection(
    dsn: str | None = None,
    *,
    settings: AppSettings | None = None,
) -> Iterator[Connection]:
    engine = get_engine(dsn, settings=settings)
    with engine.begin() as conn:
        yield conn


def ping_database(dsn: str | None = None) -> bool:
    try:
        with db_connection(dsn) as conn:
            conn.execute(text("select 1"))
        return True
    except Exception:
        return False
