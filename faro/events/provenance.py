"""Procedencias (F-05, CU-03): cuántas fuentes son realmente independientes.

Una agencia replicada por 5 medios cuenta como **una** procedencia. Dos medios
que publican el mismo titular sin agencia cuentan como procedencias separadas
solo si son dominios distintos y no son casi-duplicados de una misma agencia.
"""

from __future__ import annotations

from faro.scrape.medios import es_institucional


def procedencias_de_evento(noticias: list[dict]) -> dict:
    """Dado las noticias de un evento, devuelve el desglose de procedencias."""
    agencias: set[str] = set()
    medios: set[str] = set()
    dominios: set[str] = set()
    sin_agencia: set[str] = set()

    for nc in noticias:
        dominios.add(nc.get("dominio", ""))
        ag = nc.get("agencia")
        if ag:
            agencias.add(ag)
        else:
            sin_agencia.add(nc["medio"])
        # Las fuentes institucionales (.gob.pa) cuentan como procedencia pero no como medio.
        if not es_institucional(nc.get("dominio", "")):
            medios.add(nc["medio"])

    # Cada agencia cuenta como una procedencia; cada medio sin agencia también.
    procedencias = sorted(agencias) + sorted(sin_agencia)
    return {
        "n_menciones": len(noticias),
        "n_medios": len(medios),
        "n_procedencias": len(procedencias),
        "agencias": sorted(agencias),
        "medios_sin_agencia": sorted(sin_agencia),
        "procedencias": procedencias,
    }


def es_replicacion(procedencias: dict) -> bool:
    """True si varias menciones provienen de una única procedencia (CU-03)."""
    return procedencias["n_menciones"] > 1 and procedencias["n_procedencias"] == 1
