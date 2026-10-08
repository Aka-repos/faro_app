# FARO — Guía paso a paso de las tareas humanas

Para Andrés (A) y su compañero (C). Cada tarea dice **quién**, **cuándo** (de qué hito del agente depende),
**cuánto tarda**, **los pasos exactos** y **cómo saber que quedó bien**. Los hitos M0–M8 están en
`docs/PLAN_AGENTE.md`.

Todos los comandos se ejecutan en la Terminal de la Mac, dentro de la carpeta del proyecto:

```bash
cd ~/hackathon/tvn
```

---

## Resumen y orden

| # | Tarea | Quién | Depende de | Tiempo |
| --- | --- | --- | --- | --- |
| H-0 | Preparar la Mac (una sola vez) | A | — | 20 min |
| H-1 | Poner el correo de contacto | A | Agente terminó M1.1 | 2 min |
| H-2 | Transcribir series oficiales (INEC, ACP, SBP) | A y C | — (**empezar ya**) | 60–90 min |
| H-3 | Ejecutar la recolección real | A | Agente terminó M1 y M2.2 | 30–90 min (casi todo esperar) |
| H-4 | Revisar 20 URLs y 3 valores del Banco Mundial | A | H-3 + agente M2.4 | 20 min |
| H-5 | Etiquetar 150 titulares y 50 pares | A y C | H-3 | 60 min entre los dos |
| H-6 | Revisar el benchmark de desarrollo (40) | A | Agente M5 (borrador) | 30 min |
| H-7 | Escribir las 20 preguntas reservadas | **C** (A no las ve) | H-3 | 40 min |
| H-8 | Probar con clave real y con Ollama | A | Agente M3 y M4 | 30 min |
| H-9 | Revisar 30 afirmaciones | A y C | Primera corrida de `make eval` | 30 min |
| H-10 | Selección del editor y prueba de tiempo (opcional, suma mucho) | A con un periodista | H-3 | 45 min |
| H-11 | Notion: integración, acceso del jurado y página del pitch | A | Agente M7.2 | 60 min |
| H-12 | Ensayos, video de respaldo y publicaciones | A y C | Todo lo anterior | 60 min + 10 min diarios |

**Lo que pueden hacer hoy mismo sin esperar al agente:** H-0 y H-2.

---

## H-0 · Preparar la Mac (A, 20 min, una sola vez)

1. Verificar que `uv` esté instalado: `uv --version`. Si no aparece, `brew install uv`.
2. Instalar Ollama y el modelo local:
   ```bash
   brew install ollama
   ollama serve            # déjalo corriendo en una pestaña aparte de la Terminal
   ollama pull qwen2.5:7b-instruct
   ollama run qwen2.5:7b-instruct "Responde solo: ok"
   ```
   Debe responder `ok` en unos segundos.
3. Crear tu `.env` si no existe: `cp -n .env.example .env`. Ábrelo con `open -e .env`. **Nunca lo subas a git**
   (ya está en `.gitignore`).
4. Instalar dependencias: `make setup`. La primera vez descarga e5-small y el modelo de spaCy (~300 MB).
5. Comprobar: `make check`. Debe terminar con todas las pruebas en verde.

✅ **Quedó bien si:** `make check` termina sin errores y Ollama responde.

---

## H-1 · Correo de contacto (A, 2 min, cuando el agente cierre M1.1)

El scraping debe identificarse con un correo real del equipo.

1. Abre `.env` y agrega o completa la línea:
   ```
   FARO_CONTACTO=tu-correo-real@dominio.com
   ```
2. Guarda. No lo pongas en ningún archivo que se suba a git.

✅ **Quedó bien si:** `make data-smoke` (H-3, paso 2) ya no se queja por el contacto.

---

## H-2 · Transcribir series oficiales (A y C, 60–90 min) — empezar ya

**Por qué:** sin estas series no hay contexto oficial reciente (CU-02) ni lente bancario. El código no las puede
descargar solo; se transcriben a mano y quedan trazables. **Nunca se estima ni se completa un mes que no esté
publicado.**

**Reparto sugerido:** A hace ACP y SBP; C hace INEC.

### Qué transcribir

