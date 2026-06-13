"""Modèle MLB : log5 sur les win % d'équipe + avantage du terrain.

Le baseball est le sport le plus 'modélisable' (gros volume de matchs, données
riches). API-Sports baseball expose surtout les win % via /standings ; on
applique donc la formule log5 (Bill James) qui combine deux win % en une proba
de victoire d'une équipe contre l'autre, puis on ajuste l'avantage domicile.

LIMITE ASSUMÉE : le facteur le plus prédictif au baseball est le lanceur
partant, non disponible proprement dans cette API. Ce modèle est donc une base
solide mais incomplète — à enrichir avec une source pitcher (Baseball Savant)
pour un vrai edge.
"""

from __future__ import annotations

# Avantage du terrain MLB : ~54% historiquement pour le domicile à forces égales.
HOME_FIELD_WINP = 0.54


def log5(p_a: float, p_b: float) -> float:
    """Proba que A batte B, à partir de leurs win % respectifs (terrain neutre)."""
    p_a = min(max(p_a, 1e-6), 1 - 1e-6)
    p_b = min(max(p_b, 1e-6), 1 - 1e-6)
    num = p_a - p_a * p_b
    den = p_a + p_b - 2 * p_a * p_b
    if den <= 0:
        return 0.5
    return num / den


def _apply_home_advantage(p_home_neutral: float) -> float:
    """Décale la proba neutre vers le domicile selon HOME_FIELD_WINP."""
    shift = HOME_FIELD_WINP - 0.5
    return min(max(p_home_neutral + shift, 1e-6), 1 - 1e-6)


def probabilities(home_winp: float, away_winp: float) -> dict[str, float]:
    p_home_neutral = log5(home_winp, away_winp)
    p_home = _apply_home_advantage(p_home_neutral)
    return {"Home": p_home, "Away": 1.0 - p_home}


def model_from_winpct(home_winp: float, away_winp: float) -> dict[str, float]:
    return probabilities(home_winp, away_winp)
