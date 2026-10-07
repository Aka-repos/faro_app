"""T08 — Prioridad alta: expone componentes y regla; no habilita publicación."""

from __future__ import annotations

from faro.review.states import puede_publicar
from faro.scoring.score import puntuar_evento


def _evento_alto():
    return {
        "id": "ev-x",
        "tema": "logistica",
        "titulo_canonico": "Récord de tránsito en el Canal de Panamá",
        "fecha_primera": "2026-09-01T00:00:00+00:00",
        "n_medios": 5,
        "n_procedencias": 4,
        "recirculada": False,
    }


def test_expone_componentes_y_regla():
    p = puntuar_evento(_evento_alto(), n_contexto=2, lente="editorial")
    for c in ("R", "I", "U", "N", "E"):
        assert c in p
    assert p["reglas_version"]
    assert p["fecha_referencia"]
    assert p["P"] >= 70  # alto


def test_prioridad_no_publica():
    # Ningún estado, ni siquiera "aprobado como borrador", publica.
    for estado in (
        "nuevo",
        "en revisión",
        "requiere evidencia",
        "aprobado como borrador",
        "descartado",
    ):
        assert puede_publicar(estado) is False


def test_alta_con_evidencia_insuficiente_requiere_evidencia():
    ev = _evento_alto()
    ev["n_procedencias"] = 1  # una sola fuente, sin contexto -> insuficiente
    p = puntuar_evento(ev, n_contexto=0, lente="editorial")
    assert p["estado_evidencia"] == "insuficiente"
    assert puede_publicar("aprobado como borrador") is False
