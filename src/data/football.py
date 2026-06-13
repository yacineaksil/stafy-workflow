"""
Données football via API-Football (https://api-sports.io).
Free tier : 100 req/jour. Clé : variable d'env API_FOOTBALL_KEY.
Fallback sur des données de démo si pas de clé.
"""

from datetime import date
from config import Config
from src.data.fetcher import fetch

_HEADERS = {
    "x-rapidapi-key": Config.API_FOOTBALL_KEY,
    "x-rapidapi-host": "v3.football.api-sports.io",
}

# Ligues suivies par défaut (id API-Football)
DEFAULT_LEAGUES = {
    "Ligue 1": 61,
    "Premier League": 39,
    "La Liga": 140,
    "Bundesliga": 78,
    "Serie A": 135,
    "Champions League": 2,
}


def get_fixtures(target_date: date = None, league_id: int = None) -> list[dict]:
    """Retourne les matchs du jour avec stats de base."""
    if not Config.API_FOOTBALL_KEY:
        return _demo_fixtures(target_date)

    d = target_date or date.today()
    params = {"date": str(d)}
    if league_id:
        params["league"] = league_id
        params["season"] = d.year

    data = fetch(
        f"{Config.API_FOOTBALL_BASE}/fixtures",
        headers=_HEADERS,
        params=params,
        cache_key=f"football_fixtures_{d}_{league_id}",
    )
    return data.get("response", [])


def get_team_stats(team_id: int, league_id: int, season: int) -> dict:
    """Statistiques d'une équipe sur la saison (buts, forme, xG si dispo)."""
    if not Config.API_FOOTBALL_KEY:
        return {}

    data = fetch(
        f"{Config.API_FOOTBALL_BASE}/teams/statistics",
        headers=_HEADERS,
        params={"team": team_id, "league": league_id, "season": season},
        cache_key=f"football_stats_{team_id}_{league_id}_{season}",
    )
    return data.get("response", {})


def build_team_strengths(fixtures_history: list[dict]) -> dict[int, dict]:
    """
    Calcule attack/defense strength pour le modèle de Poisson.
    Retourne {team_id: {attack: float, defense: float, played: int}}
    """
    goals_for: dict[int, list] = {}
    goals_against: dict[int, list] = {}

    for f in fixtures_history:
        goals = f.get("goals", {})
        teams = f.get("teams", {})
        home_id = teams.get("home", {}).get("id")
        away_id = teams.get("away", {}).get("id")
        gf = goals.get("home")
        ga = goals.get("away")
        if None in (home_id, away_id, gf, ga):
            continue
        goals_for.setdefault(home_id, []).append(gf)
        goals_against.setdefault(home_id, []).append(ga)
        goals_for.setdefault(away_id, []).append(ga)
        goals_against.setdefault(away_id, []).append(gf)

    all_gf = [g for gs in goals_for.values() for g in gs]
    league_avg = sum(all_gf) / len(all_gf) if all_gf else 1.3

    result = {}
    for tid in set(goals_for) | set(goals_against):
        gf_list = goals_for.get(tid, [1.3])
        ga_list = goals_against.get(tid, [1.3])
        result[tid] = {
            "attack": (sum(gf_list) / len(gf_list)) / league_avg,
            "defense": (sum(ga_list) / len(ga_list)) / league_avg,
            "played": len(gf_list),
        }
    return result


# --- Demo data (utilisé sans clé API) ---

def _demo_fixtures(target_date) -> list[dict]:
    d = str(target_date or date.today())
    return [
        {
            "fixture": {"id": 1001, "date": f"{d}T20:00:00+00:00"},
            "league": {"id": 61, "name": "Ligue 1", "country": "France"},
            "teams": {
                "home": {"id": 85, "name": "Paris Saint-Germain"},
                "away": {"id": 80, "name": "Lyon"},
            },
            "goals": {"home": None, "away": None},
            "_demo": True,
            "_stats": {
                "home": {"attack": 1.82, "defense": 0.61, "form": "WWWDW"},
                "away": {"attack": 1.05, "defense": 1.12, "form": "WDLWL"},
            },
        },
        {
            "fixture": {"id": 1002, "date": f"{d}T17:00:00+00:00"},
            "league": {"id": 39, "name": "Premier League", "country": "England"},
            "teams": {
                "home": {"id": 40, "name": "Liverpool"},
                "away": {"id": 42, "name": "Arsenal"},
            },
            "goals": {"home": None, "away": None},
            "_demo": True,
            "_stats": {
                "home": {"attack": 1.65, "defense": 0.78, "form": "WWWWL"},
                "away": {"attack": 1.45, "defense": 0.85, "form": "WDWWW"},
            },
        },
        {
            "fixture": {"id": 1003, "date": f"{d}T19:45:00+00:00"},
            "league": {"id": 140, "name": "La Liga", "country": "Spain"},
            "teams": {
                "home": {"id": 541, "name": "Real Madrid"},
                "away": {"id": 529, "name": "Barcelona"},
            },
            "goals": {"home": None, "away": None},
            "_demo": True,
            "_stats": {
                "home": {"attack": 1.75, "defense": 0.70, "form": "WWDWW"},
                "away": {"attack": 1.80, "defense": 0.75, "form": "WWWWW"},
            },
        },
    ]
