"""Fixtures compartidas: construyen el snapshot de pruebas en una carpeta temporal.

WP-1.7: las pruebas **nunca** tocan la base real de la demo. Se usa `tempfile`
y variables `FARO_DATA_DIR`/`FARO_DB` antes de importar `config.settings`.
"""

from __future__ import annotations

import os
import pathlib
import tempfile

_TMP = pathlib.Path(tempfile.mkdtemp(prefix="faro-tests-"))
os.environ["FARO_DATA_DIR"] = str(_TMP)
os.environ["FARO_DB"] = str(_TMP / "faro.db")
os.environ["FARO_PERMITIR_SINTETICO"] = "1"  # solo pruebas
os.environ.setdefault("FARO_PERMITIR_FALLBACK", "1")  # embeddings por hashing en tests

import pytest  # noqa: E402

import config.settings as S  # noqa: E402
from faro import db, pipeline, seed  # noqa: E402


@pytest.fixture(scope="session")
def built_db():
    """Construye el pipeline completo (seed sintético en tempdir) una sola vez."""
    S.ensure_dirs()
    seed.write_raw()
    pipeline.build()
    return str(S.DB_PATH)


@pytest.fixture()
def conn(built_db):
    c = db.connect(built_db)
    yield c
    c.close()
