"""Punto 4: eval-nlp ajusta n_splits y excluye clases con <2 ejemplos."""

from __future__ import annotations

from faro.cli import _n_splits_y_clases_raras


def test_n_splits_reducido_por_min_por_clase():
    n, raras = _n_splits_y_clases_raras(["a"] * 3 + ["b"] * 10)
    assert n == 3  # min(5, 3)
    assert raras == []


def test_clase_con_1_ejemplo_se_excluye():
    n, raras = _n_splits_y_clases_raras(["a"] * 1 + ["b"] * 10 + ["c"] * 10)
    assert raras == ["a"]
    assert n == 5  # b y c tienen 10 -> min(5,10)=5


def test_todas_clases_suficientes():
    n, raras = _n_splits_y_clases_raras(["a"] * 6 + ["b"] * 6 + ["c"] * 6)
    assert n == 5
    assert raras == []
