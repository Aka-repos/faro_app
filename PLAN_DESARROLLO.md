# FARO — Plan de desarrollo

Plan de construcción de FARO (hackIAthon Panamá 4ta edición · reto TVN Media) en `/Users/andresvega/hackathon/tvn/`.
Fuente de verdad del *qué*: el documento técnico de FARO (secciones 1–12). Este plan define el *cómo* y el *cuándo*,
organizado en **11 hitos de confianza (H0–H10)**. Ningún hito empieza si el anterior no pasó su compuerta.

Referencias usadas en todo el plan:
- **F-xx / E-xx / B-xx / L-xx:** funcionalidades (documento técnico, sección 5).
- **D-xx:** decisiones de diseño (sección 3).
- **T01–T10:** pruebas de aceptación del reto (sección 10).

---

## 0. Reglas de trabajo

1. **Un hito = una rama = un PR.** Al cerrar cada hito: `make check` verde, commit con la etiqueta `H<n>`, y una
   entrada en `docs/bitacora.md` (fecha, hora, qué se hizo, qué falló, qué se decidió). Esa bitácora se copia a Notion.
2. **Compuerta antes de avanzar.** Cada hito tiene criterios medibles y un comando que los demuestra. Si la compuerta
   falla, se aplica el plan B del hito; no se sigue construyendo encima de algo no validado.
3. **Validación humana en cada hito.** Al cerrar un hito, Claude se detiene y presenta la evidencia (salida de
   comandos, métricas, capturas). Andrés valida o pide correcciones antes del siguiente hito.
4. **Nada de secretos en el repo.** Claves solo en `.env` (en `.gitignore`) o en memoria de la sesión de Streamlit.
5. **Datos congelados.** Después de H2, el núcleo solo lee del snapshot (`data/raw/` + manifest). Ningún módulo
   del núcleo hace peticiones a sitios de noticias (D-13).
6. **Decisiones nuevas** se registran como D-17, D-18… en `docs/decisiones.md` con su justificación.

> **Pendiente con la organización:** confirmar si se puede escribir código o recolectar datos antes del evento.
> Si **sí**, H0 y H1 (y parte de H2) se adelantan. Si **no**, el plan arranca en H0 el día 1 y sigue igual.

---

## 1. Stack tecnológico (D-04, D-11)

Todo es **Python en un solo proceso**: un paquete `faro/` con la lógica, una CLI (`make …`) que corre el pipeline
y una UI en **Streamlit** que llama al mismo paquete. Sin servidores ni bases externas: todo vive en archivos
locales para que la demo funcione sin red (T10). Si después se quiere una UI en React, se monta FastAPI encima de
`faro/` sin tocar el núcleo.

### 1.1 Qué se usa, para qué y en qué hito

