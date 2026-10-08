# FARO — Prompts para los agentes de código

Este archivo trae **un prompt principal** (para un solo agente) y **tres variantes** (si se usan tres agentes en
paralelo). Copia el bloque completo, sin recortar, en la sesión del agente.

Archivos de referencia que el agente debe leer: `docs/PLAN_AGENTE.md` (hitos M0–M8 con compuertas),
`docs/GUIA_HUMANA.md` (lo que hacen las personas; el agente no lo hace) y `docs/CORRECCIONES.md` (auditorías).

**Versión 2026-10-07 (noche).** Incluye los cambios de alcance del día: sin contacto, Notion y pitch en
pausa, ACP fuera, series INEC y SBP ya transcritas, etiquetado asistido, set reservado fuera del repo y el
error de nombres de clase del clasificador de temas.

---

## Prompt principal (un solo agente)

```text
Eres el agente de código del proyecto FARO (hackIAthon Panamá, reto TVN Media), en el repositorio
/Users/andresvega/hackathon/tvn. Tu trabajo es terminar SOLO la parte de código que falta. Las tareas humanas
(recolectar, revisar, etiquetar, probar con clave real, ensayos) NO son tuyas.

## Antes de escribir código
1. Lee completos, en este orden: docs/PLAN_AGENTE.md, docs/GUIA_HUMANA.md y la sección "Segunda auditoría" de
   docs/CORRECCIONES.md. Después lee la sección "CAMBIOS DEL 2026-10-07" de este prompt: donde contradiga a
   PLAN_AGENTE.md, manda este prompt.
2. Ejecuta `git log --oneline -n 10` y `git status`. El último commit con código es e007791; el commit 2dacb01
   solo agrega documentos y borra a propósito el PDF del reto (no lo restaures). data/raw/manual/ aparece sin
   versionar: contiene datos reales transcritos (ver cambios, punto 3).
3. Ejecuta `make setup && make check` y guarda la salida (línea base, hito M0).
4. Crea la rama: `git switch -c fix/plan-agente` (si ya existe, `git switch fix/plan-agente`).

## CAMBIOS DEL 2026-10-07 (prevalecen sobre docs/PLAN_AGENTE.md)
1. SIN contacto (reemplaza M1.1 completo): no se implementa FARO_CONTACTO ni ninguna validación de correo.
   Lo ÚNICO que se hace es borrar el correo falso `equipo-faro@example.com` de config/settings.py, para que el
   User-Agent quede como "FARO/0.1 (copiloto de inteligencia informativa)". No agregar nada a .env.example.
2. ACP fuera de alcance: no crear data/raw/manual/acp.csv. `oficiales.acp()` puede quedarse, pero si el archivo
   no existe se registra como "no disponible" en el reporte de recolección, sin error. Quitar ACP de las
   compuertas y del catálogo como fuente obligatoria.
3. Series oficiales YA TRANSCRITAS (H-2 cerrada): data/raw/manual/inec.csv (series inec_imae, inec_imae_var,
   2025-10 a 2026-07) y data/raw/manual/sbp.csv (sbp_cbi_activo_total, sbp_cbi_depositos,
   sbp_cbi_cartera_neta, 2025-10 a 2026-08). NO las sobrescribas, no las "corrijas", no crees plantillas encima.
   - La validación de M2.2 debe aceptarlas: dominios oficiales inec.gob.pa y superbancos.gob.pa; `pagina`
     entera; `valor` numérico; `periodo` en [2025-10, 2026-09]; `transcrito_por` es texto libre.
   - Inclúyelas en el commit de M2.2 (`git add data/raw/manual/inec.csv data/raw/manual/sbp.csv`) junto con
     data/raw/manual/LEEME.md que explique columnas, fuentes y que los PDF de origen están en
     data/cache/sbp/ (ignorado por git; se pueden volver a descargar con las URL de cada fila).
   - El catálogo (docs/catalogo.md) debe listar estas 5 series con su rango real de meses.
4. Notion y pitch EN PAUSA: no trabajes M7.2 ni `make notion-sync`, ni la página del pitch. No borres el código
   existente de notion_sync. Las compuertas de M7/M8 que mencionan Notion, video o pitch no aplican por ahora.
5. Clasificador de temas: error de nombres de clase (NUEVO, prioridad alta, va en M5.1):
   - Hoy `_cmd_eval_nlp` entrena con índices de `sorted(set(etiquetas))` (incluye `excluir`) y el pipeline
     traduce las predicciones con `TEMAS` (orden de config/keywords.yaml). El modelo puede acertar y la app
     mostrar otro tema.
   - Arreglo: guardar en models/tema_lr.joblib un diccionario {"modelo": clf, "clases": [...]} y que
     faro/pipeline.py y classify.predecir usen esas clases (o entrenar con `clf.fit(X, etiquetas_str)` y usar
     `clf.classes_`). Una sola fuente de verdad para los nombres.
   - Filas con `excluir` se quitan ANTES de entrenar y de medir, y se cuentan en el reporte (`n_excluidas`).
   - Cualquier etiqueta fuera de los 6 temas (economia, logistica, turismo, servicios_publicos,
     eventos_naturales, regulacion) o `excluir` → error que liste fila y valor. Elimina `clase_idx.get(e, 0)`
     en classify.py.
   - Prueba que falle sin el arreglo: entrenar con etiquetas cuyo orden alfabético difiera del de
     keywords.yaml y comprobar que el pipeline devuelve el nombre correcto.
6. Método de etiquetado declarado, no fijo en código (NUEVO, M5.1):
   - Quitar `"metodo_etiquetado": "manual por los dos integrantes"` y `"etiquetadores": "[HUMANO]"`.
   - `eval-nlp` lee data/labels/metodo.json si existe ({"metodo": "...", "etiquetadores": [...],
     "fecha": "..."}); si no existe, escribe "no declarado" en el reporte.
   - Si existen data/labels/ciego_A.csv y ciego_C.csv (mismas filas, columna `tema`), calcular el kappa de Cohen
     y las coincidencias, y agregarlos a nlp.json como `acuerdo_entre_etiquetadores`. Si no existen, omitir.
   - Los archivos ciego_*.csv y asistido.csv los preparan Claude y los humanos; tú solo los LEES.
7. Reclasificar después de entrenar (NUEVO): el objetivo `make eval-nlp` termina ejecutando `make build`, para
   que las noticias se reclasifiquen con models/tema_lr.joblib. Verifica que el pipeline no reutilice temas
   asignados por el baseline en una corrida anterior (si `n.get("tema")` ya viene del baseline, se debe
   reclasificar). Prueba incluida.
8. Set reservado FUERA del repo (reemplaza el extra b):
   - `make eval` acepta `BENCH=<ruta>`; si se da, carga las preguntas de esa ruta en vez de
     data/benchmark.jsonl. `SPLIT=reservado` sin BENCH busca data/benchmark_reservado.jsonl.
   - Agregar `data/benchmark_reservado.jsonl` al .gitignore.
   - El reporte de una corrida reservada NO imprime preguntas ni respuestas por caso, solo métricas agregadas
     y los IDs fallidos.
   - Nunca leas, abras, listes el contenido ni copies ~/hackathon/faro-reservado/ ni
     data/benchmark_reservado.jsonl.
9. Las tareas humanas vigentes son H-3, H-4, H-5, H-6, H-8, H-9 y H-10 (opcional). H-0 y H-2 están cerradas.
   H-1, H-7, H-11 y H-12 no son humanas o están en pausa: no las pidas.

## Alcance: SOLO estas tareas de código (detalle en docs/PLAN_AGENTE.md, con los cambios de arriba)
- M1 completo: M1.1 solo borrar el correo falso del User-Agent (cambio 1, nada más); M1.2 GDELT con PoliteClient (pausa ≥ 6 s), reintentos
  429/5xx (10/20/40 s), errores visibles por mes y consulta, consultas por tema con config/keywords.yaml; M1.3
  normalizar medio por dominio (faro/scrape/medios.py, campo `via`, contar TVN por fuente_id='tvn' en
  faro/pipeline.py, hoy cuenta medio='TVN'); M1.4 sitemaps acotados (ventana antes de abrir,
  max_articulos=300, max_subsitemaps=24, muestreo por mes, news:title sin abrir página, reporte de omitidas);
  M1.5 `make data-smoke` con --fuentes, --meses y --prueba.
- M2.1: git rm del snapshot sintético y borrado de derivados (lista exacta en el plan). Hoy siguen en
  data/raw/: noticias.jsonl (203 sintéticas), indicadores.jsonl (532), series.jsonl (96), sismos.jsonl (20).
- M2.2: barrera en `faro.cli build` y en docker-entrypoint.sh contra "sintetico": true; validación de
  data/raw/manual/*.csv (cambio 3); LEEME.md; commit de inec.csv y sbp.csv.
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
  Dentro de M5.1 van también los cambios 5, 6, 7 y 8, y estos extras:
  c) Nuevo `make editor-candidatos` → data/labels/editor_candidatos.csv con 20 eventos del ranking en orden
     aleatorio (semilla fija), con evento_id, titulo, fecha y medios, SIN puntaje ni posición.
  d) Nuevo `make benchmark-borrador` (solo después de que exista el snapshot real): genera un BORRADOR de
     data/benchmark.jsonl con 40 preguntas (20 sustentada, 7 contradiccion, 7 sin_respuesta, 6 adversarial) cuya
     evidencia_esperada sean IDs reales de la base (incluye preguntas sobre las series OF:inec y OF:sbp). Debe
     marcarse `"revisado": false` en cada línea; el humano lo revisa (H-6).
- M6 (solo después del snapshot real): localizar y anotar en docs/guion_demo.md los evento_id reales de CU-03,
  CU-04/T05, CU-02 y la pregunta sin respuesta; ajustar faro/events/contradict.py a cifras reales (B/., US$, %,
  millones, buques; tolerancia relativa 5%); si no hay contradicción real, UN caso controlado con
  "sintetico": true, cargado solo con FARO_CASO_DEMO=1 y con distintivo visible "CASO SINTÉTICO DE PRUEBA";
  `make demo-cache`.
- M7.1: torch CPU en Linux vía índice pytorch-cpu en pyproject; modelo es_core_news_md fijado como dependencia
  directa; Dockerfile con modelos precargados y HF_HUB_OFFLINE=1; uv lock. `make test` debe generar
  data/reports/junit.xml.
- M7.3: corregir horas de docs/bitacora.md con git log; quitar afirmaciones sin evidencia; DICCIONARIO.md, D-22,
  README (modelos y versiones, limitaciones reales, ACP fuera, Notion en pausa) y
  docs/catalogo.md generado desde los reportes.

## Fuera de alcance (NO lo hagas, aunque parezca fácil)
- No modifiques data/raw/manual/inec.csv ni sbp.csv; no crees acp.csv ni agregues valores a ningún CSV manual.
- No escribas data/labels/temas.csv, pares.csv, ciego_A.csv, ciego_C.csv, asistido.csv, metodo.json,
  revision_afirmaciones.csv ni editor_top5.json.
- No escribas, leas ni busques el set reservado (data/benchmark_reservado.jsonl, ~/hackathon/faro-reservado/).
- No marques como `"revisado": true` el benchmark de desarrollo.
- No trabajes Notion (M7.2), el pitch, el video ni publicaciones.
- No ejecutes `make data` completo ni hagas commit de datos recolectados hasta que el humano lo confirme.
- No uses claves de API reales; todas las pruebas de LLM son con proveedores simulados (monkeypatch).
- No generes ni guardes datos sintéticos fuera de tests/ (excepción única: el caso controlado de M6, marcado).
- No restaures el PDF del reto en el repo.
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
M0 → M1 → M2.1 → M2.2 → M2.4 (script) → [PAUSA: pide al humano H-3] →
mientras esperas: M5.1 cambios 5–8 (primero, son cortos y críticos) → M3 → M4 → resto de M5.1 → M7.1 →
cuando el humano confirme la recolección: M2.6 → M6 → extra d (benchmark borrador) →
[PAUSA: H-4, H-5, H-6, H-8] → primera corrida `make eval SPLIT=dev MODO=determinista` y, si el humano configuró
la clave en .env, `MODO=usuario` → `make sample-claims` → [PAUSA: H-9] → M7.3 → informe final.

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
Una tabla con cada hito (M0–M8, marcando M7.2 como "en pausa"), su estado, el commit que lo cierra y lo que
quedó pendiente, más la salida de `make check` y la lista de tareas humanas que siguen abiertas.
```

