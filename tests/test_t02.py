"""T02 — Tres registros del mismo evento: agrupa sin perder fuentes ni triplicar."""

from __future__ import annotations

from faro.events.cluster import agrupar_eventos
from faro.events.provenance import procedencias_de_evento
from faro.nlp.embed import Embedder


def _n(titulo, medio, agencia=None):
    return {
        "titulo": titulo,
        "medio": medio,
        "dominio": f"{medio}.com",
        "agencia": agencia,
        "fecha_publicacion": "2026-05-01T00:00:00+00:00",
    }


def test_agrupa_y_cuenta_procedencias():
    noticias = [
        _n("Aumenta el tonelaje del Canal de Panamá", "TVN"),
        _n("Aumenta el tonelaje del Canal de Panamá", "La Prensa"),
        _n("Aumenta el tonelaje del Canal de Panamá (EFE)", "Telemetro", "EFE"),
    ]
    embs = Embedder().encode([n["titulo"] for n in noticias])
    grupos = agrupar_eventos(noticias, embs)
    assert len(grupos) == 1
    proc = procedencias_de_evento(noticias)
    assert proc["n_menciones"] == 3
    assert proc["n_medios"] == 3
    # TVN y La Prensa son independientes + EFE = 3 procedencias (no triplica EFE solo).
    assert proc["n_procedencias"] == 3
    assert proc["agencias"] == ["EFE"]
