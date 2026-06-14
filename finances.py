from datetime import datetime, date
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.columns import Columns
from rich.text import Text
from rich import box

from database import get_connection
from utils import (
    console, aujourd_hui, saisir_float, saisir_int,
    saisir_date, choisir_parmi, formater_montant
)

CATEGORIES_DEPENSES = [
    "loyer", "salaires", "électricité / eau", "téléphone / internet",
    "pièces de rechange", "fournitures", "marketing", "transport", "divers"
]


def menu_finances():
    while True:
        console.print("\n[bold magenta]═══ FINANCES & RAPPORTS ═══[/bold magenta]")
        console.print("  [cyan]1[/cyan]. Rapport du jour")
        console.print("  [cyan]2[/cyan]. Rapport mensuel")
        console.print("  [cyan]3[/cyan]. Rapport par période")
        console.print("  [cyan]4[/cyan]. Chiffre d'affaires global")
        console.print("  [cyan]5[/cyan]. Enregistrer une dépense")
        console.print("  [cyan]6[/cyan]. Historique des dépenses")
        console.print("  [cyan]7[/cyan]. Tableau de bord (résumé)")
        console.print("  [cyan]0[/cyan]. Retour")

        choix = Prompt.ask("\n[bold]Votre choix[/bold]")
        if choix == "1":
            rapport_journalier()
        elif choix == "2":
            rapport_mensuel()
        elif choix == "3":
            rapport_periode()
        elif choix == "4":
            ca_global()
        elif choix == "5":
            enregistrer_depense()
        elif choix == "6":
            historique_depenses()
        elif choix == "7":
            tableau_de_bord()
        elif choix == "0":
            break


# ──────────────────────────────────────────────────
#  Rapport journalier
# ──────────────────────────────────────────────────

def rapport_journalier(jour: str | None = None):
    jour = jour or aujourd_hui()
    console.print(f"\n[bold magenta]── Rapport du {jour} ──[/bold magenta]")

    with get_connection() as conn:
        ventes = conn.execute(
            "SELECT * FROM ventes WHERE date(date_vente)=?", (jour,)
        ).fetchall()

        reps_livrees = conn.execute(
            "SELECT * FROM reparations WHERE statut='livré' AND date_rendu_reel=?", (jour,)
        ).fetchall()

        depenses = conn.execute(
            "SELECT * FROM depenses WHERE date_depense=?", (jour,)
        ).fetchall()

    ca_ventes = sum(r["prix_total"] for r in ventes)
    benefice_ventes = sum(r["benefice"] for r in ventes)
    recettes_rep = sum(r["avance_recue"] for r in reps_livrees if r["avance_recue"])
    total_depenses = sum(r["montant"] for r in depenses)
    ca_total = ca_ventes + recettes_rep
    resultat_net = ca_total - total_depenses

    # ── Ventes ──
    if ventes:
        _afficher_mini_ventes(ventes)

    # ── Réparations livrées ──
    if reps_livrees:
        console.print("\n[bold]Réparations livrées :[/bold]")
        for r in reps_livrees:
            console.print(f"  • #{r['id']} {r['marque_telephone']} {r['modele_telephone']} — {r['client_nom']} — {formater_montant(r['avance_recue'] or 0)}")

    # ── Dépenses ──
    if depenses:
        console.print("\n[bold]Dépenses :[/bold]")
        for d in depenses:
            console.print(f"  • {d['description']} [{d['categorie']}] — [red]{formater_montant(d['montant'])}[/red]")

    # ── Résumé ──
    _afficher_resume(
        nb_ventes=len(ventes),
        ca_ventes=ca_ventes,
        benefice_ventes=benefice_ventes,
        recettes_rep=recettes_rep,
        ca_total=ca_total,
        total_depenses=total_depenses,
        resultat_net=resultat_net,
    )


# ──────────────────────────────────────────────────
#  Rapport mensuel
# ──────────────────────────────────────────────────

