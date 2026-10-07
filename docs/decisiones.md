# Decisiones de diseño (D-01 … D-16)

Copiadas del documento técnico de FARO (sección 3). Se exportan a Notion ("Plan y decisiones").
Las decisiones nuevas (D-17 en adelante) se registran aquí con fecha y justificación.

| ID | Decisión | Justificación |
| --- | --- | --- |
| D-01 | Noticias de la demo en [2025-10-02, 2026-10-01); se excluye [2024-01-01, 2025-10-01) | Respuesta expresa de la organización: del 2 de octubre de 2025 al último mes completo (septiembre 2026). |
| D-02 | Precision@5 exploratorio si no hay editor evaluador | Lo admite la sección 9.1 del reto. |
| D-03 | Sin base vectorial gestionada: matriz numpy local | Corpus de 1.000–3.000 documentos y demo offline obligatoria (T10). |
| D-04 | Python + SQLite + Streamlit en un solo proceso | Máxima velocidad para 2 personas en 3 días; FastAPI se puede montar después sin tocar el núcleo. |
| D-05 | ID de evidencia universal y verificador en código | Hace verificable el 100% de cobertura de citas; no depende de que el LLM se porte bien. |
| D-06 | Cascada de LLM: proveedor del usuario → Ollama local → extractivo | La demo nunca se cae (T10). |
| D-07 | Scraping responsable: RSS, sitemaps, secciones públicas y APIs; solo título, fecha, URL, medio y resumen publicado | La organización pide scraping general; las secciones 6 y 8 exigen respetar derechos. |
| D-08 | Comparar palabras clave vs. embeddings + regresión logística | La sección 8 exige un baseline y medir la mejora. |
| D-09 | Fecha de referencia = corte del snapshot: 2026-09-30 23:59 hora de Panamá (configurable) | Urgencia, novedad y bandeja se calculan contra el corte de los datos. |
| D-10 | El acceso al sistema es un agente investigador con herramientas de solo lectura | El reto habla de "el agente" y el jurado lo probará en vivo. |
| D-11 | Stack: Python 3.11 + uv + SQLite + Streamlit (sección 8) | Evaluación de 4 alternativas por velocidad, offline, ecosistema de IA y reproducibilidad. |
| D-12 | El LLM principal lo elige el usuario: pega su clave de cualquier proveedor (BYOK) | Ningún proveedor queda fijado; el costo es medible y la clave nunca se guarda. |
| D-13 | Snapshot propio congelado (raw/ + manifest con SHA-256) antes de construir el núcleo | La demo no puede depender de sitios en vivo (T10). |
| D-14 | Datos históricos solo para entrenar y como contexto rotulado por año | La organización lo permite; la agenda que ve el editor es siempre reciente. |
| D-15 | El agente puede mover la interfaz (filtros, vistas, abrir fichas) y recibe lo que el usuario ve | Menos clics y respuestas en contexto; las acciones solo cambian la vista, nunca los datos. |
| D-16 | Grafo de procedencias como vista propia | Hace visible el CU-03: cuántas fuentes son realmente independientes. |

## Decisiones nuevas (durante la implementación)

| ID | Fecha | Decisión | Justificación |
| --- | --- | --- | --- |
| D-17 | 2026-10-06 | Seed sintético determinístico como snapshot de demostración por defecto | Permite que el pipeline, T01–T10 y la demo corran sin red y en máquina limpia (T10); el snapshot real se obtiene con `FUENTES_LIVE=1 make data`. |
| D-18 | 2026-10-06 | Dependencias pesadas (sentence-transformers, spacy) como extra `ml` | `make setup` debe ser rápido y funcionar sin red; `faro/nlp` degrada a hashing de n-gramas y regex determinísticos. |
| D-19 | 2026-10-06 | Verificador exige respaldo literal solo a `hecho`/`observacion`; inferencias/hipótesis/declaraciones se marcan como tales | Las inferencias derivan de la evidencia pero no son literales; el candado de cifras sigue aplicando a todos los tipos. |
