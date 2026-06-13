"""
Données MLB via l'API officielle MLB Stats (gratuit, sans clé).
https://statsapi.mlb.com/api/v1/
"""

from datetime import date
from config import Config
from src.data.fetcher import fetch


def get_schedule(target_date: date = None) -> list[dict]:
    """Matchs MLB du jour."""
    d = target_date or date.today()
    params = {
        "sportId": 1,
        "date": d.strftime("%m/%d/%Y"),
        "hydrate": "team,linescore,pitchers,stats",
    }
    try:
        data = fetch(
            f"{Config.MLB_STATS_BASE}/schedule",
            params=params,
            cache_key=f"mlb_schedule_{d}",
        )
        games = []
        for game_date in data.get("dates", []):
            games.extend(game_date.get("games", []))
        return games if games else _demo_games(d)
    except Exception:
        return _demo_games(d)


def get_team_season_stats(team_id: int, season: int = None) -> dict:
    """Stats d'une équipe sur la saison (ERA, runs, batting avg...)."""
    s = season or date.today().year
    try:
        data = fetch(
            f"{Config.MLB_STATS_BASE}/teams/{team_id}/stats",
            params={"stats": "season", "season": s, "sportId": 1},
            cache_key=f"mlb_team_stats_{team_id}_{s}",
        )
        splits = data.get("stats", [{}])[0].get("splits", [{}])
        return splits[0].get("stat", {}) if splits else {}
    except Exception:
        return {}


def get_pitcher_stats(pitcher_id: int, season: int = None) -> dict:
    """Stats du lanceur partant (ERA, WHIP, K/9...)."""
    s = season or date.today().year
    try:
        data = fetch(
            f"{Config.MLB_STATS_BASE}/people/{pitcher_id}/stats",
            params={"stats": "season", "season": s, "group": "pitching"},
            cache_key=f"mlb_pitcher_{pitcher_id}_{s}",
        )
        splits = data.get("stats", [{}])[0].get("splits", [{}])
        return splits[0].get("stat", {}) if splits else {}
    except Exception:
        return {}


def extract_game_info(game: dict) -> dict:
    """Normalise un match MLB brut en dict simple."""
    teams = game.get("teams", {})
    home = teams.get("home", {})
    away = teams.get("away", {})
    return {
        "id": game.get("gamePk"),
        "date": game.get("gameDate", ""),
        "home": {
            "id": home.get("team", {}).get("id"),
            "name": home.get("team", {}).get("name", ""),
            "wins": home.get("leagueRecord", {}).get("wins", 0),
            "losses": home.get("leagueRecord", {}).get("losses", 0),
        },
        "away": {
            "id": away.get("team", {}).get("id"),
            "name": away.get("team", {}).get("name", ""),
            "wins": away.get("leagueRecord", {}).get("wins", 0),
            "losses": away.get("leagueRecord", {}).get("losses", 0),
        },
        "status": game.get("status", {}).get("detailedState", ""),
        "_demo": game.get("_demo", False),
        "_stats": game.get("_stats", {}),
    }


# --- Demo data ---

def _demo_games(d: date) -> list[dict]:
    return [
        {
            "gamePk": 2001,
            "gameDate": f"{d}T23:10:00Z",
            "_demo": True,
            "_stats": {
                "home": {"era": 3.21, "battingAvg": 0.268, "runsScored": 312, "runsAllowed": 241, "wins": 38, "losses": 22},
                "away": {"era": 4.05, "battingAvg": 0.251, "runsScored": 280, "runsAllowed": 295, "wins": 29, "losses": 31},
                "home_pitcher": {"era": 2.85, "whip": 1.05, "strikeoutsPer9Inn": 10.2},
                "away_pitcher": {"era": 4.32, "whip": 1.28, "strikeoutsPer9Inn": 7.8},
            },
            "teams": {
                "home": {
                    "team": {"id": 147, "name": "New York Yankees"},
                    "leagueRecord": {"wins": 38, "losses": 22},
                },
                "away": {
                    "team": {"id": 111, "name": "Boston Red Sox"},
                    "leagueRecord": {"wins": 29, "losses": 31},
                },
            },
            "status": {"detailedState": "Scheduled"},
        },
        {
            "gamePk": 2002,
            "gameDate": f"{d}T00:10:00Z",
            "_demo": True,
            "_stats": {
                "home": {"era": 3.55, "battingAvg": 0.261, "runsScored": 298, "runsAllowed": 270, "wins": 35, "losses": 25},
                "away": {"era": 3.10, "battingAvg": 0.274, "runsScored": 330, "runsAllowed": 255, "wins": 40, "losses": 20},
                "home_pitcher": {"era": 3.80, "whip": 1.18, "strikeoutsPer9Inn": 9.1},
                "away_pitcher": {"era": 2.95, "whip": 1.02, "strikeoutsPer9Inn": 11.4},
            },
            "teams": {
                "home": {
                    "team": {"id": 137, "name": "San Francisco Giants"},
                    "leagueRecord": {"wins": 35, "losses": 25},
                },
                "away": {
                    "team": {"id": 119, "name": "Los Angeles Dodgers"},
                    "leagueRecord": {"wins": 40, "losses": 20},
                },
            },
            "status": {"detailedState": "Scheduled"},
        },
    ]