def rapport_mensuel():
    annee = Prompt.ask("Année (AAAA)", default=str(datetime.now().year))
    mois = Prompt.ask("Mois (MM)", default=f"{datetime.now().month:02d}")
    debut = f"{annee}-{mois}-01"
    # fin du mois
    m = int(mois)
    y = int(annee)
    m_suiv = m % 12 + 1
    y_suiv = y + (1 if m == 12 else 0)
    fin = f"{y_suiv}-{m_suiv:02d}-01"

    console.print(f"\n[bold magenta]── Rapport mensuel {mois}/{annee} ──[/bold magenta]")
    _rapport_pour_periode(debut, fin, label=f"{mois}/{annee}")


# ──────────────────────────────────────────────────
#  Rapport par période
# ──────────────────────────────────────────────────

def rapport_periode():
    debut = saisir_date("Date de début")
    fin = saisir_date("Date de fin")
    console.print(f"\n[bold magenta]── Rapport du {debut} au {fin} ──[/bold magenta]")
    _rapport_pour_periode(debut, fin, label=f"{debut} → {fin}")


def _rapport_pour_periode(debut: str, fin: str, label: str = ""):
    with get_connection() as conn:
        ventes = conn.execute(
            "SELECT * FROM ventes WHERE date(date_vente) >= ? AND date(date_vente) < ?",
            (debut, fin)
        ).fetchall()

        reps_livrees = conn.execute(
            """SELECT * FROM reparations WHERE statut='livré'
               AND date_rendu_reel >= ? AND date_rendu_reel < ?""",
            (debut, fin)
        ).fetchall()

        depenses = conn.execute(
            "SELECT * FROM depenses WHERE date_depense >= ? AND date_depense < ?",
            (debut, fin)
        ).fetchall()

    ca_ventes = sum(r["prix_total"] for r in ventes)
    benefice_ventes = sum(r["benefice"] for r in ventes)
    recettes_rep = sum(r["avance_recue"] for r in reps_livrees if r["avance_recue"])
    total_depenses = sum(r["montant"] for r in depenses)
    ca_total = ca_ventes + recettes_rep
    resultat_net = ca_total - total_depenses

    if ventes:
        _afficher_mini_ventes(ventes)

    # Dépenses par catégorie
    if depenses:
        _afficher_depenses_par_categorie(depenses)

    _afficher_resume(
        nb_ventes=len(ventes),
        ca_ventes=ca_ventes,
        benefice_ventes=benefice_ventes,
        recettes_rep=recettes_rep,
        ca_total=ca_total,
        total_depenses=total_depenses,
        resultat_net=resultat_net,
    )


# ──────────────────────────────────────────────────
#  CA global
# ──────────────────────────────────────────────────

def ca_global():
    with get_connection() as conn:
        ventes = conn.execute("SELECT * FROM ventes").fetchall()
        reps = conn.execute(
            "SELECT * FROM reparations WHERE statut='livré'"
        ).fetchall()
        depenses = conn.execute("SELECT * FROM depenses").fetchall()

    ca_ventes = sum(r["prix_total"] for r in ventes)
    benefice_ventes = sum(r["benefice"] for r in ventes)
    recettes_rep = sum(r["avance_recue"] for r in reps if r["avance_recue"])
    total_depenses = sum(r["montant"] for r in depenses)
    ca_total = ca_ventes + recettes_rep
    resultat_net = ca_total - total_depenses

    console.print("\n[bold magenta]── Chiffre d'affaires GLOBAL ──[/bold magenta]")
    _afficher_resume(
        nb_ventes=len(ventes),
        ca_ventes=ca_ventes,
        benefice_ventes=benefice_ventes,
        recettes_rep=recettes_rep,
        ca_total=ca_total,
        total_depenses=total_depenses,
        resultat_net=resultat_net,
    )


# ──────────────────────────────────────────────────
#  Dépenses
# ──────────────────────────────────────────────────

def enregistrer_depense():
    console.print("\n[bold red]── Enregistrer une dépense ──[/bold red]")
    description = Prompt.ask("Description").strip()
    montant = saisir_float("Montant (FCFA)")
    categorie = choisir_parmi(CATEGORIES_DEPENSES, "Catégorie (numéro)")
    date_dep = saisir_date("Date", defaut=aujourd_hui())
    notes = Prompt.ask("Notes (optionnel)", default="").strip() or None

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO depenses (description, montant, categorie, date_depense, notes) VALUES (?,?,?,?,?)",
            (description, montant, categorie, date_dep, notes)
        )
        conn.commit()
    console.print(f"[green]✓ Dépense de {formater_montant(montant)} enregistrée.[/green]")


