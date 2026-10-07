"""Configuración central de FARO.

Lee variables de entorno (``.env``) y expone rutas, fecha de referencia y
parámetros de red/LLM. Todo módulo del núcleo importa de aquí para que la demo
sea reproducible con solo cambiar ``.env``.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

# Raíz del repositorio (un nivel por encima de faro/).
REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


# --- Rutas ---------------------------------------------------------------
DATA_DIR = Path(_env("FARO_DATA_DIR", "data"))
if not DATA_DIR.is_absolute():
    DATA_DIR = REPO_ROOT / DATA_DIR

RAW_DIR = DATA_DIR / "raw"
REPORTS_DIR = DATA_DIR / "reports"
OUT_DIR = DATA_DIR / "out"
LABELS_DIR = DATA_DIR / "labels"
SEED_DIR = DATA_DIR / "seed"

DB_PATH = Path(_env("FARO_DB", str(DATA_DIR / "faro.db")))
if not DB_PATH.is_absolute():
    DB_PATH = REPO_ROOT / DB_PATH

MANIFEST_PATH = DATA_DIR / "manifest.json"
VECTOR_PATH = DATA_DIR / "vectores.npy"
VECTOR_IDX_PATH = DATA_DIR / "vectores_idx.json"

CONFIG_DIR = REPO_ROOT / "config"
PROMPTS_DIR = REPO_ROOT / "prompts"
SCHEMAS_DIR = REPO_ROOT / "schemas"

# --- Fecha de referencia (D-09) ------------------------------------------
FECHA_REFERENCIA = _env("FARO_FECHA_REFERENCIA", "2026-09-30T23:59:00-05:00")

# Ventana de la demo (D-01): [2025-10-02, 2026-10-01) — UTC.
VENTANA_INICIO = datetime(2025, 10, 2, 0, 0, 0, tzinfo=UTC)
VENTANA_FIN = datetime(2026, 10, 1, 0, 0, 0, tzinfo=UTC)

# --- Scraping -------------------------------------------------------------
HTTP_TIMEOUT = 20.0
USER_AGENT = (
    "FARO/0.1 (copiloto de inteligencia informativa; contacto: equipo-faro@example.com; "
    "respeta robots.txt y pausa por dominio)"
)

# --- NLP / modelos (WP-2) ---------------------------------------------------
# Cache de modelos en data/cache/hf para que la demo funcione sin red (T10).
HF_HOME = DATA_DIR / "cache" / "hf"
os.environ.setdefault("HF_HOME", str(HF_HOME))
if _env("HF_HUB_OFFLINE") == "1":
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"

# Permite el fallback por hashing de n-gramas / regex solo en tests.
PERMITIR_FALLBACK = _env("FARO_PERMITIR_FALLBACK") == "1"
PERMITIR_SINTETICO = _env("FARO_PERMITIR_SINTETICO") == "1"

# --- LLM -------------------------------------------------------------------
LLM_MODO = _env("FARO_LLM_MODO", "auto")
LLM_PROVEEDOR = _env("FARO_LLM_PROVEEDOR")
LLM_MODELO = _env("FARO_LLM_MODELO")
LLM_API_KEY = _env("FARO_LLM_API_KEY")
LLM_BASE_URL = _env("FARO_LLM_BASE_URL")
OLLAMA_BASE_URL = _env("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODELO = _env("FARO_OLLAMA_MODELO", "qwen2.5:7b-instruct")

NOTION_TOKEN = _env("NOTION_TOKEN")
NOTION_PARENT_PAGE_ID = _env("NOTION_PARENT_PAGE_ID")

# Versión de reglas de puntaje (cambia solo si se cambian pesos/normalización).
REGLAS_VERSION = "1.0"


def ensure_dirs() -> None:
    """Crea las carpetas de datos que el pipeline necesita."""
    for d in (RAW_DIR, REPORTS_DIR, OUT_DIR, LABELS_DIR, SEED_DIR):
        d.mkdir(parents=True, exist_ok=True)
