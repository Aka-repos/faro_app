"""Puntaje de atención (F-07, T08) y estado de evidencia.

P = 30R + 25I + 20U + 15N + 10E, con cada componente normalizado a 0–1.
El estado de evidencia es **independiente** del puntaje (una prioridad alta con
evidencia insuficiente sigue siendo "requiere evidencia", no habilita publicar).
"""

from __future__ import annotations

from datetime import UTC, datetime

import config.settings as S
from faro.loaders import load_lente

_PANAMA_TOKENS = [
    "panamá",
    "panama",
    "canal",
    "chiriquí",
    "colón",
    "david",
    "balboa",
    "gatún",
    "metro de panamá",
    "zona libre",
    "asamblea",
    "banco central",
]

_TEMA_PRIORIDAD = {
    "economia": 1.0,
    "logistica": 1.0,
    "turismo": 0.9,
    "servicios_publicos": 0.85,
    "eventos_naturales": 0.8,
    "regulacion": 0.7,
    "sin_tema": 0.3,
}


def _iso_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
    except ValueError:
        return None


def _ref_dt() -> datetime:
    return _iso_dt(S.FECHA_REFERENCIA) or datetime.now(UTC)


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def _panama_score(titulo: str) -> float:
    t = (titulo or "").lower()
    hits = sum(1 for tok in _PANAMA_TOKENS if tok in t)
    return 1.0 if hits > 0 else 0.5


def _urgencia(fecha_primera: str | None) -> float:
    """Recencia relativa a la ventana: más reciente = más urgente."""
    fp = _iso_dt(fecha_primera)
    if fp is None:
        return 0.5
    start, end = S.VENTANA_INICIO, S.VENTANA_FIN
    frac = (fp - start).total_seconds() / max(1.0, (end - start).total_seconds())
    return _clamp(frac)


def puntuar_evento(ev: dict, n_contexto: int = 0, lente: str = "editorial") -> dict:
    """Calcula R,I,U,N,E, P, rango y estado de evidencia para un evento."""
    pesos = load_lente(lente)["pesos"]
    titulo = ev.get("titulo_canonico", "")
    n_medios = max(1, int(ev.get("n_medios", 1)))
    n_proc = max(0, int(ev.get("n_procedencias", 0)))
    recirculada = bool(ev.get("recirculada", False))

    R = _clamp(0.5 * _panama_score(titulo) + 0.5 * _TEMA_PRIORIDAD.get(ev.get("tema", ""), 0.5))
    impacto = _clamp(0.4 * (n_medios / 5) + 0.3 * (n_proc / 3) + 0.3 * (1.0 if n_contexto else 0.0))
    U = _urgencia(ev.get("fecha_primera"))
    N = _clamp(0.6 * (0.3 if recirculada else 1.0) + 0.4 * (n_proc / 3))
    E = _clamp(0.6 * (n_proc / 3) + 0.4 * (n_contexto / 3))

    P = pesos["R"] * R + pesos["I"] * impacto + pesos["U"] * U + pesos["N"] * N + pesos["E"] * E
    P = round(P, 1)

    rangos = load_lente(lente)["rangos"]
    rango = "medio"
    if P < rangos["bajo"]["max"]:
        rango = "bajo"
    elif P >= rangos["alto"]["min"]:
        rango = "alto"

    # Estado de evidencia, independiente del puntaje (T08).
    if n_proc >= 2 and n_contexto >= 1:
        estado = "suficiente para el borrador"
    elif n_proc <= 1 and n_contexto == 0:
        estado = "insuficiente"
    else:
        estado = "parcial"

    return {
        "evento_id": ev["id"],
        "lente": lente,
        "R": round(R, 3),
        "I": round(impacto, 3),
        "U": round(U, 3),
        "N": round(N, 3),
        "E": round(E, 3),
        "P": P,
        "rango": rango,
        "estado_evidencia": estado,
        "reglas_version": S.REGLAS_VERSION,
        "fecha_referencia": S.FECHA_REFERENCIA,
    }


def ordenar_ranking(puntajes: list[dict]) -> list[dict]:
    """Ordena por P desc; empate por mayor urgencia (U) y luego por ID (D-09)."""
    return sorted(puntajes, key=lambda p: (-p["P"], -p["U"], p["evento_id"]))
