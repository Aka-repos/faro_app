"""M1.3: normalización de medios por dominio."""

from __future__ import annotations

from faro.events.provenance import procedencias_de_evento
from faro.scrape.medios import es_institucional, normalizar_medio


def test_tvn_por_dominio():
    assert normalizar_medio("www.tvn-2.com") == ("tvn", "TVN Panamá")
    assert normalizar_medio("tvn-2.com") == ("tvn", "TVN Panamá")


def test_dominio_desconocido_none():
    assert normalizar_medio("sitio-desconocido.com") is None


def test_dominio_vacio_none():
    assert normalizar_medio("") is None


def test_nombres_legibles_medios_adicionales():
    assert normalizar_medio("critica.com.pa") == ("critica", "Crítica")
    assert normalizar_medio("diaadia.com.pa") == ("diaadia", "Día a Día")
    assert normalizar_medio("midiario.com") == ("midiario", "Mi Diario")
    assert normalizar_medio("www.rpctv.com") == ("rpc", "RPC")  # subdominio
    assert normalizar_medio("revistasumma.com") == ("revistasumma", "Revista Summa")


def test_institucional_gob_pa():
    assert es_institucional("mire.gob.pa") is True
    assert es_institucional("asamblea.gob.pa") is True
    assert es_institucional("critica.com.pa") is False


def test_institucional_no_cuenta_como_medio_pero_si_procedencia():
    noticias = [
        {"medio": "TVN Panamá", "dominio": "www.tvn-2.com", "agencia": None},
        {"medio": "mire.gob.pa", "dominio": "mire.gob.pa", "agencia": None},
        {"medio": "asamblea.gob.pa", "dominio": "asamblea.gob.pa", "agencia": None},
    ]
    p = procedencias_de_evento(noticias)
    assert p["n_medios"] == 1  # solo TVN (institucionales excluidas)
    assert p["n_procedencias"] == 3  # las 3 cuentan como procedencia


def test_normalizar_medio_en_ingesta():
    from faro.pipeline import _normalizar_medios

    noticias = [
        {"dominio": "critica.com.pa", "medio": "critica.com.pa"},
        {"dominio": "www.rpctv.com", "medio": "www.rpctv.com"},
        {"dominio": "mire.gob.pa", "medio": "mire.gob.pa"},
        {"dominio": "", "medio": "sin-dominio"},
    ]
    _normalizar_medios(noticias)
    assert noticias[0]["medio"] == "Crítica"
    assert noticias[1]["medio"] == "RPC"
    assert noticias[2]["medio"] == "mire.gob.pa"  # institucional conserva el dominio
    assert noticias[3]["medio"] == "sin-dominio"  # sin dominio no se toca
