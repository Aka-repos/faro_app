"""Fixtures compartidas: construyen el snapshot y la base una sola vez por sesión."""

from __future__ import annotations

import pytest

import config.settings as S
from faro import db, pipeline


@pytest.fixture(scope="session")
def built_db():
    """Construye el pipeline completo (seed sintético -> SQLite -> capas deducidas)."""
    S.ensure_dirs()
    pipeline.build()
    return str(S.DB_PATH)


@pytest.fixture()
def conn(built_db):
    c = db.connect(built_db)
    yield c
    c.close()
