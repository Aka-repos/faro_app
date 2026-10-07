"""Clasificación temática (F-04, D-08): baseline de palabras clave vs. embeddings+LR."""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from faro.loaders import load_keywords

TEMAS = list(load_keywords()["temas"].keys())


def clasificar_baseline(titulo: str) -> str:
    """Clasifica por palabras clave (baseline, D-08)."""
    kw = load_keywords()["temas"]
    t = titulo.lower()
    mejor = "economia"
    mejor_puntos = -1
    for tema, palabras in kw.items():
        puntos = sum(1 for p in palabras if p in t)
        if puntos > mejor_puntos:
            mejor, mejor_puntos = tema, puntos
    return mejor if mejor_puntos > 0 else "economia"


def _scores_a_clase(pred: np.ndarray) -> list[str]:
    return [TEMAS[i] for i in pred]


def entrenar_clasificador(embeddings: np.ndarray, etiquetas: list[str]):
    clf = LogisticRegression(max_iter=1000, class_weight="balanced")
    return clf


def evaluar_clasificador(embeddings: np.ndarray, etiquetas: list[str]) -> dict:
    """Validación cruzada 5-fold de embeddings+LR vs. baseline por palabras clave."""
    clase_idx = {c: i for i, c in enumerate(TEMAS)}
    y = np.array([clase_idx.get(e, 0) for e in etiquetas])
    clf = LogisticRegression(max_iter=1000, class_weight="balanced")
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    preds = cross_val_predict(clf, embeddings, y, cv=skf)
    macro_lr = f1_score(y, preds, average="macro")

    # Baseline necesita los textos; aquí recibe solo embeddings, así que se estima
    # el baseline en la función wrapper `evaluar_nlp` que sí tiene los titulares.
    return {"macro_f1_lr": float(macro_lr), "preds": preds.tolist()}


def entrenar_final(embeddings: np.ndarray, etiquetas: list[str]) -> LogisticRegression:
    clase_idx = {c: i for i, c in enumerate(TEMAS)}
    y = np.array([clase_idx.get(e, 0) for e in etiquetas])
    clf = LogisticRegression(max_iter=1000, class_weight="balanced")
    clf.fit(embeddings, y)
    return clf


def predecir(clf, embeddings: np.ndarray) -> list[str]:
    pred = clf.predict(embeddings)
    return _scores_a_clase(pred)
