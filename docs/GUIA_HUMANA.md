# FARO — Guía paso a paso de las tareas humanas

Para Andrés (A) y su compañero (C). Cada tarea dice **quién**, **cuándo** (de qué hito del agente depende),
**cuánto tarda**, **los pasos exactos** y **cómo saber que quedó bien**. Los hitos M0–M8 están en
`docs/PLAN_AGENTE.md`.

Todos los comandos se ejecutan en la Terminal de la Mac, dentro de la carpeta del proyecto:

```bash
cd ~/hackathon/tvn
```

> **Alcance de esta versión (2026-10-07):** fuera de esta guía por ahora: Notion, pitch, video de respaldo y
> publicaciones (antes H-11 y H-12). El correo de contacto (antes H-1) se eliminó, y las preguntas reservadas
> (H-7) ya no requieren trabajo humano. Los números H-x se mantienen para no romper las referencias de los
> otros documentos.

---

## Resumen y orden

| # | Tarea | Quién | Depende de | Tiempo |
| --- | --- | --- | --- | --- |
| H-0 | Preparar la Mac (una sola vez) | A | — | 20 min |
| H-2 | Transcribir series oficiales (INEC, ACP, SBP) | A y C (o Claude, ver nota) | — (**empezar ya**) | 60–90 min |
| H-3 | Ejecutar la recolección real | A | Agente terminó M1 y M2.2 | 30–90 min (casi todo esperar) |
| H-4 | Revisar 20 URLs y 3 valores del Banco Mundial | A | H-3 + agente M2.4 | 20 min |
| H-5 | Etiquetar temas y pares (asistido + prueba de acuerdo) | A y C | H-3 | 40–50 min entre los dos |
| H-6 | Revisar el benchmark de desarrollo (40) | A | Agente M5 (borrador) | 30 min |
| H-7 | Preguntas reservadas | Claude (sin trabajo humano) | H-3 | 0 min |
| H-8 | Probar con clave real y con Ollama | A | Agente M3 y M4 | 30 min |
| H-9 | Revisar 30 afirmaciones | A y C | Primera corrida de `make eval` | 30 min |
| H-10 | Selección del editor y prueba de tiempo (opcional, suma mucho) | A con un periodista | H-3 | 45 min |

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

## H-1 · Correo de contacto — ELIMINADA

El reto no lo exige. No hay nada que hacer.

---

## H-2 · Transcribir series oficiales (A y C, 60–90 min) — empezar ya

> **Nota:** Claude puede hacer esta transcripción desde los sitios oficiales y dejarte los CSV para revisar.
> En ese caso tu trabajo es solo el paso 8 (verificar dos filas por serie) y poner tu nombre en
> `transcrito_por` solo en las filas que verificaste.

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
   Mientras corre puedes hacer H-2.
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

## H-5 · Etiquetar temas y pares (A y C, 40–50 min entre los dos)

### Para qué sirve

FARO clasifica cada noticia en un tema y decide si dos noticias hablan del mismo evento. Para decir "la IA
acierta el X %" y "supera al método simple de palabras clave" hace falta una **respuesta correcta** puesta por
personas contra la cual comparar. Eso es la etiqueta. Sin ella, `make eval-nlp` no tiene con qué medir.

El reto lo pide así (sección 9.1): *"reportar macro-F1 o precisión/recall sobre etiquetas humanas, incluyendo
tamaño y método de etiquetado"*. No es condición de admisión, pero sostiene los 15 puntos de "Uso efectivo
de IA".

### Método elegido: pre-etiquetado asistido + revisión humana + prueba de acuerdo a ciegas

| Parte | Filas | Quién | Con sugerencia | Para qué |
| --- | --- | --- | --- | --- |
| Bloque ciego | 30 titulares | A **y** C, cada uno por separado | **No** | Medir cuánto coinciden dos humanos (kappa) y detectar si la sugerencia sesga |
| Bloque asistido | 120 titulares | Mitad A, mitad C | Sí (columna `sugerido`) | Rapidez: confirmar o corregir |
| Pares | 50 pares | Mitad A, mitad C | No | Mismo evento sí/no (es rápido, no hace falta sugerencia) |

