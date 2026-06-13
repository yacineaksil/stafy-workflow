"""Chargement de la configuration depuis l'environnement / fichier .env."""

from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv non installé : on lit l'env brut
    pass


@dataclass(frozen=True)
class Config:
    api_key: str
    bookmaker_name: str
    min_value: float
    kelly_fraction: float

    @classmethod
    def from_env(cls) -> "Config":
        key = os.environ.get("APISPORTS_KEY", "").strip()
        if not key:
            raise RuntimeError(
                "APISPORTS_KEY manquante. Copie .env.example en .env et renseigne ta clé."
            )
        return cls(
            api_key=key,
            bookmaker_name=os.environ.get("BOOKMAKER_NAME", "1xBet").strip(),
            min_value=float(os.environ.get("MIN_VALUE", "0.05")),
            kelly_fraction=float(os.environ.get("KELLY_FRACTION", "0.25")),
        )
