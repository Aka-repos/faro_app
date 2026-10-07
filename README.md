# FARO — Copiloto de inteligencia informativa con IA

**FARO no escribe noticias. Le dice al editor qué sabe, de dónde lo sabe y qué le falta saber.**

Prototipo para el reto **"De la señal a la decisión"** (hackIAthon Panamá 4ta edición · reto TVN Media).
Convierte noticias públicas de Panamá (2025-10-02 → 2026-09-30) y datos oficiales en una **bandeja
priorizada** de eventos con **fichas** donde cada afirmación cita su fuente, fecha y alcance. Con un
cambio de **lente**, el mismo núcleo sirve al analista bancario para preparar un boletín de entorno.

- **Lente editorial (principal):** agenda priorizada, ficha de investigación, brief, guion 45–60 s y copy digital.
- **Lente bancario (extensión):** boletín de entorno con sectores, horizonte, evidencia y preguntas.

## Principios de seguridad (en código, no en instrucciones al modelo)

| Riesgo | Control |
| --- | --- |
| Alucinación de cifras | **Candado de cifras**: todo número del borrador debe existir literal en la evidencia citada |
| Cita inventada | **ID de evidencia universal** (`N:`, `OF:`, `WB:`, `USGS:`, `SBP:`) + verificador en código |
| Inyección desde una fuente | Contenido delimitado como **dato**, filtro de patrones y **clave canario** |
| Prioridad ≠ verdad | Estado de evidencia **independiente** del puntaje; aprobar un borrador **no** publica |
| Fuga de credenciales | Clave del usuario solo en `st.session_state`; `.env` fuera del repo; logs enmascarados |

## Instalación

```bash
# 1. Requisitos: Python 3.11 y uv
brew install uv
uv python install 3.11

# 2. Dependencias
make setup

# 3. Generar snapshot (seed sintético por defecto; ver FUENTES_LIVE abajo)
make data

# 4. Construir la base y las capas deducidas
make build
```

### Snapshot real vs. sintético

El repositorio trae un **seed sintético determinístico** (`faro/seed.py`) para que el pipeline, las pruebas
y la demo funcionen **sin red** y en una máquina limpia (T10). El snapshot real se obtiene con los
recolectores de `faro/scrape/` (RSS, sitemap, HTML, GDELT, Banco Mundial, USGS, SBP) ejecutando:

```bash
FUENTES_LIVE=1 make data      # recolecta de las fuentes reales (respeta robots.txt)
make freeze                   # congela v1 y escribe manifest.json con SHA-256
make verify-snapshot          # recalcula hashes y los compara
```

## Ejecutar

```bash
make run          # Streamlit con las 7 vistas
make test         # smoke + T01–T10 + módulos
make check        # ruff + pytest
make eval         # benchmark y métricas -> reports/metrics_*.json
make eval-nlp     # clasificación vs. baseline -> reports/nlp.json
make check-sources # robots.txt + método + volumen -> reports/fuentes_check.json
make demo-offline  # instala en carpeta temporal, carga snapshot y arranca la demo
```

## Configuración

Copia `.env.example` a `.env` y completa (nunca commitees `.env`):

- `FARO_FECHA_REFERENCIA` — corte del snapshot (por defecto 2026-09-30 23:59 Panamá).
- `FARO_LLM_MODO` — `auto | usuario | local`.
- `FARO_LLM_PROVEEDOR/MODELO/API_KEY` — proveedor BYOK (LiteLLM).
- `OLLAMA_BASE_URL`, `FARO_OLLAMA_MODELO` — fallback local.
- `NOTION_TOKEN`, `NOTION_PARENT_PAGE_ID` — sincronización (opcional; la carga manual está permitida).

Los lentes, fuentes, mapas y sectores se configuran en YAML bajo `config/` (sin tocar el núcleo).

## Estructura

```
faro/       lógica (scrape, quality, nlp, events, context, scoring, agent, llm, guard, lenses, review, eval)
config/     fuentes.yaml, keywords.yaml, mapas.yaml, sectores.yaml, lentes/*.yaml, settings.py
prompts/    agente_v1.md, brief_v1.md, guion_v1.md, boletin_v1.md
schemas/    modelos Pydantic (validación y JSON Schema para el LLM)
app/        streamlit_app.py + pages/ (7 vistas)
data/       raw/, reports/, out/, manifest.json, faro.db
tests/      test_smoke.py, test_t01..t10.py, test_verifier.py, test_e2e.py, test_ui_actions.py, test_banca.py
docs/       bitacora.md, decisiones.md, catalogo.md
```

## Limitaciones conocidas

- El seed es un corpus **sintético de demostración**; los volúmenes reales dependen de la recolección.
- `sentence-transformers` y `spacy` son opcionales (`uv sync --extra ml`); sin ellos, embeddings por
  hashing de n-gramas y entidades por regex (determinístico, sin red).
- El agente degrada a un enrutador determinístico si no hay LLM/red; la pasarela cae a **extractivo**.
- No se redacta sobre el cuerpo completo de artículos; solo titular/metadatos/resumen publicado (D-07).
