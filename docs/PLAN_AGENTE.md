# FARO — Plan de trabajo para el agente (desde el commit `e007791`)

Instrucciones autocontenidas para que un agente de código lleve FARO a cumplir el reto TVN Media.
El agente trabaja en `/Users/andresvega/hackathon/tvn/`. Contexto adicional (no obligatorio):
`docs/CORRECCIONES.md` (auditorías), `PLAN_DESARROLLO.md` (hitos originales) y el PDF del reto.

**Estado de partida, verificado el 2026-10-07 11:40:** las pruebas pasan y ruff está limpio en Python 3.11, pero
- `data/raw/*.jsonl` contiene **851 registros sintéticos versionados en git** (URLs inventadas en dominios reales);
- la recolección real nunca se ejecutó y tiene tres fallas que la dejarían incompleta;
- no hay series oficiales (INEC, ACP, SBP);
- el paquete editorial, el boletín y las fichas no usan el LLM;
- las acciones del agente no se aplican en la interfaz;
- `make eval` calcula la cobertura de citas sobre una lista vacía y faltan 6 métricas;
- `data/labels/` está vacío, no existe el benchmark y Notion solo tiene títulos.

---

## 1. Reglas que el agente no puede romper

1. **Nunca inventar datos.** Ninguna noticia, URL, fecha, cifra o serie puede generarse por código y presentarse
   como real. Si algo no se puede obtener, se deja faltante y se documenta.
2. **Lo sintético vive solo en `tests/`**, con dominios `*.example.invalid` y `"sintetico": true`.
3. **Respetar `robots.txt`** y las pausas por dominio. No usar modo sigiloso contra un sitio que lo prohíbe.
   No guardar el cuerpo completo de artículos.
4. **Ninguna clave** en código, logs, caché, pruebas, commits ni capturas.
5. **Un commit por tarea**, con el código de la tarea en el mensaje (`M1.2: GDELT con pausa y reintentos`).
6. **`make check` en verde** antes de cada commit.
7. **Bitácora:** cada hito cerrado agrega una fila en `docs/bitacora.md` con la hora **del commit**
   (`git log -1 --date=format:'%Y-%m-%d %H:%M' --pretty=%ad`), qué se hizo, qué falló y qué se decidió.
8. **Si la red está bloqueada** (403, 429 persistente, sin DNS), detenerse y reportar. Nunca simular respuestas.
9. **Si una compuerta falla dos veces seguidas**, detenerse, reportar con evidencia y esperar instrucciones.
10. **Pausas humanas:** las tareas marcadas 🧑 las hace Andrés o su compañero. El agente prepara todo, se detiene
    y explica exactamente qué tiene que hacer la persona.

### Formato de reporte al cerrar cada hito

```
## Hito Mx — <nombre> · <CERRADO | FALLIDO | ESPERANDO HUMANO>
Commits: <hash> <mensaje> (uno por línea)
Compuerta:
  - [x] <criterio> → <evidencia: salida del comando, número, ruta del archivo>
  - [ ] <criterio> → <por qué no se cumple>
Señales rojas observadas: <ninguna | lista>
Siguiente paso: <hito siguiente | qué necesita el humano>
```

---

## 2. Mapa de hitos

| Hito | Nombre | Depende de | Quién | Tiempo |
| --- | --- | --- | --- | --- |
| M0 | Línea base | — | Agente | 10 min |
| M1 | Recolector robusto | M0 | Agente | 2–3 h |
| M2 | Snapshot real congelado | M1 + 🧑 | Agente + humano | 1,5–2 h (incluye la recolección) |
| M3 | LLM en la redacción | M0 | Agente | 2 h |
| M4 | Interfaz agéntica | M0 | Agente | 2–3 h |
| M5 | Evaluación completa | M2, M4 + 🧑 | Agente + humano | 3 h (incluye etiquetado) |
| M6 | Casos reales de la demo | M2 | Agente | 1 h |
| M7 | Entrega: Docker, Notion y documentos | M5, M6 + 🧑 | Agente + humano | 2–3 h |
| M8 | Cierre y ensayo | Todos | Agente + humano | 1 h |

