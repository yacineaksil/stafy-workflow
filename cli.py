#!/usr/bin/env python3
"""CLI stafy : analyse un ou plusieurs matchs et sort les value bets 1xBet.

Exemples :
    python cli.py football 1035000
    python cli.py baseball 7890 --bankroll 200
    python cli.py basketball 12345 football 1035001
"""

from __future__ import annotations

import argparse
import sys

from stafy.api_client import ApiSportsClient, ApiSportsError
from stafy.config import Config
from stafy.pipeline import AnalysisResult, analyze

SPORTS = {"football", "baseball", "basketball"}


def _print_result(res: AnalysisResult, bankroll: float) -> None:
    print(f"\n=== {res.sport.upper()} — {res.home} vs {res.away} (id {res.match_id}) ===")
    print("Probabilités modèle :")
    for k, v in res.model_probs.items():
        print(f"  {k:<12} {v*100:5.1f}%")
    if res.odds:
        marge = (res.book_overround - 1) * 100 if res.book_overround else 0.0
        print(f"Cotes book (marge {marge:.1f}%) :")
        for k, v in res.odds.items():
            print(f"  {k:<12} {v:.2f}")
    for note in res.notes:
        print(f"  [note] {note}")

    if not res.recommendations:
        print(">> Aucun value bet au-dessus du seuil. Ne rien parier est une décision.")
        return
    print(">> VALUE BETS (meilleur en premier) :")
    for r in res.recommendations:
        stake = bankroll * r.kelly_stake
        print(
            f"  {r.outcome:<10} cote {r.odd:.2f} | "
            f"proba modèle {r.model_prob*100:4.1f}% vs book {r.book_fair_prob*100:4.1f}% | "
            f"edge {r.edge*100:+5.1f}% | mise {r.kelly_stake*100:4.1f}% bankroll"
            + (f" (~{stake:.2f})" if bankroll else "")
        )


def _parse_pairs(tokens: list[str]) -> list[tuple[str, int]]:
    if len(tokens) % 2 != 0:
        raise SystemExit("Arguments attendus par paires : <sport> <match_id> ...")
    pairs = []
    for i in range(0, len(tokens), 2):
        sport = tokens[i].lower()
        if sport not in SPORTS:
            raise SystemExit(f"Sport invalide '{sport}'. Choix : {sorted(SPORTS)}")
        try:
            mid = int(tokens[i + 1])
        except ValueError:
            raise SystemExit(f"match_id invalide : {tokens[i + 1]}")
        pairs.append((sport, mid))
    return pairs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Détecteur de value bets (foot/MLB/NBA) sur 1xBet.")
    parser.add_argument("pairs", nargs="+", help="Suite de <sport> <match_id> (ex: football 1035000)")
    parser.add_argument("--bankroll", type=float, default=0.0, help="Bankroll pour chiffrer les mises Kelly.")
    args = parser.parse_args(argv)

    pairs = _parse_pairs(args.pairs)

    try:
        cfg = Config.from_env()
    except RuntimeError as exc:
        print(f"Erreur config : {exc}", file=sys.stderr)
        return 2

    client = ApiSportsClient(cfg.api_key)
    exit_code = 0
    for sport, match_id in pairs:
        try:
            res = analyze(client, cfg, sport, match_id)
            _print_result(res, args.bankroll)
        except (ApiSportsError, ValueError) as exc:
            print(f"\n[ÉCHEC] {sport} {match_id} : {exc}", file=sys.stderr)
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
