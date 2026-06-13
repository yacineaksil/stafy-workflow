"""
Dashboard terminal avec Rich.
Affiche les matchs du jour, probabilités, cotes, EV et mises recommandées.
"""

from datetime import date, datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.rule import Rule
from rich import box
from rich.align import Align

from src.analysis.ev_calculator import BetOpportunity
from src.analysis.kelly import recommended_stake, expected_profit

console = Console()

SPORT_EMOJI = {"football": "⚽", "mlb": "⚾", "basketball": "🏀"}
SPORT_COLOR = {"football": "green", "mlb": "red", "basketball": "orange1"}

CONFIDENCE_COLOR = {"high": "green", "medium": "yellow", "low": "red"}
CONFIDENCE_LABEL = {"high": "●●●", "medium": "●●○", "low": "●○○"}


def render_header(target_date: date) -> None:
    title = Text()
    title.append("  STAFY ", style="bold white on dark_blue")
    title.append(" Sports Betting Intelligence ", style="bold cyan")
    title.append(f"  {target_date.strftime('%A %d %B %Y')}  ", style="dim white")

    console.print()
    console.print(Align.center(title))
    console.print()


def render_ev_badge(ev: float) -> Text:
    t = Text()
    if ev >= 0.08:
        t.append(f" +{ev*100:.1f}% EV ", style="bold white on green")
    elif ev >= Config_min_ev():
        t.append(f" +{ev*100:.1f}% EV ", style="bold black on yellow")
    elif ev >= 0:
        t.append(f" +{ev*100:.1f}% EV ", style="dim green")
    else:
        t.append(f" {ev*100:.1f}% EV ", style="dim red")
    return t


def Config_min_ev():
    from config import Config
    return Config.MIN_EV_THRESHOLD


def render_sport_section(
    sport: str,
    matches: list[dict],
    bankroll: float = 1000.0,
) -> None:
    """Affiche une section sport avec tous ses matchs."""
    if not matches:
        return

    emoji = SPORT_EMOJI.get(sport, "🏟")
    color = SPORT_COLOR.get(sport, "white")

    console.print(Rule(
        f"{emoji}  [bold {color}]{sport.upper()}[/bold {color}]",
        style=color
    ))
    console.print()

    for match in matches:
        render_match_card(match, sport, bankroll)

    console.print()


def render_match_card(match: dict, sport: str, bankroll: float) -> None:
    """Affiche un match avec sa prédiction et les opportunités de pari."""
    prediction = match.get("prediction")
    opportunities: list[BetOpportunity] = match.get("opportunities", [])
    meta = match.get("meta", {})
    is_demo = match.get("is_demo", False)

    home_name = match.get("home_name", "?")
    away_name = match.get("away_name", "?")
    kick_off = match.get("kickoff", "")
    league = match.get("league", "")

    # --- En-tête du match ---
    header = Text()
    header.append(f"  {home_name} ", style="bold white")
    header.append("vs", style="dim")
    header.append(f" {away_name}  ", style="bold white")
    if kick_off:
        header.append(f"[{kick_off}]", style="dim cyan")
    if league:
        header.append(f"  {league}", style="dim")
    if is_demo:
        header.append("  [DEMO]", style="dim yellow")

    # --- Table des probabilités ---
    prob_table = Table(box=box.SIMPLE, show_header=True, padding=(0, 1))
    prob_table.add_column("Résultat", style="white", width=20)
    prob_table.add_column("Notre proba", style="cyan", justify="center", width=14)
    prob_table.add_column("Cote bookie", justify="center", width=12)
    prob_table.add_column("Proba implicite", justify="center", width=16)
    prob_table.add_column("EV", justify="center", width=12)
    prob_table.add_column("Recommandation", width=30)

    value_bets = []
    for opp in opportunities:
        is_val = opp.is_value
        odd_str = f"{opp.bookmaker_odd:.2f}" if opp.bookmaker_odd > 0 else "N/D"
        impl_str = f"{opp.implied_prob*100:.1f}%" if opp.implied_prob > 0 else "—"

        if is_val:
            value_bets.append(opp)
            stake_info = recommended_stake(opp.our_prob, opp.bookmaker_odd, bankroll)
            profit_info = expected_profit(opp.our_prob, opp.bookmaker_odd, stake_info["recommended_eur"])
            rec = Text()
            rec.append(f"✓ Miser {stake_info['recommended_eur']:.0f}€", style="bold green")
            rec.append(f" (EV: +{profit_info['expected_value_eur']:.1f}€)", style="green")
            row_style = "bold"
        else:
            rec = Text("—", style="dim")
            row_style = ""

        label = opp.label
        if len(label) > 19:
            label = label[:17] + "…"

        prob_table.add_row(
            Text(label, style="bold white" if is_val else "white"),
            Text(f"{opp.our_prob*100:.1f}%", style="bold cyan" if is_val else "cyan"),
            Text(odd_str, style="bold yellow" if is_val else "yellow"),
            Text(impl_str, style="dim"),
            render_ev_badge(opp.ev),
            rec,
        )

    # Confiance du modèle
    confidence = getattr(prediction, "confidence", "medium")
    conf_color = CONFIDENCE_COLOR.get(confidence, "white")
    conf_label = CONFIDENCE_LABEL.get(confidence, "?")

    subtitle = Text()
    subtitle.append("Confiance modèle : ", style="dim")
    subtitle.append(conf_label, style=conf_color)

    # Infos supplémentaires selon sport
    if sport == "football" and prediction:
        subtitle.append(f"  |  xG attendus : ", style="dim")
        subtitle.append(f"{prediction.lambda_home:.2f}", style="cyan")
        subtitle.append(" - ", style="dim")
        subtitle.append(f"{prediction.lambda_away:.2f}", style="cyan")
    elif sport == "mlb" and prediction:
        subtitle.append(f"  |  ERA diff : ", style="dim")
        adj = getattr(prediction, "adj_era_diff", 0)
        col = "green" if adj > 0 else "red"
        subtitle.append(f"{adj:+.2f}", style=col)
    elif sport == "basketball" and prediction:
        subtitle.append(f"  |  Elo diff : ", style="dim")
        diff = getattr(prediction, "elo_diff", 0)
        col = "green" if diff > 0 else "red"
        subtitle.append(f"{diff:+.0f}", style=col)

    panel_content = Text()
    panel_content.append_text(subtitle)
    panel_content.append("\n")

    # Assembler le panel
    from rich.console import Group
    content_group = Group(
        panel_content,
        prob_table,
    )

    border_style = "bold green" if value_bets else "dim white"
    console.print(Panel(
        content_group,
        title=header,
        title_align="left",
        border_style=border_style,
        padding=(0, 1),
    ))


