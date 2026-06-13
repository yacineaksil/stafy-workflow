"""
Modèle MLB : Pythagorean expectation + ajustement pitching.
Référence : Bill James Pythagorean formula, FanGraphs.
"""

import math
from dataclasses import dataclass


PYTHAGOREAN_EXP = 1.83   # exposant calibré pour MLB (Smyth/Patriot)
HOME_WIN_BONUS = 0.04     # +4% pour domicile en MLB
ERA_WEIGHT = 0.35         # poids du pitcher partant dans le modèle


@dataclass
class MLBPrediction:
    home_team: str
    away_team: str
    prob_home: float
    prob_away: float
    pythag_home: float     # Pythagorean win% domicile
    pythag_away: float     # Pythagorean win% extérieur
    adj_era_diff: float    # Différence ERA ajustée (>0 = avantage domicile)
    confidence: str


def pythagorean_win_pct(runs_scored: float, runs_allowed: float) -> float:
    """Pourcentage de victoires attendu selon la formule Pythagoricienne."""
    if runs_scored <= 0 or runs_allowed <= 0:
        return 0.5
    rs = runs_scored ** PYTHAGOREAN_EXP
    ra = runs_allowed ** PYTHAGOREAN_EXP
    return rs / (rs + ra)


def predict(
    home_stats: dict,
    away_stats: dict,
    home_pitcher: dict = None,
    away_pitcher: dict = None,
    home_team: str = "",
    away_team: str = "",
) -> MLBPrediction:
    """
    Prédit la victoire MLB.

    Stats attendues : {era, battingAvg, runsScored, runsAllowed, wins, losses}
    Pitcher stats   : {era, whip, strikeoutsPer9Inn}
    """
    home_runs_scored = home_stats.get("runsScored", 300)
    home_runs_allowed = home_stats.get("runsAllowed", 300)
    away_runs_scored = away_stats.get("runsScored", 300)
    away_runs_allowed = away_stats.get("runsAllowed", 300)

    pythag_home = pythagorean_win_pct(home_runs_scored, home_runs_allowed)
    pythag_away = pythagorean_win_pct(away_runs_scored, away_runs_allowed)

    # Ajustement pitching : ERA plus basse = meilleure
    home_era = (home_pitcher or home_stats).get("era", home_stats.get("era", 4.0))
    away_era = (away_pitcher or away_stats).get("era", away_stats.get("era", 4.0))
    era_diff = away_era - home_era  # positif = domicile meilleur lanceur

    # Score composite
    strength_home = pythag_home + ERA_WEIGHT * (era_diff / 10.0) + HOME_WIN_BONUS
    strength_away = pythag_away - ERA_WEIGHT * (era_diff / 10.0)

    # Convertir en probabilités normalisées
    total = strength_home + strength_away
    if total <= 0:
        prob_home = prob_away = 0.5
    else:
        prob_home = min(0.85, max(0.15, strength_home / total))
        prob_away = 1.0 - prob_home

    # Confiance : bilan de saison + différence ERA
    wins_h = home_stats.get("wins", 0) + home_stats.get("losses", 1)
    wins_a = away_stats.get("wins", 0) + away_stats.get("losses", 1)
    games_played = min(wins_h, wins_a)
    confidence = "high" if games_played > 40 else ("medium" if games_played > 20 else "low")

    return MLBPrediction(
        home_team=home_team,
        away_team=away_team,
        prob_home=round(prob_home, 4),
        prob_away=round(prob_away, 4),
        pythag_home=round(pythag_home, 4),
        pythag_away=round(pythag_away, 4),
        adj_era_diff=round(era_diff, 2),
        confidence=confidence,
    )


def predict_from_game(game: dict) -> MLBPrediction:
    """Prédit depuis un game dict (réel ou démo)."""
    stats = game.get("_stats", {})
    teams = game.get("teams", {})

    home_name = teams.get("home", {}).get("team", {}).get("name", "Home")
    away_name = teams.get("away", {}).get("team", {}).get("name", "Away")

    return predict(
        home_stats=stats.get("home", {}),
        away_stats=stats.get("away", {}),
        home_pitcher=stats.get("home_pitcher"),
        away_pitcher=stats.get("away_pitcher"),
        home_team=home_name,
        away_team=away_name,
    )
