"""Especificaciones de herramientas y acciones de interfaz en JSON Schema (WP-4.2).

Estos esquemas se envían al LLM para que haga llamadas a herramientas. Cada
resultado debe incluir `evidencia_id` por fila (usando faro/evidence.py).
"""

from __future__ import annotations

TOOL_SPECS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "buscar_noticias",
            "description": "Busca noticias por término, fechas y tema. Devuelve filas con evidencia_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "q": {"type": "string", "description": "Término de búsqueda"},
                    "desde": {"type": "string", "description": "Fecha ISO desde (opcional)"},
                    "hasta": {"type": "string", "description": "Fecha ISO hasta (opcional)"},
                    "tema": {"type": "string", "description": "Tema (opcional)"},
                    "limite": {"type": "integer", "default": 20},
                },
                "required": ["q"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "abrir_evento",
            "description": "Abre un evento con sus noticias, contexto oficial y puntaje.",
            "parameters": {
                "type": "object",
                "properties": {"evento_id": {"type": "string"}},
                "required": ["evento_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ver_procedencias",
            "description": "Cuenta menciones, medios y procedencias independientes de un evento.",
            "parameters": {
                "type": "object",
                "properties": {"evento_id": {"type": "string"}},
                "required": ["evento_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_indicador",
            "description": "Valor de un indicador del Banco Mundial: país, año y unidad.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pais": {"type": "string", "description": "ISO3, ej. PAN"},
                    "indicador": {"type": "string", "description": "ej. NY.GDP.MKTP.KD.ZG"},
                    "anio": {"type": "integer"},
                },
                "required": ["pais", "indicador"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_serie",
            "description": "Serie oficial mensual (INEC/ACP/SBP) con unidad y URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fuente": {"type": "string"},
                    "serie": {"type": "string"},
                    "periodo": {"type": "string"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_sbp",
            "description": "Serie de la Superintendencia de Bancos de Panamá.",
            "parameters": {
                "type": "object",
                "properties": {"serie": {"type": "string"}, "periodo": {"type": "string"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_sismos",
            "description": "Sismos USGS en la caja regional, con magnitud mínima.",
            "parameters": {
                "type": "object",
                "properties": {
                    "desde": {"type": "string"},
                    "hasta": {"type": "string"},
                    "mag_min": {"type": "number"},
                    "limite": {"type": "integer"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ranking",
            "description": "Top n eventos por puntaje para un lente, con componentes.",
            "parameters": {
                "type": "object",
                "properties": {"lente": {"type": "string"}, "n": {"type": "integer"}},
            },
        },
    },
]

ACCIONES_SPEC: dict = {
    "type": "object",
    "properties": {
        "respuesta": {"type": "string"},
        "abstencion": {"type": "boolean"},
        "vacios": {"type": "array", "items": {"type": "string"}},
        "afirmaciones": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "texto": {"type": "string"},
                    "tipo": {
                        "type": "string",
                        "enum": ["hecho", "declaracion", "inferencia", "hipotesis", "observacion"],
                    },
                    "evidencia_id": {"type": "string"},
                    "campo": {"type": "string"},
                },
                "required": ["texto", "tipo"],
            },
        },
        "acciones": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "accion": {
                        "type": "string",
                        "enum": [
                            "filtrar_bandeja",
                            "abrir_ficha",
                            "ir_a",
                            "resaltar_en_grafo",
                            "mostrar_evidencia",
                        ],
                    },
                    "argumentos": {"type": "object"},
                },
                "required": ["accion"],
            },
        },
    },
    "required": ["respuesta", "abstencion"],
}
