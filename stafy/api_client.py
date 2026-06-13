"""Client minimal et défensif pour les APIs API-Sports (foot, baseball, basket).

La même clé fonctionne sur les trois hôtes. Les structures de réponse sont
proches mais pas identiques entre v3 (football) et v1 (baseball/basketball) ;
le parsing des cotes est donc isolé dans des helpers dédiés.

NOTE : depuis le sandbox Claude Code web, les hôtes api-sports.io sont bloqués
par la politique réseau. Lance ce code sur ta machine, ou ajoute les hôtes à
l'allowlist d'egress de l'environnement.
"""

from __future__ import annotations

import time
from typing import Any, Optional

import requests

HOSTS = {
    "football": "https://v3.football.api-sports.io",
    "baseball": "https://v1.baseball.api-sports.io",
    "basketball": "https://v1.basketball.api-sports.io",
}


class ApiSportsError(RuntimeError):
    pass


class ApiSportsClient:
    def __init__(self, api_key: str, timeout: int = 20, max_retries: int = 3):
        if not api_key:
            raise ApiSportsError("Clé API vide.")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({"x-apisports-key": api_key})

    def _get(self, sport: str, path: str, params: dict[str, Any]) -> list[dict]:
        if sport not in HOSTS:
            raise ApiSportsError(f"Sport inconnu : {sport}")
        url = f"{HOSTS[sport]}/{path.lstrip('/')}"
        last_err: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout)
                resp.raise_for_status()
                payload = resp.json()
                errors = payload.get("errors")
                # API-Sports renvoie parfois errors={} (ok) ou une liste/dict non vide.
                if errors and (isinstance(errors, dict) and errors or isinstance(errors, list)):
                    raise ApiSportsError(f"Erreur API ({sport}/{path}) : {errors}")
                return payload.get("response", []) or []
            except (requests.RequestException, ValueError) as exc:
                last_err = exc
                time.sleep(2 ** attempt)
        raise ApiSportsError(f"Echec requête {url} après {self.max_retries} essais : {last_err}")

    # ---- Endpoints génériques -------------------------------------------------

    def fixture(self, sport: str, match_id: int) -> Optional[dict]:
        """Récupère un match. 'fixtures' pour le foot, 'games' pour baseball/basket."""
        path = "fixtures" if sport == "football" else "games"
        param = "id"
        res = self._get(sport, path, {param: match_id})
        return res[0] if res else None

    def odds(self, sport: str, match_id: int) -> list[dict]:
        """Cotes d'un match. Param 'fixture' pour le foot, 'game' pour les autres."""
        param = "fixture" if sport == "football" else "game"
        return self._get(sport, "odds", {param: match_id})

    def team_statistics(self, league: int, season: int, team: int) -> Optional[dict]:
        """Stats de saison d'une équipe de foot (buts marqués/encaissés par lieu)."""
        res = self._get("football", "teams/statistics",
                        {"league": league, "season": season, "team": team})
        return res if isinstance(res, dict) else (res[0] if res else None)

    def standings(self, sport: str, league: int, season: int) -> list[dict]:
        """Classements (baseball/basket) : sert de base aux win % pour log5."""
        return self._get(sport, "standings", {"league": league, "season": season})
