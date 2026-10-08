"""Punto 1 y 2: GDELT con caché por consulta y rearmado de noticias.jsonl."""

from __future__ import annotations

import json
from datetime import datetime

import config.settings as S
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


def test_recolectar_gdelt_solo_rearma_noticias(monkeypatch, tmp_path):
    raw = tmp_path / "raw"
    reports = tmp_path / "reports"
    raw.mkdir()
    reports.mkdir()
    monkeypatch.setattr(S, "RAW_DIR", raw)
    monkeypatch.setattr(S, "REPORTS_DIR", reports)
    monkeypatch.setattr(collect, "_GDELT_CACHE_DIR", tmp_path / "cache_gdelt")

    def _fake_gdelt(desde, hasta):
        return (
            [
                {
                    "url": "https://gdelt/nueva",
                    "via": "gdelt",
                    "titulo": "nueva",
                    "fecha_publicacion": "2026-01-01T00:00:00Z",
                }
            ],
            {"ok": 1, "errores": 0, "intentos": 1, "detalle": []},
        )

    monkeypatch.setattr(collect, "_recolectar_gdelt", _fake_gdelt)
    raw.joinpath("noticias.jsonl").write_text(
        json.dumps({"url": "https://tvn/x", "via": "sitemap", "titulo": "tvn"})
        + "\n"
        + json.dumps({"url": "https://gdelt/vieja", "via": "gdelt", "titulo": "vieja"})
        + "\n"
    )

    res = collect.recolectar_gdelt_solo()
    lineas = [
        json.loads(x) for x in raw.joinpath("noticias.jsonl").read_text().splitlines() if x.strip()
    ]
    urls = [n["url"] for n in lineas]
    assert "https://tvn/x" in urls  # TVN se conserva
    assert "https://gdelt/nueva" in urls  # GDELT nueva entra
    assert "https://gdelt/vieja" not in urls  # GDELT vieja se reemplaza
    assert res["conteos"]["nuevas_gdelt"] == 1