Las sugerencias **no** las genera FARO: las pone Claude, que es un modelo distinto del clasificador que se
evalúa. Si FARO se sugiriera a sí mismo, ustedes tenderían a aceptar su respuesta y la métrica saldría inflada.

### Pasos

1. Genera la muestra (después de H-3):
   ```bash
   make labels-sample
   ```
   Se crean `data/labels/temas_pendientes.csv` (150 filas: `noticia_id,titulo,medio,tema`) y
   `data/labels/pares_pendientes.csv` (50 filas: `id_a,titulo_a,id_b,titulo_b,mismo_evento`).
2. Pásale `temas_pendientes.csv` a Claude (en esta conversación). Te devuelve tres archivos en `data/labels/`:
   - `ciego_A.csv` y `ciego_C.csv`: las mismas 30 filas, **sin** sugerencia, columna `tema` vacía.
   - `asistido.csv`: las otras 120 filas con columnas `noticia_id,titulo,medio,sugerido,tema`. `tema` va vacía.
3. **Bloque ciego (10 min cada uno, por separado, sin hablar entre ustedes):** A llena `ciego_A.csv` y C llena
   `ciego_C.csv`.
4. **Bloque asistido (15 min cada uno):** A hace las filas 1–60 de `asistido.csv` y C las 61–120. En cada fila
   lee **primero el titular** y luego mira `sugerido`. Si estás de acuerdo, copia el valor en `tema`; si no,
   escribe el correcto. **Nunca dejes `tema` vacía ni la llenes en bloque copiando la columna entera.**
5. **Pares (10 min cada uno):** A hace los pares 1–25 y C los 26–50 en `pares_pendientes.csv`.
6. Abran los archivos en Numbers, Excel o Google Sheets y guárdenlos como **CSV UTF-8**, sin cambiar los
   nombres de columna.

### Temas: valores permitidos en `tema`

Escribe **exactamente** uno de estos valores, en minúsculas y sin tildes. Cualquier otra palabra se cuenta mal:

| Valor | Cuándo usarlo |
| --- | --- |
| `economia` | Precios, inflación, empleo, PIB, finanzas públicas, banca, empresas, inversión |
| `logistica` | Canal de Panamá, puertos, carga, Zona Libre, transporte de mercancías, aviación de carga |
| `turismo` | Visitantes, hoteles, vuelos de pasajeros, eventos turísticos, cruceros |
| `servicios_publicos` | Agua, electricidad, salud pública, transporte público, educación pública, basura |
| `eventos_naturales` | Lluvias, inundaciones, deslizamientos, sismos, sequía, incendios forestales |
| `regulacion` | Leyes, decretos, resoluciones, decisiones de la Asamblea, tribunales, normas |
| `excluir` | No encaja en ninguno (deportes, farándula, internacional sin relación con Panamá) |

Reglas de desempate:
- Si toca dos temas, elige el **principal del titular** (lo que pasó, no el contexto). "Lluvias retrasan
  tránsitos del Canal" → `logistica` si el foco es el Canal; `eventos_naturales` si el foco son las lluvias.
- **No inventes un tema nuevo.**

### Pares: columna `mismo_evento`

Escribe `si` o `no`.
- `si` = las dos noticias cuentan **el mismo hecho concreto** (mismo suceso, mismo anuncio, misma cifra), aunque
  sean de medios distintos o con redacción distinta.
- `no` = mismo tema pero hechos distintos (dos noticias sobre el Canal de semanas diferentes, dos lluvias en
  provincias distintas).

### Unir, medir el acuerdo y evaluar