**Orden de ejecución recomendado para un solo agente:**
M0 → M1 → M2 (hasta la pausa humana) → **mientras el humano recolecta:** M3 → M4 → M5 (solo código) →
M2 (validación del snapshot) → M6 → M5 (etiquetado y corridas) → M7 → M8.

**Ruta crítica:** M1 → M2. Sin snapshot real no hay benchmark, ni etiquetas, ni casos de demo válidos.

---

## M0 · Línea base (10 min)

Tareas:
1. `git switch -c fix/plan-agente` desde `e007791` (o desde `main` si ya incluye ese commit).
2. `make setup && make check` y guardar la salida.
3. Confirmar que existen los archivos que se van a tocar: `faro/scrape/{collect,apis,sitemap,html,rss,politeness,oficiales}.py`,
   `faro/agent/{loop,loop_llm,tool_specs}.py`, `faro/llm/{gateway,providers,extractive}.py`, `faro/lenses/{editorial,banca}.py`,
   `faro/export.py`, `faro/eval/{benchmark,metrics}.py`, `faro/cli.py`, `faro/review/notion_sync.py`,
   `app/streamlit_app.py`, `app/views/*.py`, `config/{settings.py,fuentes.yaml}`, `docker-entrypoint.sh`, `Dockerfile`.

**Compuerta M0**

| Criterio | Evidencia esperada |
| --- | --- |
| Pruebas | `make check` → todas en verde, ruff sin errores |
| Python | `uv run python -V` → 3.11.x |

🔴 **Señal roja:** pruebas rotas antes de empezar → reportar y no continuar.

---

## M1 · Recolector robusto (2–3 h)

Objetivo: que `make data` pueda traer datos reales completos en menos de 90 minutos, sin fallar en silencio.

### M1.1 · Contacto real en el User-Agent
- `config/settings.py`: `FARO_CONTACTO = _env("FARO_CONTACTO")`; construir `USER_AGENT` con ese valor. Quitar
  `equipo-faro@example.com`.
- `faro/cli.py::_cmd_data`: si `FARO_CONTACTO` está vacío, salir con `"Define FARO_CONTACTO en .env (correo real del equipo)"`.
- `.env.example`: agregar `FARO_CONTACTO=`.

### M1.2 · GDELT con pausa, reintentos y errores visibles
- `faro/scrape/apis.py::gdelt(query, inicio, fin, maxrec=250, client=None) -> tuple[list[dict], str | None]`:
  - usar `politeness.PoliteClient` con pausa mínima de **6 s** para `api.gdeltproject.org`;
  - reintentar 429 y 5xx 3 veces con espera de 10, 20 y 40 s;
  - devolver `(filas, None)` si todo va bien, o `([], "HTTP 429 tras 3 intentos")` si falla. Nunca `[]` mudo.
- `faro/scrape/collect.py::_recolectar_noticias`: mover el `try/except` **dentro** del bucle de meses y consultas;
  registrar por consulta en `reporte["gdelt"]["detalle"]`: `{mes, query, ok, error}`.
- Consultas por mes (12 meses de la ventana):
  1. `domain:tvn-2.com`
  2. `sourcecountry:PM` + palabras clave de cada tema de `config/keywords.yaml`, una consulta por tema
     (por ejemplo `sourcecountry:PM (canal OR portuario OR contenedores)`), con un máximo de 3 palabras por tema.
- Prueba nueva `tests/test_scrape_gdelt.py` (respuestas simuladas con `httpx.MockTransport`):
  (a) 429 y luego 200 → devuelve filas; (b) 429 permanente → error en el reporte; (c) un mes que falla no corta
  los demás.

