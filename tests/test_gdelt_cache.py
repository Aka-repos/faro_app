"""Punto 1: GDELT con caché por consulta (solo respuestas exitosas)."""

from __future__ import annotations

from datetime import datetime

from faro.loaders import load_keywords
from faro.scrape import collect


def _queries_mes():
    temas = [f"({(' OR '.join(palabras[:3]))})" for palabras in load_keywords()["temas"].values()]
    return ["domain:tvn-2.com"] + [f"sourcecountry:PM {t}" for t in temas]


def test_cache_roundtrip(monkeypatch, tmp_path):
    monkeypatch.setattr(collect, "_GDELT_CACHE_DIR", tmp_path)
    collect._gdelt_guardar_cache("202510", "q1", [{"url": "u1"}])
    assert collect._gdelt_leer_cache("202510", "q1") == [{"url": "u1"}]
    assert collect._gdelt_leer_cache("202510", "q2") is None


def test_recolectar_gdelt_salta_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(collect, "_GDELT_CACHE_DIR", tmp_path)
    queries = _queries_mes()
    for q in queries:
        collect._gdelt_guardar_cache("202510", q, [{"url": f"cached-{q}"}])

    llamadas: list[str] = []

    def _fake_gdelt(q, ini, fin, maxrec=250, client=None):
        llamadas.append(q)
        return [], None

    monkeypatch.setattr(collect.apis, "gdelt", _fake_gdelt)
    noticias, g = collect._recolectar_gdelt(datetime(2025, 10, 1), datetime(2025, 11, 1))

    assert llamadas == []  # ninguna petición repetida
    assert g["desde_cache"] == len(queries)
    assert len(noticias) == len(queries)


def test_error_no_se_cachea(monkeypatch, tmp_path):
    monkeypatch.setattr(collect, "_GDELT_CACHE_DIR", tmp_path)

    def _fake_gdelt(q, ini, fin, maxrec=250, client=None):
        return [], "HTTP 429 tras 3 intentos"

    monkeypatch.setattr(collect.apis, "gdelt", _fake_gdelt)
    _noticias, g = collect._recolectar_gdelt(datetime(2025, 10, 1), datetime(2025, 11, 1))
    assert g["errores"] == len(_queries_mes())
    assert list(tmp_path.glob("*.json")) == []  # nada cacheado