| Capa | Herramienta | Para qué se usa en FARO | Módulo | Hito |
| --- | --- | --- | --- | --- |
| Lenguaje | Python 3.11 | Todo el sistema | — | H0 |
| Entorno | uv + `pyproject.toml` + `uv.lock` | Instalar dependencias con versiones fijadas; reproducible para el jurado | raíz | H0 |
| Tareas | Makefile | Un comando por paso: `setup`, `data`, `freeze`, `build`, `run`, `test`, `eval`, `demo-offline` | raíz | H0 |
| Configuración | PyYAML + python-dotenv | Fuentes, lentes, mapas y sectores en YAML; rutas y fecha de referencia en `.env` | `config/` | H0 |
| Esquemas | Pydantic v2 | Validar registros recolectados, salidas del LLM y acciones de interfaz; generar el JSON Schema que se envía al modelo | `schemas/`, `faro/quality` | H0–H7 |
| Scraping: RSS | feedparser | Leer los RSS de TVN y otros medios | `faro/scrape/rss.py` | H1–H2 |
| Scraping: HTTP | httpx | Peticiones con timeout, reintentos y user-agent identificado | `faro/scrape/` | H1–H2 |
| Scraping: HTML | Scrapling | Leer sitemaps y secciones de medios; selectores que aguantan cambios de diseño; modo sigiloso si hay anti-bot | `faro/scrape/html.py`, `sitemap.py` | H1–H2 |
| Metadatos del artículo | trafilatura | Sacar título, fecha de publicación y resumen de forma uniforme entre medios | `faro/scrape/html.py` | H2 |
| Robots y ritmo | `urllib.robotparser` (librería estándar) | Respetar `robots.txt` y pausar por dominio (D-07) | `faro/scrape/check.py` | H1 |
| APIs | httpx | GDELT DOC 2.0, Banco Mundial v2, USGS FDSN | `faro/scrape/apis.py` | H2 |
| PDFs | pdfplumber | Extraer tablas de los boletines SBP con su página de origen | `faro/scrape/pdf.py` | H2, H8 |
| Datos tabulares | pandas | Limpieza, cuadrícula del Banco Mundial, reportes de calidad | `faro/quality` | H2 |
| Base de datos | SQLite (`sqlite3`, librería estándar) | Todas las tablas del modelo de datos en `data/faro.db` | `faro/` | H2 |
| Integridad | `hashlib` (librería estándar) | SHA-256 de cada archivo del snapshot para el manifest | `faro/quality/manifest.py` | H2 |
| Embeddings | sentence-transformers + `intfloat/multilingual-e5-small` | Vectores de cada noticia, en local y en CPU | `faro/nlp/embed.py` | H3 |
| Vectores | numpy | Matriz de vectores en `data/vectores.npy`; búsqueda por coseno (sin base vectorial, D-03) | `faro/nlp/embed.py` | H3 |
| Clasificación y clustering | scikit-learn | Regresión logística para el tema; clustering aglomerativo para eventos; métricas (macro-F1, precisión, recall) | `faro/nlp/classify.py`, `faro/events/cluster.py` | H3 |
| Casi duplicados | rapidfuzz | Detectar titulares casi iguales (misma agencia replicada) | `faro/events/provenance.py` | H3 |
| Entidades | spaCy + `es_core_news_md` | Personas, organizaciones y lugares; base del grafo | `faro/nlp/entities.py` | H3 |
| Pasarela LLM | LiteLLM | Una sola interfaz para el proveedor que elija el usuario (cualquiera de pago) y para Ollama; cálculo de costo | `faro/llm/gateway.py` | H5 |
| LLM local | Ollama + Qwen 2.5 7B Instruct (o Qwen 3 8B) | Respaldo sin red y modo 100% local | `faro/llm/providers.py` | H5, H8 |
| Agente | Bucle propio (~150 líneas) sobre LiteLLM | Plan → herramientas de solo lectura → respuesta; traza; acciones de interfaz | `faro/agent/` | H6–H7 |
| Interfaz | Streamlit | Las 7 vistas, barra lateral (lente, proveedor y clave, modo, fecha), estados de revisión | `app/` | H0, H6–H8 |
| Grafo | networkx + streamlit-agraph | Construir y mostrar el grafo de procedencias | `faro/events/`, `app/pages/grafo.py` | H7 |
| Notion | notion-client | Subir fichas, decisiones y resultados de pruebas | `faro/review/notion_sync.py` | H8 |
| Pruebas | pytest | T01–T10 y pruebas de cada módulo | `tests/` | H0–H9 |
| Calidad de código | ruff | Formato y lint en `make check` | raíz | H0 |
| Observabilidad | Log JSONL propio | Tokens, costo, latencia y proveedor por llamada; funciona offline | `faro/llm/gateway.py` | H5 |
| Repositorio | Git + GitHub (gh) | Repo con acceso al jurado | raíz | H0 |
| Despliegue (opcional) | Railway | Enlace público de la demo; la demo oficial corre en la laptop | — | H10 |

**Lo que no se usa, y por qué:** Pinecone u otra base vectorial gestionada (corpus pequeño y demo offline, D-03);
LangChain, LangGraph o CrewAI (capas que dificultan mostrar la traza y medir la abstención); Postgres o Supabase
(requieren servidor o red); React (cuesta un día que se necesita para el núcleo).

### 1.2 Requisitos de la máquina

| Requisito | Comando |
| --- | --- |
| Python 3.11 y uv | `brew install uv` · `uv python install 3.11` |
| Dependencias del proyecto | `make setup` (corre `uv sync`) |
| Modelo de spaCy | `uv run python -m spacy download es_core_news_md` |
| Navegadores de Scrapling (solo si un medio exige modo sigiloso) | `uv run scrapling install` |
| Ollama y el modelo local | `brew install ollama` · `ollama pull qwen2.5:7b-instruct` |
| Modelo de embeddings | Se descarga solo la primera vez (~120 MB); `make setup` lo precarga para que funcione sin red |

### 1.3 Dependencias (`pyproject.toml`)

Las versiones exactas se fijan con `uv lock` el día de la instalación y no se cambian durante el evento.

```toml
[project]
name = "faro"
requires-python = ">=3.11,<3.12"
dependencies = [
  # configuración y esquemas
  "pydantic>=2", "pyyaml", "python-dotenv",
  # scraping y fuentes
  "httpx", "feedparser", "scrapling", "trafilatura", "pdfplumber",
  # datos
  "pandas", "numpy",
  # NLP
  "sentence-transformers", "scikit-learn", "rapidfuzz", "spacy",
  # LLM
  "litellm",
  # interfaz y grafo
  "streamlit", "streamlit-agraph", "networkx",
  # integración
  "notion-client",
]

[dependency-groups]
dev = ["pytest", "ruff"]
```

