"""F-17: acciones de interfaz. Válidas funcionan; inválidas se ignoran; no tocan la DB."""

from __future__ import annotations

import hashlib

import pytest
from pydantic import ValidationError

from faro.agent import loop
from schemas import AccionInterfaz, RespuestaAgente


def _db_firma(conn) -> str:
    h = hashlib.sha256()
    for tabla in ("noticia", "evento", "evento_puntaje", "serie_oficial", "indicador", "sismo"):
        for r in conn.execute(f"SELECT * FROM {tabla} ORDER BY rowid"):
            h.update(repr(tuple(r)).encode())
    return h.hexdigest()


def test_acciones_validas_desde_lenguaje_natural(conn):
    r = loop.consultar("Muéstrame el top 5 de la bandeja y el grafo de procedencias", conn)
    assert any(
        a["accion"] in ("filtrar_bandeja", "ir_a", "resaltar_en_grafo") for a in r["acciones"]
    )


def test_accion_invalida_rechazada_por_esquema():
    with pytest.raises(ValidationError):
        AccionInterfaz(accion="borrar_base_de_datos", argumentos={})


def test_respuesta_con_acciones_validas():
    r = RespuestaAgente(
        respuesta="ok", acciones=[{"accion": "filtrar_bandeja", "argumentos": {"top_n": 5}}]
    )
    assert r.acciones[0].accion == "filtrar_bandeja"


def test_acciones_no_modifican_db(conn):
    antes = _db_firma(conn)
    loop.consultar("¿Qué cinco temas merecen revisión hoy y por qué?", conn)
    loop.consultar("¿Cuál fue el crecimiento del PIB según el Banco Mundial?", conn)
    despues = _db_firma(conn)
    assert antes == despues
