"""Orchestration : match -> données -> proba modèle -> cotes 1xBet -> value bets.

Chaque sport a besoin d'inputs différents pour son modèle, d'où une fonction
d'analyse par sport. Toutes renvoient un AnalysisResult uniforme.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .api_client import ApiSportsClient
from .config import Config
from .models import baseball, basketball, football
from .odds import extract_match_winner_odds, list_available_bookmakers
from .value import BetRecommendation, find_value_bets, overround


@dataclass
class AnalysisResult:
    sport: str
    match_id: int
    home: str
    away: str
    model_probs: dict[str, float]
    odds: dict[str, float]
    book_overround: Optional[float]
    recommendations: list[BetRecommendation]
    notes: list[str] = field(default_factory=list)


def _winp_from_standing(row: dict) -> Optional[float]:
    """Extrait un win % d'une ligne de classement API-Sports (formes variables)."""
    games = row.get("games") or {}
    win = (games.get("win") or {})
    # baseball: games.win.percentage ; sinon on calcule win/(win+lose).
    pct = win.get("percentage")
    if pct is not None:
        try:
            return float(pct)
        except (TypeError, ValueError):
            pass
    w = (win.get("total") if isinstance(win, dict) else None)
    lose = (games.get("lose") or {})
    l = (lose.get("total") if isinstance(lose, dict) else None)
    if isinstance(w, (int, float)) and isinstance(l, (int, float)) and (w + l) > 0:
        return w / (w + l)
    return None


def _points_from_standing(row: dict) -> tuple[Optional[float], Optional[float]]:
    """Points marqués/encaissés moyens d'une ligne de classement basket."""
    pts = row.get("points") or {}
    games = row.get("games") or {}
    played = games.get("played")
    pf = pts.get("for")
    pa = pts.get("against")
    if isinstance(played, (int, float)) and played > 0:
        if isinstance(pf, (int, float)):
            pf = pf / played
        if isinstance(pa, (int, float)):
            pa = pa / played
    return (pf if isinstance(pf, (int, float)) else None,
            pa if isinstance(pa, (int, float)) else None)


def _flatten_standings(standings_resp: list) -> dict[int, dict]:
    """Indexe les lignes de classement par team id, quelle que soit la profondeur."""
    out: dict[int, dict] = {}

    def walk(node):
        if isinstance(node, dict):
            team = node.get("team")
            if isinstance(team, dict) and "id" in team:
                out[int(team["id"])] = node
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(standings_resp)
    return out


def analyze_football(client: ApiSportsClient, cfg: Config, match_id: int) -> AnalysisResult:
    notes: list[str] = []
    fx = client.fixture("football", match_id)
    if not fx:
        raise ValueError(f"Match football {match_id} introuvable.")
    league = fx["league"]["id"]
    season = fx["league"]["season"]
    home_team = fx["teams"]["home"]
    away_team = fx["teams"]["away"]

    home_stats = client.team_statistics(league, season, home_team["id"])
    away_stats = client.team_statistics(league, season, away_team["id"])
    model_probs = football.model_from_stats(home_stats, away_stats)

    odds_resp = client.odds("football", match_id)
    odds = extract_match_winner_odds(odds_resp, "football", cfg.bookmaker_name)
    if not odds:
        notes.append(
            f"Cotes '{cfg.bookmaker_name}' introuvables. Books dispo : "
            f"{list_available_bookmakers(odds_resp)}"
        )

    recs = find_value_bets(model_probs, odds, cfg.min_value, cfg.kelly_fraction) if odds else []
    return AnalysisResult(
        sport="football",
        match_id=match_id,
        home=home_team["name"],
        away=away_team["name"],
        model_probs=model_probs,
        odds=odds,
        book_overround=overround(odds) if odds else None,
        recommendations=recs,
        notes=notes,
    )


def _analyze_standings_sport(
    client: ApiSportsClient, cfg: Config, sport: str, match_id: int
) -> AnalysisResult:
    notes: list[str] = []
    game = client.fixture(sport, match_id)
    if not game:
        raise ValueError(f"Match {sport} {match_id} introuvable.")
    league = game["league"]["id"]
    season = game["league"]["season"]
    home_team = game["teams"]["home"]
    away_team = game["teams"]["away"]

    standings_resp = client.standings(sport, league, season)
    table = _flatten_standings(standings_resp)
    home_row = table.get(int(home_team["id"]))
    away_row = table.get(int(away_team["id"]))
    if not home_row or not away_row:
        raise ValueError("Classement indisponible pour une des équipes.")

    if sport == "baseball":
        hw = _winp_from_standing(home_row)
        aw = _winp_from_standing(away_row)
        if hw is None or aw is None:
            raise ValueError("Win % indisponible dans le classement baseball.")
        model_probs = baseball.model_from_winpct(hw, aw)
        notes.append("Modèle log5 sur win % — sans facteur lanceur partant.")
    else:  # basketball
        hpf, hpa = _points_from_standing(home_row)
        apf, apa = _points_from_standing(away_row)
        if None in (hpf, hpa, apf, apa):
            # repli sur win % si les points ne sont pas exposés
            hw = _winp_from_standing(home_row)
            aw = _winp_from_standing(away_row)
            if hw is None or aw is None:
                raise ValueError("Ni points ni win % exploitables (basket).")
            model_probs = basketball.probabilities(hw * 100 + 100, 100, aw * 100 + 100, 100)
            notes.append("Repli sur win % (points indisponibles).")
        else:
            model_probs = basketball.model_from_points(hpf, hpa, apf, apa)
            notes.append("Modèle Pythagore sur points — sans ajustement de pace.")

    odds_resp = client.odds(sport, match_id)
    odds = extract_match_winner_odds(odds_resp, sport, cfg.bookmaker_name)
    if not odds:
        notes.append(
            f"Cotes '{cfg.bookmaker_name}' introuvables. Books dispo : "
            f"{list_available_bookmakers(odds_resp)}"
        )

    recs = find_value_bets(model_probs, odds, cfg.min_value, cfg.kelly_fraction) if odds else []
    return AnalysisResult(
        sport=sport,
        match_id=match_id,
        home=home_team["name"],
        away=away_team["name"],
        model_probs=model_probs,
        odds=odds,
        book_overround=overround(odds) if odds else None,
        recommendations=recs,
        notes=notes,
    )


def analyze(client: ApiSportsClient, cfg: Config, sport: str, match_id: int) -> AnalysisResult:
    if sport == "football":
        return analyze_football(client, cfg, match_id)
    if sport in ("baseball", "basketball"):
        return _analyze_standings_sport(client, cfg, sport, match_id)
    raise ValueError(f"Sport non supporté : {sport}")