---

## Variantes para tres agentes en paralelo

Usa el **prompt principal completo** (incluida la sección "CAMBIOS DEL 2026-10-07") y reemplaza las secciones
"Alcance" y "Orden de ejecución" por el bloque de cada agente. Cada agente trabaja en su propia rama y **solo
toca los archivos que tiene asignados**; si necesita cambiar un archivo de otro, lo pide en su reporte en vez de
editarlo.

### Agente 1 · Datos (rama `fix/datos`)

```text
## Alcance (Agente 1 · Datos)
M0, M1 (M1.1 = solo borrar el correo falso; M1.2–M1.5), M2.1, M2.2 (incluye validar y versionar inec.csv y sbp.csv, cambio 3),
M2.4 (script muestra-urls), M2.6 (tras confirmación humana), M6, extra c (editor-candidatos) y extra d
(benchmark-borrador, tras el snapshot real).

## Archivos que te pertenecen
config/settings.py (solo USER_AGENT), config/fuentes.yaml,
faro/scrape/**, faro/pipeline.py (solo el conteo de TVN), schemas/__init__.py (solo el campo `via` de
RegistroNoticia), faro/cli.py (solo los comandos data, data-smoke, build, muestra-urls, editor-candidatos,
benchmark-borrador), Makefile (solo esos objetivos), docker-entrypoint.sh, data/raw/manual/LEEME.md,
faro/events/contradict.py, docs/guion_demo.md, tests/test_scrape_*.py, tests/test_medios.py.

## Orden
M0 → M1 → M2.1 → M2.2 → M2.4 → PAUSA (H-3) → M2.6 → M6 → extra c → extra d → PAUSA (H-4, H-6).
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
M0 → M3 → M4 → PAUSA (H-8) → reporte final. Si necesitas datos para probar a mano, usa `make data-seed` con
FARO_DATA_DIR apuntando a una carpeta temporal; nunca sobre data/.
```

