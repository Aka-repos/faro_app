"""T05 — Dos afirmaciones incompatibles: muestra ambas y la verificación pendiente."""

from __future__ import annotations

from faro.events.contradict import detectar_contradicciones


def test_detecta_cifras_incompatibles():
    noticias = [
        {
            "titulo": "Tránsito del Canal alcanza 1.200 buques en agosto",
            "medio": "TVN",
            "resumen": "",
        },
        {
            "titulo": "Tránsito del Canal cae a 900 buques en agosto",
            "medio": "La Prensa",
            "resumen": "",
        },
    ]
    contras = detectar_contradicciones(noticias)
    assert contras
    c = contras[0]
    assert c["verificacion"] == "pendiente"
    assert len(c["titulos"]) == 2  # ambas versiones


def test_no_escoge_arbitrariamente():
    noticias = [
        {"titulo": "Inflación del 2.1% en el trimestre", "medio": "TVN", "resumen": ""},
        {"titulo": "Inflación del 3.5% en el trimestre", "medio": "Metro Libre", "resumen": ""},
    ]
    contras = detectar_contradicciones(noticias)
    assert contras
    # Reporta ambas cifras (no una sola).
    assert 2.1 in contras[0]["cifras"]
    assert 3.5 in contras[0]["cifras"]
