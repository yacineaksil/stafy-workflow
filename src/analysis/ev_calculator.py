"""
Calcul de l'Expected Value (EV) et détection des paris à valeur positive.
"""

from dataclasses import dataclass
from typing import Optional
from config import Config


@dataclass
class BetOpportunity:
    selection: str       # "home" | "draw" | "away"
    label: str           # ex: "PSG (domicile)"
    our_prob: float      # probabilité calculée par nos modèles
    bookmaker_odd: float # cote décimale proposée
    implied_prob: float  # probabilité implicite de la cote (sans marge)
    ev: float            # Expected Value (ex: 0.08 = +8%)
    is_value: bool       # True si EV > seuil config
    bookmaker: str


def remove_margin(odds: list[float]) -> list[float]:
    """Supprime la marge bookmaker pour obtenir les probabilités réelles implicites."""
    if not odds or 0 in odds:
        return odds
    total_implied = sum(1 / o for o in odds)
    return [1 / (o * total_implied) for o in odds]


def calculate_ev(our_prob: float, bookmaker_odd: float) -> float:
    """EV = prob_modèle * cote - 1"""
    return our_prob * bookmaker_odd - 1.0


def find_value_bets(
    probs: dict,          # {"home": float, "draw": float, "away": float}
    odds: dict,           # {"home": float, "draw": float, "away": float, "bookmaker": str}
    labels: dict,         # {"home": "PSG", "away": "Lyon"}
    min_odd: float = 1.30,
    max_odd: float = 8.0,
) -> list[BetOpportunity]:
    """
    Retourne la liste des paris à valeur positive pour un match.

    Seuls les paris avec EV > MIN_EV_THRESHOLD et dans la plage de cotes
    acceptable sont retournés.
    """
    if not odds:
        return []

    bm = odds.get("bookmaker", "unknown")
    raw_odds = [odds.get(k, 0) for k in ("home", "draw", "away") if odds.get(k, 0) > 0]
    fair_probs = remove_margin(raw_odds) if len(raw_odds) >= 2 else [None, None, None]

    opportunities = []
    selections = [
        ("home",  probs.get("home", 0), odds.get("home", 0),  labels.get("home", "Domicile")),
        ("draw",  probs.get("draw", 0), odds.get("draw", 0),  "Match nul"),
        ("away",  probs.get("away", 0), odds.get("away", 0),  labels.get("away", "Extérieur")),
    ]

    for sel, our_p, odd, label in selections:
        if odd <= 0 or our_p <= 0:
            continue
        if odd < min_odd or odd > max_odd:
            continue

        ev = calculate_ev(our_p, odd)
        implied = 1.0 / odd

        opportunities.append(BetOpportunity(
            selection=sel,
            label=label,
            our_prob=round(our_p, 4),
            bookmaker_odd=round(odd, 2),
            implied_prob=round(implied, 4),
            ev=round(ev, 4),
            is_value=ev >= Config.MIN_EV_THRESHOLD,
            bookmaker=bm,
        ))

    return sorted(opportunities, key=lambda x: x.ev, reverse=True)


def generate_demo_odds(home_prob: float, away_prob: float, draw_prob: float = 0.0) -> dict:
    """
    Génère des cotes de démo légèrement décalées par rapport à nos probabilités
    pour simuler la marge bookmaker et quelques opportunités de valeur.
    """
    import random
    random.seed(42)

    def prob_to_odd_with_margin(p: float, bias: float = 0.0) -> float:
        # Marge 5% + léger biais aléatoire
        p_biased = min(0.95, max(0.05, p * 0.95 + bias))
        return round(1 / p_biased, 2)

    # Introduire un biais sur certains matchs pour créer de la valeur
    biases = [random.uniform(-0.03, 0.03) for _ in range(3)]

    odds = {
        "home": prob_to_odd_with_margin(home_prob, biases[0]),
        "bookmaker": "1xbet (demo)",
    }
    if draw_prob > 0:
        odds["draw"] = prob_to_odd_with_margin(draw_prob, biases[1])
    odds["away"] = prob_to_odd_with_margin(away_prob, biases[2])
    return odds