### M1.3 · Normalizar el medio y contar TVN bien
- `config/fuentes.yaml`: agregar a cada medio `dominios: [...]` (por ejemplo `["tvn-2.com", "www.tvn-2.com"]`).
- Nuevo `faro/scrape/medios.py::normalizar_medio(dominio: str) -> tuple[str, str] | None` → `(fuente_id, nombre)`.
- Aplicarlo en `apis.gdelt` y en `collect` antes de deduplicar. Si el dominio no es de un medio del catálogo,
  `fuente_id="gdelt"` y `medio=<dominio>`.
- Agregar el campo `via` (`rss | sitemap | html | gdelt`) a cada registro y a `schemas.RegistroNoticia`.
- `faro/pipeline.py`: contar TVN con `WHERE fuente_id='tvn'` (hoy es `medio='TVN'`).
- Prueba: un registro GDELT de `www.tvn-2.com` queda con `fuente_id="tvn"`, `medio="TVN Panamá"`, `via="gdelt"`.

### M1.4 · Sitemaps acotados
- `config/fuentes.yaml`: por medio, `max_articulos: 300` y `max_subsitemaps: 24`.
- `faro/scrape/sitemap.py` / `collect.py`:
  - descartar sub-sitemaps cuyo `<lastmod>` esté fuera de la ventana **antes** de abrirlos;
  - descartar URLs fuera de la ventana antes de pedir el artículo;
  - si la entrada trae `<news:title>` y `<news:publication_date>`, crear el registro sin abrir la página
    (`alcance_texto="titular"`, `via="sitemap"`);
  - si se supera `max_articulos`, muestrear de manera uniforme por mes;
  - reportar `omitidas_por_limite` y `omitidas_fuera_de_ventana` por fuente.
- Prueba con un sitemap de ejemplo (fixture local) de 2.000 URLs en 24 meses → se piden ≤ 300 artículos, todos en
  la ventana y repartidos por mes.

### M1.5 · Modo de prueba rápida
- `faro/cli.py data`: opciones `--fuentes tvn,telemetro` y `--meses 2025-10` para recolectar un subconjunto
  (escribir en `FARO_DATA_DIR` temporal si se pasa `--prueba`).
- `make data-smoke` → `faro.cli data --prueba --fuentes tvn --meses 2025-10`.

**Compuerta M1**

| Criterio | Evidencia esperada |
| --- | --- |
| Pruebas nuevas | `pytest tests/test_scrape_gdelt.py tests/test_scrape_sitemap.py tests/test_medios.py` en verde |
| Suite completa | `make check` en verde |
| Humo con red real | `make data-smoke` (en la Mac de Andrés si el agente no tiene red) produce `recoleccion_<ts>.json` con TVN `ok > 0` y sin errores mudos |
| Tiempo estimado | El reporte del humo muestra tiempo y conteos; la extrapolación a 12 meses y todas las fuentes da < 90 min |

🟢 **Va bien si:** el humo trae noticias de TVN con `fecha_publicacion` o `fecha_deteccion` en octubre de 2025 y
URLs que abren en el navegador.
🔴 **Señal roja:** 0 resultados en el humo; muchos `robots: false` en medios clave; tiempo extrapolado > 3 h.
→ Reportar el `recoleccion_<ts>.json` y detenerse.

---

## M2 · Snapshot real congelado (1,5–2 h, con pausa humana)

### M2.1 · Retirar el snapshot sintético (agente)
```bash
git rm data/raw/noticias.jsonl data/raw/series.jsonl data/raw/indicadores.jsonl data/raw/sismos.jsonl
rm -f data/faro.db data/vectores.npy data/vectores_idx.json data/manifest.json \
      data/reports/calidad_v1.json data/reports/ranking_v1.json data/reports/nlp.json \
      data/reports/metrics_*.json data/out/fichas.jsonl
```
Commit: `M2.1: retirar snapshot sintético del paquete de entrega`.

### M2.2 · Barreras contra datos sintéticos (agente)
- `faro/cli.py::_cmd_build`: si algún `data/raw/*.jsonl` contiene `"sintetico": true` y no está
  `FARO_PERMITIR_SINTETICO=1`, terminar con error claro (hoy se construiría una base vacía en silencio).
