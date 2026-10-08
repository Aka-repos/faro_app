"""Clasificación temática (F-04, D-08): baseline de palabras clave vs. embeddings+LR.

Cambio 5 (2026-10-07): el clasificador se entrena con etiquetas **string**, así
`clf.classes_` es la única fuente de verdad de los nombres de tema. Se elimina el
mapeo por índice (`clase_idx.get(e, 0)`) que producía el desajuste de nombres.
"""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from faro.loaders import load_keywords

TEMAS = list(load_keywords()["temas"].keys())


def etiquetas_permitidas() -> list[str]:
    """Los 6 temas más 'excluir'."""
    return TEMAS + ["excluir"]


def validar_etiquetas(etiquetas: list[str], filas: list[dict] | None = None) -> list[str]:
    """Devuelve los valores no permitidos (error que lista fila y valor)."""
    permitidas = set(etiquetas_permitidas())
    invalidas = []
    for i, e in enumerate(etiquetas):
        if e not in permitidas:
            fila = (filas[i].get("noticia_id") or filas[i].get("titulo")) if filas else i
            invalidas.append(f"fila={fila} valor={e!r}")
    return invalidas


def clasificar_baseline(titulo: str) -> str:
    """Clasifica por palabras clave (baseline, D-08). Sin coincidencias -> 'sin_tema'."""
    kw = load_keywords()["temas"]
    t = titulo.lower()
    mejor = "sin_tema"
    mejor_puntos = 0
    for tema, palabras in kw.items():
        puntos = sum(1 for p in palabras if p in t)
        if puntos > mejor_puntos:
            mejor, mejor_puntos = tema, puntos
    return mejor


def entrenar_final(embeddings: np.ndarray, etiquetas: list[str]) -> LogisticRegression:
    """Entrena con etiquetas string; `clf.classes_` conserva el orden real de clases."""
    clf = LogisticRegression(max_iter=1000, class_weight="balanced")
    clf.fit(embeddings, etiquetas)
    return clf


def predecir(clf, embeddings: np.ndarray) -> list[str]:
    """Predice y devuelve los nombres reales de clase (usando `clf.classes_`)."""
    pred = clf.predict(embeddings)
    if np.issubdtype(np.asarray(pred).dtype, np.integer):
        return [clf.classes_[i] for i in pred]
    return list(pred)


def evaluar_clasificador(embeddings: np.ndarray, etiquetas: list[str]) -> dict:
    """Validación cruzada 5-fold (etiquetas string). Devuelve macro-F1."""
    clf = LogisticRegression(max_iter=1000, class_weight="balanced")
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    preds = cross_val_predict(clf, embeddings, etiquetas, cv=skf)
    macro_lr = f1_score(etiquetas, preds, average="macro")
    return {"macro_f1_lr": float(macro_lr), "preds": list(preds)}
