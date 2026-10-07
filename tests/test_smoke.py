"""Pruebas de humo (H0): el paquete importa y el pipeline construye."""

from __future__ import annotations


def test_import_paquete():
    import faro  # noqa: F401
    from faro import db, evidence, pipeline  # noqa: F401

    assert faro.__version__


def test_schema_crea_tablas():
    from faro import db

    conn = db.connect(":memory:")
    tablas = {r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for t in (
        "fuente",
        "noticia",
        "serie_oficial",
        "indicador",
        "sismo",
        "cuarentena",
        "evento",
        "evento_noticia",
        "entidad",
        "evento_contexto",
        "evento_puntaje",
        "sector",
        "ficha",
        "afirmacion",
        "traza_agente",
        "ejecucion",
    ):
        assert t in tablas
    conn.close()


def test_build_produce_datos(built_db):
    from faro import db

    conn = db.connect(built_db)
    n = conn.execute("SELECT COUNT(*) c FROM noticia").fetchone()[0]
    e = conn.execute("SELECT COUNT(*) c FROM evento").fetchone()[0]
    conn.close()
    assert n >= 100
    assert e >= 5


def test_medio_principal_minimo_20(built_db):
    from faro import db, seed

    conn = db.connect(built_db)
    n = conn.execute(
        "SELECT COUNT(*) c FROM noticia WHERE medio=?", (seed.MEDIO_PRINCIPAL,)
    ).fetchone()[0]
    conn.close()
    assert n >= 20
