"""Cambio 5: el clasificador usa las clases reales (sin desajuste de nombres)."""

from __future__ import annotations

import numpy as np

from faro.nlp import classify


def _emb(titulos):
    # embeddings simples por hashing de longitud fija (para el test, no el modelo real).
    rng = np.random.RandomState(0)
    return rng.randn(len(titulos), 16)


def test_predecir_devuelve_nombres_correctos_sin_desajuste():
    # Etiquetas en orden distinto al alfabético y al de keywords.yaml.
    etiquetas = ["regulacion", "turismo", "economia", "logistica", "regulacion", "turismo"]
    X = _emb(etiquetas)
    clf = classify.entrenar_final(X, etiquetas)
    preds = classify.predecir(clf, X)
    assert preds == etiquetas  # clf.classes_ es la fuente de verdad, no un mapeo por índice


def test_validar_etiquetas_rechaza_fuera_de_temas():
    invalidas = classify.validar_etiquetas(["economia", "deportes", "excluir"])
    assert len(invalidas) == 1
    assert "deportes" in invalidas[0]


def test_excluir_es_permitida():
    assert classify.validar_etiquetas(["economia", "excluir"]) == []


def test_baseline_sin_keywords_devuelve_sin_tema():
    assert classify.clasificar_baseline("zzz título sin ninguna palabra clave xxx") == "sin_tema"


def test_baseline_con_keyword_devuelve_tema():
    assert classify.clasificar_baseline("el pib de Panamá creció") == "economia"


def test_sin_tema_prioridad_baja_y_label_ui():
    from app.db_ui import tema_label
    from faro.scoring.score import _TEMA_PRIORIDAD

    assert _TEMA_PRIORIDAD["sin_tema"] == 0.3
    assert tema_label("sin_tema") == "Sin clasificar"
    assert tema_label("economia") == "economia"
