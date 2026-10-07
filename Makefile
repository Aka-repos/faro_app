# Makefile de FARO — un comando por paso del pipeline.
# Uso: `make <objetivo>`. Requiere `uv` instalado (o activar el plan B con venv).
SHELL := /bin/bash
PY := uv run python
UV := uv

.PHONY: setup data freeze verify-snapshot build run test eval eval-nlp check check-sources demo-offline clean

## Instala dependencias (uv sync) y precarga config mínima.
setup:
	$(UV) sync
	$(PY) -c "from config import settings; settings.ensure_dirs()"
	@echo "setup OK"

## Genera el snapshot (seed sintético por defecto; usa scraping si FUENTES_LIVE=1).
data:
	$(PY) -m faro.cli data

## Congela la versión v1 del snapshot (raw/ + manifest con SHA-256).
freeze:
	$(PY) -m faro.cli freeze

## Recalcula los hashes del snapshot y los compara con manifest.json.
verify-snapshot:
	$(PY) -m faro.cli verify

## Reconstruye la base (faro.db) y las capas deducidas desde raw/.
build:
	$(PY) -m faro.cli build

## Arranca la interfaz Streamlit.
run:
	uv run streamlit run app/streamlit_app.py

## Corre la suite de pruebas (smoke + T01–T10 + módulos).
test:
	$(UV) run pytest

## Corre el benchmark y genera reports/metrics_*.json.
eval:
	$(PY) -m faro.cli eval

## Evalúa solo el núcleo NLP (clasificación + agrupación) -> reports/nlp.json.
eval-nlp:
	$(PY) -m faro.cli eval-nlp

## Formato + lint + pruebas.
check: 
	$(UV) run ruff check faro schemas app config tests || true
	$(UV) run ruff format --check faro schemas app config tests || true
	$(UV) run pytest

## Revisa fuentes candidatas (robots.txt + método + volumen) -> reports/fuentes_check.json.
check-sources:
	$(PY) -m faro.cli check-sources

## Demo offline: instala en carpeta temporal, carga snapshot y arranca Streamlit.
demo-offline:
	$(PY) -m faro.cli demo-offline

## Limpia artefactos regenerables.
clean:
	rm -rf .pytest_cache .ruff_cache data/faro.db data/vectores.npy data/vectores_idx.json data/out/*.jsonl
