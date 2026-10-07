# Makefile de FARO — un comando por paso del pipeline.
# Uso: `make <objetivo>`. Requiere `uv` instalado (o activar el plan B con venv).
SHELL := /bin/bash
PY := uv run python
UV := uv

.PHONY: setup data data-seed freeze verify-snapshot build run test eval eval-nlp labels-sample check check-sources demo-offline demo-cache notion-sync clean

## Instala dependencias (uv sync), precarga e5-small y el modelo de spaCy (offline).
setup:
	$(UV) sync
	$(PY) -c "from config import settings; settings.ensure_dirs()"
	$(UV) run python -m spacy download es_core_news_md
	$(PY) -c "from faro.nlp.embed import Embedder; Embedder(require_model=True).encode(['ok']); print('e5-small OK')"
	@echo "setup OK"

## Recolecta el snapshot REAL (RSS, sitemaps, GDELT, Banco Mundial, USGS, INEC/ACP/SBP).
data:
	$(PY) -m faro.cli data

## Escribe el seed sintético SOLO en una carpeta temporal (para pruebas, nunca en data/).
data-seed:
	$(PY) -m faro.cli data-seed

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

## Corre la suite de pruebas (smoke + T01–T10 + módulos) y genera junit.xml.
test:
	$(UV) run pytest --junitxml=data/reports/junit.xml

## Corre el benchmark (SPLIT=dev|reservado MODO=usuario|local|determinista) -> reports/metrics_*.json|md.
eval:
	$(PY) -m faro.cli eval

## Sincroniza las 8 páginas obligatorias con Notion (o exporta índice para carga manual).
notion-sync:
	$(PY) -m faro.cli notion-sync

## Evalúa solo el núcleo NLP (clasificación + agrupación) -> reports/nlp.json.
eval-nlp:
	$(PY) -m faro.cli eval-nlp

## Muestra titulares y pares para etiquetar a mano -> data/labels/*_pendientes.csv.
labels-sample:
	$(PY) -m faro.cli labels-sample

## Formato + lint + pruebas.
check: 
	$(UV) run ruff check faro schemas app config tests
	$(UV) run ruff format --check faro schemas app config tests
	$(UV) run pytest

## Revisa fuentes candidatas (robots.txt + método + volumen) -> reports/fuentes_check.json.
check-sources:
	$(PY) -m faro.cli check-sources

## Demo offline: clona en carpeta temporal, carga snapshot y arranca Streamlit sin red.
demo-offline:
	$(PY) -m faro.cli demo-offline

## Precalienta la caché con las preguntas de docs/guion_demo.md (para la demo sin red).
demo-cache:
	$(PY) -m faro.cli demo-cache

## Limpia artefactos regenerables.
clean:
	rm -rf .pytest_cache .ruff_cache data/faro.db data/vectores.npy data/vectores_idx.json data/out/*.jsonl
