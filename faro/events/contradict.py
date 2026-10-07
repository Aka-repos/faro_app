"""Detección de contradicciones (F-09, T05).

Compara cifras y entidades incompatibles dentro de un evento. No escoge
arbitrariamente: muestra ambas versiones y deja la verificación pendiente.
"""

from __future__ import annotations

import re

_NUMERO = re.compile(r"(\d[\d.,]*)\s*(%|millones|miles|millones de dólares|USD|buques)?")


def _cifras(texto: str) -> set[tuple[float, str]]:
    out = set()
    for m in _NUMERO.finditer(texto):
        try:
            num = float(m.group(1).replace(",", ""))
        except ValueError:
            continue
        out.add((num, m.group(2) or ""))
    return out


def detectar_contradicciones(noticias: list[dict]) -> list[dict]:
    """Devuelve pares de afirmaciones incompatibles (misma unidad, cifras dispares)."""
    resultados = []
    por_unidad: dict[str, dict] = {}
    for nc in noticias:
        for num, unidad in _cifras(nc["titulo"] + " " + (nc.get("resumen") or "")):
            key = unidad or "sin_unidad"
            if key not in por_unidad:
                por_unidad[key] = {"valores": {}, "fuentes": []}
            por_unidad[key]["valores"][num] = nc["titulo"]
            por_unidad[key]["fuentes"].append(
                {"titulo": nc["titulo"], "medio": nc["medio"], "cifra": num}
            )

    for unidad, data in por_unidad.items():
        valores = sorted(data["valores"])
        if len(valores) < 2:
            continue
        # Incompatibilidad: difieren más de un 15% entre extremos.
        lo, hi = valores[0], valores[-1]
        if lo > 0 and (hi - lo) / lo > 0.15:
            resultados.append(
                {
                    "unidad": unidad,
                    "cifras": [lo, hi],
                    "titulos": [data["valores"][lo], data["valores"][hi]],
                    "verificacion": "pendiente",
                    "nota": "Dos cifras incompatibles del mismo evento; mostrar ambas versiones.",
                }
            )
    return resultados