### 1.4 Cómo se conectan las piezas

```
fuentes.yaml ─► faro/scrape (feedparser · httpx · Scrapling · trafilatura · pdfplumber)
                    │  respeta robots.txt, guarda data/raw/
                    ▼
               faro/quality (Pydantic · pandas · hashlib) ─► data/faro.db (SQLite) + manifest.json
                    ▼
               faro/nlp + faro/events (sentence-transformers · numpy · scikit-learn · rapidfuzz · spaCy)
                    ▼
               faro/context + faro/scoring (YAML de lentes y mapas)
                    ▼
               faro/agent ─► faro/llm/gateway (LiteLLM: proveedor del usuario → Ollama → extractivo)
                    ▼
               faro/guard (verificador y escudo, código puro)
                    ▼
               app/ (Streamlit · streamlit-agraph) ─► faro/review (estados, notion-client)
```

---

## 2. Mapa de hitos

| Hito | Nombre | Confianza que gana | Funcionalidades | Pruebas del reto | Cuándo |
| --- | --- | --- | --- | --- | --- |
| H0 | Esqueleto ejecutable | El repo instala y corre en una máquina limpia | — | — | Día 1, 1 h |
| H1 | Fuentes verificadas | Sabemos qué se puede recolectar, legalmente y en volumen | F-01 (inventario) | — | Día 1 mañana |
| H2 | Snapshot v1 congelado | Hay datos suficientes, limpios y trazables | F-01, F-02, F-03 | T01 | Día 1 tarde |
| H3 | Núcleo NLP | La IA agrupa y clasifica mejor que el baseline | F-04, F-05 | T02, T03 | Día 2 mañana |
| H4 | Contexto y puntaje | La bandeja prioriza de forma reproducible y explicable | F-06, F-07, F-09 | T04, T05, T08 | Día 2 mañana |
| H5 | Generación segura | Nada sin evidencia llega al borrador; la demo no se cae | F-10, F-11, F-12, L-01 | T06, T07, T10 (parcial) | Día 1 tarde – Día 2 |
| H6 | Recorrido completo | Del dato a la ficha revisada, de punta a punta | F-08, F-13, E-01–E-03 | T09 | **Día 2 tarde (punto de control)** |
| H7 | Interfaz agéntica y grafo | El agente maneja la vista y el grafo explica procedencias | F-16, F-17, F-18, E-04, E-05 | CU-03 en vivo | Día 2 noche |
| H8 | Lente bancario y comparador | El núcleo es reutilizable; local vs. nube medido | B-01–B-06, L-02, L-03, F-14 | CU-05 | Día 2 noche |
| H9 | Evaluación completa | Métricas reales con numerador y denominador | F-15 | T01–T10 completas | Día 3 mañana |
| H10 | Congelamiento y demo | Funciona sin red, en máquina limpia, y se presenta desde Notion | — | T10 | Día 3 tarde |

**Regla de recorte:** si a las 12:00 del día 2 H6 no está cerrado, **H8 pasa a "próximos pasos"** y ese tiempo se
dedica a H6, H7 y H9.

---

## 3. Hitos en detalle

### H0 — Esqueleto ejecutable

**Objetivo:** un repositorio que cualquiera clona, instala y ejecuta con un comando.

Tareas:
- `git init`, `.gitignore` (incluye `.env`, `data/raw/*` pesado si aplica, `.cache/`, `*.npy` regenerables).
- `pyproject.toml` con **uv** y versiones fijadas; Python 3.11.
- Estructura de carpetas de la sección 8 del documento técnico: `faro/{scrape,quality,nlp,events,context,scoring,agent,llm,guard,lenses,review,eval}`, `config/`, `prompts/`, `schemas/`, `data/`, `app/`, `tests/`, `docs/`.
- `Makefile` con objetivos: `setup`, `data`, `freeze`, `verify-snapshot`, `build`, `run`, `test`, `eval`, `check`, `demo-offline`.
- `.env.example` sin valores; `config/settings.py` que lee `.env` (fecha de referencia, rutas, timeouts).
- `app/streamlit_app.py` con las 7 páginas vacías (Bandeja, Ficha, Paquete, Agente, Grafo, Comparador, Calidad) y la barra lateral (lente, proveedor y clave, modo, fecha de referencia).
- `tests/test_smoke.py`.
- `docs/bitacora.md`, `docs/decisiones.md` (D-01 a D-16 copiadas del documento técnico).

**Compuerta H0:**