def historique_depenses(date_debut: str | None = None, date_fin: str | None = None) -> list:
    with get_connection() as conn:
        if date_debut and date_fin:
            rows = conn.execute(
                "SELECT * FROM depenses WHERE date_depense BETWEEN ? AND ? ORDER BY date_depense DESC",
                (date_debut, date_fin)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM depenses ORDER BY date_depense DESC").fetchall()

    table = Table(title="[bold]DÉPENSES[/bold]", box=box.ROUNDED, header_style="bold magenta")
    table.add_column("ID", style="dim", width=4)
    table.add_column("Date")
    table.add_column("Description")
    table.add_column("Catégorie")
    table.add_column("Montant", justify="right", style="red")
    table.add_column("Notes", style="dim")

    for r in rows:
        table.add_row(
            str(r["id"]),
            r["date_depense"],
            r["description"],
            r["categorie"],
            formater_montant(r["montant"]),
            r["notes"] or "-",
        )

    console.print()
    console.print(table)
    total = sum(r["montant"] for r in rows)
    console.print(f"[bold]Total dépenses : [red]{formater_montant(total)}[/red][/bold]")
    return list(rows)


# ──────────────────────────────────────────────────
#  Tableau de bord
# ──────────────────────────────────────────────────

def tableau_de_bord():
    aujourd = aujourd_hui()
    mois_debut = aujourd[:8] + "01"

    with get_connection() as conn:
        stock_rows = conn.execute("SELECT quantite, prix_achat, prix_vente FROM telephones").fetchall()
        ventes_jour = conn.execute(
            "SELECT prix_total, benefice FROM ventes WHERE date(date_vente)=?", (aujourd,)
        ).fetchall()
        ventes_mois = conn.execute(
            "SELECT prix_total, benefice FROM ventes WHERE date(date_vente)>=?", (mois_debut,)
        ).fetchall()
        reps_en_cours = conn.execute(
            "SELECT count(*) as n FROM reparations WHERE statut IN ('en_attente','en_cours')"
        ).fetchone()["n"]
        reps_livrees_mois = conn.execute(
            """SELECT avance_recue FROM reparations
               WHERE statut='livré' AND date_rendu_reel>=?""", (mois_debut,)
        ).fetchall()
        depenses_mois = conn.execute(
            "SELECT montant FROM depenses WHERE date_depense>=?", (mois_debut,)
        ).fetchall()

    total_unites = sum(r["quantite"] for r in stock_rows)
    valeur_stock = sum(r["prix_achat"] * r["quantite"] for r in stock_rows)
    valeur_vente_stock = sum(r["prix_vente"] * r["quantite"] for r in stock_rows)

    ca_jour = sum(r["prix_total"] for r in ventes_jour)
    benef_jour = sum(r["benefice"] for r in ventes_jour)
    ca_mois_ventes = sum(r["prix_total"] for r in ventes_mois)
    benef_mois = sum(r["benefice"] for r in ventes_mois)
    rec_rep_mois = sum(r["avance_recue"] for r in reps_livrees_mois if r["avance_recue"])
    ca_mois = ca_mois_ventes + rec_rep_mois
    dep_mois = sum(r["montant"] for r in depenses_mois)
    resultat_mois = ca_mois - dep_mois

    console.print()
    console.rule("[bold magenta]TABLEAU DE BORD[/bold magenta]")

    panels = [
        Panel(
            f"[bold]{total_unites}[/bold] unités\n"
            f"Valeur achat : [yellow]{formater_montant(valeur_stock)}[/yellow]\n"
            f"Valeur vente : [green]{formater_montant(valeur_vente_stock)}[/green]",
            title="[bold cyan]STOCK[/bold cyan]",
            border_style="cyan",
        ),
        Panel(
            f"CA : [green]{formater_montant(ca_jour)}[/green]\n"
            f"Bénéfice : [yellow]{formater_montant(benef_jour)}[/yellow]\n"
            f"Ventes : {len(ventes_jour)}",
            title=f"[bold green]AUJOURD'HUI ({aujourd})[/bold green]",
            border_style="green",
        ),
        Panel(
            f"CA total : [green]{formater_montant(ca_mois)}[/green]\n"
            f"  dont ventes : {formater_montant(ca_mois_ventes)}\n"
            f"  dont réparations : {formater_montant(rec_rep_mois)}\n"
            f"Bénéfice ventes : [yellow]{formater_montant(benef_mois)}[/yellow]\n"
            f"Dépenses : [red]{formater_montant(dep_mois)}[/red]\n"
            f"Résultat net : [bold {'green' if resultat_mois >= 0 else 'red'}]{formater_montant(resultat_mois)}[/bold {'green' if resultat_mois >= 0 else 'red'}]",
            title=f"[bold magenta]CE MOIS ({aujourd[:7]})[/bold magenta]",
            border_style="magenta",
        ),
        Panel(
            f"[bold yellow]{reps_en_cours}[/bold yellow] en attente / en cours\n"
            f"Recettes répa ce mois : [green]{formater_montant(rec_rep_mois)}[/green]",
            title="[bold yellow]RÉPARATIONS[/bold yellow]",
            border_style="yellow",
        ),
    ]

    console.print(Columns(panels, equal=True, expand=True))


# ──────────────────────────────────────────────────
#  Helpers d'affichage
# ──────────────────────────────────────────────────

def _afficher_mini_ventes(ventes: list):
    table = Table(box=box.SIMPLE, header_style="bold green", show_lines=False)
    table.add_column("Marque / Modèle")
    table.add_column("Qté", justify="center")
    table.add_column("Total", justify="right", style="green")
    table.add_column("Bénéfice", justify="right", style="yellow")
    table.add_column("Paiement")
    table.add_column("Client")

    for r in ventes:
        table.add_row(
            f"{r['marque']} {r['modele']}",
            str(r["quantite"]),
            formater_montant(r["prix_total"]),
            formater_montant(r["benefice"]),
            r["mode_paiement"],
            r["client_nom"] or "-",
        )

    console.print("\n[bold]Ventes :[/bold]")
    console.print(table)


def _afficher_depenses_par_categorie(depenses: list):
    from collections import defaultdict
    par_cat: dict[str, float] = defaultdict(float)
    for d in depenses:
        par_cat[d["categorie"]] += d["montant"]

    table = Table(box=box.SIMPLE, header_style="bold red")
    table.add_column("Catégorie")
    table.add_column("Montant", justify="right", style="red")

    for cat, montant in sorted(par_cat.items(), key=lambda x: -x[1]):
        table.add_row(cat, formater_montant(montant))

    console.print("\n[bold]Dépenses par catégorie :[/bold]")
    console.print(table)


def _afficher_resume(
    nb_ventes: int,
    ca_ventes: float,
    benefice_ventes: float,
    recettes_rep: float,
    ca_total: float,
    total_depenses: float,
    resultat_net: float,
):
    couleur_net = "green" if resultat_net >= 0 else "red"
    signe = "+" if resultat_net >= 0 else ""

    console.print()
    console.rule("[bold]RÉSUMÉ FINANCIER[/bold]")
    console.print(f"  Nombre de ventes       : [bold]{nb_ventes}[/bold]")
    console.print(f"  CA ventes              : [green]{formater_montant(ca_ventes)}[/green]")
    console.print(f"  Bénéfice brut ventes   : [yellow]{formater_montant(benefice_ventes)}[/yellow]")
    console.print(f"  Recettes réparations   : [green]{formater_montant(recettes_rep)}[/green]")
    console.print(f"  [bold]CA TOTAL               : [green bold]{formater_montant(ca_total)}[/green bold][/bold]")
    console.print(f"  Total dépenses         : [red]{formater_montant(total_depenses)}[/red]")
    console.rule()
    console.print(f"  [bold]RÉSULTAT NET           : [{couleur_net} bold]{signe}{formater_montant(resultat_net)}[/{couleur_net} bold][/bold]")
    console.rule()