- `docker-entrypoint.sh`: misma comprobación con `grep -q '"sintetico": true'` → `exit 1`.
- `faro/scrape/oficiales.py::_leer_manual`: validar cada fila: `periodo` con formato `AAAA-MM` dentro de la
  ventana; `valor` numérico; `url` de dominio oficial (`inec.gob.pa`, `pancanal.com`, `superbancos.gob.pa`);
  `pagina` obligatoria si la URL termina en `.pdf`. Filas inválidas → cuarentena con motivo.
- Crear las plantillas vacías `data/raw/manual/{inec,acp,sbp}.csv` con el encabezado
  `serie,periodo,valor,unidad,url,pagina,transcrito_por,fecha` y un `data/raw/manual/LEEME.md` con instrucciones.

### M2.3 · 🧑 Pausa humana: series oficiales y recolección
El agente se detiene y pide a Andrés:
1. Poner `FARO_CONTACTO=<correo real>` en `.env`.
2. Transcribir a `data/raw/manual/` las series oficiales de **oct-2025 a sep-2026** (solo meses publicados):
   - INEC: 2–3 series mensuales (por ejemplo IMAE, IPC, entrada de visitantes);
   - ACP: tránsitos y toneladas por mes;
   - SBP: 4–5 series agregadas del boletín mensual.
   Cada fila con la URL exacta del archivo oficial y la página si es PDF.
3. Correr en su Mac: `make check-sources`, luego `make data` (30–90 min).

### M2.4 · Construir, congelar y validar (agente)
```bash
make build && make freeze && make verify-snapshot
```
Luego generar `data/reports/muestra_urls.csv` con 20 URLs al azar (medio, título, fecha, URL) para la revisión
humana.

### M2.5 · 🧑 Revisión humana
Abrir las 20 URLs y comparar 3 valores del Banco Mundial con data.worldbank.org. Anotar el resultado en la
bitácora.

### M2.6 · Versionar (agente)
Commit de `data/raw/*.jsonl`, `data/raw/manual/*.csv`, `data/raw/http/index.jsonl`, `data/manifest.json`,
`data/reports/recoleccion_<ts>.json` y `data/reports/calidad_v1.json`. Los `.gz` de evidencia van comprimidos en
`snapshot-v1-http.tar.gz` como asset de un release (`gh release create snapshot-v1 …`), con su SHA-256 anotado
en el manifest.

**Compuerta M2**

| Criterio | Umbral | Comando |
| --- | --- | --- |
| Cero sintéticos | 0 en todos los archivos | `grep -c '"sintetico": true' data/raw/*.jsonl` |
| Volumen | ≥ 1.000 noticias (mínimo aceptable 300) | `calidad_v1.json` |
| TVN | ≥ 20 | `SELECT COUNT(*) FROM noticia WHERE fuente_id='tvn'` |
| Medios | ≥ 5 distintos | `calidad_v1.json` |
| Ventana | 0 fuera de [2025-10-02, 2026-10-01) | `calidad_v1.json` |
| Series oficiales | ≥ 3 series con URL oficial | `SELECT fuente_id, serie, COUNT(*) FROM serie_oficial GROUP BY 1,2` |
| Banco Mundial | Cuadrícula 6×6×15 con nulos conservados; 3 valores verificados por humano | Bitácora |
| Integridad | OK en un clon nuevo | `git clone . /tmp/c && cd /tmp/c && make verify-snapshot` |
| Barrera | `make build` con un archivo sintético copiado a `data/raw` falla con mensaje claro | prueba manual o test |

🟢 **Va bien si:** el reporte de recolección muestra todas las fuentes con `ok > 0` o con la razón exacta.
🔴 **Señal roja:** < 300 noticias o < 20 de TVN → revisar el detalle de GDELT y los sitemaps; si persiste, reportar
y proponer fuentes adicionales (no rellenar con nada inventado).

---

## M3 · El LLM redacta el paquete, el boletín y las fichas (2 h)

Hoy `app/views/paquete.py`, `faro/lenses/editorial.py`, `faro/lenses/banca.py` y `faro/export.py` llaman solo a
`extractive.generar_*`.

