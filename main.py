#!/usr/bin/env python3
"""
Boutique Téléphone — Système de gestion complet
Fonctionnalités : stock, ventes, réparations, finances
"""

import sys
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich import box

from database import initialize_db
from utils import console, aujourd_hui, formater_montant
from stock import menu_stock
from ventes import menu_ventes
from reparations import menu_reparations
from finances import menu_finances, tableau_de_bord


BANNER = """
╔══════════════════════════════════════════════════╗
║        BOUTIQUE TÉLÉPHONE — STAFY               ║
║        Gestion complète de votre commerce       ║
╚══════════════════════════════════════════════════╝
"""


def afficher_menu_principal():
    console.print(f"\n[bold cyan]{BANNER}[/bold cyan]")
    console.print(f"[dim]Aujourd'hui : {aujourd_hui()}[/dim]\n")

    console.print("  [cyan]1[/cyan].  📦  Gestion du Stock          (entrées, inventaire)")
    console.print("  [cyan]2[/cyan].  💰  Ventes                    (sorties, encaissements)")
    console.print("  [cyan]3[/cyan].  🔧  Réparations               (dépôts, suivi, livraisons)")
    console.print("  [cyan]4[/cyan].  📊  Finances & Rapports       (CA, recettes, dépenses)")
    console.print("  [cyan]5[/cyan].  🗂️   Tableau de bord          (résumé instantané)")
    console.print("  [cyan]0[/cyan].  🚪  Quitter")


def main():
    initialize_db()

    while True:
        afficher_menu_principal()
        choix = Prompt.ask("\n[bold]Votre choix[/bold]")

        if choix == "1":
            menu_stock()
        elif choix == "2":
            menu_ventes()
        elif choix == "3":
            menu_reparations()
        elif choix == "4":
            menu_finances()
        elif choix == "5":
            tableau_de_bord()
        elif choix == "0":
            console.print("\n[bold cyan]À bientôt ![/bold cyan]\n")
            sys.exit(0)
        else:
            console.print("[red]Choix invalide, veuillez réessayer.[/red]")


if __name__ == "__main__":
    main()
