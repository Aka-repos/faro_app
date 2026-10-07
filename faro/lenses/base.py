"""Lente base: carga la configuración YAML de un lente."""

from __future__ import annotations

from dataclasses import dataclass, field

from faro.loaders import load_lente


@dataclass
class Lente:
    id: str
    nombre: str = ""
    pesos: dict = field(default_factory=dict)
    rangos: dict = field(default_factory=dict)
    tipos_afirmacion: list = field(default_factory=list)
    frases_prohibidas: list = field(default_factory=list)
    plantillas: dict = field(default_factory=dict)
    limites: dict = field(default_factory=dict)

    @classmethod
    def cargar(cls, lente_id: str) -> Lente:
        cfg = load_lente(lente_id)
        return cls(
            id=lente_id,
            nombre=cfg.get("nombre", lente_id),
            pesos=cfg.get("pesos", {}),
            rangos=cfg.get("rangos", {}),
            tipos_afirmacion=cfg.get("tipos_afirmacion", []),
            frases_prohibidas=cfg.get("frases_prohibidas", []),
            plantillas=cfg.get("plantillas", {}),
            limites=cfg.get("limites", {}),
        )

    def tipos_permitidos(self) -> list[str]:
        return self.tipos_afirmacion