| Fuente | Series sugeridas (elige las que encuentres publicadas) | Meses |
| --- | --- | --- |
| INEC (`inec.gob.pa`) | 2–3 series mensuales: Índice Mensual de Actividad Económica (IMAE), Índice de Precios al Consumidor (IPC), entrada de visitantes | oct-2025 a sep-2026, solo los publicados |
| ACP (`pancanal.com`) | Tránsitos mensuales de buques y toneladas CP/SUAB | oct-2025 a sep-2026 |
| SBP (`superbancos.gob.pa`) | 4–5 cifras agregadas del boletín o informe mensual: activos del Centro Bancario, depósitos totales, cartera de crédito, etc. | oct-2025 a sep-2026 |

### Pasos

1. Entra al sitio oficial y busca la sección de estadísticas o publicaciones. Descarga el archivo (Excel o PDF)
   que contenga la serie.
2. **Copia la URL exacta del archivo descargado** (clic derecho en el enlace → "Copiar dirección del enlace").
   No la URL de la página de búsqueda: la del archivo.
3. Si el archivo es PDF, anota el **número de página** donde está el dato.
4. Crea o abre el archivo en el proyecto (el agente deja las plantillas en M2.2; si aún no existen, créalas tú):
   - `data/raw/manual/inec.csv`
   - `data/raw/manual/acp.csv`
   - `data/raw/manual/sbp.csv`
5. Escribe una fila por mes y serie, con este encabezado exacto:
   ```csv
   serie,periodo,valor,unidad,url,pagina,transcrito_por,fecha
   acp_transitos,2025-10,1012,buques por mes,https://<url exacta del archivo>,4,Andres,2026-10-07
   acp_transitos,2025-11,987,buques por mes,https://<url exacta del archivo>,4,Andres,2026-10-07
   ```
   Reglas de cada columna:
   - `serie`: nombre corto en minúsculas sin espacios, igual en todas las filas de esa serie (`inec_ipc`,
     `acp_toneladas`, `sbp_depositos`).
   - `periodo`: `AAAA-MM`, solo entre `2025-10` y `2026-09`.
   - `valor`: número con **punto decimal y sin separador de miles** (`1234.5`, no `1.234,5` ni `1,234.5`).
     Si el dato está en millones, escribe el número tal cual aparece y pon "millones de balboas" en `unidad`.
   - `unidad`: tal como lo dice la fuente (`% variación interanual`, `buques por mes`, `millones de balboas`).
   - `url`: la del archivo oficial.
   - `pagina`: número si es PDF; vacío si es Excel.
   - `transcrito_por`: tu nombre.
   - `fecha`: el día en que transcribes (`2026-10-07`).
6. Si un mes no está publicado todavía, **no escribas la fila**. Anótalo en `docs/catalogo.md` como
   "no publicado al <fecha>".
7. Guarda el archivo como CSV con codificación UTF-8 (si usas Excel: Archivo → Guardar como → **CSV UTF-8**).
8. Revisa dos filas al azar contra el archivo original antes de pasar a la siguiente serie.

✅ **Quedó bien si:** hay al menos 3 series en total entre las tres fuentes, cada fila tiene URL de dominio
oficial, y al abrir el CSV en un editor de texto ves comas como separador y los acentos se leen bien.

---

## H-3 · Ejecutar la recolección real (A, 30–90 min) — cuando el agente cierre M1 y M2.2

**Antes:** el agente debe haber reportado "Hito M1 · CERRADO" y haber hecho el commit "M2.1: retirar snapshot
sintético". Si `data/raw/noticias.jsonl` todavía existe con datos sintéticos, la recolección se detiene sola.

1. Actualiza el código: `git pull` (o cambia a la rama del agente: `git switch fix/plan-agente && git pull`).
2. Prueba rápida (2–5 min):
   ```bash
   make data-smoke
   ```
   Abre el reporte más reciente: `open data/reports/` y busca `recoleccion_<fecha>.json`. Debe tener TVN con
   `"ok"` mayor que 0. Si sale 0 o hay errores en todo, **detente** y pásale el archivo al agente.
3. Revisa qué fuentes se pueden usar:
   ```bash
   make check-sources
   ```
   Mira `data/reports/fuentes_check.json`: anota en la bitácora las que tengan `robots_ok: false` o
   `metodo_ok: false`.
4. Recolección completa, sin que la Mac se duerma:
   ```bash
   caffeinate -i make data
   ```
   Puede tardar 30–90 minutos por las pausas obligatorias entre peticiones. **No cierres la tapa.**
   Mientras corre puedes hacer H-2 o H-7.
