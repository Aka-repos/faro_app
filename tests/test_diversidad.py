"""Punto 3: diversidad en la Bandeja (máx. 3 eventos por tema, configurable)."""

from __future__ import annotations

import pandas as pd

from app.db_ui import top_diverso
from faro.loaders import load_lente


def test_top_diverso_max_3_por_tema():
    ev = pd.DataFrame(
        [
            {"tema": "logistica", "P": 99},
            {"tema": "logistica", "P": 98},
            {"tema": "logistica", "P": 97},
            {"tema": "logistica", "P": 96},  # 4º logistica -> descartado
            {"tema": "economia", "P": 95},
            {"tema": "economia", "P": 94},
        ]
    )
    top, aplicada = top_diverso(ev, 3, n=10)
    assert aplicada is True
    assert list(top["tema"]).count("logistica") == 3
    assert list(top["tema"]).count("economia") == 2
    assert len(top) == 5  # 3 logistica + 2 economia (el 4º logistica se descartó)


def test_top_diverso_sin_exceso_no_aplicada():
    ev = pd.DataFrame(
        [
            {"tema": "logistica", "P": 99},
            {"tema": "economia", "P": 98},
            {"tema": "turismo", "P": 97},
        ]
    )
    top, aplicada = top_diverso(ev, 3, n=10)
    assert aplicada is False
    assert len(top) == 3


def test_lente_tiene_diversidad_configurada():
    for lente in ("editorial", "banca"):
        assert load_lente(lente)["diversidad"]["max_por_tema"] == 3
