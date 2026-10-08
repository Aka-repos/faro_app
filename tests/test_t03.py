"""T03 — Noticia antigua recirculada: conserva fecha original, no es evento nuevo."""

from __future__ import annotations

from faro.events.cluster import agrupar_eventos
from faro.nlp.embed import Embedder
from faro.quality.validate import validar_noticia


def test_recirculada_conserva_fecha_original():
    raw = {
        "tipo": "noticia",
        "id": "old",
        "fuente_id": "tvn",
        "titulo": "Superávit fiscal (recirculada)",
        "url": "https://a.b/old",
        "medio": "TVN",
        "fecha_publicacion": "2025-09-01T00:00:00+00:00",  # antes de la ventana
        "fecha_deteccion": "2026-06-01T00:00:00+00:00",
    }  # detectada dentro de la ventana
    rec, motivo = validar_noticia(raw)
    assert rec is not None and motivo is None
    # Conserva la fecha original (no se reescribe a la de detección).
    assert rec["fecha_publicacion"].startswith("2025-09-01")
    assert rec["fecha_deteccion"].startswith("2026-06-01")


def test_recirculada_no_se_fusiona_con_evento_reciente():
    noticias = [
        {
            "titulo": "Panamá cierra año fiscal con superávit",
            "medio": "TVN",
            "fecha_publicacion": "2026-06-01T00:00:00+00:00",
        },
        {
            "titulo": "Panamá cierra año fiscal con superávit (recirculada)",
            "medio": "Telemetro",
            "fecha_publicacion": "2025-09-01T00:00:00+00:00",
        },  # vieja: fuera de la ventana de 72h
    ]
    embs = Embedder().encode([n["titulo"] for n in noticias])
    grupos = agrupar_eventos(noticias, embs, ventana_h=72)
    # La recirculada queda en su propio grupo (no se fusiona por la ventana temporal).
    assert len(grupos) == 2


def test_gdelt_sin_pub_y_tvn_mismo_evento():
    # GDELT sin fecha_publicacion (solo deteccion) + TVN del mismo día -> mismo evento.
    noticias = [
        {
            "titulo": "Canasta básica sube en octubre",
            "medio": "GDELT",
            "fecha_publicacion": None,
            "fecha_deteccion": "2026-06-01T00:00:00+00:00",
        },
        {
            "titulo": "Canasta básica sube en octubre",
            "medio": "TVN Panamá",
            "fecha_publicacion": "2026-06-01T03:00:00+00:00",
            "fecha_deteccion": None,
        },
    ]
    embs = Embedder().encode([n["titulo"] for n in noticias])
    grupos = agrupar_eventos(noticias, embs, ventana_h=72)
    assert len(grupos) == 1  # fecha efectiva los une en el mismo evento