def render_summary(all_value_bets: list[dict], bankroll: float) -> None:
    """Affiche le résumé des meilleures opportunités de la journée."""
    if not all_value_bets:
        console.print(Panel(
            "[dim]Aucune opportunité à valeur positive détectée aujourd'hui.[/dim]\n"
            "[dim]• Vérifiez vos clés API pour des données en temps réel[/dim]\n"
            "[dim]• Ajustez MIN_EV_THRESHOLD dans config.py si nécessaire[/dim]",
            title="[yellow]Résumé du jour[/yellow]",
            border_style="yellow",
        ))
        return

    table = Table(
        title=f"[bold green]⭐ {len(all_value_bets)} Pari(s) à Valeur Positive Détecté(s)[/bold green]",
        box=box.ROUNDED,
        border_style="green",
        show_lines=True,
    )
    table.add_column("Sport", style="cyan", width=12)
    table.add_column("Match", style="white", width=28)
    table.add_column("Sélection", style="bold white", width=22)
    table.add_column("Cote", justify="center", style="yellow", width=8)
    table.add_column("EV", justify="center", width=10)
    table.add_column("Mise (€)", justify="right", style="bold green", width=10)
    table.add_column("EV (€)", justify="right", style="green", width=10)

    total_stake = 0
    total_ev_eur = 0

    for vb in sorted(all_value_bets, key=lambda x: x["ev"], reverse=True):
        stake_info = recommended_stake(vb["our_prob"], vb["odd"], bankroll)
        profit_info = expected_profit(vb["our_prob"], vb["odd"], stake_info["recommended_eur"])
        total_stake += stake_info["recommended_eur"]
        total_ev_eur += profit_info["expected_value_eur"]

        ev_pct = vb["ev"] * 100
        ev_color = "bold green" if ev_pct >= 8 else "green"

        table.add_row(
            f"{SPORT_EMOJI.get(vb['sport'], '🏟')} {vb['sport'].upper()}",
            vb["match"],
            vb["selection"],
            f"{vb['odd']:.2f}",
            Text(f"+{ev_pct:.1f}%", style=ev_color),
            f"{stake_info['recommended_eur']:.0f}€",
            f"+{profit_info['expected_value_eur']:.1f}€",
        )

    console.print(table)
    console.print()

    # Totaux
    footer = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    footer.add_column("", style="dim")
    footer.add_column("", style="bold")
    footer.add_row("Bankroll :", f"{bankroll:.0f}€")
    footer.add_row("Mise totale recommandée :", f"[yellow]{total_stake:.0f}€[/yellow] ({total_stake/bankroll*100:.1f}%)")
    footer.add_row("EV total attendu :", f"[green]+{total_ev_eur:.1f}€[/green]")
    footer.add_row("ROI espéré :", f"[bold green]+{(total_ev_eur/total_stake*100) if total_stake > 0 else 0:.1f}%[/bold green]")
    console.print(Align.right(footer))


def render_no_data_warning(sport: str, reason: str) -> None:
    console.print(f"  [dim yellow]⚠ {sport.upper()} : {reason}[/dim yellow]")


def render_api_status(api_football: bool, odds_api: bool) -> None:
    status = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    status.add_column("")
    status.add_column("")
    status.add_row(
        "API-Football :",
        "[green]✓ Connecté[/green]" if api_football else "[dim]○ Mode démo (configurez API_FOOTBALL_KEY)[/dim]"
    )
    status.add_row(
        "Odds API (1xBet) :",
        "[green]✓ Connecté[/green]" if odds_api else "[dim]○ Mode démo (configurez ODDS_API_KEY)[/dim]"
    )
    status.add_row(
        "MLB Stats API :",
        "[green]✓ Sans clé requise[/green]"
    )
    status.add_row(
        "NBA (balldontlie) :",
        "[green]✓ Sans clé requise[/green]"
    )
    console.print(Panel(status, title="[dim]Statut APIs[/dim]", border_style="dim", padding=(0, 1)))
    console.print()
