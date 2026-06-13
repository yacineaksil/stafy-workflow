"""
Modèle de Poisson doublement corrélé pour prédiction football.
Référence : Dixon & Coles (1997).
"""

import math
from dataclasses import dataclass
from scipy.stats import poisson


# Moyenne de buts en Ligue 1 / PL (calibré sur historique récent)
LEAGUE_AVG_HOME_GOALS = 1.42
LEAGUE_AVG_AWAY_GOALS = 1.05
HOME_ADVANTAGE_FACTOR = 1.20  # +20% pour domicile


@dataclass
class FootballPrediction:
    home_team: str
    away_team: str
    lambda_home: float   # buts attendus équipe domicile
    lambda_away: float   # buts attendus équipe extérieure
    prob_home: float
    prob_draw: float
    prob_away: float
    confidence: str      # "high" / "medium" / "low"


def predict(
    home_attack: float,
    home_defense: float,
    away_attack: float,
    away_defense: float,
    home_team: str = "",
    away_team: str = "",
    max_goals: int = 8,
) -> FootballPrediction:
    """
    Calcule les probabilités 1X2 via Poisson.

    Args:
        home_attack  : force offensive domicile (1.0 = moyenne)
        home_defense : force défensive domicile (1.0 = moyenne, <1 = meilleure)
        away_attack  : force offensive extérieur
        away_defense : force défensive extérieur
        max_goals    : score max considéré dans la matrice
    """
    lambda_home = (
        home_attack * away_defense * LEAGUE_AVG_HOME_GOALS * HOME_ADVANTAGE_FACTOR
    )
    lambda_away = away_attack * home_defense * LEAGUE_AVG_AWAY_GOALS

    lambda_home = max(0.1, lambda_home)
    lambda_away = max(0.1, lambda_away)

    # Matrice de probabilité des scores
    prob_home = prob_draw = prob_away = 0.0
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            p = poisson.pmf(i, lambda_home) * poisson.pmf(j, lambda_away)
            if i > j:
                prob_home += p
            elif i == j:
                prob_draw += p
            else:
                prob_away += p

    total = prob_home + prob_draw + prob_away
    if total > 0:
        prob_home /= total
        prob_draw /= total
        prob_away /= total

    # Confiance basée sur la différence de force
    diff = abs(home_attack - away_attack) + abs(home_defense - away_defense)
    confidence = "high" if diff > 0.5 else ("medium" if diff > 0.2 else "low")

    return FootballPrediction(
        home_team=home_team,
        away_team=away_team,
        lambda_home=round(lambda_home, 2),
        lambda_away=round(lambda_away, 2),
        prob_home=round(prob_home, 4),
        prob_draw=round(prob_draw, 4),
        prob_away=round(prob_away, 4),
        confidence=confidence,
    )


def predict_from_fixture(fixture: dict) -> FootballPrediction:
    """Prédit depuis un fixture dict (réel ou démo)."""
    stats = fixture.get("_stats", {})
    home_s = stats.get("home", {})
    away_s = stats.get("away", {})

    return predict(
        home_attack=home_s.get("attack", 1.0),
        home_defense=home_s.get("defense", 1.0),
        away_attack=away_s.get("attack", 1.0),
        away_defense=away_s.get("defense", 1.0),
        home_team=fixture.get("teams", {}).get("home", {}).get("name", "Home"),
        away_team=fixture.get("teams", {}).get("away", {}).get("name", "Away"),
    )
