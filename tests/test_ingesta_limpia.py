"""Punto 5: la ingesta limpia la Capa 1 antes de cargar (sin acumular cuarentena)."""
from __future__ import annotations

from faro import db
from faro.pipeline import ingesta


def test_ingesta_no_acumula_cuarentena(built_db):
    conn = db.connect(built_db)
    # Fila "vieja" que no debe sobrevivir a la siguiente ingesta.
    conn.execute(
        "INSERT INTO cuarentena (fuente_id, fila_raw, motivo) VALUES ('viejo','{}','sintetico_no_permitido')"
    )
    conn.commit()

    ingesta(conn)

    n = conn.execute("SELECT COUNT(*) c FROM cuarentena WHERE fuente_id='viejo'").fetchone()[0]
    conn.close()
    assert n == 0