7. Medir el acuerdo entre ustedes en el bloque ciego (kappa de Cohen: 1 = acuerdo total, 0 = azar):
   ```bash
   uv run python -c "
   import csv; from sklearn.metrics import cohen_kappa_score as k
   a=[r['tema'].strip() for r in csv.DictReader(open('data/labels/ciego_A.csv'))]
   c=[r['tema'].strip() for r in csv.DictReader(open('data/labels/ciego_C.csv'))]
   print('kappa', round(k(a,c),3), '| coinciden', sum(x==y for x,y in zip(a,c)), 'de', len(a))"
   ```
   Referencia: ≥ 0,6 es acuerdo bueno; ≥ 0,8, muy bueno. Si sale menor de 0,6, revisen juntos las filas en que
   no coincidieron, aclaren la regla y anoten la decisión en la bitácora.
8. Resolver el bloque ciego: en las filas donde no coincidieron, decidan juntos un valor final.
9. Armar `data/labels/temas.csv` (encabezado `noticia_id,titulo,medio,tema`) con las 30 filas ciegas
   resueltas y las 120 asistidas (sin la columna `sugerido`). Guardar `pares_pendientes.csv` lleno como
   `data/labels/pares.csv`. Claude o el agente pueden hacer esta unión si se lo piden.
10. Comprobar que no quedaron vacíos:
    ```bash
    awk -F, 'NR>1 && $NF==""' data/labels/temas.csv | wc -l     # debe dar 0
    awk -F, 'NR>1 && $NF==""' data/labels/pares.csv | wc -l     # debe dar 0
    ```
11. Correr:
    ```bash
    make eval-nlp
    ```
12. Anotar en la bitácora: quién etiquetó, cuántas filas cada uno, el kappa, cuántas sugerencias se
    corrigieron en el bloque asistido y cuántas marcaron `excluir`. Así se declara el método:
    *"150 titulares: 30 etiquetados a ciegas por dos personas (kappa = X) y 120 pre-etiquetados por un LLM
    distinto del clasificador evaluado y revisados fila por fila por una persona (N corregidos); 50 pares
    etiquetados a mano."*

✅ **Quedó bien si:** `data/reports/nlp.json` muestra `n_etiquetas` cercano a 150 (menos las excluidas),
`embedder: intfloat/multilingual-e5-small`, y tienen el kappa anotado.

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

## H-7 · Preguntas reservadas — sin trabajo humano

Según el reto (sección 11), el set reservado lo prepara la organización. Si el jurado trae el suyo, no hace falta
nada más. Como prueba interna, Claude redacta 20 preguntas (10 `sustentada`, 4 `contradiccion`,
3 `sin_respuesta`, 3 `adversarial`, `"split":"reservado"`) después de H-3, y las deja **fuera del proyecto**
(`~/hackathon/faro-reservado/benchmark_reservado.jsonl`). Reglas:

- Nadie las lee ni las usa para ajustar prompts, reglas ni código.
- Se corren una sola vez, al final (M5.4):
  ```bash
  make eval SPLIT=reservado MODO=usuario BENCH=~/hackathon/faro-reservado/benchmark_reservado.jsonl
  ```
  (si el agente no implementó `BENCH`, copia el archivo a `data/benchmark_reservado.jsonl`, corre, y bórralo
  después; el agente debe agregar ese nombre al `.gitignore` — confírmalo con `git status`: el archivo no debe
  aparecer).
- Solo se mira el reporte `data/reports/metrics_<fecha>.md`.

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

## H-11 y H-12 · Notion, pitch, video y publicaciones — fuera de esta guía por ahora

Se retoman cuando lo decidan.

---

## Bitácora: cómo anotar todo lo humano

Cada tarea humana terminada lleva una fila en `docs/bitacora.md`, con la hora real del momento:

```
| 2026-10-08 22:10 | H-5 | Etiquetado: ciego 30 (kappa 0,72), asistido A 60 + C 60 (14 sugerencias corregidas), pares 25 + 25; 9 excluidas; 45 min | OK | Desempate Canal/lluvias: tema principal del titular |
```

La columna "Qué falló / se decidió" es la que el jurado busca para la pregunta "muéstrame una prueba fallida y
su corrección": no la dejen vacía cuando algo salió mal.