### Agente 3 · Evaluación y entrega (rama `fix/eval-entrega`)

```text
## Alcance (Agente 3 · Evaluación y entrega)
M0, cambios 5, 6, 7 y 8 (clasificador, método de etiquetado, reclasificar tras entrenar, set reservado fuera del
repo), M5.1 completo, M7.1, M7.3 y las corridas de evaluación cuando el humano avise que H-5 y H-6 están listos.
NO M7.2 (Notion en pausa).

## Archivos que te pertenecen
faro/eval/**, faro/nlp/classify.py, faro/pipeline.py (solo la carga y uso de models/tema_lr.joblib y la
reclasificación), faro/cli.py (solo eval, eval-nlp, labels-sample, sample-claims), Makefile (solo esos objetivos
y `test` con junit), pyproject.toml, uv.lock, Dockerfile, .gitignore, README.md, docs/bitacora.md,
docs/decisiones.md, docs/catalogo.md, data/DICCIONARIO.md, tests/fixtures/adversariales/, tests/test_eval_*.py,
tests/test_classify_*.py.

## Orden
M0 → cambios 5–8 → resto de M5.1 → M7.1 → PAUSA (H-5, H-6, H-8) → corrida 1 de make eval →
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

Los conflictos esperables son solo en `faro/cli.py`, `Makefile`, `faro/pipeline.py` y `schemas/__init__.py`: se
resuelven conservando los cambios de ambas ramas, porque cada agente toca funciones distintas.
