# Diccionario del paquete de datos "Panamá · Señales y Evidencias v1"

Cada archivo es JSONL (una línea = un registro UTF-8). Fechas en ISO 8601 UTC. Nulos conservados.
`manifest.json` trae la versión, el corte UTC, los conteos, condiciones y SHA-256 por archivo.

## data/raw/noticias.jsonl

| Campo | Tipo | Descripción |
| --- | --- | --- |
| tipo | str | `noticia` |
| id | str | `n-<sha1(url normalizada)>` |
| fuente_id | str | id en `config/fuentes.yaml` |
| titulo | str | titular publicado |
| url | str | URL real |
| medio | str | nombre del medio |
| dominio | str | dominio de la URL |
| idioma | str | `es` |
| fecha_publicacion | str\|null | fecha de publicación (null si la fuente no la da) |
| fecha_deteccion | str\|null | cuándo se detectó (seendate en GDELT) |
| fecha_extraccion | str | cuándo se recolectó |
| alcance_texto | str | `titular` \| `metadatos` \| `resumen` |
| resumen | str\|null | ≤ 400 caracteres; nunca el cuerpo completo |
| es_agencia | bool | si es de agencia |
| agencia | str\|null | EFE/AFP/AP/Reuters… |
| sintetico | bool | siempre `false` en el snapshot real |

## data/raw/series.jsonl (oficiales mensuales)

`tipo=serie_oficial` · `id`, `fuente_id`, `serie`, `periodo` (YYYY-MM), `valor` (null si falta),
`unidad`, `url`, `pagina` (PDF), `fecha_extraccion`, `condiciones`, `sintetico=false`.

## data/raw/indicadores.jsonl (Banco Mundial)

`tipo=indicador` · `pais_iso3`, `indicador_id`, `anio`, `valor` (null si falta), `unidad`,
`fuente_url`, `fecha_extraccion`, `licencia` (CC BY 4.0), `sintetico=false`.

## data/raw/sismos.jsonl (USGS)

`tipo=sismo` · `id`, `magnitud`, `fecha`, `lat`, `lon`, `profundidad`, `lugar`, `status`, `url`, `sintetico=false`.

## data/raw/http/index.jsonl (evidencia de origen)

`url`, `fuente_id`, `status`, `fecha_UTC`, `sha256` — una fila por petición hecha.

## data/raw/manual/<fuente>.csv (transcripciones manuales)

`serie, periodo, valor, unidad, url, pagina, transcrito_por, fecha` — para fuentes oficiales
no automatizables (INEC/ACP/SBP). Es trazable; el valor nunca se inventa.
