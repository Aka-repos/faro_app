"""Recolectores por fuente (F-01).

Cada módulo respeta robots.txt, pausa por dominio y guarda la respuesta cruda en
``data/raw/<fuente>/<fecha>/``. Si no hay red, devuelven listas vacías; la demo
usa el snapshot congelado (D-13) o el seed sintético.
"""

from faro.scrape import apis, check, html, pdf, rss, sitemap  # noqa: F401
