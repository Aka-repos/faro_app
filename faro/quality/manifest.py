"""Manifest del snapshot (F-03): versión, corte, conteos, SHA-256 y condiciones."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import config.settings as S
from faro.loaders import load_fuentes


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def file_hashes(raw_dir: Path) -> dict[str, str]:
    return {p.name: _sha256(p) for p in sorted(raw_dir.glob("*.jsonl"))}


def build_manifest(conteos: dict[str, int], raw_dir: Path | None = None) -> dict:
    raw_dir = raw_dir or S.RAW_DIR
    fuentes = load_fuentes()
    manifest = {
        "version": "v1",
        "fecha_corte_UTC": datetime.now(UTC).isoformat(),
        "consultas": {
            "ventana": [S.VENTANA_INICIO.isoformat(), S.VENTANA_FIN.isoformat()],
            "paises": ["PAN", "CRI", "COL", "DOM", "MEX", "GTM"],
            "indicadores": [
                "NY.GDP.MKTP.KD.ZG",
                "FP.CPI.TOTL.ZG",
                "SL.UEM.TOTL.ZS",
                "SP.POP.TOTL",
                "IT.NET.USER.ZS",
                "NE.EXP.GNFS.ZS",
            ],
            "usgs_caja": {"lat": [5, 12], "lon": [-86, -76], "minmag": 3.0},
        },
        "cantidad_por_archivo": conteos,
        "licencia_condiciones": [
            {
                "fuente": f["id"],
                "licencia": f.get("licencia", ""),
                "condiciones": f.get("condiciones", ""),
            }
            for f in fuentes
        ],
        "transformaciones": [
            "normalización de fechas a ISO 8601 UTC",
            "deduplicación por URL normalizada",
            "nulos conservados (nunca rellenados con cero)",
            "registros inválidos a cuarentena con motivo",
            "sintético: el seed es un corpus de demostración, no datos reales",
        ],
        "sha256": file_hashes(raw_dir),
    }
    return manifest


def write_manifest(manifest: dict) -> Path:
    S.ensure_dirs()
    S.MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    return S.MANIFEST_PATH


def verify_manifest() -> dict:
    """Recalcula hashes y los compara con manifest.json (make verify-snapshot)."""
    if not S.MANIFEST_PATH.exists():
        return {"ok": False, "error": "manifest.json no existe"}
    actual = file_hashes(S.RAW_DIR)
    guardado = json.loads(S.MANIFEST_PATH.read_text(encoding="utf-8")).get("sha256", {})
    diferencias = []
    for name in sorted(set(actual) | set(guardado)):
        if actual.get(name) != guardado.get(name):
            diferencias.append(
                {"archivo": name, "manifest": guardado.get(name), "disco": actual.get(name)}
            )
    return {"ok": not diferencias, "diferencias": diferencias, "archivos": len(actual)}
