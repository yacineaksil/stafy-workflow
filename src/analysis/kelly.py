"""
Kelly Criterion pour le dimensionnement optimal des mises.
On utilise systématiquement le Kelly fractionné (divisé par Config.KELLY_FRACTION)
pour limiter la variance et les risques de ruine.
"""

from config import Config


def kelly_fraction(prob: float, odd: float) -> float:
    """
    Formule Kelly standard : f = (p*b - q) / b
    où b = odd - 1, p = notre probabilité, q = 1 - p
    Retourne la fraction du bankroll à miser (entre 0 et 1).
    """
    b = odd - 1.0
    if b <= 0:
        return 0.0
    q = 1.0 - prob
    f = (prob * b - q) / b
    return max(0.0, f)


def recommended_stake(prob: float, odd: float, bankroll: float = None) -> dict:
    """
    Retourne la mise recommandée en € et en % du bankroll.

    Applique Kelly fractionné (/ Config.KELLY_FRACTION).
    Plafonne à 10% du bankroll par pari (gestion du risque).
    """
    bank = bankroll or Config.DEFAULT_BANKROLL
    full_kelly = kelly_fraction(prob, odd)
    fractional = full_kelly / Config.KELLY_FRACTION

    # Plafond de sécurité
    fractional = min(fractional, 0.10)

    stake_eur = round(bank * fractional, 2)
    return {
        "full_kelly_pct": round(full_kelly * 100, 2),
        "recommended_pct": round(fractional * 100, 2),
        "recommended_eur": stake_eur,
        "bankroll": bank,
        "kelly_fraction_divisor": Config.KELLY_FRACTION,
    }


def expected_profit(prob: float, odd: float, stake: float) -> dict:
    """Espérance de gain/perte pour une mise donnée."""
    win_amount = stake * (odd - 1)
    ev = prob * win_amount - (1 - prob) * stake
    return {
        "stake": stake,
        "potential_win": round(win_amount, 2),
        "expected_value_eur": round(ev, 2),
        "roi_pct": round((ev / stake) * 100, 2) if stake > 0 else 0,
    }
