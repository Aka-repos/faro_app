"""Generador de snapshot sintético (semilla determinística).

Produce un corpus de noticias panameñas realistas, series oficiales, indicadores
del Banco Mundial y sismos USGS, y los escribe como JSONL crudo en ``data/raw/``
para que el pipeline completo funcione sin red (D-13, T10).

El corpus está **marcado como sintético** en el manifest y en los metadatos; el
snapshot real de la demo se obtiene con los recolectores de ``faro/scrape``.
"""

from __future__ import annotations

import json
import random
from datetime import UTC, datetime, timedelta

import config.settings as S

RNG = random.Random(42)

# Tema -> (lista de titulares canónicos por evento)
EVENTOS = {
    "economia": [
        "Inflación interanual de Panamá se modera en el tercer trimestre",
        "Crecimiento del PIB panameño supera las proyecciones del FMI",
        "Exportaciones del Canal impulsan los ingresos fiscales",
        "Desempleo nacional baja a su menor nivel en una década",
        "Banco Central revisa al alza la proyección de inversión extranjera",
        "Presupuesto 2027 prioriza infraestructura y educación",
    ],
    "logistica": [
        "Tránsito de buques por el Canal de Panamá alcanza récord mensual",
        "Aumenta el tonelaje de carga neopanamax en la vía interoceánica",
        "Puerto de Balboa moderniza su terminal de contenedores",
        "Naviera amplía rutas entre Panamá y Asia",
        "Aduanas agiliza despacho de carga en la Zona Libre de Colón",
    ],
    "turismo": [
        "Llegada de visitantes internacionales crece en temporada alta",
        "Ocupación hotelera supera el 80% en la ciudad de Panamá",
        "Nueva ruta aérea conecta Panamá con Europa",
        "Turismo de reuniones repunta tras congresos regionales",
    ],
    "servicios_publicos": [
        "Avanza la ampliación de la red eléctrica en el interior",
        "Nueva planta de tratamiento mejora el suministro de agua potable",
        "Regulador revisa tarifas de telecomunicaciones",
        "Ampliación del Metro de Panamá inicia nueva fase",
    ],
    "eventos_naturales": [
        "Sismo de magnitud 5.4 se siente en la frontera con Costa Rica",
        "Lluvias intensas provocan deslizamientos en Chiriquí",
        "Alerta verde por onda tropical en el Caribe panameño",
        "Sequía estacional reduce el nivel del lago Gatún",
    ],
    "regulacion": [
        "Asamblea aprueba reforma a la ley de contrataciones públicas",
        "Nueva normativa regula las fintech en Panamá",
        "Decreto ejecutivo actualiza estándares ambientales",
        "Licitación del cuarto puente sobre el Canal avanza",
    ],
}

# Medios ficticios (WP-1.7): el seed solo existe para pruebas; nunca en la demo.
# Dominios `.example.invalid` reservados para documentación/pruebas.
MEDIOS = [
    {"medio": "Medio Ficticio A", "dominio": "medio-a.example.invalid"},
    {"medio": "Medio Ficticio B", "dominio": "medio-b.example.invalid"},
    {"medio": "Medio Ficticio C", "dominio": "medio-c.example.invalid"},
    {"medio": "Medio Ficticio D", "dominio": "medio-d.example.invalid"},
    {"medio": "Medio Ficticio E", "dominio": "medio-e.example.invalid"},
    {"medio": "Medio Ficticio F", "dominio": "medio-f.example.invalid"},
]

# El primer medio ficticio cumple el rol del "patrocinador" en los tests.
MEDIO_PRINCIPAL = MEDIOS[0]["medio"]

# Titulares adicionales de una sola fuente (para volumen, sin perder trazabilidad).
EXTRA = {
    "economia": [
        "Sector bancario panameño reporta crecimiento del crédito",
        "Precios de la canasta básica muestran leve alza mensual",
        "Inversión extranjera directa crece en el primer semestre",
        "Exportaciones de banano y café repuntan en el mercado regional",
        "Gobierno presenta plan de reactivación económica",
        "Tasa de desempleo juvenil sigue en el foco del Gobierno",
    ],
    "logistica": [
        "Ampliación de puertos del Pacífico avanza según cronograma",
        "Ferrocarril Panamá-Colón mejora su capacidad de carga",
        "Nueva línea de cabotaje conecta islas del Caribe",
        "Aeropuerto de Tocumen procesa récord de carga aérea",
        "Invierten en dragado para mantener el calado del Canal",
    ],
    "turismo": [
        "Cruceros programan más escalas en puertos panameños",
        "Bocas del Toro y Boquete lideran reservas de temporada",
        "Panamá promociona turismo de convenciones en el exterior",
        "Aerolínea amplía frecuencias hacia Suramérica",
        "Casco Antiguo atrae nueva inversión hotelera",
    ],
    "servicios_publicos": [
        "Avanza proyecto de agua potable en Panamá Oeste",
        "Instalan nueva subestación eléctrica en Veraguas",
        "Amplían cobertura de internet en zonas rurales",
        "Modernizan red de alcantarillado en la capital",
        "Regulador audita calidad del servicio eléctrico",
    ],
    "eventos_naturales": [
        "Onda tropical deja lluvias en la vertiente del Caribe",
        "Monitorean niveles del río en la provincia de Darién",
        "Sismo de baja magnitud se registra frente a Veraguas",
        "Autoridades emiten aviso por vientos fuertes en el Pacífico",
        "Sequía moderada afecta cultivos en Azuero",
    ],
    "regulacion": [
        "Publican en Gaceta nueva norma sobre energía renovable",
        "Asamblea debate ley de protección de datos personales",
        "Actualizan reglamento de transporte público",
        "Licitación de obras sanitarias recibe ofertas",
        "Nuevo marco regulatorio para la economía digital",
    ],
}

