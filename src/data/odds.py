"""
Récupère les cotes réelles via The Odds API (https://the-odds-api.com).
Free tier : 500 requêtes/mois — suffisant pour un usage quotidien.
Clé : variable d'env ODDS_API_KEY
"""

from datetime import date
from typing import Optional
from config import Config
from src.data.fetcher import fetch

# Mapping sport interne → identifiant Odds API
_SPORT_MAP = {
    "football": Config.ODDS_SPORTS["football"],
    "mlb": Config.ODDS_SPORTS["mlb"],
    "basketball": Config.ODDS_SPORTS["basketball"],
}


def get_odds(sport: str, target_date: Optional[date] = None) -> list[dict]:
    """
    Retourne la liste de matchs avec cotes pour le sport donné.
    Chaque élément : {home, away, commence_time, bookmakers: [{key, markets: [{outcomes}]}]}
    """
    if not Config.ODDS_API_KEY:
        return []

    sport_key = _SPORT_MAP.get(sport)
    if not sport_key:
        return []

    params = {
        "apiKey": Config.ODDS_API_KEY,
        "regions": "eu",
        "markets": "h2h",
        "oddsFormat": "decimal",
        "dateFormat": "iso",
    }
    if target_date:
        params["commenceTimeFrom"] = f"{target_date}T00:00:00Z"
        params["commenceTimeTo"] = f"{target_date}T23:59:59Z"

    url = f"{Config.ODDS_API_BASE}/sports/{sport_key}/odds"
    cache_key = f"odds_{sport}_{target_date}"
    try:
        data = fetch(url, params=params, cache_key=cache_key)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def extract_best_odds(game: dict) -> dict:
    """
    Extrait les meilleures cotes disponibles pour home/draw/away
    en priorisant 1xBet, sinon prend la meilleure cote parmi tous les bookmakers.
    Retourne : {home: float, draw: float, away: float, bookmaker: str}
    """
    bookmakers = game.get("bookmakers", [])
    if not bookmakers:
        return {}

    # Chercher 1xBet en priorité
    for priority in Config.BOOKMAKER_PRIORITY:
        for bm in bookmakers:
            if bm["key"] == priority:
                return _parse_h2h(bm, priority)

    # Sinon, meilleures cotes agrégées
    best = {"home": 0.0, "draw": 0.0, "away": 0.0, "bookmaker": "best_of_market"}
    for bm in bookmakers:
        parsed = _parse_h2h(bm, bm["key"])
        best["home"] = max(best["home"], parsed.get("home", 0))
        best["draw"] = max(best["draw"], parsed.get("draw", 0))
        best["away"] = max(best["away"], parsed.get("away", 0))
    return best


def _parse_h2h(bookmaker: dict, bm_key: str) -> dict:
    for market in bookmaker.get("markets", []):
        if market["key"] != "h2h":
            continue
        outcomes = {o["name"]: o["price"] for o in market.get("outcomes", [])}
        home_name = list(outcomes.keys())[0] if outcomes else ""
        away_name = list(outcomes.keys())[1] if len(outcomes) > 1 else ""
        return {
            "home": outcomes.get(home_name, 0),
            "draw": outcomes.get("Draw", 0),
            "away": outcomes.get(away_name, 0),
            "bookmaker": bm_key,
        }
    return {}