| Criterio | Cómo se demuestra |
| --- | --- |
| Instala desde cero | `rm -rf .venv && make setup` sin errores |
| Pruebas corren | `make test` → smoke verde |
| UI arranca | `make run` abre Streamlit con las 7 páginas |
| Sin secretos | `git grep -nE "(sk-|api[_-]?key\s*=\s*['\"][^'\"]+)"` sin resultados |

**Plan B:** si uv da problemas en la máquina, `python -m venv` + `requirements.txt` con versiones fijadas.

---

### H1 — Fuentes verificadas

**Objetivo:** saber, antes de recolectar en serio, qué fuentes sirven, por qué método, con qué condiciones y con
qué volumen esperado en la ventana D-01 **[2025-10-02, 2026-10-01)**.

Tareas:
- `config/fuentes.yaml`: una entrada por fuente candidata (sección 6 del documento técnico): id, familia, url_base,
  método (`rss | sitemap | html | api | pdf`), rate_limit_s, user_agent, notas de condiciones.
- `faro/scrape/check.py` (`make check-sources`): para cada fuente
  - descarga `robots.txt` y evalúa las rutas que se usarán (`urllib.robotparser`);
  - prueba el método (lee el RSS, lista el sitemap, pide una página de sección, llama la API);
  - estima volumen por mes dentro de la ventana (URLs con fecha en sitemap/RSS/GDELT);
  - escribe `data/reports/fuentes_check.json` y una tabla en `docs/catalogo.md`.
- Llamadas de prueba a fuentes oficiales: INEC, ACP, SBP (último mes publicado), Banco Mundial (API v2), USGS (FDSN).

**Compuerta H1:**

| Criterio | Umbral | Cómo se demuestra |
| --- | --- | --- |
| Medios utilizables | ≥ 5 medios con método funcional y `robots.txt` permitido | `fuentes_check.json` |
| TVN | ≥ 20 noticias estimadas en la ventana | Conteo por mes de TVN |
| Volumen total estimado | ≥ 1.000 noticias (mínimo para continuar: 300) | Suma de estimaciones |
| Series oficiales | ≥ 3 series mensuales con datos hasta jun-2026 o posterior | Último período por serie |
| Condiciones registradas | 100% de fuentes con nota de condiciones | `docs/catalogo.md` |

**Plan B:** si un medio bloquea o no tiene RSS/sitemap → Scrapling en modo sigiloso con pausa; si aun así falla,
se reemplaza por GDELT filtrado por `domain:`. Si TVN no llega a 20 → completar con GDELT `domain:tvn-2.com`.

---

### H2 — Snapshot v1 congelado

**Objetivo:** un conjunto de datos limpio, deduplicado, dentro de la ventana, con manifest verificable (D-13).

Tareas:
- Recolectores (`faro/scrape/`): `rss.py` (feedparser), `sitemap.py`, `html.py` (Scrapling + trafilatura para
  título, fecha y resumen), `apis.py` (GDELT, Banco Mundial, USGS), `pdf.py` (SBP con pdfplumber).
  Todos respetan `robots.txt`, pausa por dominio y guardan la respuesta cruda en `data/raw/<fuente>/<fecha>/`.
- `faro/quality/validate.py` (F-02): esquema Pydantic por tipo de registro; fechas ISO UTC; URL válida; ventana D-01;
  nulos conservados; duplicados por URL normalizada; lo inválido va a `cuarentena` con su motivo.
- Carga a SQLite (`data/faro.db`) con el esquema de la sección 6 (tablas `fuente`, `noticia`, `serie_oficial`,
  `indicador`, `sismo`, `cuarentena`).
- `faro/quality/manifest.py` (F-03): `data/manifest.json` con versión, fecha de corte UTC, consultas, conteos por
  archivo y fuente, SHA-256 por archivo, condiciones y transformaciones.
- `make freeze` congela la versión `v1`; `make verify-snapshot` recalcula los hashes.
- `data/reports/calidad_v1.json` + página Calidad en Streamlit (conteos, cuarentena, cobertura por medio y mes).

**Compuerta H2:**

| Criterio | Umbral | Cómo se demuestra |
| --- | --- | --- |
| Noticias únicas | ≥ 1.000 (mínimo para continuar: 300) | `calidad_v1.json` |
| TVN | ≥ 20 | Conteo por fuente |
| Medios distintos | ≥ 5 | Conteo por medio |
| Fuera de ventana | 0 registros en `noticia` | Consulta SQL |
| Integridad | `make verify-snapshot` sin diferencias | Salida del comando |
| T01 | Archivo sintético con fechas inválidas y nulos: se separan errores, se conservan nulos, la carga no se bloquea | `pytest tests/test_t01.py` |
| Reproducibilidad | Borrar `faro.db` y reconstruir desde `raw/` da los mismos conteos | `make build` dos veces |

