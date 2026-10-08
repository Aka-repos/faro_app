# Bitácora de desarrollo

Registro de fecha/hora, qué se hizo, qué falló y qué se decidió. Se copia a Notion ("Plan y decisiones").

## 2026-10-06 — Sesión de implementación inicial

| Hora (aprox.) | Hito | Qué se hizo | Resultado | Qué falló / se decidió |
| --- | --- | --- | --- | --- |
| — | H0 | Repo, `pyproject.toml`, `.gitignore`, `.env.example`, Makefile, `config/settings.py`, estructura de carpetas | Esqueleto listo | D-18: dependencias pesadas a extra `ml` |
| — | H1–H2 | `faro/scrape/` (rss, sitemap, html, apis, pdf, check), `faro/quality/` (validate, manifest), `faro/seed.py` | Snapshot sintético + validación + manifest | D-17: seed determinístico como snapshot de demo |
| — | H3 | `faro/nlp/` (embed, classify, entities), `faro/events/` (cluster, provenance, contradict) | Clasificación + agrupación + procedencias | Embeddings con fallback sin red |
| — | H4 | `faro/context/link.py`, `faro/scoring/score.py` | Puntaje desglosado + estado de evidencia independiente | Pesos 30/25/20/15/10 |
| — | H5 | `faro/llm/` (gateway, providers, extractive, cache), `faro/guard/` (verifier, shield), `schemas/` | Cascada BYOK + verificador + escudo | D-19: respaldo literal solo a tipos factuales |
| — | H6 | `faro/agent/` (tools, loop), `faro/review/`, `faro/export.py`, `prompts/` | Agente de solo lectura + revisión + export fichas.jsonl | Agente degrada a enrutador determinístico |
| — | H7–H8 | `faro/lenses/`, `faro/events/graph.py`, `app/` (7 vistas) | Interfaz + grafo + lente bancario + comparador | — |
| — | H9 | `faro/eval/` (benchmark, baselines, metrics) | Benchmark + métricas numerador/denominador | — |
| — | — | `tests/` T01–T10, verifier, e2e, ui_actions, banca | Suite completa | Se correrá `make test` para cerrar compuertas |

## Próximos pasos (en la competencia)

1. `FUENTES_LIVE=1 make data` + `make freeze` para el snapshot real (≥ 20 TVN, ≥ 5 medios, ≥ 1.000 noticias meta).
2. Etiquetar ~150 titulares (`data/labels/temas.csv`) y ~50 pares para medir macro-F1 y precisión de pares.
3. Configurar proveedor BYOK + Ollama y medir latencia/costo en el Comparador.
4. Sincronizar fichas/decisiones/pruebas a Notion y ensayar el pitch de 10 min (uno con wifi apagado).

## 2026-10-06 (tarde) — Docker y limpieza