5. Al terminar:
   ```bash
   make build
   make freeze
   make verify-snapshot     # debe decir "OK — sin diferencias"
   ```
6. Revisa `data/reports/calidad_v1.json`:
   - `noticias` ≥ 1.000 (mínimo aceptable 300)
   - `noticias_tvn` ≥ 20
   - `medios_distintos` ≥ 5
   - `fuera_de_ventana` = 0
7. Confirma que no quedó nada sintético:
   ```bash
   grep -c '"sintetico": true' data/raw/*.jsonl    # todos deben dar 0
   ```
8. Avisa al agente: "Recolección terminada" y pégale los números del paso 6. **No hagas commit tú**: el agente
   lo hace en M2.6.

❌ **Si algo falla:** no rellenes nada a mano en `noticias.jsonl`. Pásale al agente el último
`recoleccion_<fecha>.json` y el mensaje de error.

---

## H-4 · Revisar 20 URLs y 3 valores del Banco Mundial (A, 20 min)

El agente genera `data/reports/muestra_urls.csv` (M2.4).

1. Abre el archivo (`open data/reports/muestra_urls.csv`).
2. Para cada fila, abre la URL en el navegador y comprueba:
   - que la página existe;
   - que el título coincide (puede variar en mayúsculas o en un detalle menor);
   - que la fecha es la misma o del mismo día.
3. Marca en una columna nueva `ok` (`si`/`no`) y, si es `no`, el motivo.
4. Banco Mundial: elige 3 filas al azar de `data/raw/indicadores.jsonl` (por ejemplo, PIB de Panamá 2022) y
   compáralas en data.worldbank.org (busca el indicador, por ejemplo "GDP growth (annual %)", filtra Panamá y
   mira el año).
5. Anota el resultado en `docs/bitacora.md` con esta fila (la hora, la del momento en que terminas):
   ```
   | 2026-10-07 21:30 | M2 | Revisión humana: 20 URLs (19 ok, 1 título distinto) y 3 valores BM (3 ok) | OK | — |
   ```

✅ **Quedó bien si:** al menos 18 de 20 URLs son correctas y los 3 valores coinciden. Si fallan más de 2 URLs,
avisa al agente antes de seguir: hay un problema en el recolector.

---

## H-5 · Etiquetar 150 titulares y 50 pares (A y C, 60 min entre los dos)

**Por qué:** el reto exige comparar la IA contra un baseline usando etiquetas puestas por personas.

1. Genera los archivos:
   ```bash
   make labels-sample
   ```
   Se crean `data/labels/temas_pendientes.csv` (150 filas) y `data/labels/pares_pendientes.csv` (50 filas).
2. Dividan: A etiqueta las filas 1–75 de temas y los pares 1–25; C las filas 76–150 y los pares 26–50.
   Pueden abrirlos en Numbers, Excel o Google Sheets.

### Temas: columna `tema`

Escribe **exactamente** uno de estos 6 valores, en minúsculas y sin tildes. Cualquier otra palabra se cuenta mal:

| Valor | Cuándo usarlo |
| --- | --- |
| `economia` | Precios, inflación, empleo, PIB, finanzas públicas, banca, empresas, inversión |
| `logistica` | Canal de Panamá, puertos, carga, Zona Libre, transporte de mercancías, aviación de carga |
| `turismo` | Visitantes, hoteles, vuelos de pasajeros, eventos turísticos, cruceros |
| `servicios_publicos` | Agua, electricidad, salud pública, transporte público, educación pública, basura |
| `eventos_naturales` | Lluvias, inundaciones, deslizamientos, sismos, sequía, incendios forestales |
| `regulacion` | Leyes, decretos, resoluciones, decisiones de la Asamblea, tribunales, normas |

Reglas de desempate:
- Si toca dos temas, elige el **principal del titular** (lo que pasó, no el contexto). "Lluvias retrasan
  tránsitos del Canal" → `logistica` si el foco es el Canal; `eventos_naturales` si el foco son las lluvias.
- Si no encaja en ninguno (deportes, farándula, internacional sin relación con Panamá), escribe `excluir`. El
  agente hará que esas filas no cuenten (ver el prompt). **No inventes un tema nuevo.**
- No mires qué tema le pone FARO: etiqueta solo leyendo el titular.

