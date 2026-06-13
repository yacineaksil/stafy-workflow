"""Tests de la logique pure (pas d'appel réseau)."""

import math

from stafy.models import baseball, basketball, football
from stafy.value import (
    find_value_bets,
    implied_prob,
    kelly_fraction,
    overround,
    remove_margin,
    value,
)


def test_implied_prob():
    assert math.isclose(implied_prob(2.0), 0.5)
    assert implied_prob(1.0) == 0.0  # cote dégénérée


def test_remove_margin_sums_to_one():
    odds = {"Home": 2.10, "Draw": 3.40, "Away": 3.10}
    fair = remove_margin(odds)
    assert math.isclose(sum(fair.values()), 1.0, rel_tol=1e-9)
    assert overround(odds) > 1.0  # il y a bien une marge


def test_value_positive_when_model_beats_odds():
    # modèle 55% sur une cote 2.0 (implicite 50%) => value positive
    assert value(0.55, 2.0) > 0
    assert value(0.45, 2.0) < 0


def test_kelly_zero_without_edge():
    assert kelly_fraction(0.40, 2.0) == 0.0
    assert kelly_fraction(0.60, 2.0) > 0.0


def test_find_value_bets_picks_best_first():
    model = {"Home": 0.60, "Draw": 0.20, "Away": 0.20}
    odds = {"Home": 2.0, "Draw": 3.0, "Away": 6.0}  # Away surcoté => value
    recs = find_value_bets(model, odds, min_value=0.05, kelly_frac=0.25)
    assert recs, "doit trouver au moins un value bet"
    assert recs[0].edge >= recs[-1].edge  # trié par edge décroissant


def test_football_probabilities_sum():
    p = football.probabilities(1.5, 1.1)
    assert math.isclose(p["Home"] + p["Draw"] + p["Away"], 1.0, rel_tol=1e-6)
    assert math.isclose(p["Over 2.5"] + p["Under 2.5"], 1.0, rel_tol=1e-6)
    # équipe domicile plus offensive => plus de chances de gagner
    assert p["Home"] > p["Away"]


def test_baseball_home_advantage():
    p = baseball.model_from_winpct(0.5, 0.5)
    assert math.isclose(p["Home"] + p["Away"], 1.0)
    assert p["Home"] > 0.5  # avantage du terrain à forces égales


def test_basketball_stronger_team_favored():
    p = basketball.model_from_points(115, 105, 105, 115)
    assert math.isclose(p["Home"] + p["Away"], 1.0)
    assert p["Home"] > p["Away"]
