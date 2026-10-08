"""M1.2: GDELT con pausa, reintentos y errores visibles (respuestas simuladas)."""

from __future__ import annotations

import time

from faro.scrape import apis


class _Resp:
    def __init__(self, status_code, data=None):
        self.status_code = status_code
        self._data = data or {"articles": []}

    def json(self):
        return self._data


class _Cliente:
    def __init__(self, respuestas):
        self._resp = list(respuestas)
        self.registro = []

    def get(self, url, fuente_id="", params=None, **kw):
        self.registro.append(url)
        if self._resp:
            status, data = self._resp.pop(0)
        else:
            status, data = 500, None
        return _Resp(status, data)


def _articulo(url="https://www.tvn-2.com/x", titulo="Título TVN", dominio="www.tvn-2.com"):
    return {"url": url, "title": titulo, "domain": dominio, "seendate": "20251005000000"}


def test_429_y_luego_200_recupera(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    c = _Cliente([(429, None), (200, {"articles": [_articulo()]})])
    filas, error = apis.gdelt("domain:tvn-2.com", "20251001000000", "20251031235959", client=c)
    assert error is None
    assert len(filas) == 1
    assert filas[0]["fuente_id"] == "tvn"  # normalizado por dominio (M1.3)
    assert filas[0]["via"] == "gdelt"
    assert filas[0]["fecha_deteccion"] == "20251005000000"
    assert filas[0]["fecha_publicacion"] is None


def test_429_permanente_error(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    c = _Cliente([(429, None), (429, None), (429, None)])
    filas, error = apis.gdelt("domain:tvn-2.com", "20251001000000", "20251031235959", client=c)
    assert filas == []
    assert error and "429" in error


def test_un_error_no_corta_los_demas():
    # A nivel de gdelt, un error devuelve (filas, error) sin lanzar excepción.
    c = _Cliente([(500, None)])
    filas, error = apis.gdelt("q", "20251001000000", "20251031235959", client=c)
    assert filas == []
    assert error is not None