**Plan B:** si a las 18:00 del día 1 no se llega a 1.000, se congela con lo que haya (≥ 300) y se documenta como
decisión; la ampliación queda para después de H6, solo si sobra tiempo.

---

### H3 — Núcleo NLP

**Objetivo:** clasificación temática y agrupación de eventos medibles contra un baseline.

Tareas:
- **Etiquetado humano (1 h, los dos):** ~150 titulares con tema (6 clases) → `data/labels/temas.csv`;
  ~50 pares de noticias marcados como "mismo evento / distinto" → `data/labels/pares.csv`.
- `faro/nlp/embed.py`: `multilingual-e5-small`, vectores en `data/vectores.npy` con su índice de IDs.
- `faro/nlp/classify.py`: baseline por palabras clave (`config/keywords.yaml`) vs. regresión logística sobre embeddings.
- `faro/nlp/entities.py`: spaCy `es_core_news_md`; detección de agencia (EFE, AFP, AP, Reuters) y de acusación.
- `faro/events/cluster.py`: clustering aglomerativo por coseno + ventana de 72 h + entidades compartidas.
- `faro/events/provenance.py`: procedencias (agencia declarada, casi duplicado con rapidfuzz, mismo dominio).

**Compuerta H3:**

| Criterio | Umbral | Cómo se demuestra |
| --- | --- | --- |
| Clasificador | macro-F1 de embeddings+LR **>** baseline, con validación cruzada 5-fold sobre las 150 etiquetas | `make eval-nlp` → `reports/nlp.json` |
| Agrupación | Precisión de pares ≥ 0,80 sobre los 50 pares etiquetados (recall reportado) | Mismo reporte |
| T02 | 3 registros del mismo evento → 1 evento, 3 fuentes, sin triplicar corroboración | `pytest tests/test_t02.py` |
| T03 | Noticia antigua recirculada → conserva fecha original, no cuenta como evento nuevo | `pytest tests/test_t03.py` |
| CU-03 | Un caso real o sintético de agencia replicada: 5 menciones → 1 procedencia | Test + captura |

**Plan B:** si e5 no supera al baseline → probar `bge-m3`; si sigue sin superarlo, se reporta honestamente
("la IA no ayudó en esta tarea") y se usa el mejor de los dos. Eso también suma en la rúbrica.

---

### H4 — Contexto y puntaje

**Objetivo:** cada evento con contexto oficial pertinente, puntaje desglosado y estado de evidencia independiente.

Tareas:
- `config/mapas.yaml`: tema → series oficiales / indicadores / sismos que aplican.
- `faro/context/link.py` (F-06): enlaza solo si hay regla; guarda `motivo_enlace`; nunca fuerza.
- `config/lentes/editorial.yaml`: pesos 30/25/20/15/10, normalización 0–1 de R, I, U, N, E documentada.
- `faro/scoring/score.py` (F-07): P, rango bajo/medio/alto, desempate (urgencia, luego ID), `reglas_version`,
  `fecha_referencia` = 2026-09-30 23:59 Panamá (D-09).
- Estado de evidencia: insuficiente / parcial / suficiente, calculado aparte del puntaje.
- `faro/events/contradict.py` (F-09): cifras y entidades incompatibles dentro de un evento.

**Compuerta H4:**

| Criterio | Umbral | Cómo se demuestra |
| --- | --- | --- |
| Reproducible | Dos corridas con la misma versión dan el mismo ranking (hash del top 50 idéntico) | `make build && make build` |
| Explicable | 100% de eventos con R, I, U, N, E y versión de reglas | Consulta SQL |
| T04 | Cifra anual del Banco Mundial se muestra con país, año y unidad, nunca como "de hoy" | `pytest tests/test_t04.py` |
| T05 | Dos afirmaciones incompatibles → ambas visibles + verificación pendiente | `pytest tests/test_t05.py` |
| T08 | Prioridad alta expone componentes y regla; no habilita publicación | `pytest tests/test_t08.py` |
| Sensatez | Revisión manual del top 10 por Andrés: ningún evento absurdo en el top 5 | Captura + nota en bitácora |

**Plan B:** si el top 10 no convence, se ajustan pesos o normalización y se registra el cambio como decisión
(el reto pide justificar cambios de pesos).

---

### H5 — Generación segura

**Objetivo:** pasarela BYOK con cascada, verificador en código y escudo anti-inyección. Puede construirse en
paralelo a H2–H4 porque solo necesita datos de prueba.

Tareas:
- `faro/llm/gateway.py` (F-10): LiteLLM; modos `usuario | local | auto`; cascada usuario → Ollama → extractivo;
  timeouts 20 s / 60 s; caché por `sha256(prompt_version + lente + ids_evidencia + modelo)`; log JSONL con
  proveedor, modelo, tokens, costo, latencia.
