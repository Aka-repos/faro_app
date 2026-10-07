"""Capa de datos SQLite (sección 6 del documento técnico).

Un único archivo ``data/faro.db`` con las tablas de la Capa 1 (normalizados),
Capa 2 (deducido) y Capa 3 (salida y revisión). Sin servidor ni red.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import config.settings as S

SCHEMA = """
CREATE TABLE IF NOT EXISTS fuente (
  id TEXT PRIMARY KEY,
  nombre TEXT NOT NULL,
  familia TEXT NOT NULL,
  url_base TEXT,
  metodo TEXT,
  robots_ok INTEGER,
  condiciones TEXT,
  rate_limit_s REAL,
  user_agent TEXT,
  licencia TEXT,
  notas TEXT
);

CREATE TABLE IF NOT EXISTS noticia (
  id TEXT PRIMARY KEY,
  fuente_id TEXT NOT NULL,
  titulo TEXT NOT NULL,
  url TEXT NOT NULL,
  medio TEXT,
  dominio TEXT,
  idioma TEXT,
  fecha_publicacion TEXT,
  fecha_deteccion TEXT,
  fecha_extraccion TEXT,
  alcance_texto TEXT,
  resumen TEXT,
  tema TEXT,
  tema_conf REAL,
  es_agencia INTEGER DEFAULT 0,
  agencia TEXT,
  hash TEXT
);

CREATE TABLE IF NOT EXISTS serie_oficial (
  id TEXT PRIMARY KEY,
  fuente_id TEXT,
  serie TEXT,
  periodo TEXT,
  valor REAL,
  unidad TEXT,
  url TEXT,
  pagina INTEGER,
  fecha_extraccion TEXT,
  condiciones TEXT
);

CREATE TABLE IF NOT EXISTS indicador (
  pais_iso3 TEXT,
  indicador_id TEXT,
  anio INTEGER,
  valor REAL,
  unidad TEXT,
  fuente_url TEXT,
  fecha_extraccion TEXT,
  licencia TEXT,
  PRIMARY KEY (pais_iso3, indicador_id, anio)
);

CREATE TABLE IF NOT EXISTS sismo (
  id TEXT PRIMARY KEY,
  magnitud REAL,
  fecha TEXT,
  lat REAL,
  lon REAL,
  profundidad REAL,
  lugar TEXT,
  status TEXT,
  url TEXT
);

CREATE TABLE IF NOT EXISTS cuarentena (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  fuente_id TEXT,
  fila_raw TEXT,
  motivo TEXT
);

CREATE TABLE IF NOT EXISTS evento (
  id TEXT PRIMARY KEY,
  tema TEXT,
  titulo_canonico TEXT,
  fecha_primera TEXT,
  fecha_ultima TEXT,
  n_menciones INTEGER DEFAULT 0,
  n_medios INTEGER DEFAULT 0,
  n_procedencias INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS evento_noticia (
  evento_id TEXT,
  noticia_id TEXT,
  procedencia_id TEXT,
  PRIMARY KEY (evento_id, noticia_id)
);

CREATE TABLE IF NOT EXISTS entidad (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT,
  tipo TEXT
);

CREATE TABLE IF NOT EXISTS evento_entidad (
  evento_id TEXT,
  entidad_id INTEGER,
  PRIMARY KEY (evento_id, entidad_id)
);

CREATE TABLE IF NOT EXISTS evento_contexto (
  evento_id TEXT,
  evidencia_id TEXT,
  motivo_enlace TEXT,
  PRIMARY KEY (evento_id, evidencia_id)
);

CREATE TABLE IF NOT EXISTS evento_puntaje (
  evento_id TEXT,
  lente TEXT,
  R REAL, I REAL, U REAL, N REAL, E REAL, P REAL,
  rango TEXT,
  estado_evidencia TEXT,
  reglas_version TEXT,
  fecha_referencia TEXT,
  PRIMARY KEY (evento_id, lente)
);

CREATE TABLE IF NOT EXISTS sector (
  id TEXT PRIMARY KEY,
  nombre TEXT,
  descripcion TEXT
);

CREATE TABLE IF NOT EXISTS evento_sector (
  evento_id TEXT,
  sector_id TEXT,
  regla TEXT,
  confianza REAL,
  PRIMARY KEY (evento_id, sector_id)
);

CREATE TABLE IF NOT EXISTS ficha (
  id TEXT PRIMARY KEY,
  evento_id TEXT,
  lente TEXT,
  borrador_json TEXT,
  vacios_json TEXT,
  estado_revision TEXT,
  revisor TEXT,
  nota_revision TEXT,
  proveedor TEXT,
  modelo TEXT,
  prompt_version TEXT,
  desde_cache INTEGER DEFAULT 0,
  tokens_in INTEGER,
  tokens_out INTEGER,
  costo_usd REAL,
  latencia_ms INTEGER,
  creado TEXT
);

CREATE TABLE IF NOT EXISTS afirmacion (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ficha_id TEXT,
  texto TEXT,
  tipo TEXT,
  evidencia_id TEXT,
  campo TEXT,
  verificada INTEGER,
  motivo_rechazo TEXT
);

CREATE TABLE IF NOT EXISTS traza_agente (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  consulta_id TEXT,
  paso INTEGER,
  herramienta TEXT,
  argumentos TEXT,
  resultado_ids TEXT,
  ms INTEGER
);

CREATE TABLE IF NOT EXISTS ejecucion (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  caso_id TEXT,
  lente TEXT,
  proveedor TEXT,
  modelo TEXT,
  tokens_in INTEGER,
  tokens_out INTEGER,
  costo_usd REAL,
  latencia_ms INTEGER,
  citas_validas INTEGER,
  citas_total INTEGER,
  abstuvo INTEGER,
  fecha TEXT
);
"""


def connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Abre la base y crea el esquema si hace falta."""
    path = Path(db_path) if db_path else S.DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


def upsert(conn: sqlite3.Connection, table: str, rows: Iterable[dict[str, Any]]) -> int:
    """Inserta/reemplaza filas por clave primaria. Devuelve el conteo."""
    rows = list(rows)
    if not rows:
        return 0
    cols = list(rows[0].keys())
    placeholders = ", ".join("?" for _ in cols)
    sql = f"INSERT OR REPLACE INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"
    conn.executemany(sql, [tuple(r[c] for c in cols) for r in rows])
    conn.commit()
    return len(rows)


def fetchall(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    cur = conn.execute(sql, params)
    return [dict(r) for r in cur.fetchall()]


def count(conn: sqlite3.Connection, table: str) -> int:
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
