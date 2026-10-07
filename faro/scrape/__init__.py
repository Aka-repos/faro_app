"""Recolectores por fuente (F-01).

Cada módulo respeta robots.txt, pausa por dominio y guarda la evidencia de origen
en ``data/raw/http/``. La demo usa el snapshot real congelado (D-13).
"""

from faro.scrape import (  # noqa: F401
    apis,
    check,
    collect,
    html,
    oficiales,
    pdf,
    politeness,
    rss,
    sitemap,
)
