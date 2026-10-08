"""M1.3: normalización de medios por dominio."""

from __future__ import annotations

from faro.scrape.medios import normalizar_medio


def test_tvn_por_dominio():
    assert normalizar_medio("www.tvn-2.com") == ("tvn", "TVN Panamá")
    assert normalizar_medio("tvn-2.com") == ("tvn", "TVN Panamá")


def test_dominio_desconocido_none():
    assert normalizar_medio("sitio-desconocido.com") is None


def test_dominio_vacio_none():
    assert normalizar_medio("") is None