- Detección de capacidades al conectar (JSON con esquema, herramientas, precio conocido) y degradación (sección 7.1).
- Clave del usuario solo en `st.session_state`; enmascarado de claves en logs.
- `faro/llm/extractive.py`: modo sin LLM a partir de afirmaciones verificadas.
- `schemas/`: modelos Pydantic de afirmación, ficha, paquete editorial, boletín y acciones de interfaz.
- `faro/guard/verifier.py` (F-11): evidencia existente; campo citado contiene la afirmación; **candado de cifras**
  (todo número del borrador existe literal en la evidencia citada, con año y unidad); tipos permitidos por lente;
  etiqueta "basado únicamente en titular/metadatos"; frases prohibidas por lente.
- `faro/guard/shield.py` (F-12): contenido de fuentes delimitado como datos; filtro de patrones de inyección;
  clave canario en el prompt que nunca debe aparecer en la salida.

**Compuerta H5:**

| Criterio | Umbral | Cómo se demuestra |
| --- | --- | --- |
| Verificador | Rechaza 100% de los casos sintéticos: cifra inventada, cita inexistente, campo que no respalda, hipótesis sin marcar | `pytest tests/test_verifier.py` (≥ 15 casos) |
| T06 | Consulta sin respuesta → abstención explícita, cero cifras o citas inventadas | `pytest tests/test_t06.py` |
| T07 | Fuente sintética que pide ignorar instrucciones → la salida no cambia de comportamiento ni contiene el canario | `pytest tests/test_t07.py` |
| Multiproveedor | El mismo caso funciona con ≥ 2 proveedores (uno de pago con la clave de Andrés + Ollama) | Log JSONL |
| Cascada offline | Con red cortada, `auto` cae a Ollama y luego a extractivo sin error | `make test-offline` (bloquea red en el proceso) |
| Secretos | La clave no aparece en logs, caché ni archivos | `grep` sobre `data/` y logs |

**Plan B:** si el modelo elegido no soporta herramientas o JSON fiable → plan fijo + reintento + siguiente
proveedor (degradación de la sección 7.1). Si Ollama es muy lento → caché de los casos de la demo + extractivo.

---

### H6 — Recorrido completo (punto de control del día 2)

**Objetivo:** del dato a la ficha revisada y exportada, de punta a punta, aunque la interfaz sea simple.

Tareas:
- `faro/agent/tools.py`: herramientas de solo lectura de la sección 7.3 (`buscar_noticias`, `abrir_evento`,
  `ver_procedencias`, `consultar_indicador`, `consultar_serie`, `buscar_sismos`, `consultar_sbp`, `ranking`).
- `faro/agent/loop.py` (F-08): plan → herramienta → observación, máx. 6 pasos y 15 s; traza en `traza_agente`;
  respuesta final por el verificador; abstención si no hay evidencia.
- `prompts/agente_v1.md`, `prompts/brief_v1.md`, `prompts/guion_v1.md`.
- Streamlit: Bandeja (E-01), Ficha (E-02), Paquete editorial (E-03), página Agente con traza visible.
- `faro/review/states.py` (F-13): cinco estados, revisor, nota; "aprobado como borrador" no publica.
- Exportación `data/out/fichas.jsonl` con el contrato del reto.

**Compuerta H6:**

| Criterio | Umbral | Cómo se demuestra |
| --- | --- | --- |
| E2E automatizado | Pregunta → traza → ficha → paquete → revisión → `fichas.jsonl` válido | `pytest tests/test_e2e.py` |
| T09 | Brief ≤ 250 palabras, guion 45–60 s, copy ≤ 80 palabras, citas pertinentes, hechos vs. inferencias separados | `pytest tests/test_t09.py` |
| CU-01 | "¿Qué cinco temas merecen revisión hoy y por qué?" → top 5 con evidencia y vacíos | Captura + traza |
| CU-02 | Tema económico + serie oficial → brief sin confundir dato anual con medición actual | Captura + traza |
| CU-04 | Cifra inexistente → abstención; contradicción → versiones | Captura + traza |
| Latencia | Mediana ≤ 15 s en 10 consultas con el proveedor del usuario (p95 reportado) | `reports/latencia.json` |
| Demo manual | Andrés recorre el guion de demo sin ayuda | Nota en bitácora |

**Plan B:** si a las 12:00 del día 2 no está cerrado → se activa la regla de recorte (H8 sale) y los dos trabajan
en H6.

---

### H7 — Interfaz agéntica y grafo

**Objetivo:** el agente maneja la interfaz y sabe qué ve el usuario; el grafo hace visible la procedencia.

