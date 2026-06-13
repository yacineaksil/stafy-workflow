"""Extraction des cotes du bookmaker cible (1xBet) depuis la réponse API-Sports.

Les structures v3 (foot) et v1 (baseball/basket) partagent la forme :
    response[].bookmakers[].bets[].values[] = {"value": "...", "odd": "..."}
On cible un bookmaker par nom et un marché (bet) par son libellé.
"""

from __future__ import annotations

from typing import Optional

# Libellés du marché "vainqueur" selon le sport (API-Sports).
MATCH_WINNER_BETS = {
    "football": ["Match Winner", "1X2", "Full Time Result"],
    "baseball": ["Home/Away", "Money Line", "Moneyline"],
    "basketball": ["Home/Away", "Money Line", "Moneyline", "Winner"],
}


def _to_float(odd: object) -> Optional[float]:
    try:
        return float(odd)
    except (TypeError, ValueError):
        return None


def extract_match_winner_odds(
    odds_response: list[dict],
    sport: str,
    bookmaker_name: str,
) -> dict[str, float]:
    """Renvoie {issue: cote} pour le bookmaker et le marché vainqueur du sport.

    issue ∈ {"Home","Draw","Away"} pour matcher les clés des modèles.
    Renvoie {} si le bookmaker ou le marché est introuvable.
    """
    wanted_bets = [b.lower() for b in MATCH_WINNER_BETS.get(sport, [])]
    target_book = bookmaker_name.lower().strip()

    for item in odds_response:
        for book in item.get("bookmakers", []):
            if str(book.get("name", "")).lower().strip() != target_book:
                continue
            for bet in book.get("bets", []):
                if str(bet.get("name", "")).lower().strip() not in wanted_bets:
                    continue
                result: dict[str, float] = {}
                for v in bet.get("values", []):
                    label = str(v.get("value", "")).strip()
                    odd = _to_float(v.get("odd"))
                    if odd is None:
                        continue
                    key = _normalize_outcome(label)
                    if key:
                        result[key] = odd
                if result:
                    return result
    return {}


def _normalize_outcome(label: str) -> Optional[str]:
    low = label.lower()
    if low in ("home", "1"):
        return "Home"
    if low in ("draw", "x", "n"):
        return "Draw"
    if low in ("away", "2"):
        return "Away"
    return None


def list_available_bookmakers(odds_response: list[dict]) -> list[str]:
    """Diagnostic : liste les bookmakers présents dans la réponse."""
    names: set[str] = set()
    for item in odds_response:
        for book in item.get("bookmakers", []):
            n = book.get("name")
            if n:
                names.add(str(n))
    return sorted(names)
