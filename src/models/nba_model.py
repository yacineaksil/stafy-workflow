"""
Modèle NBA : Elo + Four Factors (Dean Oliver).
Référence : 538 Elo, Basketball-Reference Four Factors.
"""

import math
from dataclasses import dataclass


ELO_K = 20
HOME_COURT_ELO = 75        # ~+75 points Elo pour le domicile (équiv. ~3 pts)
BACK_TO_BACK_PENALTY = 30  # pénalité Elo pour back-to-back (0 repos)
FOUR_FACTORS_WEIGHT = 0.35  # poids des Four Factors vs Elo pur


@dataclass
class NBAPrediction:
    home_team: str
    away_team: str
    prob_home: float
    prob_away: float
    elo_home: float
    elo_away: float
    elo_diff: float           # elo_home - elo_away (incl. home court)
    four_factors_score: float # >0 = avantage domicile
    confidence: str


def elo_win_prob(elo_diff: float) -> float:
    """Probabilité de victoire basée sur différence Elo."""
    return 1.0 / (1.0 + 10.0 ** (-elo_diff / 400.0))


def four_factors_score(home: dict, away: dict) -> float:
    """
    Score des Four Factors (positif = avantage domicile).
    Facteurs : eFG%, TOV%, OREB%, FT Rate
    Pondération Dean Oliver : 40% / 25% / 20% / 15%
    """
    w = [0.40, 0.25, 0.20, 0.15]

    # eFG% (higher = better offensively)
    efg = (home.get("efg_pct", 0.5) - away.get("efg_pct", 0.5)) * w[0]

    # TOV% (lower = better → invert)
    tov = (away.get("tov_pct", 0.14) - home.get("tov_pct", 0.14)) * w[1]

    # OREB% (higher = better)
    oreb = (home.get("oreb_pct", 0.27) - away.get("oreb_pct", 0.27)) * w[2]

    # FT Rate (higher = better)
    ftr = (home.get("ft_rate", 0.22) - away.get("ft_rate", 0.22)) * w[3]

    return efg + tov + oreb + ftr


def predict(
    home_stats: dict,
    away_stats: dict,
    home_team: str = "",
    away_team: str = "",
) -> NBAPrediction:
    """
    Prédit le match NBA.

    Stats attendues :
    {elo, ortg, drtg, pace, efg_pct, tov_pct, oreb_pct, ft_rate, wins, losses, rest_days}
    """
    elo_h = home_stats.get("elo", 1500)
    elo_a = away_stats.get("elo", 1500)

    # Pénalité back-to-back
    rest_h = home_stats.get("rest_days", 1)
    rest_a = away_stats.get("rest_days", 1)
    elo_h -= BACK_TO_BACK_PENALTY if rest_h == 0 else 0
    elo_a -= BACK_TO_BACK_PENALTY if rest_a == 0 else 0

    # Elo avec avantage domicile
    elo_diff = (elo_h + HOME_COURT_ELO) - elo_a
    elo_prob_home = elo_win_prob(elo_diff)

    # Four Factors
    ff_score = four_factors_score(home_stats, away_stats)
    # Convertir le score FF en probabilité additionnelle (centré sur 0.5)
    ff_prob_home = min(0.85, max(0.15, 0.5 + ff_score * 2.5))

    # Combinaison pondérée
    prob_home = (1 - FOUR_FACTORS_WEIGHT) * elo_prob_home + FOUR_FACTORS_WEIGHT * ff_prob_home
    prob_home = min(0.88, max(0.12, prob_home))
    prob_away = 1.0 - prob_home

    # Confiance
    wins_h = home_stats.get("wins", 0)
    wins_a = away_stats.get("wins", 0)
    games = min(wins_h + home_stats.get("losses", 0), wins_a + away_stats.get("losses", 0))
    confidence = "high" if games > 40 else ("medium" if games > 20 else "low")

    return NBAPrediction(
        home_team=home_team,
        away_team=away_team,
        prob_home=round(prob_home, 4),
        prob_away=round(prob_away, 4),
        elo_home=elo_h,
        elo_away=elo_a,
        elo_diff=round(elo_diff, 1),
        four_factors_score=round(ff_score, 4),
        confidence=confidence,
    )


def predict_from_game(game: dict) -> NBAPrediction:
    """Prédit depuis un game dict (réel ou démo)."""
    stats = game.get("_stats", {})
    home_name = game.get("home_team", {}).get("full_name", "Home")
    away_name = game.get("visitor_team", {}).get("full_name", "Away")

    return predict(
        home_stats=stats.get("home", {}),
        away_stats=stats.get("away", {}),
        home_team=home_name,
        away_team=away_name,
    )
