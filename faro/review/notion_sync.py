"""Sincronización con Notion (F-14): API o exportación para carga manual.

La carga manual está permitida por el reto; la API usa notion-client y solo se
activa si ``NOTION_TOKEN`` y ``NOTION_PARENT_PAGE_ID`` están configurados.
"""

from __future__ import annotations

import json

import config.settings as S


def _exportar(datos: list[dict], nombre: str) -> str:
    S.ensure_dirs()
    path = S.OUT_DIR / nombre
    path.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


def exportar_fichas(fichas: list[dict]) -> str:
    """Exporta fichas a JSON (para carga manual en Notion)."""
    return _exportar(fichas, "fichas_notion.json")


def exportar_decisiones(decisiones: list[dict]) -> str:
    return _exportar(decisiones, "decisiones_notion.json")


def exportar_pruebas(pruebas: list[dict]) -> str:
    return _exportar(pruebas, "pruebas_notion.json")


def sync_fichas(fichas: list[dict]) -> dict:
    """Intenta subir vía API; si no hay token, exporta para carga manual."""
    if S.NOTION_TOKEN and S.NOTION_PARENT_PAGE_ID:
        try:
            from notion_client import Client  # type: ignore

            client = Client(auth=S.NOTION_TOKEN)
            creados = 0
            for f in fichas:
                client.pages.create(
                    parent={"page_id": S.NOTION_PARENT_PAGE_ID},
                    properties={
                        "title": {"title": [{"text": {"content": f.get("id_caso", "ficha")}}]},
                    },
                    children=[
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [
                                    {"text": {"content": json.dumps(f, ensure_ascii=False)[:1900]}}
                                ]
                            },
                        },
                    ],
                )
                creados += 1
            return {"modo": "api", "creadas": creados}
        except Exception as e:  # noqa: BLE001
            return {"modo": "export", "archivo": exportar_fichas(fichas), "error": str(e)}
    return {"modo": "export", "archivo": exportar_fichas(fichas)}


PAGINAS_OBLIGATORIAS = {
    "Inicio del reto": "Equipo, modalidad, problema, usuario, alcance, criterios de éxito, enlaces a demo y repo.",
    "Plan y decisiones": "Tareas (≥8) y decisiones (D-01…D-n) con fecha y responsable.",
    "Catálogo de datos": "Una fila por fuente: URL, fecha, cobertura, condiciones, transformaciones, SHA-256.",
    "Diseño de solución": "Arquitectura, modelo de datos, reglas, modelos, prompts, versiones y límites.",
    "Casos y evidencias": "≥5 fichas con IDs, fuentes, puntaje, estado de evidencia, borrador y revisor.",
    "Pruebas y métricas": "Matriz T01–T10 + métricas de las dos corridas.",
    "Riesgos y ética": "Tabla de la sección 9 del documento técnico.",
    "Presentación al jurado": "Pitch: problema → solución → demo → IA y evidencias → resultados → límites.",
}


def sync_notion() -> dict:
    """Crea o actualiza las 8 páginas obligatorias (idempotente por título).

    Sin NOTION_TOKEN/NOTION_PARENT_PAGE_ID, exporta el índice para carga manual.
    """
    ids_path = S.DATA_DIR / "notion_ids.json"
    ids = json.loads(ids_path.read_text(encoding="utf-8")) if ids_path.exists() else {}

    if not (S.NOTION_TOKEN and S.NOTION_PARENT_PAGE_ID):
        _exportar(list(PAGINAS_OBLIGATORIAS.items()), "notion_indice.json")
        return {"modo": "export", "archivo": str(S.OUT_DIR / "notion_indice.json")}

    try:
        from notion_client import Client  # type: ignore

        client = Client(auth=S.NOTION_TOKEN)
        for titulo, contenido in PAGINAS_OBLIGATORIAS.items():
            if titulo in ids:
                try:
                    client.pages.update(
                        page_id=ids[titulo],
                        properties={"title": {"title": [{"text": {"content": titulo}}]}},
                    )
                    continue
                except Exception:  # noqa: BLE001
                    pass
            page = client.pages.create(
                parent={"page_id": S.NOTION_PARENT_PAGE_ID},
                properties={"title": {"title": [{"text": {"content": titulo}}]}},
                children=[
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {"rich_text": [{"text": {"content": contenido}}]},
                    }
                ],
            )
            ids[titulo] = page["id"]
        ids_path.write_text(json.dumps(ids, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"modo": "api", "paginas": len(ids)}
    except Exception as e:  # noqa: BLE001
        return {
            "modo": "export",
            "archivo": _exportar(list(PAGINAS_OBLIGATORIAS.items()), "notion_indice.json"),
            "error": str(e),
        }