Tareas:
- Acciones de interfaz (F-17, sección 7.4): `filtrar_bandeja`, `abrir_ficha`, `ir_a`, `resaltar_en_grafo`,
  `mostrar_evidencia`; JSON validado con Pydantic; aplicadas sobre `st.session_state` y `st.switch_page`;
  filtros visibles como chips quitables; acciones desconocidas ignoradas y registradas.
- Contexto de pantalla (F-18): vista activa, evento abierto, filtros y lente viajan con cada pregunta.
- Grafo de procedencias (F-16): networkx + streamlit-agraph; nodos medio / agencia / evento / entidad; color por
  estado de evidencia; detalle al pasar el cursor; selector de evento o medio.
- E-04 (verificaciones como tareas en Notion) y E-05 (validación del guion).

**Compuerta H7:**

| Criterio | Umbral | Cómo se demuestra |
| --- | --- | --- |
| Acciones | Las 5 acciones funcionan desde lenguaje natural en 5 consultas de prueba | Captura + traza |
| Robustez | Una acción inválida o inventada se ignora y queda en la traza | `pytest tests/test_ui_actions.py` |
| Contexto | Con un evento abierto, "¿por qué tiene prioridad alta?" responde sin pedir aclaración | Captura |
| Grafo | El caso CU-03 (agencia replicada) se ve como 1 procedencia con varios medios | Captura |
| Seguridad | Ninguna acción de interfaz modifica la base de datos | Test que compara hash de `faro.db` antes y después |

**Plan B:** si streamlit-agraph da problemas → pyvis embebido como HTML. Si el control de interfaz se complica →
se deja solo `filtrar_bandeja` y `abrir_ficha`, que son las que más lucen en la demo.

---

### H8 — Lente bancario y comparador local vs. nube

**Objetivo:** demostrar que el núcleo es reutilizable y medir local vs. proveedor.

Tareas:
- `config/lentes/banca.yaml`, `prompts/boletin_v1.md`, esquema de boletín (B-04).
- `config/sectores.yaml` + enlace evento → sector con regla (B-02).
- 4–5 series SBP de oct-2025 a sep-2026 con página de origen (B-03).
- Verificador por lente: observación vs. hipótesis (B-05) y frases prohibidas (B-06).
- Interruptor "100% local" (L-02) y página Comparador (L-03): mismo caso, dos proveedores; citas válidas,
  abstención, latencia, tokens y costo.
- F-14: sincronización de fichas, decisiones y resultados de pruebas a Notion (o exportación para carga manual).

**Compuerta H8:**

| Criterio | Umbral | Cómo se demuestra |
| --- | --- | --- |
| CU-05 | "¿Qué señales públicas del entorno logístico debo revisar?" → boletín con sectores, horizonte, evidencia y 3 preguntas | Captura + traza |
| Barreras | 0 frases prohibidas en 10 boletines generados; toda hipótesis marcada | `pytest tests/test_banca.py` |
| Cambio de lente | El mismo evento pasa de paquete editorial a boletín con un clic | Captura |
| Comparador | Tabla nube vs. local con al menos 10 casos | `reports/comparador.json` |

**Plan B:** si la SBP consume tiempo → el boletín usa series INEC/ACP y Banco Mundial; SBP queda como próximo paso.

---

### H9 — Evaluación completa

**Objetivo:** métricas reales, reproducibles y honestas (sección 9.1 del reto).

Tareas:
- `data/benchmark.jsonl`: 40 preguntas de desarrollo (Andrés) — 20 sustentadas, 7 contradicción/ambigüedad,
  7 sin respuesta, 6 adversariales — y 20 reservadas (compañero) con las mismas proporciones, guardadas fuera del
  repo hasta la corrida final.
- `faro/eval/benchmark.py`, `baselines.py`, `metrics.py` → `make eval` genera `reports/metrics_<fecha>.json` y
  una tabla Markdown lista para Notion.
- Revisión humana de ≥ 30 afirmaciones para la validez de sustento.
- Precision@5 contra la selección de un editor (o exploratorio, D-02).
- Prueba de tiempo: tarea manual vs. asistida, 3 repeticiones cada una (si se consigue un editor).
- Las 10 pruebas T01–T10 como tests de pytest; matriz exportada a Notion.

**Compuerta H9:**

| Métrica | Umbral | Fuente |
| --- | --- | --- |
| T01–T10 | 10/10 en verde | `make test` |
| Cobertura de citas | 100% de afirmaciones factuales con evidencia identificable | `metrics.json` |
| Validez de sustento | ≥ 90% sobre ≥ 30 afirmaciones revisadas | Revisión humana registrada |
| Abstención correcta | ≥ 80% de las preguntas sin respuesta | `metrics.json` |
| Abstención incorrecta | Reportada con IDs | `metrics.json` |
| Inyección | 100% de adversariales superadas | `metrics.json` |
| Clasificación | macro-F1 vs. baseline reportado | `reports/nlp.json` |
| Ranking | Precision@5 reportado (o "exploratorio") | `metrics.json` |
| Latencia y costo | Mediana ≤ 15 s; p95, tokens y USD por consulta | `metrics.json` |
| Formato | Todo como numerador/denominador + lista de fallos | Tabla de Notion |

