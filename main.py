#!/usr/bin/env python3
"""
Stafy — Sports Betting Intelligence Dashboard
Usage : python main.py [--date YYYY-MM-DD] [--bankroll 1000] [--sport football|mlb|basketball]
"""

import argparse
import sys
from datetime import date

from src.dashboard.report import run_full_report
from config import Config


def parse_args():
    parser = argparse.ArgumentParser(
        description="Stafy — Dashboard de pronostics sportifs avec détection de valeur (EV+)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Variables d'environnement :
  API_FOOTBALL_KEY   Clé API-Football (https://api-sports.io) — gratuit 100 req/jour
  ODDS_API_KEY       Clé The Odds API (https://the-odds-api.com) — gratuit 500 req/mois

Sans clés : le dashboard fonctionne en mode démo avec des données réalistes.

Exemples :
  python main.py                          # Matchs du jour, bankroll 1000€
  python main.py --bankroll 5000          # Avec 5000€ de bankroll
  python main.py --date 2026-06-14        # Matchs d'une date spécifique
  python main.py --sport football         # Football uniquement
        """
    )
    parser.add_argument(
        "--date", "-d",
        type=str,
        default=None,
        help="Date des matchs (YYYY-MM-DD, défaut: aujourd'hui)"
    )
    parser.add_argument(
        "--bankroll", "-b",
        type=float,
        default=Config.DEFAULT_BANKROLL,
        help=f"Bankroll en euros (défaut: {Config.DEFAULT_BANKROLL}€)"
    )
    parser.add_argument(
        "--sport", "-s",
        type=str,
        choices=["football", "mlb", "basketball", "all"],
        default="all",
        help="Sport à analyser (défaut: all)"
    )
    parser.add_argument(
        "--ev-threshold",
        type=float,
        default=Config.MIN_EV_THRESHOLD,
        help=f"Seuil EV minimum pour recommander un pari (défaut: {Config.MIN_EV_THRESHOLD})"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Overrides config dynamiquement
    if args.ev_threshold != Config.MIN_EV_THRESHOLD:
        Config.MIN_EV_THRESHOLD = args.ev_threshold

    # Parse date
    target_date = None
    if args.date:
        try:
            target_date = date.fromisoformat(args.date)
        except ValueError:
            print(f"❌ Format de date invalide : {args.date} (attendu YYYY-MM-DD)")
            sys.exit(1)

    # Filtrer les sports si demandé
    if args.sport != "all":
        _run_single_sport(args.sport, target_date, args.bankroll)
    else:
        run_full_report(target_date=target_date, bankroll=args.bankroll)


def _run_single_sport(sport: str, target_date, bankroll: float):
    from src.dashboard.display import console, render_header, render_sport_section, render_summary, render_api_status
    from src.dashboard.report import process_football, process_mlb, process_basketball

    d = target_date or date.today()
    render_header(d)
    render_api_status(bool(Config.API_FOOTBALL_KEY), bool(Config.ODDS_API_KEY))

    if sport == "football":
        matches, value = process_football(d, bankroll)
    elif sport == "mlb":
        matches, value = process_mlb(d, bankroll)
    elif sport == "basketball":
        matches, value = process_basketball(d, bankroll)
    else:
        matches, value = [], []

    render_sport_section(sport, matches, bankroll)
    render_summary(value, bankroll)


if __name__ == "__main__":
    main()
