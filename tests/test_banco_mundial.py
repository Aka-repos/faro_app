"""Punto 7: Banco Mundial con PoliteClient (pausa 1 s, timeout 30 s, fallos registrados)."""

from __future__ import annotations

from faro.scrape import apis, politeness


class _Resp:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or [{"page": 1}, []]
        self.content = b""

    def json(self):
        return self._payload


def test_banco_mundial_devuelve_tupla_y_registra_fallos(monkeypatch):
    def _fail(self, url, fuente_id="", params=None, **kw):
        return None  # simula fallo de red

    monkeypatch.setattr(politeness.PoliteClient, "get", _fail)
    obs, fallos = apis.banco_mundial()
    assert obs == []
    assert len(fallos) == len(apis.WB_COUNTRIES) * len(apis.WB_INDICATORS)


def test_banco_mundial_extrae_observados(monkeypatch):
    def _ok(self, url, fuente_id="", params=None, **kw):
        return _Resp(payload=[{"page": 1}, [{"date": "2023", "value": 5.0}]])

    monkeypatch.setattr(politeness.PoliteClient, "get", _ok)
    obs, fallos = apis.banco_mundial()
    assert fallos == []
    assert any(o["valor"] == 5.0 for o in obs)


def test_politeclient_timeout_parametro():
    c = politeness.PoliteClient(rate_limit_s=1.0, timeout=30.0)
    assert c.client.timeout.read == 30.0
