"""Normalización de medios por dominio (M1.3).

Mapa dominio -> (fuente_id, nombre) desde `config/fuentes.yaml`. Las noticias de
GDELT (o de cualquier origen) cuyo dominio sea de un medio del catálogo se
atribuyen a ese medio; si no, quedan como `gdelt`/`<dominio>`.
"""

from __future__ import annotations

from functools import lru_cache

from faro.loaders import load_fuentes

# Medios periodísticos adicionales que no están en el catálogo principal pero sí
# aparecen en GDELT; les damos nombre legible para la UI y el conteo de medios.
_MEDIOS_ADICIONALES = {
    "critica.com.pa": ("critica", "Crítica"),
    "diaadia.com.pa": ("diaadia", "Día a Día"),
    "midiario.com": ("midiario", "Mi Diario"),
    "newsroompanama.com": ("newsroompanama", "Newsroom Panama"),
    "rpctv.com": ("rpc", "RPC"),
    "revistasumma.com": ("revistasumma", "Revista Summa"),
    "tupolitica.com": ("tupolitica", "Tu Política"),
    "elvenezolano.com.pa": ("elvenezolano", "El Venezolano"),
    "thebocasbreeze.com": ("thebocasbreeze", "The Bocas Breeze"),
    "quiuboestereo.com": ("quiuboestereo", "Quiubo Estéreo"),
}


@lru_cache(maxsize=1)
def _mapa() -> list[tuple[str, str, str]]:
    out = []
    for f in load_fuentes():
        if f.get("familia") != "noticias":
            continue
        for d in f.get("dominios", []):
            out.append((d.lower(), f["id"], f["nombre"]))
    return out


def _coincide(dom: str, d: str) -> bool:
    return dom == d or dom.endswith("." + d)


def normalizar_medio(dominio: str) -> tuple[str, str] | None:
    """Devuelve (fuente_id, nombre) si el dominio es de un medio (catálogo o adicional); si no, None."""
    dom = (dominio or "").lower().strip()
    if not dom:
        return None
    for d, fid, nombre in _mapa():
        if _coincide(dom, d):
            return (fid, nombre)
    for d, (fid, nombre) in _MEDIOS_ADICIONALES.items():
        if _coincide(dom, d):
            return (fid, nombre)
    return None


def es_institucional(dominio: str) -> bool:
    """True si el dominio es una fuente institucional (.gob.pa), no un medio periodístico."""
    dom = (dominio or "").lower().strip()
    return dom == "gob.pa" or dom.endswith(".gob.pa")
