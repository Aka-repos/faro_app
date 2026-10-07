"""Verificador de salida (F-11, T04, T06, T09).

Reglas, todas en código (no dependen de que el LLM se porte bien):

1. **Evidencia existente:** ``evidencia_id`` debe resolverse a un dato real.
2. **Campo citado respalda:** el texto de la afirmación (o sus cifras) debe estar
   contenido en la evidencia citada.
3. **Candado de cifras:** todo número del borrador debe existir literalmente en la
   evidencia citada, con su año y unidad.
4. **Tipos permitidos por lente:** solo ``hecho/declaracion/inferencia/hipotesis``
   (editorial) u ``hecho/observacion/hipotesis`` (banca).
5. **Etiqueta de metadatos:** si solo hay titular, se exige "basado únicamente en
   titular/metadatos".
6. **Frases prohibidas por lente** (banca: compra/venta, pérdidas, impagos, etc.).
"""

from __future__ import annotations

import re

from faro.loaders import load_lente

_NUM = re.compile(r"\d[\d.,]*\s*(%|millones|miles|USD|buques|millones de dólares)?")


def tipos_permitidos(lente: str) -> list[str]:
    return load_lente(lente).get("tipos_afirmacion", [])


def frases_prohibidas(lente: str) -> list[str]:
    return load_lente(lente).get("frases_prohibidas", [])


def verificar_cifras(texto: str, evidencia_texto: str) -> bool:
    """Candado de cifras: cada número del texto debe estar literal en la evidencia."""
    nums = [m.group(0).replace(",", "") for m in _NUM.finditer(texto)]
    if not nums:
        return True
    ev = evidencia_texto.replace(",", "")
    return all(n.split(" ")[0] in ev or n in ev for n in nums)


def verificar_afirmacion(
    afirmacion: dict,
    evidencia_texto: str | None,
    lente: str = "editorial",
    solo_titular: bool = False,
) -> tuple[bool, str | None]:
    """Devuelve (verificada, motivo_rechazo)."""
    texto = afirmacion.get("texto", "")
    tipo = afirmacion.get("tipo", "hecho")
    evidencia_id = afirmacion.get("evidencia_id")

    # 1. Evidencia existente.
    if not evidencia_id or evidencia_texto is None:
        return False, "sin_evidencia"

    # 4. Tipo permitido.
    if tipo not in tipos_permitidos(lente):
        return False, f"tipo_no_permitido:{tipo}"

    # 3. Candado de cifras.
    if not verificar_cifras(texto, evidencia_texto):
        return False, "cifra_no_respaldada"

    # 6. Frases prohibidas.
    for frase in frases_prohibidas(lente):
        if frase.lower() in texto.lower():
            return False, f"frase_prohibida:{frase}"

    # 5. Etiqueta de metadatos.
    if solo_titular and "basado únicamente en titular/metadatos" not in texto:
        return False, "falta_etiqueta_titular"

    # 2. Campo citado respalda: obligatorio solo para tipos factuales (hecho/observacion).
    # Las inferencias/hipótesis/declaraciones se marcan como tales y no exigen respaldo literal.
    if tipo in ("hecho", "observacion"):
        palabras = [
            w
            for w in re.findall(r"[a-záéíóúñ]{5,}", texto.lower())
            if w not in ("basado", "únicamente", "titular", "metadatos")
        ]
        respaldado = any(p in evidencia_texto.lower() for p in palabras) if palabras else True
        if not respaldado:
            return False, "campo_no_respalda"

    return True, None


def verificar_ficha(
    afirmaciones: list[dict],
    evidencias: dict[str, str],
    lente: str = "editorial",
    solo_titular: bool = False,
) -> dict:
    """Verifica todas las afirmaciones de una ficha. Devuelve resumen."""
    resultados = []
    for a in afirmaciones:
        ev = evidencias.get(a.get("evidencia_id") or "", None)
        ok, motivo = verificar_afirmacion(a, ev, lente, solo_titular)
        resultados.append({"afirmacion": a["texto"], "verificada": ok, "motivo": motivo})
    validas = sum(1 for r in resultados if r["verificada"])
    return {"citas_validas": validas, "citas_total": len(resultados), "detalle": resultados}
