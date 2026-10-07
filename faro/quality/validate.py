"""Validación y calidad (F-02, T01).

Lee el JSONL crudo, valida cada registro con Pydantic, separa los inválidos en
``cuarentena`` (con su motivo), conserva nulos sin rellenar con cero y deduplica
por URL normalizada. La carga nunca se bloquea: un registro malo se aparta.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from urllib.parse import urlparse

from pydantic import ValidationError

import config.settings as S
from schemas import Indicador, RegistroNoticia, SerieOficial, Sismo


def _iso_utc(s: str | None) -> datetime | None:
    if s is None or s == "":
        return None
    if isinstance(s, datetime):
        return s.astimezone(UTC)
    try:
        dt = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)
    except ValueError:
        return None


def normalize_url(url: str) -> str:
    u = urlparse(url.strip())
    return f"{u.netloc.lower()}{u.path.rstrip('/')}"


def _en_ventana(dt: datetime | None) -> bool:
    if dt is None:
        return False
    return S.VENTANA_INICIO <= dt < S.VENTANA_FIN


def validar_noticia(raw: dict) -> tuple[dict | None, str | None]:
    """Valida una noticia cruda. Devuelve (registro_normalizado|None, motivo_rechazo|None)."""
    # Fecha de publicación obligatoria y válida (T01: separar errores).
    pub = _iso_utc(raw.get("fecha_publicacion"))
    if raw.get("fecha_publicacion") and pub is None:
        return None, "fecha_publicacion_invalida"
    det = _iso_utc(raw.get("fecha_deteccion"))
    if raw.get("fecha_deteccion") and det is None:
        return None, "fecha_deteccion_invalida"
    # La fecha de "ventana" es la de detección (cuándo lo vimos) o la publicación.
    fecha_ventana = det or pub
    if fecha_ventana is not None and not _en_ventana(fecha_ventana):
        return None, "fuera_de_ventana"

    try:
        reg = RegistroNoticia(**{k: v for k, v in raw.items() if k in RegistroNoticia.model_fields})
    except ValidationError as e:
        return None, f"schema:{_primera(e)}"
    return reg.model_dump(), None


def validar_serie(raw: dict) -> tuple[dict | None, str | None]:
    try:
        reg = SerieOficial(**{k: v for k, v in raw.items() if k in SerieOficial.model_fields})
    except ValidationError as e:
        return None, f"schema:{_primera(e)}"
    return reg.model_dump(), None


def validar_indicador(raw: dict) -> tuple[dict | None, str | None]:
    try:
        reg = Indicador(**{k: v for k, v in raw.items() if k in Indicador.model_fields})
    except ValidationError as e:
        return None, f"schema:{_primera(e)}"
    return reg.model_dump(), None


def validar_sismo(raw: dict) -> tuple[dict | None, str | None]:
    try:
        reg = Sismo(**{k: v for k, v in raw.items() if k in Sismo.model_fields})
    except ValidationError as e:
        return None, f"schema:{_primera(e)}"
    return reg.model_dump(), None


def _primera(e: ValidationError) -> str:
    try:
        return "; ".join(f"{err['loc']}:{err['msg']}" for err in e.errors()[:2])
    except Exception:  # noqa: BLE001
        return "schema"


def load_raw() -> dict[str, list[dict]]:
    """Carga todos los JSONL crudos de ``data/raw/``."""
    out: dict[str, list[dict]] = {"noticia": [], "serie_oficial": [], "indicador": [], "sismo": []}
    mapeo = {
        "noticias.jsonl": "noticia",
        "series.jsonl": "serie_oficial",
        "indicadores.jsonl": "indicador",
        "sismos.jsonl": "sismo",
    }
    if not S.RAW_DIR.exists():
        return out
    for fname, key in mapeo.items():
        path = S.RAW_DIR / fname
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out[key].append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


VALIDATORS = {
    "noticia": validar_noticia,
    "serie_oficial": validar_serie,
    "indicador": validar_indicador,
    "sismo": validar_sismo,
}


def validar_todo(raw: dict[str, list[dict]] | None = None) -> dict:
    """Valida todo el snapshot y devuelve normalizados + cuarentena."""
    raw = raw or load_raw()
    resultado = {"noticia": [], "serie_oficial": [], "indicador": [], "sismo": [], "cuarentena": []}
    seen_urls: set[str] = set()
    for key, rows in raw.items():
        fn = VALIDATORS[key]
        for r in rows:
            rec, motivo = fn(r)
            if rec is None:
                resultado["cuarentena"].append(
                    {
                        "fuente_id": r.get("fuente_id", r.get("pais_iso3", "")),
                        "fila_raw": json.dumps(r, ensure_ascii=False)[:300],
                        "motivo": motivo,
                    }
                )
                continue
            if key == "noticia":
                # Dedup por URL normalizada (F-02).
                nu = normalize_url(rec["url"])
                if nu in seen_urls:
                    continue
                seen_urls.add(nu)
            resultado[key].append(rec)
    return resultado