Tareas:
1. `faro/lenses/editorial.py::generar_paquete(evento, conn, llm_cfg=None) -> dict`:
   - armar la evidencia: noticias del cluster (con `evidencia_id`, medio, fecha, título, resumen y
     `alcance_texto`) + contexto oficial enlazado;
   - mensajes: sistema = `prompts/brief_v1.md` + `prompts/guion_v1.md` + reglas (solo afirmar lo que está en
     `<datos>`, cada afirmación con `evidencia_id`, distinguir hecho, declaración, inferencia e hipótesis);
     usuario = la evidencia envuelta con `shield.delimitar_como_dato`;
   - `gateway.generate(mensajes, esquema=PaqueteEditorial, plantilla=extractive.generar_editorial, plantilla_args=…, **llm_cfg)`;
   - `verifier.verificar_ficha` sobre las afirmaciones; eliminar las que fallen y guardar el motivo.
2. Límites en código: brief ≤ 250 palabras; copy ≤ 80; guion entre 104 y 138 palabras (45–60 s). Si se excede:
   1 reintento pidiendo recorte; si sigue, recortar por oraciones y marcar `recortado: true`.
3. Etiqueta "basado únicamente en titular/metadatos" agregada por código si todas las evidencias tienen
   `alcance_texto` en (`titular`, `metadatos`).
4. `faro/lenses/banca.py::generar_boletin(evento, conn, llm_cfg=None)`: igual con `Boletin`,
   `prompts/boletin_v1.md` y las frases prohibidas del lente.
5. `faro/export.py::generar_fichas(conn, lente, n, llm_cfg=None)`: usar estas funciones; guardar en `ficha`:
   `proveedor`, `modelo`, `prompt_version`, `tokens_in`, `tokens_out`, `costo_usd`, `latencia_ms`, `desde_cache`.
6. `app/views/paquete.py`: pasar `st.session_state.get("llm")`; mostrar qué proveedor generó el texto, las
   afirmaciones eliminadas por el verificador y si hubo recorte.
7. Pruebas `tests/test_generacion_llm.py` con `providers.call_litellm` simulado:
   (a) brief de 400 palabras → recortado y marcado; (b) cita a un `evidencia_id` inexistente → eliminada;
   (c) cifra que no está en la evidencia → eliminada; (d) sin proveedor → plantilla con `proveedor="extractivo"`;
   (e) boletín con "recomendamos comprar" → frase bloqueada.

**Compuerta M3**

| Criterio | Evidencia |
| --- | --- |
| Pruebas nuevas | 5/5 en verde |
| Sin proveedor | Vista Paquete funciona igual que antes (plantilla) |
| Con proveedor simulado | `ficha.proveedor ≠ extractivo` y tokens > 0 en la base |
| T09 | `pytest tests/test_t09.py` sigue en verde |

🔴 **Señal roja:** el verificador elimina todas las afirmaciones en más de la mitad de los casos simulados →
revisar cómo se pasa la evidencia al verificador (el campo citado debe contener la afirmación).

---

## M4 · Interfaz agéntica: acciones, contexto, plan fijo y comparador (2–3 h)

### M4.1 · Aplicar las acciones del agente
- Nuevo `app/acciones.py::aplicar(acciones: list[dict]) -> list[str]` que devuelve una línea legible por acción:
  - `filtrar_bandeja` → `st.session_state["filtros_bandeja"]`; la Bandeja lee esos filtros y los muestra como
    chips con botón para quitarlos;
  - `abrir_ficha` → `st.session_state["evento_abierto"] = id` y cambia a la vista Ficha;
  - `ir_a` → `st.session_state["vista"] = <vista>` y `st.rerun()` (la app usa un `st.radio` con `key="vista"`;
    si no tiene `key`, agregarlo);
  - `resaltar_en_grafo` → `st.session_state["grafo_resaltar"] = ids` (el Grafo los destaca);
  - `mostrar_evidencia` → `st.session_state["evidencia_abierta"] = evidencia_id` (panel con el dato exacto).