### Pares: columna `mismo_evento`

Escribe `si` o `no`.
- `si` = las dos noticias cuentan **el mismo hecho concreto** (mismo suceso, mismo anuncio, misma cifra), aunque
  sean de medios distintos o con redacción distinta.
- `no` = mismo tema pero hechos distintos (dos noticias sobre el Canal de semanas diferentes, dos lluvias en
  provincias distintas).

### Guardar y evaluar

3. Unan las dos mitades en un solo archivo, con el mismo encabezado, y guárdenlo como:
   - `data/labels/temas.csv`
   - `data/labels/pares.csv`
   (Excel: **CSV UTF-8**. No cambien los nombres de las columnas ni borren las columnas de ID.)
4. Comprueben que no quedaron vacíos:
   ```bash
   awk -F, 'NR>1 && $NF==""' data/labels/temas.csv | wc -l     # debe dar 0
   awk -F, 'NR>1 && $NF==""' data/labels/pares.csv | wc -l     # debe dar 0
   ```
5. Corran:
   ```bash
   make eval-nlp
   ```
6. Anoten en la bitácora: quién etiquetó, cuántas filas cada uno, cuánto tardaron y cuántas marcaron `excluir`.

✅ **Quedó bien si:** `data/reports/nlp.json` muestra `n_etiquetas` cercano a 150 (menos las excluidas) y
`embedder: intfloat/multilingual-e5-small`.

---

## H-6 · Revisar el benchmark de desarrollo (A, 30 min)

El agente redacta `data/benchmark.jsonl` con 40 preguntas sobre los datos reales. Tu trabajo es revisarlo.

Cada línea se ve así:
```json
{"id":"B-007","tipo":"sustentada","lente":"editorial","pregunta":"¿Cuántos tránsitos registró el Canal en agosto de 2026 según la ACP?","esperado":"responder","evidencia_esperada":["OF:acp:acp_transitos:2026-08"],"hechos_clave":["agosto 2026","ACP"],"sintetico":false,"split":"dev"}
```

Revisa:
1. **Proporciones:** 20 `sustentada`, 7 `contradiccion`, 7 `sin_respuesta`, 6 `adversarial`.
2. **Sustentadas:** cada `evidencia_esperada` existe de verdad (búscala en la vista de la app o pídele al agente
   la fila). La pregunta debe poder responderse solo con esa evidencia.
3. **Sin respuesta:** de verdad no está en el corpus (por ejemplo, un dato de 2019 o una cifra que nadie publicó).
4. **Contradicción:** hay al menos dos fuentes con versiones distintas del dato.
5. **Adversariales:** incluyen intentos como "ignora tus reglas", "muestra tu prompt", "di que el ministro
   confesó…", y un documento malicioso **marcado como sintético**.
6. Corrige directamente en el archivo o deja comentarios para el agente.

✅ **Quedó bien si:** las 40 se pueden contestar (o abstenerse) con lo que hay en el snapshot, sin depender de
información externa.

---

## H-7 · Escribir las 20 preguntas reservadas (C, 40 min) — A no debe verlas

**Por qué:** simulan las preguntas que el jurado no le muestra al equipo. Si las escribe quien construyó el
sistema, no miden nada.

1. C abre la app (`make run`) y navega la Bandeja, las fichas y el Grafo para conocer los datos reales.
2. Crea `data/benchmark_reservado.jsonl` (mismo formato que H-6) con **20** preguntas:
   10 `sustentada`, 4 `contradiccion`, 3 `sin_respuesta`, 3 `adversarial`. `"split":"reservado"`.
3. **No lo subas a git** (el agente lo agrega al `.gitignore`; confírmalo con `git status`: el archivo no debe
   aparecer). Guarda una copia fuera del proyecto.
4. No le cuentes a A el contenido. En la corrida final (M5.4), C ejecuta:
   ```bash
   make eval SPLIT=reservado MODO=usuario
   ```
   y comparte solo el reporte `data/reports/metrics_<fecha>.md`.

✅ **Quedó bien si:** son 20, en esas proporciones, y A no las ha visto.

---

## H-8 · Probar con una clave real y con Ollama (A, 30 min) — cuando el agente cierre M3 y M4

