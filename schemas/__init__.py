"""Modelos Pydantic v2 de FARO.

Cubren registros recolectados, salidas del LLM, acciones de interfaz y el
contrato de exportación (fichas.jsonl). Son la fuente del JSON Schema que se
envía al modelo y de la validación en `faro/guard/verifier.py`.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Registros de datos (Capa 1)
# ---------------------------------------------------------------------------


class RegistroNoticia(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    fuente_id: str
    titulo: str
    url: str
    medio: str
    dominio: str = ""
    idioma: str = "es"
    fecha_publicacion: str | None = None  # ISO 8601 UTC (puede faltar en GDELT; ver fecha_deteccion)
    fecha_deteccion: str | None = None
    fecha_extraccion: str | None = None
    alcance_texto: Literal["titular", "metadatos", "resumen", "cuerpo"] = "titular"
    resumen: str | None = None
    tema: str | None = None
    tema_conf: float | None = None
    es_agencia: bool = False
    agencia: str | None = None
    hash: str | None = None
    via: str | None = None  # rss | sitemap | html | gdelt


class SerieOficial(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    fuente_id: str
    serie: str
    periodo: str  # e.g. "2026-08"
    valor: float | None = None
    unidad: str | None = None
    url: str = ""
    pagina: int | None = None
    fecha_extraccion: str | None = None
    condiciones: str = ""


class Indicador(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pais_iso3: str
    indicador_id: str
    anio: int
    valor: float | None = None
    unidad: str | None = None
    fuente_url: str = ""
    fecha_extraccion: str | None = None
    licencia: str = "CC BY 4.0"


class Sismo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    magnitud: float
    fecha: str  # ISO 8601 UTC
    lat: float
    lon: float
    profundidad: float | None = None
    lugar: str = ""
    status: str = ""
    url: str = ""


# ---------------------------------------------------------------------------
# Salidas del LLM (Capa 3)
# ---------------------------------------------------------------------------

TipoAfirmacion = Literal["hecho", "declaracion", "inferencia", "hipotesis", "observacion"]


class Afirmacion(BaseModel):
    """Una afirmación citable. `evidencia_id` y `campo` la hacen verificable (D-05)."""

    model_config = ConfigDict(extra="forbid")

    texto: str
    tipo: TipoAfirmacion = "hecho"
    evidencia_id: str | None = None
    campo: str | None = None


class Vacio(BaseModel):
    model_config = ConfigDict(extra="forbid")

    descripcion: str
    evidencia_faltante: str = ""


class PaqueteEditorial(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titulo: str
    enfoque: str
    brief: str
    preguntas: list[str] = Field(default_factory=list)
    fuentes: list[str] = Field(default_factory=list)
    verificaciones: list[str] = Field(default_factory=list)
    guion: str
    copy_digital: str
    afirmaciones: list[Afirmacion] = Field(default_factory=list)
    vacios: list[Vacio] = Field(default_factory=list)
    basado_solo_titular: bool = False


class Boletin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resumen: str
    sectores: list[str] = Field(default_factory=list)
    horizonte: str
    evidencia: list[str] = Field(default_factory=list)
    preguntas: list[str] = Field(default_factory=list)
    afirmaciones: list[Afirmacion] = Field(default_factory=list)
    observaciones: list[str] = Field(default_factory=list)
    hipotesis: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Acciones de interfaz (F-17)
# ---------------------------------------------------------------------------


class AccionInterfaz(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accion: Literal[
        "filtrar_bandeja", "abrir_ficha", "ir_a", "resaltar_en_grafo", "mostrar_evidencia"
    ]
    argumentos: dict[str, Any] = Field(default_factory=dict)


class RespuestaAgente(BaseModel):
    model_config = ConfigDict(extra="forbid")

    respuesta: str
    acciones: list[AccionInterfaz] = Field(default_factory=list)
    abstencion: bool = False
    vacios: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Contrato de exportación (fichas.jsonl)
# ---------------------------------------------------------------------------


class FichaExport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id_caso: str
    modalidad: str
    ids_fuente: list[str] = Field(default_factory=list)
    afirmaciones: list[Afirmacion] = Field(default_factory=list)
    citas: list[str] = Field(default_factory=list)
    puntaje: float | None = None
    componentes: dict[str, float] = Field(default_factory=dict)
    estado_evidencia: str
    borrador: dict[str, Any] = Field(default_factory=dict)
    estado_revision: str
