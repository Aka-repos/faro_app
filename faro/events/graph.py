"""Grafo de procedencias (F-16): agencias → medios → eventos → entidades.

Grafo dirigido y acíclico (DAG) para que se dibuje de forma jerárquica y legible:
- agencia → medio ("replicada_por")
- medio → evento ("reporta")
- evento → entidad ("involucra")
"""

from __future__ import annotations

import sqlite3

import networkx as nx

COLOR_ESTADO = {
    "suficiente para el borrador": "#2e7d32",
    "parcial": "#f9a825",
    "insuficiente": "#c62828",
}


def construir_grafo(conn: sqlite3.Connection, evento_id: str | None = None) -> nx.DiGraph:
    """Construye el grafo de procedencias. Si `evento_id`, lo acota a ese evento."""
    G = nx.DiGraph()

    where = "WHERE en.evento_id=?" if evento_id else ""
    params = (evento_id,) if evento_id else ()

    noticias = conn.execute(
        f"""SELECT en.evento_id, n.medio, n.agencia, e.titulo_canonico, e.tema
            FROM evento_noticia en
            JOIN noticia n ON n.id=en.noticia_id
            JOIN evento e ON e.id=en.evento_id
            {where}""",
        params,
    ).fetchall()

    for row in noticias:
        d = dict(row)
        medio = d["medio"] or "desconocido"
        G.add_node(f"medio:{medio}", tipo="medio", label=medio)
        G.add_node(
            f"evento:{d['evento_id']}",
            tipo="evento",
            label=d["titulo_canonico"][:60],
            tema=d["tema"],
        )
        if d["agencia"]:
            G.add_node(f"agencia:{d['agencia']}", tipo="agencia", label=d["agencia"])
            G.add_edge(f"agencia:{d['agencia']}", f"medio:{medio}", rel="replicada_por")
        G.add_edge(f"medio:{medio}", f"evento:{d['evento_id']}", rel="reporta")

    # Estado de evidencia como color de nodo evento.
    for eid, estado in conn.execute(
        "SELECT evento_id, estado_evidencia FROM evento_puntaje WHERE lente='editorial'"
    ):
        if f"evento:{eid}" in G:
            G.nodes[f"evento:{eid}"]["color"] = COLOR_ESTADO.get(estado, "#888")
            G.nodes[f"evento:{eid}"]["estado"] = estado

    # Entidades del evento.
    sql_ent = (
        "SELECT en.evento_id, e.nombre, e.tipo FROM evento_entidad en "
        "JOIN entidad e ON e.id=en.entidad_id"
    )
    if evento_id:
        sql_ent += " WHERE en.evento_id=?"
        ent = conn.execute(sql_ent, (evento_id,)).fetchall()
    else:
        ent = conn.execute(sql_ent).fetchall()
    for row in ent:
        d = dict(row)
        G.add_node(
            f"entidad:{d['nombre']}", tipo="entidad", label=d["nombre"], entidad_tipo=d["tipo"]
        )
        G.add_edge(f"evento:{d['evento_id']}", f"entidad:{d['nombre']}", rel="involucra")

    return G
