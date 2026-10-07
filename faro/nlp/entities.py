"""Entidades (F-04): personas, organizaciones y lugares; agencia y acusación.

Usa spaCy ``es_core_news_md`` si está disponible; si no, cae a un extractor por
expresiones regulares y diccionarios (offline, sin descargas).
"""

from __future__ import annotations

import re

try:
    import spacy  # type: ignore

    _SPACY = True
except Exception:  # noqa: BLE001
    _SPACY = False

_NLP = None

AGENCIAS = ["EFE", "AFP", "AP", "Reuters", "Notimex", "DPA"]
_ACUSACION = re.compile(
    r"\b(acus|denunci|imputad|investigad|detenid|corrupci|soborn|fraude|lavado|malversac)\w*", re.I
)
_PERSONA = re.compile(r"\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+ [A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\b")
_ORGS = [
    "Canal de Panamá",
    "Autoridad del Canal",
    "ACP",
    "Banco Central",
    "Asamblea Nacional",
    "Superintendencia de Bancos",
    "SBP",
    "INEC",
    "Ministerio de Economía",
    "Gobierno",
    "SINAPROC",
    "ASEP",
    "Metro de Panamá",
    "Zona Libre de Colón",
    "FMI",
]
_LUGARES = [
    "Panamá",
    "Chiriquí",
    "Colón",
    "David",
    "Costa Rica",
    "Caribe",
    "lago Gatún",
    "Balboa",
    "ciudad de Panamá",
    "Asia",
    "Europa",
]


def _nlp():
    global _NLP
    if _NLP is not None:
        return _NLP
    if _SPACY:
        try:
            _NLP = spacy.load("es_core_news_md")
            return _NLP
        except Exception:  # noqa: BLE001
            _NLP = None
    return _NLP


def extraer_entidades(texto: str) -> list[dict]:
    """Devuelve [{nombre, tipo}] con tipo en {PER, ORG, LOC}."""
    out: list[dict] = []
    nlp = _nlp()
    if nlp is not None:
        doc = nlp(texto)
        for ent in doc.ents:
            if ent.label_ in ("PER", "ORG", "LOC"):
                out.append({"nombre": ent.text, "tipo": ent.label_})
    else:
        for m in _PERSONA.finditer(texto):
            out.append({"nombre": m.group(0), "tipo": "PER"})
        for org in _ORGS:
            if org.lower() in texto.lower():
                out.append({"nombre": org, "tipo": "ORG"})
        for loc in _LUGARES:
            if loc.lower() in texto.lower():
                out.append({"nombre": loc, "tipo": "LOC"})
    # deduplicar conservando orden
    seen = set()
    unicos = []
    for e in out:
        key = (e["nombre"].lower(), e["tipo"])
        if key not in seen:
            seen.add(key)
            unicos.append(e)
    return unicos


def detectar_agencia(texto: str) -> str | None:
    for a in AGENCIAS:
        if re.search(rf"\b{re.escape(a)}\b", texto, re.I):
            return a
    return None


def es_acusacion(texto: str) -> bool:
    return bool(_ACUSACION.search(texto))
