"""Modèle football : Poisson bivarié avec correction Dixon-Coles.

On estime un nombre de buts attendu pour chaque équipe (lambda) à partir des
moyennes de buts marqués/encaissés par lieu (domicile/extérieur), puis on
construit la grille des scores pour en déduire P(1), P(N), P(2), et les marchés
dérivés (over/under 2.5, BTTS).

C'est l'approche de référence pour le foot : robuste, interprétable, et qui bat
en pratique des modèles plus lourds mal calibrés. Le rho de Dixon-Coles corrige
la dépendance sur les scores faibles (0-0, 1-0, 0-1, 1-1) que le Poisson pur
sous-estime.
"""

from __future__ import annotations

import math
from typing import Optional

MAX_GOALS = 10
DEFAULT_RHO = -0.10  # corrélation Dixon-Coles typique pour les scores faibles


def _poisson_pmf(k: int, lam: float) -> float:
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * lam ** k / math.factorial(k)


def _dc_tau(x: int, y: int, lam: float, mu: float, rho: float) -> float:
    """Facteur de correction Dixon-Coles sur les cellules de score faible."""
    if x == 0 and y == 0:
        return 1.0 - lam * mu * rho
    if x == 0 and y == 1:
        return 1.0 + lam * rho
    if x == 1 and y == 0:
        return 1.0 + mu * rho
    if x == 1 and y == 1:
        return 1.0 - rho
    return 1.0


def score_matrix(lam_home: float, lam_away: float, rho: float = DEFAULT_RHO) -> list[list[float]]:
    matrix = [[0.0] * (MAX_GOALS + 1) for _ in range(MAX_GOALS + 1)]
    total = 0.0
    for i in range(MAX_GOALS + 1):
        for j in range(MAX_GOALS + 1):
            p = _poisson_pmf(i, lam_home) * _poisson_pmf(j, lam_away)
            p *= _dc_tau(i, j, lam_home, lam_away, rho)
            p = max(p, 0.0)
            matrix[i][j] = p
            total += p
    if total > 0:  # renormalisation après troncature + correction DC
        for i in range(MAX_GOALS + 1):
            for j in range(MAX_GOALS + 1):
                matrix[i][j] /= total
    return matrix


def probabilities(lam_home: float, lam_away: float, rho: float = DEFAULT_RHO) -> dict[str, float]:
    m = score_matrix(lam_home, lam_away, rho)
    p_home = p_draw = p_away = 0.0
    p_over25 = p_btts = 0.0
    for i in range(MAX_GOALS + 1):
        for j in range(MAX_GOALS + 1):
            p = m[i][j]
            if i > j:
                p_home += p
            elif i == j:
                p_draw += p
            else:
                p_away += p
            if i + j >= 3:
                p_over25 += p
            if i >= 1 and j >= 1:
                p_btts += p
    return {
        "Home": p_home,
        "Draw": p_draw,
        "Away": p_away,
        "Over 2.5": p_over25,
        "Under 2.5": 1.0 - p_over25,
        "BTTS Yes": p_btts,
        "BTTS No": 1.0 - p_btts,
    }


def _avg(node: dict, *path, default: float = 1.0) -> float:
    cur = node
    for key in path:
        if not isinstance(cur, dict) or cur.get(key) is None:
            return default
        cur = cur[key]
    try:
        return float(cur)
    except (TypeError, ValueError):
        return default


def expected_goals(home_stats: dict, away_stats: dict) -> tuple[float, float]:
    """Lambda attendus à partir des stats de saison API-Sports /teams/statistics.

    Heuristique sans normalisation de ligue (suffisante et stable) :
      lambda_home = moyenne(buts marqués domicile par home, buts encaissés ext par away)
      lambda_away = moyenne(buts marqués ext par away,     buts encaissés dom par home)
    """
    hg_for = _avg(home_stats, "goals", "for", "average", "home")
    ag_against = _avg(away_stats, "goals", "against", "average", "away")
    ag_for = _avg(away_stats, "goals", "for", "average", "away")
    hg_against = _avg(home_stats, "goals", "against", "average", "home")
    lam_home = max(0.05, (hg_for + ag_against) / 2.0)
    lam_away = max(0.05, (ag_for + hg_against) / 2.0)
    return lam_home, lam_away


def model_from_stats(home_stats: Optional[dict], away_stats: Optional[dict]) -> dict[str, float]:
    if not home_stats or not away_stats:
        raise ValueError("Stats d'équipe manquantes pour estimer les buts attendus.")
    lam_home, lam_away = expected_goals(home_stats, away_stats)
    return probabilities(lam_home, lam_away)