Se corre **dos veces**: noche del día 2 (corrida 1) y día 3 después de corregir (corrida 2). La diferencia entre
ambas, con los fallos corregidos, es la evidencia de "prueba fallida y su corrección" que pide el jurado.

**Plan B:** si una métrica no llega al umbral, no se esconde: se reporta con los IDs que fallan y la causa.

---

### H10 — Congelamiento y demo

**Objetivo:** que todo funcione el día del pitch, sin red y en una máquina limpia.

Tareas:
- `make demo-offline`: clona en una carpeta temporal, instala, carga el snapshot congelado, precalienta Ollama,
  llena la caché de los casos de la demo y arranca Streamlit.
- README: instalación, comando de ejecución, dependencias, `.env.example`, cómo correr pruebas y benchmark,
  limitaciones conocidas.
- Notion: 8 páginas completas, ≥ 8 tareas con historial, decisiones D-01…D-n, catálogo de datos, ≥ 5 fichas
  (una con evidencia insuficiente), matriz T01–T10, métricas y página del pitch con embeds.
- Grabación de respaldo de la demo (2–3 min) incrustada en Notion.
- Dos ensayos completos del pitch de 10 minutos; uno con el wifi apagado.

**Compuerta H10 (lista de admisión del reto):**

- [ ] `make demo-offline` funciona en una carpeta recién clonada y con la red desactivada (T10)
- [ ] El jurado tiene acceso al repositorio y a Notion
- [ ] Notion tiene plan con ≥ 8 tareas y ≥ 3 decisiones registradas durante el evento
- [ ] Catálogo completo de fuentes con condiciones y hashes
- [ ] ≥ 5 fichas trazables, una sin evidencia suficiente
- [ ] Matriz T01–T10 y métricas de la ejecución final
- [ ] Pitch navegable desde Notion
- [ ] `git grep` de claves sin resultados; `.env` fuera del repo
- [ ] Las 4 preguntas dinámicas del jurado ensayadas con respuesta en pantalla

---

## 4. Cronograma por persona

| Tramo | Persona A (datos, NLP, banca) | Persona B (LLM, agente, UI, Notion) | Hito que cierra |
| --- | --- | --- | --- |
| Día 1, 08:00–09:00 | H0 (juntos) | H0 (juntos) | **H0** |
| Día 1, 09:00–12:00 | H1: inventario y prueba de medios | H1: fuentes oficiales; espacio Notion | **H1** |
| Día 1, 12:00–18:00 | H2: recolectores de medios, validación, manifest | H2: recolectores oficiales, esquema SQLite; H5: pasarela | **H2** |
| Día 1, 18:00–22:00 | Etiquetado (juntos, 1 h); H3 embeddings | H5: verificador, escudo, cascada | — |
| Día 2, 08:00–12:00 | H3 clasificador, eventos, procedencias; H4 | H5 cierre; H6: herramientas del agente, UI base | **H3, H4, H5** |
| Día 2, 12:00–18:00 | H4 cierre; apoyo a H6 | H6: agente, ficha, paquete, revisión | **H6 (punto de control)** |
| Día 2, 18:00–23:00 | H7 grafo; H8 sectores y SBP | H7 acciones y contexto; H8 lente y comparador; benchmark corrida 1 | **H7, H8** |
| Día 3, 08:00–13:00 | H9: métricas, baselines, revisión de afirmaciones | H9: T01–T10, matriz y correcciones; corrida 2 | **H9** |
| Día 3, 13:00–cierre | H10: demo offline, README | H10: Notion, pitch, grabación; ensayos (juntos) | **H10** |

---

## 5. Tablero de confianza

Se actualiza al cerrar cada hito y se copia a Notion ("Plan y decisiones").

| Hito | Estado | Fecha y hora | Evidencia | Validado por | Desviaciones |
| --- | --- | --- | --- | --- | --- |
| H0 | Pendiente | | | | |
| H1 | Pendiente | | | | |
| H2 | Pendiente | | | | |
| H3 | Pendiente | | | | |
| H4 | Pendiente | | | | |
| H5 | Pendiente | | | | |
| H6 | Pendiente | | | | |
| H7 | Pendiente | | | | |
| H8 | Pendiente | | | | |
| H9 | Pendiente | | | | |
| H10 | Pendiente | | | | |

Estados posibles: Pendiente · En curso · Compuerta fallida (plan B activo) · Cerrado.
