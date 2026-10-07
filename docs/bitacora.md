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

## Próximos pasos (para la hackathon)

1. Confirmar con la organización si se puede recolectar/codificar antes del evento.
2. `FUENTES_LIVE=1 make data` + `make freeze` para el snapshot real (≥ 20 TVN, ≥ 5 medios, ≥ 1.000 noticias meta).
3. Etiquetar ~150 titulares (`data/labels/temas.csv`) y ~50 pares para medir macro-F1 y precisión de pares.
4. Configurar proveedor BYOK + Ollama y medir latencia/costo en el Comparador.
5. Sincronizar fichas/decisiones/pruebas a Notion y ensayar el pitch de 10 min (uno con wifi apagado).
