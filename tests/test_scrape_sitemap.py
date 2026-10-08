"""M1.4: sitemaps acotados y filtrados por ventana."""

from __future__ import annotations

from faro.scrape import collect, sitemap


class _Cliente:
    def __init__(self, texto):
        self._texto = texto

    def get(self, url, fuente_id="", params=None, **kw):
        class R:
            text = self._texto

        return R()


def test_parse_sitemap_filtra_por_ventana():
    xml = (
        "<urlset xmlns:news='http://www.google.com/schemas/sitemap-news/0.9'>"
        "<url><loc>https://a.com/1</loc><news:publication_date>2026-05-01T00:00:00Z</news:publication_date>"
        "<news:title>En ventana</news:title></url>"
        "<url><loc>https://a.com/2</loc><news:publication_date>2020-01-01T00:00:00Z</news:publication_date>"
        "<news:title>Fuera de ventana</news:title></url>"
        "</urlset>"
    )
    entradas = sitemap.parse_sitemap("https://a.com/sitemap.xml", client=_Cliente(xml))
    urls = [e["url"] for e in entradas]
    assert "https://a.com/1" in urls
    assert "https://a.com/2" not in urls


def test_parse_sitemap_news_title_sin_abrir():
    xml = (
        "<urlset xmlns:news='http://www.google.com/schemas/sitemap-news/0.9'>"
        "<url><loc>https://a.com/n</loc><news:publication_date>2026-03-01T00:00:00Z</news:publication_date>"
        "<news:title>Un titular</news:title></url>"
        "</urlset>"
    )
    entradas = sitemap.parse_sitemap("https://a.com/sitemap.xml", client=_Cliente(xml))
    assert entradas[0]["titulo"] == "Un titular"
    assert entradas[0]["fecha_publicacion"]


def test_recolectar_sitemap_limite_300(monkeypatch):
    # 2000 entradas simuladas con título y fecha -> se limitan a max_articulos.
    entradas = [
        {
            "url": f"https://a.com/{i}",
            "titulo": f"Titulo {i}",
            "fecha_publicacion": f"2026-{(i % 12) + 1:02d}-01T00:00:00+00:00",
            "es_indice": False,
        }
        for i in range(2000)
    ]
    monkeypatch.setattr(sitemap, "parse_sitemap", lambda url, client=None: entradas)
    f = {
        "id": "medio_a",
        "nombre": "Medio A",
        "max_articulos": 300,
        "max_subsitemaps": 24,
        "sitemap_url": "https://a.com/sitemap.xml",
    }
    noticias, reporte = [], {"medio_a": {"ok": 0, "omitidas_por_limite": 0}}
    collect._recolectar_sitemap(f, None, noticias, reporte)
    assert len(noticias) <= 300
    assert reporte["medio_a"]["omitidas_por_limite"] == 2000 - len(noticias)
