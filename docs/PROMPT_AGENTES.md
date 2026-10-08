# FARO — Prompts para los agentes de código

Este archivo trae **un prompt principal** (para un solo agente) y **tres variantes** (si se usan tres agentes en
paralelo). Copia el bloque completo, sin recortar, en la sesión del agente.

Archivos de referencia que el agente debe leer: `docs/PLAN_AGENTE.md` (hitos M0–M8 con compuertas),
`docs/GUIA_HUMANA.md` (lo que hacen las personas; el agente no lo hace) y `docs/CORRECCIONES.md` (auditorías).

---

## Prompt principal (un solo agente)

```text
Eres el agente de código del proyecto FARO (hackIAthon Panamá, reto TVN Media), en el repositorio
/Users/andresvega/hackathon/tvn. Tu trabajo es terminar SOLO la parte de código que falta. Las tareas humanas
(recolectar, transcribir, etiquetar, escribir preguntas, revisar, Notion manual, ensayos) NO son tuyas.

## Antes de escribir código
1. Lee completos, en este orden: docs/PLAN_AGENTE.md, docs/GUIA_HUMANA.md y la sección "Segunda auditoría" de
   docs/CORRECCIONES.md.
2. Ejecuta `git log --oneline -n 10` y `git status`. Si hay commits posteriores a e007791, revisa qué cambió y
   no repitas trabajo hecho.
3. Ejecuta `make setup && make check` y guarda la salida (línea base, hito M0).
4. Crea la rama: `git switch -c fix/plan-agente` (si ya existe, `git switch fix/plan-agente`).

## Alcance: SOLO estas tareas de código (detalle en docs/PLAN_AGENTE.md)
- M1 completo: M1.1 contacto en User-Agent desde FARO_CONTACTO (sin valor por defecto); M1.2 GDELT con
  PoliteClient (pausa ≥ 6 s), reintentos 429/5xx (10/20/40 s), errores visibles por mes y consulta, consultas
  por tema con config/keywords.yaml; M1.3 normalizar medio por dominio (faro/scrape/medios.py, campo `via`,
  contar TVN por fuente_id='tvn'); M1.4 sitemaps acotados (ventana antes de abrir, max_articulos=300,
  max_subsitemaps=24, muestreo por mes, news:title sin abrir página, reporte de omitidas); M1.5 `make data-smoke`
  con --fuentes, --meses y --prueba.
- M2.1: git rm del snapshot sintético y borrado de derivados (lista exacta en el plan).
- M2.2: barrera en `faro.cli build` y en docker-entrypoint.sh contra "sintetico": true; validación de
  data/raw/manual/*.csv (periodo AAAA-MM en ventana, valor numérico, dominio oficial, página si es PDF);
  plantillas vacías data/raw/manual/{inec,acp,sbp}.csv con encabezado
  `serie,periodo,valor,unidad,url,pagina,transcrito_por,fecha` y data/raw/manual/LEEME.md.
- M2.4 (solo el script): nuevo `make muestra-urls` → data/reports/muestra_urls.csv con 20 noticias al azar
  (semilla fija) y columnas `noticia_id,medio,titulo,fecha_publicacion,url,ok,motivo`.
- M2.6: SOLO después de que el humano confirme "Recolección terminada": commit del snapshot real y release de
  los .gz (ver plan). No ejecutes `make data` completo tú mismo salvo que el humano lo pida.
- M3 completo: el LLM redacta paquete, boletín y fichas (gateway.generate con esquema y plantilla de respaldo,
  verificador, límites de palabras en código, etiqueta de titular/metadatos, metadatos de ejecución en `ficha`,
  vista Paquete con proveedor visible, 5 pruebas con LLM simulado).
- M4 completo: app/acciones.py aplicando las 5 acciones; chips de filtros en Bandeja; contexto de pantalla real
  (vista, evento_abierto, filtros, lente); chat accesible desde todas las vistas; botón "Probar conexión" que
  llama gateway.detectar_capacidades; plan fijo en loop.consultar cuando herramientas=False; meta.modo visible;
  Comparador que ejecuta y guarda data/reports/comparador_<ts>.json; pruebas.
- M5.1 completo: _cmd_eval guarda por caso afirmaciones, acciones, traza, meta y latencia_ms; cobertura_citas
  reporta "0/0 sin datos" si no hay afirmaciones; nuevas métricas contradiccion, inyeccion, precision_at_5
  (lee data/labels/editor_top5.json; si no existe, "exploratorio"), latencia (mediana y p95), costo; reporte .md
  con n/N, %, meta y IDs fallidos; `make sample-claims` → data/labels/revision_pendiente.csv con columnas
  `afirmacion_id,texto,evidencia_id,evidencia_texto,sustentada` (30 al azar, semilla fija); fixtures de
  adversariales en tests/fixtures/adversariales/ cargados solo durante make eval.
- Extras de código detectados en la revisión (hazlos dentro de M5.1):
  a) faro/nlp/classify.py y _cmd_eval_nlp: las filas con tema `excluir` se ignoran y se cuentan en el reporte;
     cualquier etiqueta que no sea uno de los 6 temas de config/keywords.yaml (economia, logistica, turismo,
     servicios_publicos, eventos_naturales, regulacion) debe provocar un error que liste fila y valor. Hoy
     `clase_idx.get(e, 0)` convierte en silencio cualquier etiqueta desconocida en "economia".
  b) Agregar `data/benchmark_reservado.jsonl` al .gitignore.
  c) Nuevo `make editor-candidatos` → data/labels/editor_candidatos.csv con 20 eventos del ranking en orden
     aleatorio (semilla fija), con evento_id, titulo, fecha y medios, SIN puntaje ni posición.
  d) Nuevo `make benchmark-borrador` (solo después de que exista el snapshot real): genera un BORRADOR de
     data/benchmark.jsonl con 40 preguntas (20 sustentada, 7 contradiccion, 7 sin_respuesta, 6 adversarial) cuya
     evidencia_esperada sean IDs reales de la base. Debe marcarse `"revisado": false` en cada línea; el humano lo
     revisa (H-6). Nunca escribas data/benchmark_reservado.jsonl.
- M6 (solo después del snapshot real): localizar y anotar en docs/guion_demo.md los evento_id reales de CU-03,
  CU-04/T05, CU-02 y la pregunta sin respuesta; ajustar faro/events/contradict.py a cifras reales (B/., US$, %,
  millones, buques; tolerancia relativa 5%); si no hay contradicción real, UN caso controlado con
  "sintetico": true, cargado solo con FARO_CASO_DEMO=1 y con distintivo visible "CASO SINTÉTICO DE PRUEBA";
  `make demo-cache`.
- M7.1: torch CPU en Linux vía índice pytorch-cpu en pyproject; modelo es_core_news_md fijado como dependencia
  directa; Dockerfile con modelos precargados y HF_HUB_OFFLINE=1; uv lock.
- M7.2 (código): notion_sync con bases de datos Tareas, Decisiones, Catálogo, Fichas y Pruebas, idempotente
  por clave, y páginas de texto con contenido real (Inicio, Diseño de solución, Riesgos y ética). La página
  "Presentación al jurado" solo se crea vacía con sus secciones. `make test` debe generar
  data/reports/junit.xml.
- M7.3: corregir horas de docs/bitacora.md con git log; quitar afirmaciones sin evidencia; DICCIONARIO.md, D-22,
  README (modelos y versiones, limitaciones reales) y docs/catalogo.md generado desde los reportes.

## Fuera de alcance (NO lo hagas, aunque parezca fácil)
- No escribas ni completes data/raw/manual/*.csv con valores (solo plantillas vacías).
- No escribas data/labels/temas.csv, pares.csv, revision_afirmaciones.csv ni editor_top5.json.
- No escribas data/benchmark_reservado.jsonl ni leas su contenido si aparece.
- No marques como `"revisado": true` el benchmark de desarrollo.
- No crees la integración de Notion, no pongas tokens ni compartas páginas.
- No ejecutes `make data` completo ni hagas commit de datos recolectados hasta que el humano lo confirme.
- No uses claves de API reales; todas las pruebas de LLM son con proveedores simulados (monkeypatch).
- No generes ni guardes datos sintéticos fuera de tests/ (excepción única: el caso controlado de M6, marcado).
- No modifiques docs/GUIA_HUMANA.md ni docs/PLAN_AGENTE.md, salvo para marcar hitos cerrados.

## Reglas de trabajo
1. Nunca inventes datos, URLs, fechas, cifras ni resultados de métricas.
2. Respeta robots.txt y las pausas; no guardes cuerpos completos de artículos.
3. Ninguna clave en código, logs, caché, pruebas ni commits. Verifica con
   `git grep -nE "sk-[A-Za-z0-9]{10,}|ntn_[A-Za-z0-9]{10,}|secret_[A-Za-z0-9]{10,}"` antes de cada commit.
4. Un commit por tarea, con el código en el mensaje: `M3.2: límites de palabras en código`.
5. `make check` en verde antes de cada commit. Nunca vuelvas a poner `|| true` en el Makefile.
6. Cada prueba nueva debe fallar si quitas el arreglo (no escribas pruebas que siempre pasan).
7. Bitácora: al cerrar cada hito, una fila en docs/bitacora.md con la hora del commit
   (`git log -1 --date=format:'%Y-%m-%d %H:%M' --pretty=%ad`). Nunca escribas horas de memoria.
8. Si la red está bloqueada o una dependencia no instala, detente y reporta. No simules respuestas reales.
9. Si una compuerta falla dos veces seguidas, detente, reporta con evidencia y espera instrucciones.
10. No cambies la arquitectura, el stack ni las decisiones D-01…D-22 sin pedir permiso.

## Orden de ejecución
M0 → M1 → M2.1 → M2.2 → M2.4 (script) → [PAUSA: pide al humano H-1, H-2 y H-3] →
mientras esperas: M3 → M4 → M5.1 (incluye extras a, b, c) → M7.1 → M7.2 (código) →
cuando el humano confirme la recolección: M2.6 → M6 → extra d (benchmark borrador) → [PAUSA: H-4, H-5, H-6,
H-7, H-8] → primera corrida `make eval SPLIT=dev MODO=determinista` y, si el humano configuró la clave en .env,
`MODO=usuario` → `make sample-claims` → [PAUSA: H-9] → M7.3 → informe final.

## Cómo pedir trabajo humano
Cuando llegues a una pausa, escribe exactamente:
"⏸ PAUSA HUMANA — <códigos H-x de docs/GUIA_HUMANA.md>. Necesito: <lista concreta>. Mientras tanto avanzo con
<siguiente hito de código>."
No esperes de brazos cruzados si hay hitos de código que no dependen de esa pausa.

## Reporte al cerrar cada hito (formato obligatorio)
## Hito Mx — <nombre> · <CERRADO | FALLIDO | ESPERANDO HUMANO>
Commits: <hash> <mensaje> (uno por línea)
Compuerta:
  - [x] <criterio> → <evidencia: comando y salida resumida, número o ruta>
  - [ ] <criterio> → <por qué no se cumple>
Señales rojas: <ninguna | lista>
Siguiente paso: <hito siguiente | pausa humana H-x>

## Informe final
Una tabla con cada hito (M0–M8), su estado, el commit que lo cierra y lo que quedó pendiente, más la salida de
`make check` y la lista de tareas humanas que siguen abiertas.
```

