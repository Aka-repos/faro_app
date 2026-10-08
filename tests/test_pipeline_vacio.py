"""Prueba: build sobre data/raw vacío no genera datos sintéticos (corrección 1)."""

from __future__ import annotations

import pytest

import config.settings as S


def test_build_vacio_aborta_sin_generar_jsonl(tmp_path, monkeypatch):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    monkeypatch.setattr(S, "RAW_DIR", raw_dir)

    from faro.pipeline import build

    with pytest.raises(RuntimeError, match="data/raw vacío"):
        build()
    assert list(raw_dir.glob("*.jsonl")) == []