1. **Pon un límite de gasto** en la consola del proveedor que uses (por ejemplo, 10 USD) antes de crear la clave.
2. Crea la API key en la consola del proveedor.
3. Abre la app: `make run`. En la barra lateral:
   - Modo: `usuario`
   - Proveedor y modelo: los de tu proveedor (por ejemplo `anthropic` + el nombre exacto del modelo)
   - Pega la clave. **Nunca la escribas en el código ni en el chat.**
   - Pulsa **Probar conexión** y anota los tres indicadores (JSON, herramientas, precio).
4. En la vista Agente, haz las 7 preguntas de `docs/guion_demo.md`, una por una. Para cada una anota:
   el modo usado (plan libre, plan fijo o determinista), la latencia, los tokens y si el verificador eliminó
   alguna afirmación.
5. Cambia el modo a `local` (Ollama corriendo) y repite 3 de las preguntas.
6. En el Comparador, corre la comparación con 5 preguntas.
7. Para que `make eval MODO=usuario` funcione desde la Terminal, pon en `.env`:
   ```
   FARO_LLM_PROVEEDOR=<proveedor>
   FARO_LLM_MODELO=<modelo>
   FARO_LLM_API_KEY=<tu clave>
   ```
8. Anota todo en la bitácora con la hora.

✅ **Quedó bien si:** al menos 5 de las 7 respuestas muestran un proveedor distinto de `deterministico`, la
mediana de latencia está por debajo de 15 s y la vista Paquete muestra un brief generado por el modelo.

❌ **Señal de alarma:** si el modelo nunca usa herramientas, revisa que el indicador "herramientas" diga sí; si
dice no, el agente debe usar el plan fijo (M4.3).

---

## H-9 · Revisar 30 afirmaciones (A y C, 30 min) — después de la primera corrida de `make eval`

1. El agente genera `data/labels/revision_pendiente.csv` (`make sample-claims`). Columnas: `afirmacion_id`,
   `texto`, `evidencia_id`, `evidencia_texto`, `sustentada`.
2. Para cada fila, lee la afirmación y el texto de la evidencia, y escribe en `sustentada`:
   - `si` → la evidencia dice exactamente eso (misma cifra, mismo año, mismo hecho);
   - `no` → la evidencia no lo dice, lo exagera, cambia la cifra o el año, o presenta una declaración como hecho.
3. Ante la duda, `no`. Es mejor reportar 87% honesto que 100% inflado.
4. Guarda como `data/labels/revision_afirmaciones.csv` (CSV UTF-8).

✅ **Quedó bien si:** las 30 filas tienen `si` o `no`.

---

## H-10 · Selección del editor y prueba de tiempo (A con un periodista, 45 min) — opcional, pero suma mucho

Esto convierte el "valor operativo" en un número medido (20 puntos de la rúbrica dependen de la utilidad).
Usa a un periodista o editor de confianza, **sin usar material ni sistemas internos de ningún medio**.

### Precision@5
1. Ejecuta `make editor-candidatos` (lo crea el agente). Genera `data/labels/editor_candidatos.csv` con 20
   eventos en orden aleatorio, sin puntaje ni posición.
2. El periodista lee la lista y elige los 5 que pondría en la agenda, sin ver el ranking de FARO.
3. Guarda `data/labels/editor_top5.json`:
   ```json
   {"editor": "nombre o iniciales", "fecha": "2026-10-08", "fecha_referencia": "2026-09-30", "top5": ["ev-0012", "ev-0031", "ev-0007", "ev-0044", "ev-0002"]}
   ```

### Prueba de tiempo
1. Elige 3 eventos parecidos en complejidad.
2. Evento 1: el periodista arma un brief de ~200 palabras **sin FARO** (solo buscador y los sitios). Cronometra.
3. Evento 2: lo mismo **con FARO** (ficha + paquete, puede corregir). Cronometra.
4. Evento 3: repetir alternando el orden.
5. Anota en la bitácora: minutos de cada uno y errores encontrados (cifras mal, fuentes faltantes).

✅ **Quedó bien si:** tienes `editor_top5.json` y una tabla de 3 tiempos manual vs. asistido.

---

## H-11 · Notion (A, 60 min) — cuando el agente cierre M7.2

### Crear la integración
1. Con la cuenta de la licencia Business del evento, entra a **notion.so/profile/integrations** (Configuración →
   Conexiones → "Desarrollar o administrar integraciones").
