"""Modèle NBA/basket : espérance de Pythagore sur points marqués/encaissés,
combinée en log5, plus avantage du terrain.

Au basket, les points pour/contre sur la saison sont très informatifs. On
convertit chaque équipe en une 'force' (win % de Pythagore), on les combine via
log5, puis on ajoute l'avantage domicile.

LIMITE ASSUMÉE : pas d'ajustement de rythme (pace) ni de blessures/repos
(back-to-back). Pour le marché des totaux (over/under), il faudrait modéliser
le pace explicitement — c'est souvent là que se cache le meilleur edge au basket.
"""

from __future__ import annotations

from .baseball import log5

# Avantage du terrain NBA : ~60% à forces égales (un peu plus marqué qu'en MLB).
HOME_COURT_WINP = 0.60
PYTHAG_EXP = 13.91  # exposant de Pythagore calibré pour le basket (Morey)


def pythagorean_winp(points_for: float, points_against: float) -> float:
    """Win % attendu d'une équipe selon ses points marqués/encaissés."""
    pf = max(points_for, 1e-6) ** PYTHAG_EXP
    pa = max(points_against, 1e-6) ** PYTHAG_EXP
    if pf + pa <= 0:
        return 0.5
    return pf / (pf + pa)


def _apply_home_advantage(p_home_neutral: float) -> float:
    shift = HOME_COURT_WINP - 0.5
    return min(max(p_home_neutral + shift, 1e-6), 1 - 1e-6)


def probabilities(
    home_pf: float, home_pa: float, away_pf: float, away_pa: float
) -> dict[str, float]:
    home_strength = pythagorean_winp(home_pf, home_pa)
    away_strength = pythagorean_winp(away_pf, away_pa)
    p_home_neutral = log5(home_strength, away_strength)
    p_home = _apply_home_advantage(p_home_neutral)
    return {"Home": p_home, "Away": 1.0 - p_home}


def model_from_points(
    home_pf: float, home_pa: float, away_pf: float, away_pa: float
) -> dict[str, float]:
    return probabilities(home_pf, home_pa, away_pf, away_pa)