AGENCIAS = ["EFE", "AFP", "AP", "Reuters"]

WINDOW = (datetime(2025, 10, 2, tzinfo=UTC), datetime(2026, 9, 30, tzinfo=UTC))


def _iso(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat()


def _fecha_en_ventana(frac: float) -> datetime:
    """Fecha dentro de la ventana según `frac` en [0,1)."""
    start, end = WINDOW
    delta = (end - start).total_seconds()
    return start + timedelta(seconds=delta * frac)


def _hash(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def gen_noticias() -> list[dict]:
    """Genera noticias con eventos, agencias replicadas y casos de control."""
    noticias: list[dict] = []
    n = 0
    total_eventos = sum(len(v) for v in EVENTOS.values())
    ev_idx = 0
    for tema, titulares in EVENTOS.items():
        for j, canonico in enumerate(titulares):
            # Fecha del evento: distribuida uniformemente en la ventana.
            frac = (ev_idx + 1) / total_eventos
            ev_idx += 1
            fecha = _fecha_en_ventana(frac)
            es_agencia = j % 3 == 0  # ~1/3 de los eventos vienen de agencia
            agencia = RNG.choice(AGENCIAS) if es_agencia else None
            # El medio principal siempre cubre (rol "patrocinador") + 2-4 medios más.
            otros = [m for m in MEDIOS if m["medio"] != MEDIO_PRINCIPAL]
            outlets = [next(m for m in MEDIOS if m["medio"] == MEDIO_PRINCIPAL)] + RNG.sample(
                otros, RNG.randint(2, 4)
            )
            for k, m in enumerate(outlets):
                titulo = f"{canonico}" + (f" ({agencia})" if agencia and k == 0 else "")
                url = f"https://www.{m['dominio']}/noticia/{_hash(titulo)}"
                noticias.append(
                    {
                        "tipo": "noticia",
                        "id": f"n-{_hash(url)}",
                        "fuente_id": _fuente_id(m["medio"]),
                        "titulo": titulo,
                        "url": url,
                        "medio": m["medio"],
                        "dominio": m["dominio"],
                        "idioma": "es",
                        "fecha_publicacion": _iso(fecha),
                        "fecha_deteccion": _iso(fecha + timedelta(hours=RNG.randint(0, 6))),
                        "fecha_extraccion": _iso(datetime.now(UTC)),
                        "alcance_texto": "resumen",
                        "resumen": f"Cobertura de {m['medio']} sobre: {canonico}.",
                        "tema": tema,
                        "es_agencia": es_agencia,
                        "agencia": agencia,
                        "sintetico": True,
                    }
                )
                n += 1

    # Noticias adicionales de una sola fuente para alcanzar el volumen meta (>=200 únicos).
    n += _gen_extra(noticias, n)

    # Caso T03: noticia antigua recirculada (fuera de ventana, recirculada dentro).
    antigua = _fecha_en_ventana(-0.05)  # antes de la ventana
    noticias.append(
        {
            "tipo": "noticia",
            "id": "n-antigua-001",
            "fuente_id": _fuente_id(MEDIO_PRINCIPAL),
            "titulo": "Panamá cierra año fiscal con superávit (recirculada)",
            "url": f"https://www.{MEDIOS[0]['dominio']}/noticia/antigua-001",
            "medio": MEDIO_PRINCIPAL,
            "dominio": MEDIOS[0]["dominio"],
            "idioma": "es",
            "fecha_publicacion": _iso(antigua),
            "fecha_deteccion": _iso(_fecha_en_ventana(0.5)),
            "fecha_extraccion": _iso(datetime.now(UTC)),
            "alcance_texto": "titular",
            "resumen": "Artículo original previo a la ventana; se detecta recirculado.",
            "tema": "economia",
            "es_agencia": False,
            "agencia": None,
            "sintetico": True,
        }
    )

    # Casos para T01: registros con fecha inválida y con nulos (se conservan/quarentena).
    noticias.append(
        {
            "tipo": "noticia",
            "id": "n-invalida-001",
            "fuente_id": _fuente_id(MEDIOS[1]["medio"]),
            "titulo": "Registro con fecha inválida (control T01)",
            "url": f"https://www.{MEDIOS[1]['dominio']}/noticia/invalida-001",
            "medio": MEDIOS[1]["medio"],
            "dominio": MEDIOS[1]["dominio"],
            "idioma": "es",
            "fecha_publicacion": "no-es-una-fecha",
            "fecha_deteccion": None,
            "fecha_extraccion": _iso(datetime.now(UTC)),
            "alcance_texto": "titular",
            "resumen": None,
            "tema": "regulacion",
            "es_agencia": False,
            "agencia": None,
            "sintetico": True,
        }
    )
    noticias.append(
        {
            "tipo": "noticia",
            "id": "n-nulos-001",
            "fuente_id": _fuente_id(MEDIOS[2]["medio"]),
            "titulo": "Registro con campos nulos (control T01)",
            "url": f"https://www.{MEDIOS[2]['dominio']}/noticia/nulos-001",
            "medio": MEDIOS[2]["medio"],
            "dominio": MEDIOS[2]["dominio"],
            "idioma": "es",
            "fecha_publicacion": _iso(_fecha_en_ventana(0.6)),
            "fecha_deteccion": None,
            "fecha_extraccion": None,
            "alcance_texto": "titular",
            "resumen": None,
            "tema": "servicios_publicos",
            "es_agencia": False,
            "agencia": None,
            "sintetico": True,
        }
    )

    return noticias


def _gen_extra(noticias: list[dict], start: int) -> int:
    """Agrega ~180 noticias de una sola fuente para superar el mínimo del reto."""
    n = start
    temas = list(EXTRA.keys())
    # Repetir plantillas con variaciones hasta superar 200 noticias totales.
    k = 0
    while n < 200:
        tema = temas[k % len(temas)]
        plantilla = EXTRA[tema][k % len(EXTRA[tema])]
        variante = (
            f"{plantilla} — actualización {k // len(temas) + 1}"
            if k // len(temas) > 0
            else plantilla
        )
        medio = MEDIOS[(k + start) % len(MEDIOS)]
        fecha = _fecha_en_ventana(((n + 1) % 100) / 100)
        url = f"https://www.{medio['dominio']}/noticia/{_hash(variante + str(n))}"
        noticias.append(
            {
                "tipo": "noticia",
                "id": f"n-{_hash(url)}",
                "fuente_id": _fuente_id(medio["medio"]),
                "titulo": variante,
                "url": url,
                "medio": medio["medio"],
                "dominio": medio["dominio"],
                "idioma": "es",
                "fecha_publicacion": _iso(fecha),
                "fecha_deteccion": _iso(fecha + timedelta(hours=RNG.randint(0, 6))),
                "fecha_extraccion": _iso(datetime.now(UTC)),
                "alcance_texto": "resumen",
                "resumen": f"Cobertura de {medio['medio']} sobre: {plantilla}.",
                "tema": tema,
                "es_agencia": False,
                "agencia": None,
                "sintetico": True,
            }
        )
        n += 1
        k += 1
    return n - start


def _fuente_id(medio: str) -> str:
    return {
        "Medio Ficticio A": "medio_a",
        "Medio Ficticio B": "medio_b",
        "Medio Ficticio C": "medio_c",
        "Medio Ficticio D": "medio_d",
        "Medio Ficticio E": "medio_e",
        "Medio Ficticio F": "medio_f",
    }.get(medio, "medio_x")


def gen_series() -> list[dict]:
    """Series oficiales mensuales oct-2025..sep-2026 (INEC, ACP, SBP)."""
    out = []
    start = datetime(2025, 10, 1, tzinfo=UTC)
    series = [
        ("inec_imae", "inec", "IMAE", "% variación interanual"),
        ("inec_ipc", "inec", "IPC", "% variación interanual"),
        ("inec_visitantes", "inec", "Visitantes", "miles de personas"),
        ("acp_transitos", "acp", "Tránsitos Canal", "buques"),
        ("acp_tonelaje", "acp", "Tonelaje Canal", "millones de toneladas CP/SUAB"),
        ("sbp_depositos", "sbp", "Depósitos totales", "millones USD"),
        ("sbp_creditos", "sbp", "Créditos al sector privado", "millones USD"),
        ("sbp_liquidez", "sbp", "Índice de liquidez", "%"),
    ]
    for serie_id, fuente, _nombre, unidad in series:
        for m in range(12):
            periodo = (start + timedelta(days=32 * m)).strftime("%Y-%m")
            base = {
                "inec_imae": 4.5,
                "inec_ipc": 2.2,
                "inec_visitantes": 220.0,
                "acp_transitos": 1150.0,
                "acp_tonelaje": 42.0,
                "sbp_depositos": 110000.0,
                "sbp_creditos": 72000.0,
                "sbp_liquidez": 62.0,
            }[serie_id]
            valor = round(base + RNG.uniform(-base * 0.15, base * 0.15), 2)
            out.append(
                {
                    "tipo": "serie_oficial",
                    "id": f"of-{serie_id}-{periodo}",
                    "fuente_id": fuente,
                    "serie": serie_id,
                    "periodo": periodo,
                    "valor": valor,
                    "unidad": unidad,
                    "url": f"https://datos.example.invalid/{fuente}/{serie_id}/{periodo}",
                    "pagina": None if fuente != "sbp" else RNG.randint(3, 20),
                    "fecha_extraccion": _iso(datetime.now(UTC)),
                    "condiciones": "Datos informativos y revisables; no es opinión oficial de la fuente.",
                    "sintetico": True,
                }
            )
    return out


def gen_indicadores() -> list[dict]:
    """Cuadrícula Banco Mundial 6 países x 6 indicadores x 2010–2024 (sintética)."""
    from faro.scrape.apis import WB_COUNTRIES, WB_INDICATORS, _unidad_wb

    out = []
    bases = {
        "NY.GDP.MKTP.KD.ZG": 4.0,
        "FP.CPI.TOTL.ZG": 3.0,
        "SL.UEM.TOTL.ZS": 6.0,
        "SP.POP.TOTL": 4_000_000.0,
        "IT.NET.USER.ZS": 60.0,
        "NE.EXP.GNFS.ZS": 40.0,
    }
    for c in WB_COUNTRIES:
        for i in WB_INDICATORS:
            for anio in range(2010, 2025):
                # Conservar algunos valores faltantes explícitamente (no rellenar con cero).
                if RNG.random() < 0.02:
                    continue
                valor = round(
                    bases[i] * (1 + RNG.uniform(-0.4, 0.4)) * (1 + (anio - 2010) * 0.005), 3
                )
                out.append(
                    {
                        "tipo": "indicador",
                        "pais_iso3": c,
                        "indicador_id": i,
                        "anio": anio,
                        "valor": valor,
                        "unidad": _unidad_wb(i),
                        "fuente_url": f"https://datos.example.invalid/wb/{c}/{i}",
                        "fecha_extraccion": _iso(datetime.now(UTC)),
                        "licencia": "CC BY 4.0",
                        "sintetico": True,
                    }
                )
    return out


def gen_sismos() -> list[dict]:
    """Sismos sintéticos en la caja regional (5–12, −86..−76), 2024 + ventana."""
    out = []
    for k in range(20):
        anio = 2024 if k < 12 else 2025
        mes = RNG.randint(1, 12)
        dia = RNG.randint(1, 28)
        fecha = datetime(anio, mes, dia, tzinfo=UTC) + timedelta(hours=RNG.randint(0, 23))
        out.append(
            {
                "tipo": "sismo",
                "id": f"us{sintetic_id(k)}",
                "magnitud": round(RNG.uniform(3.0, 6.2), 1),
                "fecha": _iso(fecha),
                "lat": round(RNG.uniform(5.0, 12.0), 3),
                "lon": round(RNG.uniform(-86.0, -76.0), 3),
                "profundidad": round(RNG.uniform(5.0, 120.0), 1),
                "lugar": RNG.choice(
                    [
                        "frente a la costa de Panamá",
                        "cerca de David, Panamá",
                        "frontera Panamá-Costa Rica",
                        "sur de Chiriquí",
                    ]
                ),
                "status": "reviewed",
                "url": "https://datos.example.invalid/usgs/eventpage/sintetico",
                "sintetico": True,
            }
        )
    return out


def sintetic_id(k: int) -> str:
    return f"{k:04d}abc"


def write_raw(noticias=None, series=None, indicadores=None, sismos=None) -> dict:
    """Escribe el snapshot sintético a ``data/raw/`` y devuelve conteos."""
    S.ensure_dirs()
    noticias = noticias or gen_noticias()
    series = series or gen_series()
    indicadores = indicadores or gen_indicadores()
    sismos = sismos or gen_sismos()

    payloads = {
        "noticias.jsonl": noticias,
        "series.jsonl": series,
        "indicadores.jsonl": indicadores,
        "sismos.jsonl": sismos,
    }
    for fname, rows in payloads.items():
        with open(S.RAW_DIR / fname, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    return {k: len(v) for k, v in payloads.items()}