- `app/views/agente.py`: después de la respuesta, `aplicar(r["acciones"])` y mostrar las líneas bajo el mensaje.

### M4.2 · Contexto de pantalla real
- Contexto enviado: `{"vista": st.session_state["vista"], "evento_abierto": …, "filtros": …, "lente": …}`.
- Mostrar el chat del agente en todas las vistas (panel en la barra lateral o `st.popover`), para que "¿por qué
  tiene prioridad alta?" funcione con una ficha abierta.
- Prueba: con `evento_abierto="ev-x"`, el mensaje de sistema que arma `loop_llm._system_prompt` contiene `ev-x`.

### M4.3 · Capacidades y plan fijo
- Barra lateral: botón **Probar conexión** que llama `gateway.detectar_capacidades` y guarda el resultado en
  `st.session_state["llm"]["capacidades"]`; mostrar los indicadores JSON, herramientas y precio.
- `faro/agent/loop.py::consultar`: si `capacidades["herramientas"]` es `False`, ejecutar **plan fijo**:
  `ranking` o `buscar_noticias` según la pregunta → `abrir_evento` del primer resultado →
  `consultar_serie`/`consultar_indicador` según el tema → una sola llamada al LLM con todos los `<datos>` y el
  esquema `RespuestaAgente` → verificador → canario.
- `meta.modo` ∈ {`plan_libre`, `plan_fijo`, `determinista`}, visible en la interfaz.
- Prueba con LLM simulado que no devuelve `tool_calls` → la traza muestra el plan fijo y la respuesta pasa por el
  verificador.

### M4.4 · Comparador que compara
- `app/views/comparador.py`: elegir hasta 5 preguntas de `docs/guion_demo.md` → botón **Comparar** → correr cada
  una con el proveedor del usuario y con Ollama (y opcionalmente el determinista) → tabla lado a lado:
  afirmaciones verificadas/totales, abstención, latencia, tokens y costo. Guardar
  `data/reports/comparador_<ts>.json`.

**Compuerta M4**

| Criterio | Evidencia |
| --- | --- |
| Pruebas | `tests/test_ui_actions.py` ampliado + pruebas de contexto y plan fijo en verde |
| Acciones visibles (manual, con LLM simulado o real) | "Muéstrame el top 10 de logística" filtra la Bandeja y cambia de vista |
| Contexto | Con una ficha abierta, "¿por qué tiene prioridad alta?" responde sobre ese evento |
| Seguridad | Acción `borrar_base` descartada y en la traza; hash de `faro.db` igual antes y después |
| Comparador | Un `comparador_<ts>.json` con ≥ 10 filas |

---

## M5 · Evaluación completa (3 h, con pausas humanas)

### M5.1 · Código de evaluación (agente, puede hacerse antes de M2)
En `faro/cli.py::_cmd_eval`, guardar por caso: `afirmaciones` (con `evidencia_id` y si pasó el verificador),
`acciones`, `traza`, `meta` y `latencia_ms` medida con `time.perf_counter()`. **Hoy no se copian las afirmaciones,
y la cobertura se calcula sobre una lista vacía.**

En `faro/eval/metrics.py`:
- `cobertura_citas`: si no hay afirmaciones, reportar `0/0 · sin datos`, nunca 100%.
- Nuevas funciones: `contradiccion(casos)`, `inyeccion(casos)` (sin canario y sin seguir la instrucción),
  `precision_at_5(top_faro, data/labels/editor_top5.json)` (o "exploratorio" si no existe el archivo),
  `latencia(casos)` (mediana y p95), `costo(casos)` (tokens y USD por proveedor).
- Reporte `.md`: una fila por métrica con `n/N`, porcentaje, meta del reto y lista de IDs fallidos.

Nuevo `make sample-claims` → `data/labels/revision_pendiente.csv` con 30 afirmaciones al azar de la última corrida.
Las adversariales usan documentos de `tests/fixtures/adversariales/`, cargados solo durante `make eval`.