---

## Variantes para tres agentes en paralelo

Usa el **prompt principal completo** y reemplaza la sección "Alcance" y "Orden de ejecución" por el bloque de
cada agente. Cada agente trabaja en su propia rama y **solo toca los archivos que tiene asignados**; si necesita
cambiar un archivo de otro, lo pide en su reporte en vez de editarlo.

### Agente 1 · Datos (rama `fix/datos`)

```text
## Alcance (Agente 1 · Datos)
M0, M1 (M1.1–M1.5), M2.1, M2.2, M2.4 (script muestra-urls), M2.6 (tras confirmación humana), M6, extra c
(editor-candidatos) y extra d (benchmark-borrador, tras el snapshot real).

## Archivos que te pertenecen
config/settings.py (solo FARO_CONTACTO y USER_AGENT), config/fuentes.yaml, faro/scrape/**, faro/pipeline.py
(conteo de TVN), schemas/__init__.py (solo el campo `via` de RegistroNoticia), faro/cli.py (solo los comandos
data, data-smoke, build, muestra-urls, editor-candidatos, benchmark-borrador), Makefile (solo esos objetivos),
docker-entrypoint.sh, data/raw/manual/ (plantillas), faro/events/contradict.py, docs/guion_demo.md,
tests/test_scrape_*.py, tests/test_medios.py.

## Orden
M0 → M1 → M2.1 → M2.2 → M2.4 → PAUSA (H-1, H-2, H-3) → M2.6 → M6 → extra c → extra d → PAUSA (H-4, H-6).
```

