"""H8/B-xx: lente bancario — sectores, barreras y boletín."""

from __future__ import annotations

from faro.guard.verifier import frases_prohibidas, verificar_afirmacion
from faro.lenses.banca import mapear_sectores
from faro.llm.extractive import generar_boletin


def _evento_logistica():
    return {
        "id": "ev-1",
        "tema": "logistica",
        "titulo_canonico": "Tránsito del Canal de Panamá sube",
        "n_menciones": 3,
        "n_medios": 3,
        "n_procedencias": 2,
    }


def test_mapeo_evento_a_sector():
    sectores = mapear_sectores(_evento_logistica(), [{"titulo": "Más buques cruzan el Canal"}])
    ids = [s["sector_id"] for s in sectores]
    assert "logistica" in ids
    assert any("regla" in s for s in sectores)


def test_boletin_sin_frases_prohibidas():
    afirm = [
        {
            "texto": "El Canal registró 1.200 buques en agosto",
            "tipo": "observacion",
            "evidencia_id": "E1",
            "campo": "valor",
        }
    ]
    out = generar_boletin(_evento_logistica(), afirm, ["Logística y transporte"])
    texto = " ".join([out["resumen"]] + out["observaciones"] + out["hipotesis"])
    for frase in frases_prohibidas("banca"):
        assert frase not in texto.lower()


def test_verificador_rechaza_recomendacion_de_compra():
    ok, motivo = verificar_afirmacion(
        {"texto": "Recomendamos comprar acciones", "tipo": "observacion", "evidencia_id": "E1"},
        "El Canal registró 1.200 buques",
        lente="banca",
    )
    assert not ok
    assert "frase_prohibida" in motivo


def test_hipotesis_siempre_marcada():
    afirm = [
        {"texto": "El Canal registró 1.200 buques", "tipo": "observacion", "evidencia_id": "E1"},
        {"texto": "Podría presionar tarifas logísticas", "tipo": "hipotesis", "evidencia_id": None},
    ]
    out = generar_boletin(_evento_logistica(), afirm, ["Logística"])
    assert out["hipotesis"]
    assert out["observaciones"]