### M5.2 · 🧑 Etiquetado (después de M2)
1. `make labels-sample` (agente) → 🧑 completar `temas.csv` (150) y `pares.csv` (50); anotar quién etiquetó y
   cuánto tardó.
2. `make eval-nlp` (agente).

### M5.3 · 🧑 Benchmark (después de M2)
- Agente: borrador de `data/benchmark.jsonl` con 40 preguntas sobre el snapshot real (20 sustentadas,
  7 contradicción o ambigüedad, 7 sin respuesta, 6 adversariales), con `evidencia_esperada` real. 🧑 Andrés las
  revisa y corrige.
- 🧑 El compañero escribe las 20 reservadas en `data/benchmark_reservado.jsonl` (en `.gitignore`) sin mostrarlas.

### M5.4 · Corridas
- Corrida 1: `make eval SPLIT=dev MODO=usuario` y `MODO=local` → corregir fallos.
- `make sample-claims` → 🧑 marcar `sustentada: si/no` → `revision_afirmaciones.csv`.
- Corrida 2: `dev` y `reservado` con el proveedor del usuario.

**Compuerta M5**

| Métrica | Meta |
| --- | --- |
| Etiquetas | `nlp.json`: `n_etiquetas = 150`, `metodo_etiquetado`, `embedder = intfloat/multilingual-e5-small` |
| Benchmark | 40 dev + 20 reservadas |
| Cobertura de citas | 100% (sobre afirmaciones reales, no 0/0) |
| Validez de sustento | ≥ 90% en ≥ 30 afirmaciones revisadas |
| Abstención correcta | ≥ 80% |
| Inyección | 100% |
| Latencia | Mediana ≤ 15 s (p95 reportado) |
| Costo | Tokens y USD por consulta reportados |
| Reportes | Dos corridas guardadas, con la mejora entre ambas |

🔴 **Señal roja:** abstención correcta < 60% o inyección < 100% en la corrida 1 → revisar prompt y verificador
antes de la corrida 2; anotar la causa en la bitácora (esto es la "prueba fallida y su corrección" que pide el
jurado).

---

## M6 · Casos reales de la demo (1 h, después de M2)

1. Buscar en el snapshot real y anotar en `docs/guion_demo.md` el `evento_id` de:
   - agencia replicada (≥ 3 medios, 1 procedencia) → CU-03;
   - cifras distintas entre medios → CU-04/T05;
   - evento económico con serie oficial enlazada → CU-02;
   - una pregunta sin respuesta en el corpus → abstención.
2. Revisar `faro/events/contradict.py` con cifras reales (B/., US$, %, millones, buques; tolerancia relativa del 5%).
3. Si no hay ninguna contradicción real: crear **un** caso controlado con `sintetico: true`, cargado solo en modo
   demo (`FARO_CASO_DEMO=1`) y mostrado con el distintivo "CASO SINTÉTICO DE PRUEBA".
4. `make demo-cache` con las preguntas del guion.

**Compuerta M6:** `make build` reporta `contradicciones ≥ 1` y las 4 filas del guion tienen ID real; las 7
preguntas del guion responden en la interfaz.

---

## M7 · Entrega: Docker, Notion y documentos (2–3 h)

### M7.1 · Instalación reproducible (torch para CPU en Linux)
- `pyproject.toml`: índice `pytorch-cpu` (`https://download.pytorch.org/whl/cpu`, `explicit = true`) y
  `[tool.uv.sources] torch = [{ index = "pytorch-cpu", marker = "sys_platform == 'linux'" }]`; agregar `torch`
  como dependencia explícita; fijar el modelo `es_core_news_md` como dependencia directa (wheel de
  `explosion/spacy-models` con la versión compatible); `uv lock`.
- `Dockerfile`: precargar e5-small y spaCy en la imagen (`HF_HOME=/app/data/cache/hf`) y arrancar con
  `HF_HUB_OFFLINE=1`.
- Compuerta: `docker build` sin paquetes `nvidia-*` en el log; el contenedor arranca con la red cortada y muestra
  datos reales.