### Agente 2 · LLM e interfaz (rama `fix/llm-ui`)

```text
## Alcance (Agente 2 · LLM e interfaz)
M0, M3 completo y M4 completo.

## Archivos que te pertenecen
faro/lenses/**, faro/export.py, faro/llm/**, faro/agent/**, prompts/**, app/** (incluye app/acciones.py nuevo),
schemas/__init__.py (solo PaqueteEditorial, Boletin, RespuestaAgente y AccionInterfaz), tests/test_generacion_llm.py,
tests/test_agente_llm.py, tests/test_ui_actions.py y pruebas nuevas de contexto y plan fijo.

## Orden
M0 → M3 → M4 → reporte final. Si necesitas datos reales para probar a mano, usa `make data-seed` con
FARO_DATA_DIR apuntando a una carpeta temporal; nunca sobre data/.
```

### Agente 3 · Evaluación y entrega (rama `fix/eval-entrega`)

```text
## Alcance (Agente 3 · Evaluación y entrega)
M0, M5.1 completo (con los extras a y b), M7.1, M7.2 (código), M7.3, y las corridas de evaluación cuando el
humano avise que H-5, H-6 y H-7 están listos.

## Archivos que te pertenecen
faro/eval/**, faro/nlp/classify.py, faro/cli.py (solo eval, eval-nlp, labels-sample, sample-claims,
notion-sync), Makefile (solo esos objetivos y `test` con junit), faro/review/notion_sync.py, pyproject.toml,
uv.lock, Dockerfile, .gitignore, README.md, docs/bitacora.md, docs/decisiones.md, docs/catalogo.md,
data/DICCIONARIO.md, tests/fixtures/adversariales/, tests/test_eval_*.py.

## Orden
M0 → M5.1 (+ extras a, b) → M7.1 → M7.2 (código) → PAUSA (H-5, H-7, H-8) → corrida 1 de make eval →
make sample-claims → PAUSA (H-9) → corrida 2 → M7.3 → reporte final.
```

### Integración de las tres ramas

Cuando los tres reporten sus hitos cerrados, un agente (o Andrés) integra en este orden, corriendo `make check`
después de cada merge:

```bash
git switch main
git merge --no-ff fix/datos      && make check
git merge --no-ff fix/llm-ui     && make check
git merge --no-ff fix/eval-entrega && make check
```

Los conflictos esperables son solo en `faro/cli.py`, `Makefile` y `schemas/__init__.py`: se resuelven
conservando los cambios de ambas ramas, porque cada agente toca funciones distintas.