- Añadido `Dockerfile`, `docker-compose.yml`, `.dockerignore` y `docker-entrypoint.sh` para la demo reproducible
  (`docker compose up --build` → http://localhost:8501).
- Eliminado el paso obsoleto de "confirmar con la organización si se puede codificar antes del evento" (ya en competencia).

## 2026-10-07 — Correcciones (guía docs/CORRECCIONES.md)

| Hora (Panamá) | WP | Qué se hizo | Resultado | Qué falló / se decidió |
| --- | --- | --- | --- | --- |
| 10:06 | WP-0 | `.python-version=3.11`, `requires-python >=3.11,<3.13`, quitar `\|\| true` de ruff en `make check`, PDF técnico a `docs/`, `*.pdf` en raíz ignorado salvo el reto, lock regenerado | `make check` real; 57/57 en verde sobre Python 3.11.15 | — |
| 10:06 | WP-1 | `politeness.py` (robots + pausa + evidencia http), `collect.py` (orquestador RSS→sitemap→GDELT→oficiales), `oficiales.py` (Banco Mundial cuadrícula completa, USGS, INEC/ACP/SBP manual), `rss/sitemap/html/apis` normalizados a RegistroNoticia, `cli data` real + `data-seed` protegido, `freeze` con evidencia http/manual | Recolección real orquestada; `make data` ya no genera seed | La ejecución real de scraping (WP-1.8) queda [HUMANO]; no se simuló red |
| 10:06 | WP-1.7 | `tests/conftest.py` con `tempfile` + `FARO_DATA_DIR/FARO_DB/FARO_PERMITIR_SINTETICO`; `seed.py` con dominios `.example.invalid` y medios ficticios; `validate.py` rechaza `sintetico:true` salvo `FARO_PERMITIR_SINTETICO=1` | Las pruebas ya no pisan la base real | — |
| 11:15 | WP-2 | `sentence-transformers`+`spacy` como dependencias obligatorias; `Embedder(require_model=True)` y spaCy obligatorio (fallback solo con `FARO_PERMITIR_FALLBACK=1`); `HF_HOME=data/cache/hf`; `make setup` descarga e5-small y `es_core_news_md` | e5-small y spaCy activos y verificados; 64 tests en verde | — |
| 11:15 | WP-4 | `gateway.generate` con `tools`+`esquema` (valida con Pydantic y reintenta); `cache_key` incluye mensajes+herramientas; `tool_specs.py`; `loop_llm.py` (agente con LLM + verificador + canario); `loop.consultar` despacha a LLM o determinista; `app` pasa `llm_cfg` desde `st.session_state['llm']`; 7 tests con LLM simulado | El LLM entra al agente; verificador como filtro | La clave real y Ollama quedan [HUMANO] (WP-4 aceptación) |
| 10:41 | WP-3 | `labels-sample` genera `temas_pendientes.csv` y `pares_pendientes.csv`; `eval-nlp` lee solo etiquetas humanas (error si faltan), entrena y guarda `models/tema_lr.joblib`; `pipeline` usa el clasificador guardado | Evaluación no circular lista; el etiquetado es [HUMANO] | — |
| 10:41 | WP-5 | `eval` con `SPLIT=dev\|reservado` y `MODO=usuario\|local\|determinista`; métricas `.md` con n/N + fallos | Benchmark y métricas listos; las 40+20 preguntas son [HUMANO] | — |
| 10:41 | WP-6 | `docs/guion_demo.md` con las 7 preguntas del pitch y los 4 casos de datos a localizar | Guion listo; los IDs reales se rellenan tras `make data` | — |
| 10:41 | WP-7 | `notion_sync.sync_notion()` idempotente (8 páginas) + `make notion-sync`; `make test` genera `junit.xml` | Notion listo; token/integración [HUMANO] | — |
| 10:41 | WP-8 | `data/DICCIONARIO.md`; versionar `data/raw/*.jsonl` + `manual/` + `http/index.jsonl` (los `.gz` como asset); `demo-offline` por `git clone`; `demo-cache`; `test_t10` bloquea red; `docker-entrypoint` exige snapshot real | Entrega verificable lista; la recolección real y el ensayo sin wifi son [HUMANO] | — |
| 10:41 | WP-9 | README/decisiones/.env.example honestos (D-17, D-18 reescritas; D-20..D-22 nuevas) | Documentación alineada con lo que hace el sistema | — |

## 2026-10-07 (noche) — Plan de agente (docs/PLAN_AGENTE.md), hitos M

| Hora (commit) | Hito | Qué se hizo | Resultado | Qué falló / se decidió |
| --- | --- | --- | --- | --- |
| 21:41 | M1 | Contacto opcional, GDELT con pausa/reintentos, normalización de medios (via), sitemaps acotados, data-smoke; ACP fuera de alcance | 9 tests de scraping en verde | — |
| 21:41 | M2.1 | `git rm` del snapshot sintético y derivados | data/raw sin sintéticos | — |
| 21:43 | M2.2 | Barrera anti-sintéticos en build+docker; validación de series manuales; `manual/LEEME.md`; commit de inec.csv y sbp.csv | 5 series reales (20 inec + 33 sbp) validadas | — |
| 21:43 | M2.4 | Script `muestra-urls` (20 URLs, semilla 42) | listo | — |
| 21:48 | Cambios 5–8 | Clasificador por `clf.classes_`; método etiquetado declarado (metodo.json) + kappa; reclasificar tras entrenar; set reservado fuera del repo (BENCH) | 4 tests nuevos | — |
| 21:56 | M3 | `lenses/_llm.py`; paquete/boletín/fichas con LLM + verificador + límites; vista Paquete muestra proveedor | 5 tests con LLM simulado | Ollama local activo hizo fallar el test de "sin proveedor"; se simuló sin Ollama |
| 21:58 | M4 | `app/acciones.py`; contexto real; botón "Probar conexión"; plan fijo si herramientas=False | acciones aplicadas y visibles | — |
| 22:15 | M5.1 + M7.1 | Métricas contradicción/inyección/Precision@5/costo; cobertura 0/0; sample-claims y editor-candidatos; torch CPU + es-core-news-md fijado | uv lock regenerado (169 paquetes) | — |

## 2026-10-08 — Revisiones humanas

| Hora (Panamá) | Tarea | Qué se hizo | Resultado | Qué falló / se decidió |
| --- | --- | --- | --- | --- |
| 13:35 | H-4 | Revisión manual de 20 URLs de `data/reports/muestra_urls.csv` (existencia, título y fecha) | 20/20 correctas | Pendiente: cotejo de 3 valores del Banco Mundial |
| 13:40 | H-5 | Etiquetado de temas: 250 titulares (30 a ciegas por 2 personas + consenso; 120 asistidos, 4 corregidos; 100 extra asistidos, 0 corregidos) y 50 pares. Archivos: data/labels/temas.csv, pares.csv, metodo.json | 250 temas (excluir 104, eventos_naturales 58, logistica 22, servicios_publicos 21, economia 17, regulacion 14, turismo 14); 50 pares (7 si) | Sin kappa: no se conservó el registro previo al consenso (acuerdo inicial aprox. 21/30) |
