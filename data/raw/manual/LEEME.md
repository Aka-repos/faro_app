# Series oficiales transcritas a mano

Estos CSV contienen series oficiales mensuales transcritas desde los archivos publicados por cada fuente.
**No se estima ni se completa ningún mes no publicado.** Cada fila tiene la URL exacta del archivo oficial
y, si es PDF, la página donde aparece el dato.

## Columnas

| Columna | Descripción |
| --- | --- |
| `serie` | Nombre corto en minúsculas, estable entre filas de la misma serie |
| `periodo` | `AAAA-MM`, entre 2025-10 y 2026-09 |
| `valor` | Número con punto decimal, sin separador de miles |
| `unidad` | Tal como la publica la fuente |
| `url` | URL exacta del archivo oficial (Excel o PDF) |
| `pagina` | Número de página si la URL es un PDF; vacío si es Excel |
| `transcrito_por` | Quién transcribió (texto libre) |
| `fecha` | Fecha de transcripción |

## Fuentes y series

- `inec.csv` — INEC (`inec.gob.pa`): `inec_imae` y `inec_imae_var` (2025-10 a 2026-07).
- `sbp.csv` — SBP (`superbancos.gob.pa`): `sbp_cbi_activo_total`, `sbp_cbi_depositos`,
  `sbp_cbi_cartera_neta` (2025-10 a 2026-08).

## PDF de origen

Los PDF descargados desde los que se transcribió están en `data/cache/sbp/` (ignorado por git). Se pueden
volver a descargar con la `url` de cada fila.

## Validación

`faro/scrape/oficiales.py::_leer_manual` valida cada fila: `periodo` en la ventana, `valor` numérico, `url`
con dominio oficial y `pagina` entera cuando la URL es PDF. Las filas inválidas se reportan y no se cargan.