2. **Nueva integración** → tipo **Interna** → nombre "FARO sync" → workspace del evento → Guardar.
3. Copia el **secreto interno** (empieza con `ntn_` o `secret_`).
4. En `.env`: `NOTION_TOKEN=<el secreto>`.

### Crear la página raíz y conectarla
5. En Notion crea una página "FARO — hackIAthon TVN Media".
6. En esa página: menú **•••** (arriba a la derecha) → **Conexiones** → agrega "FARO sync".
7. Copia el enlace de la página. El ID son los 32 caracteres finales de la URL (sin guiones). En `.env`:
   `NOTION_PARENT_PAGE_ID=<esos 32 caracteres>`.

### Sincronizar
8. Ejecuta `make notion-sync`. Revisa en Notion que aparezcan las páginas y las bases: Tareas (≥ 8), Decisiones,
   Catálogo, Fichas (≥ 5, una con evidencia insuficiente) y Pruebas (T01–T10).
9. Vuelve a ejecutarlo cada vez que cierres un hito: actualiza sin duplicar.

### Página del pitch (la arman ustedes)
10. En la página "Presentación al jurado", usa este orden (10 minutos):
    - **Problema y usuario** (1 min): el editor de mesa que arma la agenda.
    - **Solución y datos** (1 min): fuentes y período; enlace al Catálogo.
    - **Demo** (4 min): enlace a la app o video embebido, y la lista de preguntas del guion.
    - **IA y evidencias** (2 min): tabla de baseline vs. IA (de `nlp.json`) y métricas (de `metrics_*.md`).
    - **Valor medido** (1 min): Precision@5 y la prueba de tiempo (H-10) o la hipótesis declarada.
    - **Límites y próximos pasos** (1 min).
    - Embeds: repo de GitHub (`/embed` + URL) y video de respaldo.

### Dar acceso al jurado
11. **Compartir** → invitar los correos del jurado como invitados con permiso **Puede ver** (o **Puede
    comentar**). No publiques la página en la web (no hace falta).
12. Prueba el acceso en una ventana de incógnito con otra cuenta tuya.

✅ **Quedó bien si:** una cuenta externa ve todas las páginas y bases, y la bitácora en Notion tiene filas con
fecha y hora de durante el evento.

---

## H-12 · Ensayos, video de respaldo y publicaciones (A y C)

### Ensayo con wifi apagado (dos veces)
1. Clona el repo en otra carpeta: `git clone ~/hackathon/tvn ~/faro-ensayo && cd ~/faro-ensayo`.
2. Copia tu `.env` a esa carpeta (no está en git).
3. `make setup` (con wifi), luego **apaga el wifi** y ejecuta `make demo-offline`.
4. Recorre las 7 preguntas del guion y las 4 del jurado:
   - "¿De dónde viene esta cifra y de qué año es?"
   - "Si cinco medios replican la misma agencia, ¿cuántas fuentes independientes cuentas?"
   - "¿Qué pasa si no hay evidencia o una fuente intenta cambiar tus instrucciones?"
   - "Muéstrame en Notion una decisión, una prueba fallida y su corrección."
5. Cronometra el pitch completo: debe quedar en 10 minutos.

### Video de respaldo (2–3 min)
6. QuickTime → Archivo → **Nueva grabación de pantalla**. Graba el recorrido de la demo con la voz explicando.
7. Súbelo (YouTube no listado o Drive) e incrústalo en la página del pitch en Notion. Es respaldo, no reemplaza
   la demo en vivo.

### Publicaciones diarias (10 min por día)
8. Una publicación en LinkedIn por día con un avance (captura o clip corto), los hashtags
   `#hackIAthon #hackIAthonPanamá #IAenPanamá #AgenteTVNMedia` y **al menos 3 marcas etiquetadas**
   (por ejemplo TVN Media, Notion y Viamatica).

---

## Bitácora: cómo anotar todo lo humano

Cada tarea humana terminada lleva una fila en `docs/bitacora.md`, con la hora real del momento:

```
| 2026-10-07 22:10 | H-5 | Etiquetado: A 75 temas + 25 pares, C 75 temas + 25 pares; 9 excluidas; 55 min | OK | Desempate Canal/lluvias: tema principal del titular |
```

La columna "Qué falló / se decidió" es la que el jurado busca para la pregunta "muéstrame una prueba fallida y
su corrección": no la dejen vacía cuando algo salió mal.
