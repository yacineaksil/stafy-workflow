"""
Assemblage du rapport complet : collecte données → modèles → EV → affichage.
"""

from datetime import date, datetime
from config import Config
from src.data import football, mlb, basketball, odds as odds_module
from src.models import poisson, mlb_model, nba_model
from src.analysis.ev_calculator import find_value_bets, generate_demo_odds
from src.dashboard.display import (
    console, render_header, render_sport_section,
    render_summary, render_api_status,
)


def _kickoff_str(dt_str: str) -> str:
    if not dt_str:
        return ""
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%H:%M")
    except Exception:
        return dt_str[:5]


def process_football(target_date: date, bankroll: float) -> tuple[list[dict], list[dict]]:
    fixtures = football.get_fixtures(target_date)
    matches = []
    all_value = []

    for fix in fixtures:
        teams = fix.get("teams", {})
        home_name = teams.get("home", {}).get("name", "Home")
        away_name = teams.get("away", {}).get("name", "Away")
        league_name = fix.get("league", {}).get("name", "")
        kickoff = _kickoff_str(fix.get("fixture", {}).get("date", ""))
        is_demo = fix.get("_demo", False)

        pred = poisson.predict_from_fixture(fix)

        probs = {
            "home": pred.prob_home,
            "draw": pred.prob_draw,
            "away": pred.prob_away,
        }

        # Récupérer cotes réelles ou générer des cotes démo
        if is_demo or not Config.ODDS_API_KEY:
            bk_odds = generate_demo_odds(pred.prob_home, pred.prob_away, pred.prob_draw)
        else:
            game_odds = odds_module.get_odds("football", target_date)
            bk_odds = odds_module.extract_best_odds(game_odds[0]) if game_odds else \
                      generate_demo_odds(pred.prob_home, pred.prob_away, pred.prob_draw)

        labels = {"home": f"{home_name}", "away": f"{away_name}"}
        opportunities = find_value_bets(probs, bk_odds, labels)

        for opp in opportunities:
            if opp.is_value:
                all_value.append({
                    "sport": "football",
                    "match": f"{home_name} vs {away_name}",
                    "selection": opp.label,
                    "odd": opp.bookmaker_odd,
                    "our_prob": opp.our_prob,
                    "ev": opp.ev,
                })

        matches.append({
            "home_name": home_name,
            "away_name": away_name,
            "kickoff": kickoff,
            "league": league_name,
            "is_demo": is_demo,
            "prediction": pred,
            "opportunities": opportunities,
        })

    return matches, all_value


def process_mlb(target_date: date, bankroll: float) -> tuple[list[dict], list[dict]]:
    games_raw = mlb.get_schedule(target_date)
    matches = []
    all_value = []

    for game_raw in games_raw:
        info = mlb.extract_game_info(game_raw)
        home_name = info["home"]["name"]
        away_name = info["away"]["name"]
        kickoff = _kickoff_str(info["date"])
        is_demo = info.get("_demo", False)

        pred = mlb_model.predict_from_game(game_raw)

        probs = {"home": pred.prob_home, "away": pred.prob_away}

        if is_demo or not Config.ODDS_API_KEY:
            bk_odds = generate_demo_odds(pred.prob_home, pred.prob_away)
        else:
            game_odds = odds_module.get_odds("mlb", target_date)
            bk_odds = odds_module.extract_best_odds(game_odds[0]) if game_odds else \
                      generate_demo_odds(pred.prob_home, pred.prob_away)

        labels = {"home": home_name, "away": away_name}
        opportunities = find_value_bets(probs, bk_odds, labels)

        for opp in opportunities:
            if opp.is_value:
                all_value.append({
                    "sport": "mlb",
                    "match": f"{home_name} vs {away_name}",
                    "selection": opp.label,
                    "odd": opp.bookmaker_odd,
                    "our_prob": opp.our_prob,
                    "ev": opp.ev,
                })

        matches.append({
            "home_name": home_name,
            "away_name": away_name,
            "kickoff": kickoff,
            "league": "MLB",
            "is_demo": is_demo,
            "prediction": pred,
            "opportunities": opportunities,
        })

    return matches, all_value


def process_basketball(target_date: date, bankroll: float) -> tuple[list[dict], list[dict]]:
    games_raw = basketball.get_games(target_date)
    matches = []
    all_value = []

    for game_raw in games_raw:
        info = basketball.extract_game_info(game_raw)
        home_name = info["home"]["name"]
        away_name = info["away"]["name"]
        kickoff = _kickoff_str(info["date"])
        is_demo = info.get("_demo", False)

        pred = nba_model.predict_from_game(game_raw)

        probs = {"home": pred.prob_home, "away": pred.prob_away}

        if is_demo or not Config.ODDS_API_KEY:
            bk_odds = generate_demo_odds(pred.prob_home, pred.prob_away)
        else:
            game_odds = odds_module.get_odds("basketball", target_date)
            bk_odds = odds_module.extract_best_odds(game_odds[0]) if game_odds else \
                      generate_demo_odds(pred.prob_home, pred.prob_away)

        labels = {"home": home_name, "away": away_name}
        opportunities = find_value_bets(probs, bk_odds, labels)

        for opp in opportunities:
            if opp.is_value:
                all_value.append({
                    "sport": "basketball",
                    "match": f"{home_name} vs {away_name}",
                    "selection": opp.label,
                    "odd": opp.bookmaker_odd,
                    "our_prob": opp.our_prob,
                    "ev": opp.ev,
                })

        matches.append({
            "home_name": home_name,
            "away_name": away_name,
            "kickoff": kickoff,
            "league": "NBA",
            "is_demo": is_demo,
            "prediction": pred,
            "opportunities": opportunities,
        })

    return matches, all_value


def run_full_report(target_date: date = None, bankroll: float = None):
    d = target_date or date.today()
    bank = bankroll or Config.DEFAULT_BANKROLL

    render_header(d)
    render_api_status(
        api_football=bool(Config.API_FOOTBALL_KEY),
        odds_api=bool(Config.ODDS_API_KEY),
    )

    all_value_bets = []

    # Football
    fb_matches, fb_value = process_football(d, bank)
    all_value_bets.extend(fb_value)
    render_sport_section("football", fb_matches, bank)

    # MLB
    mlb_matches, mlb_value = process_mlb(d, bank)
    all_value_bets.extend(mlb_value)
    render_sport_section("mlb", mlb_matches, bank)

    # Basketball
    bball_matches, bball_value = process_basketball(d, bank)
    all_value_bets.extend(bball_value)
    render_sport_section("basketball", bball_matches, bank)

    # Résumé final
    render_summary(all_value_bets, bank)
