"""Punto 8: el User-Agent nunca se disfraza de navegador."""
from __future__ import annotations

import config.settings as S

_BROWSERS = ["Mozilla", "Chrome", "Safari", "AppleWebKit", "Firefox", "MSIE", "Edg/"]


def test_user_agent_identificado_no_navegador():
    assert S.USER_AGENT.startswith("FARO/")
    for b in _BROWSERS:
        assert b not in S.USER_AGENT


def test_fuentes_sin_user_agent_de_navegador():
    from faro.loaders import load_fuentes

    for f in load_fuentes():
        ua = f.get("user_agent") or ""
        for b in _BROWSERS:
            assert b not in ua
