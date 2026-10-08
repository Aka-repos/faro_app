"""Correcciones al recolector (antes de H-3): una prueba por punto."""

from __future__ import annotations

import time
from datetime import datetime

import config.settings as S
from faro.scrape import apis, collect, oficiales, politeness


# --- Punto 1: GDELT reintenta 10/20/40 s con respuesta 429 (no None) ----------
class _Resp:
    def __init__(self, status_code, data=None):
        self.status_code = status_code
        self._data = data or {"articles": []}
        self.content = b""

    def json(self):
        return self._data


class _Cliente429:
    def __init__(self, respuestas):
        self._resp = list(respuestas)
        self.registro = []

    def get(self, url, fuente_id="", sin_reintentos=False, params=None, **kw):
        self.registro.append(url)
        if self._resp:
            status, data = self._resp.pop(0)
        else:
            status, data = 500, None
        return _Resp(status, data)


def _art():
    return {
        "url": "https://www.tvn-2.com/x",
        "title": "T",
        "domain": "www.tvn-2.com",
        "seendate": "20251005000000",
    }


def test_gdelt_reintenta_429(monkeypatch):
    sleeps = []
    monkeypatch.setattr(time, "sleep", lambda s: sleeps.append(s))
    c = _Cliente429([(429, None), (429, None), (200, {"articles": [_art()]})])
    filas, error = apis.gdelt("domain:tvn-2.com", "20251001000000", "20251031235959", client=c)
    assert error is None
    assert len(filas) == 1
    assert sleeps == [10, 20]  # reintentos 10 y 20 s, luego 200


def test_politeness_devuelve_429_no_none(monkeypatch):
    # sin_reintentos=True -> devuelve la respuesta 429, no None.
    monkeypatch.setattr(time, "sleep", lambda s: None)
    monkeypatch.setattr(politeness.PoliteClient, "robots_permite", lambda self, u: (None, "ok"))
    c = politeness.PoliteClient(rate_limit_s=0)

    # Reemplazar el httpx.Client interno por un fake.
    class _FakeH:
        def get(self, url, **kw):
            return _Resp(429)

    c.client = _FakeH()
    resp = c.get("https://api.gdeltproject.org/x", fuente_id="gdelt", sin_reintentos=True)
    assert resp is not None
    assert resp.status_code == 429


# --- Punto 2: _meses con hasta exclusivo -------------------------------------
def test_meses_hasta_exclusivo():
    desde = datetime(2025, 10, 1)
    hasta = datetime(2025, 11, 1)
    assert collect._meses(desde, hasta) == [("20251001000000", "20251031235959")]


def test_meses_corrida_completa_termina_202609():
    desde = datetime(2025, 10, 2)
    hasta = datetime(2026, 10, 1)
    meses = collect._meses(desde, hasta)
    assert meses[0][0].startswith("202510")
    assert meses[-1][0].startswith("202609")
    assert len(meses) == 12


# --- Punto 3: ≥ 4 medios nacionales y deshabilitados con motivo ---------------
def test_fuentes_cuatro_medios():
    from faro.loaders import load_fuentes

    medios = [f for f in load_fuentes() if f.get("familia") == "noticias" and f["id"] != "gdelt"]
    activos = [f for f in medios if not f.get("deshabilitado")]
    assert len(activos) >= 4
    for f in medios:
        if f.get("deshabilitado"):
            assert f.get("motivo_deshabilitado")


# --- Punto 4: --prueba lee manual/*.csv del repo ------------------------------
def test_manual_csv_se_lee_del_repo(monkeypatch, tmp_path):
    monkeypatch.setattr(S, "RAW_DIR", tmp_path / "raw")  # simula --prueba (RAW_DIR temporal)
    filas = oficiales.inec()
    assert len(filas) > 0  # S.MANUAL_DIR sigue apuntando al repo


# --- Punto 5: reporte parcial se guarda --------------------------------------
def test_reporte_parcial_escribe_archivo(monkeypatch, tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    monkeypatch.setattr(S, "REPORTS_DIR", reports)
    collect._escribir_reporte_parcial({"tv": {"ok": 1}}, 1)
    parciales = list(reports.glob("*_parcial.json"))
    assert len(parciales) == 1


# --- Punto 6: filtro de ventana ----------------------------------------------
def test_en_ventana():
    assert collect._en_ventana("2026-06-01T00:00:00+00:00") is True
    assert collect._en_ventana("2020-01-01T00:00:00+00:00") is False
    assert collect._en_ventana("2026-12-01T00:00:00+00:00") is False
    assert collect._en_ventana(None) is True
