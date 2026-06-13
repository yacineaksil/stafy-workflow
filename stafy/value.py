"""Coeur de la stratégie : probabilité implicite, marge, value et mise Kelly.

C'est ici que se joue la rentabilité. On ne parie pas sur l'issue la plus
probable, mais sur celle dont notre proba estimée dépasse la proba implicite
des cotes (after on retire la marge du book pour comparer honnêtement).
"""

from __future__ import annotations

from dataclasses import dataclass


def implied_prob(odd: float) -> float:
    """Probabilité implicite brute d'une cote décimale (marge incluse)."""
    if odd <= 1.0:
        return 0.0
    return 1.0 / odd


def remove_margin(odds: dict[str, float]) -> dict[str, float]:
    """Retire la marge du bookmaker en normalisant les probas implicites à 1.

    odds : {issue: cote décimale}. Renvoie {issue: proba 'fair' estimée du book}.
    Utile pour mesurer à quel point ta proba diffère de l'avis réel du book.
    """
    raw = {k: implied_prob(v) for k, v in odds.items()}
    total = sum(raw.values())
    if total <= 0:
        return raw
    return {k: v / total for k, v in raw.items()}


def overround(odds: dict[str, float]) -> float:
    """Marge du book (ex: 1.07 = 7% de marge)."""
    return sum(implied_prob(v) for v in odds.values())


def value(prob: float, odd: float) -> float:
    """Espérance par unité misée : prob*cote - 1. Positif => pari à valeur."""
    return prob * odd - 1.0


def kelly_fraction(prob: float, odd: float) -> float:
    """Fraction de bankroll selon Kelly (0 si pas d'edge). À multiplier ensuite
    par un facteur prudent (ex 0.25) avant de miser réellement."""
    b = odd - 1.0
    if b <= 0:
        return 0.0
    f = (prob * odd - 1.0) / b
    return max(0.0, f)


@dataclass
class BetRecommendation:
    outcome: str          # "Home" / "Draw" / "Away"
    odd: float
    model_prob: float     # ta proba estimée
    book_fair_prob: float # proba du book sans marge
    edge: float           # value = model_prob*odd - 1
    kelly_stake: float    # fraction de bankroll recommandée (Kelly déjà fractionné)


def find_value_bets(
    model_probs: dict[str, float],
    odds: dict[str, float],
    min_value: float,
    kelly_frac: float,
) -> list[BetRecommendation]:
    """Croise les probas du modèle avec les cotes et sort les paris à value.

    Trié par edge décroissant : le premier est le 'meilleur pari'.
    """
    fair = remove_margin(odds)
    recs: list[BetRecommendation] = []
    for outcome, odd in odds.items():
        p = model_probs.get(outcome)
        if p is None or odd <= 1.0:
            continue
        v = value(p, odd)
        if v >= min_value:
            recs.append(
                BetRecommendation(
                    outcome=outcome,
                    odd=odd,
                    model_prob=p,
                    book_fair_prob=fair.get(outcome, 0.0),
                    edge=v,
                    kelly_stake=kelly_fraction(p, odd) * kelly_frac,
                )
            )
    recs.sort(key=lambda r: r.edge, reverse=True)
    return recs
