"""
Données NBA via balldontlie API v1 (gratuit, sans clé).
https://www.balldontlie.io/
"""

from datetime import date
from config import Config
from src.data.fetcher import fetch


def get_games(target_date: date = None) -> list[dict]:
    """Matchs NBA du jour."""
    d = target_date or date.today()
    try:
        data = fetch(
            f"{Config.BALLDONTLIE_BASE}/games",
            params={"dates[]": str(d), "per_page": 50},
            cache_key=f"nba_games_{d}",
        )
        games = data.get("data", [])
        return games if games else _demo_games(d)
    except Exception:
        return _demo_games(d)


def get_team_season_averages(team_id: int, season: int = None) -> dict:
    """Moyennes par match d'une équipe (points, assists, rebonds...)."""
    s = season or (date.today().year if date.today().month > 9 else date.today().year - 1)
    try:
        data = fetch(
            f"{Config.BALLDONTLIE_BASE}/season_averages",
            params={"season": s, "team_ids[]": team_id},
            cache_key=f"nba_avg_{team_id}_{s}",
        )
        return data.get("data", [{}])[0] if data.get("data") else {}
    except Exception:
        return {}


def extract_game_info(game: dict) -> dict:
    """Normalise un match NBA brut."""
    home = game.get("home_team", {})
    away = game.get("visitor_team", {})
    return {
        "id": game.get("id"),
        "date": game.get("date", ""),
        "home": {
            "id": home.get("id"),
            "name": home.get("full_name", home.get("name", "")),
            "abbreviation": home.get("abbreviation", ""),
        },
        "away": {
            "id": away.get("id"),
            "name": away.get("full_name", away.get("name", "")),
            "abbreviation": away.get("abbreviation", ""),
        },
        "status": game.get("status", ""),
        "period": game.get("period", 0),
        "_demo": game.get("_demo", False),
        "_stats": game.get("_stats", {}),
    }


# --- Demo data ---

def _demo_games(d: date) -> list[dict]:
    return [
        {
            "id": 3001,
            "date": str(d),
            "_demo": True,
            "_stats": {
                "home": {
                    "elo": 1612, "ortg": 118.5, "drtg": 110.2, "pace": 101.3,
                    "efg_pct": 0.562, "tov_pct": 0.132, "oreb_pct": 0.298, "ft_rate": 0.231,
                    "wins": 45, "losses": 17, "rest_days": 1,
                },
                "away": {
                    "elo": 1588, "ortg": 114.1, "drtg": 112.8, "pace": 98.7,
                    "efg_pct": 0.538, "tov_pct": 0.148, "oreb_pct": 0.271, "ft_rate": 0.198,
                    "wins": 40, "losses": 22, "rest_days": 0,
                },
            },
            "home_team": {"id": 14, "full_name": "Golden State Warriors", "abbreviation": "GSW"},
            "visitor_team": {"id": 2, "full_name": "Boston Celtics", "abbreviation": "BOS"},
            "status": "scheduled",
            "period": 0,
        },
        {
            "id": 3002,
            "date": str(d),
            "_demo": True,
            "_stats": {
                "home": {
                    "elo": 1635, "ortg": 120.2, "drtg": 108.5, "pace": 103.1,
                    "efg_pct": 0.581, "tov_pct": 0.121, "oreb_pct": 0.312, "ft_rate": 0.245,
                    "wins": 50, "losses": 12, "rest_days": 2,
                },
                "away": {
                    "elo": 1570, "ortg": 111.8, "drtg": 115.3, "pace": 96.5,
                    "efg_pct": 0.521, "tov_pct": 0.157, "oreb_pct": 0.255, "ft_rate": 0.188,
                    "wins": 35, "losses": 27, "rest_days": 1,
                },
            },
            "home_team": {"id": 20, "full_name": "Oklahoma City Thunder", "abbreviation": "OKC"},
            "visitor_team": {"id": 27, "full_name": "Portland Trail Blazers", "abbreviation": "POR"},
            "status": "scheduled",
            "period": 0,
        },
    ]
