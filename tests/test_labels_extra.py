"""Punto 3: labels-sample-extra muestrea 70 TVN + 30 resto priorizando temas."""

from __future__ import annotations

from faro.cli import _muestrear_extra


def _rows(n_tvn, n_resto):
    rows = []
    for i in range(n_tvn):
        rows.append(
            {"id": f"tvn-{i}", "titulo": f"sismo terremoto en panamá {i}", "fuente_id": "tvn"}
        )
    for i in range(n_resto):
        rows.append({"id": f"g-{i}", "titulo": f"turismo visitantes {i}", "fuente_id": "gdelt"})
    return rows


def test_muestrear_extra_70_30_sin_pendientes():
    rows = _rows(100, 50)
    pendientes = {"tvn-0", "tvn-1", "g-0"}
    muestra = _muestrear_extra(rows, pendientes, n_tvn=70, n_resto=30)
    tvn = [r for r in muestra if r["fuente_id"] == "tvn"]
    resto = [r for r in muestra if r["fuente_id"] != "tvn"]
    assert len(tvn) == 70
    assert len(resto) == 30
    assert all(r["id"] not in pendientes for r in muestra)


def test_muestrear_extra_prioriza_temas():
    rows = []
    for i in range(10):
        rows.append({"id": f"e-{i}", "titulo": f"sismo terremoto {i}", "fuente_id": "tvn"})
    for i in range(10):
        rows.append({"id": f"eco-{i}", "titulo": f"el pib de panamá {i}", "fuente_id": "tvn"})
    muestra = _muestrear_extra(rows, set(), n_tvn=8, n_resto=0)
    temas = [r["tema"] for r in muestra]
    assert temas[:8] == ["eventos_naturales"] * 8  # eventos_naturales antes que economia
