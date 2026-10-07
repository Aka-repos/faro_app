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
