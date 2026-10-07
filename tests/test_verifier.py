"""Verificador (F-11): ≥15 casos sintéticos de rechazo/aceptación."""

from __future__ import annotations

import pytest

from faro.guard.verifier import verificar_afirmacion, verificar_cifras

EVIDENCIA = "Canal de Panamá registró 1.200 buques en agosto de 2026 (tránsitos totales)."


@pytest.mark.parametrize(
    "afirmacion,lente,solo_titular,esperado,motivo",
    [
        # Aceptaciones
        (
            {
                "texto": "1.200 buques transitaron el Canal en agosto",
                "tipo": "hecho",
                "evidencia_id": "E1",
            },
            "editorial",
            False,
            True,
            None,
        ),
        (
            {"texto": "La tendencia podría continuar", "tipo": "inferencia", "evidencia_id": "E1"},
            "editorial",
            False,
            True,
            None,
        ),
        (
            {"texto": "Según la fuente, hubo récord", "tipo": "declaracion", "evidencia_id": "E1"},
            "editorial",
            False,
            True,
            None,
        ),
        (
            {
                "texto": "Tránsitos totales en agosto de 2026",
                "tipo": "observacion",
                "evidencia_id": "E1",
            },
            "banca",
            False,
            True,
            None,
        ),
        # Rechazos
        (
            {"texto": "1.500 buques transitaron el Canal", "tipo": "hecho", "evidencia_id": "E1"},
            "editorial",
            False,
            False,
            "cifra_no_respaldada",
        ),
        (
            {"texto": "algo sin evidencia", "tipo": "hecho", "evidencia_id": None},
            "editorial",
            False,
            False,
            "sin_evidencia",
        ),
        (
            {
                "texto": "algo con evidencia inexistente",
                "tipo": "hecho",
                "evidencia_id": "NOEXISTE",
            },
            "editorial",
            False,
            False,
            "sin_evidencia",
        ),
        (
            {"texto": "Recomendamos comprar acciones", "tipo": "observacion", "evidencia_id": "E1"},
            "banca",
            False,
            False,
            "frase_prohibida:compra",
        ),
        (
            {"texto": "Habrá pérdidas para la cartera", "tipo": "hipotesis", "evidencia_id": "E1"},
            "banca",
            False,
            False,
            "frase_prohibida:pérdida",
        ),
        (
            {"texto": "El precio del petróleo subió", "tipo": "hecho", "evidencia_id": "E1"},
            "editorial",
            False,
            False,
            "campo_no_respalda",
        ),
        (
            {
                "texto": "Hubo una declaración no atribuida",
                "tipo": "declaracion",
                "evidencia_id": "E1",
            },
            "banca",
            False,
            False,
            "tipo_no_permitido:declaracion",
        ),
        (
            {"texto": "1.200 buques, basado en titular", "tipo": "hecho", "evidencia_id": "E1"},
            "editorial",
            True,
            False,
            "falta_etiqueta_titular",
        ),
        (
            {
                "texto": "basado únicamente en titular/metadatos: 1.200 buques",
                "tipo": "hecho",
                "evidencia_id": "E1",
            },
            "editorial",
            True,
            True,
            None,
        ),
        (
            {
                "texto": "Crédito con riesgo de clientes",
                "tipo": "observacion",
                "evidencia_id": "E1",
            },
            "banca",
            False,
            False,
            "frase_prohibida:riesgo de clientes",
        ),
        (
            {"texto": "Impago de la deuda", "tipo": "hipotesis", "evidencia_id": "E1"},
            "banca",
            False,
            False,
            "frase_prohibida:impago",
        ),
    ],
)
def test_verificador(afirmacion, lente, solo_titular, esperado, motivo):
    ev = EVIDENCIA if afirmacion.get("evidencia_id") == "E1" else None
    ok, rechazo = verificar_afirmacion(afirmacion, ev, lente, solo_titular)
    assert ok is esperado
    if not esperado:
        assert rechazo == motivo


def test_candado_de_cifras():
    assert verificar_cifras("1.200 buques", EVIDENCIA)
    assert not verificar_cifras("9.999 buques", EVIDENCIA)
    # Sin números, pasa (nada que respaldar).
    assert verificar_cifras("sin cifras", EVIDENCIA)
