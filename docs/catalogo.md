# Catálogo de datos

Generado desde `config/fuentes.yaml`. Cada fuente tiene método, licencia/condiciones y hash en
`data/manifest.json`. El corpus del seed está **marcado como sintético** (D-17).

## Noticias

| Fuente | Familia | Método | Licencia / condiciones |
| --- | --- | --- | --- |
| TVN Panamá | noticias | rss | Titulares y enlaces públicos; no republicar artículos/imágenes/videos sin autorización |
| Telemetro | noticias | rss | Titulares y enlaces públicos |
| Panamá América | noticias | rss | Titulares y enlaces públicos |
| La Prensa | noticias | rss | Titulares y enlaces públicos |
| La Estrella de Panamá | noticias | rss | Titulares y enlaces públicos |
| Metro Libre | noticias | sitemap | Titulares y enlaces públicos |
| GDELT DOC 2.0 | noticias | api | Metadatos de enlaces; no transfiere derechos de los medios enlazados |

## Oficial mensual / histórico / eventos

| Fuente | Familia | Método | Licencia / condiciones |
| --- | --- | --- | --- |
| INEC | oficial_mensual | html | Datos públicos con atribución; conservar unidad y período |
| ACP | oficial_mensual | html | Estadísticas públicas con atribución |
| SBP | oficial_mensual | pdf | Información informativa y revisable; no es opinión oficial de la SBP |
| Gaceta Oficial | oficial | html | Documentos públicos |
| SINAPROC | oficial | html | Avisos públicos |
| ASEP | oficial | html | Avisos públicos |
| Banco Mundial | historico | api | CC BY 4.0 (salvo excepciones en metadatos) |
| USGS | eventos | api | Datos públicos; solo hechos sísmicos, nunca evidencia de daños |

## Reglas de integridad

- UTF-8, IDs estables, fechas ISO 8601 en UTC; hora de Panamá en la interfaz.
- `fecha_publicacion` ≠ `fecha_deteccion` (seendate de GDELT).
- Nulos conservados, nunca rellenados con cero.
- Cuerpo de artículos nunca mostrado completo ni redistribuido.
- Cada afirmación cita `evidencia_id` + campo/página.

## Transformaciones

- Normalización de fechas a ISO 8601 UTC.
- Deduplicación por URL normalizada.
- Registros inválidos → cuarentena con motivo (T01).
- Embeddings locales (sentence-transformers o hashing de n-gramas).
- Clasificación temática (6 clases) y agrupación de eventos (coseno + 72 h + entidades).