### M7.2 · Notion con contenido real
- `faro/review/notion_sync.py`: crear bases de datos bajo la página raíz y llenarlas (idempotente por clave):
  - **Tareas** (≥ 8): título, estado, responsable, inicio, fin, hito — desde este plan y `PLAN_DESARROLLO.md`;
  - **Decisiones**: desde `docs/decisiones.md`;
  - **Catálogo**: una fila por fuente desde `fuentes.yaml` + `manifest.json` + `recoleccion_<ts>.json`;
  - **Fichas** (≥ 5, una con evidencia insuficiente): desde `data/out/fichas.jsonl`;
  - **Pruebas**: T01–T10 desde `data/reports/junit.xml` + filas de las métricas.
- Páginas de texto con contenido real: Inicio del reto, Diseño de solución (arquitectura, modelo de datos,
  prompts y versiones), Riesgos y ética. La página Presentación al jurado la arma 🧑.
- 🧑 Crear la integración, compartir la página raíz y luego el espacio con el jurado; probar el acceso desde una
  cuenta externa.

### M7.3 · Documentos fieles
- `docs/bitacora.md`: corregir las horas de las filas del 2026-10-07 con `git log` (commits a las 10:07, 10:29 y
  10:41); quitar "e5-small y spaCy activos y verificados" hasta pegar la salida de `Embedder().nombre`.
- `data/DICCIONARIO.md` y D-22: referirse al snapshot real de M2 (fecha y commit).
- `README.md`: sección de modelos con versiones, costo medido (de M5) y limitaciones reales.
- `docs/catalogo.md`: generado desde `fuentes_check.json` + `recoleccion_<ts>.json`.

**Compuerta M7**

| Criterio | Evidencia |
| --- | --- |
| Docker | Build sin CUDA; arranque offline con datos reales |
| Notion | 8 páginas + 5 bases con contenido; acceso del jurado probado |
| Documentos | Bitácora con horas iguales a los commits; ninguna afirmación sin evidencia |

---

## M8 · Cierre y ensayo (1 h)

1. `git clone` limpio en otra carpeta → `make demo-offline` con el **wifi apagado**.
2. Recorrer el guion completo (7 preguntas) + las 4 preguntas dinámicas del jurado:
   - "¿De dónde viene esta cifra y de qué año es?"
   - "Si cinco medios replican la misma agencia, ¿cuántas fuentes independientes cuentas?"
   - "¿Qué pasa si no hay evidencia o una fuente intenta cambiar tus instrucciones?"
   - "Muéstrame en Notion una decisión, una prueba fallida y su corrección."
3. 🧑 Grabar un video de respaldo de 2–3 minutos y embeberlo en Notion.
4. Marcar el checklist de admisión.

### Checklist de admisión (todo debe quedar en ✅)

- [ ] 0 registros sintéticos en `data/raw/`; ≥ 20 de TVN; ≥ 5 medios; todo en la ventana
- [ ] Snapshot, manifest, diccionario y condiciones versionados; `make verify-snapshot` OK en un clon limpio
- [ ] e5-small y spaCy activos (nombre del modelo en los reportes)
- [ ] Baseline vs. IA medido con 150 etiquetas humanas
- [ ] Agente con el LLM del usuario (plan libre o fijo) + respaldos local y determinista
- [ ] Paquete, boletín y fichas generados por el LLM y filtrados por el verificador
- [ ] Modelo, versión, prompts, parámetros y costo documentados
- [ ] T01–T10 en verde y exportadas a Notion
- [ ] Benchmark 40 + 20 con dos corridas; métricas `n/N` con fallos listados
- [ ] Notion accesible al jurado: ≥ 8 tareas, ≥ 3 decisiones con fecha, catálogo, ≥ 5 fichas (una insuficiente), matriz, métricas y pitch
- [ ] `make demo-offline` ensayado dos veces con el wifi apagado
- [ ] `git grep -nE "sk-[A-Za-z0-9]{10,}"` vacío; `.env` fuera del repo
