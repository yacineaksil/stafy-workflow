from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box

from database import get_connection
from utils import (
    console, aujourd_hui, saisir_float, saisir_int,
    saisir_date, choisir_parmi, formater_montant, maintenant
)
from stock import get_telephones_disponibles, decrementer_stock, afficher_stock

MODES_PAIEMENT = ["espèces", "mobile money", "carte bancaire", "virement", "crédit"]


def menu_ventes():
    while True:
        console.print("\n[bold green]═══ GESTION DES VENTES ═══[/bold green]")
        console.print("  [cyan]1[/cyan]. Enregistrer une vente")
        console.print("  [cyan]2[/cyan]. Historique des ventes")
        console.print("  [cyan]3[/cyan]. Rechercher une vente")
        console.print("  [cyan]4[/cyan]. Annuler une vente")
        console.print("  [cyan]0[/cyan]. Retour")

        choix = Prompt.ask("\n[bold]Votre choix[/bold]")
        if choix == "1":
            enregistrer_vente()
        elif choix == "2":
            historique_ventes()
        elif choix == "3":
            rechercher_vente()
        elif choix == "4":
            annuler_vente()
        elif choix == "0":
            break


def enregistrer_vente():
    console.print("\n[bold green]── Enregistrer une vente ──[/bold green]")

    disponibles = get_telephones_disponibles()
    if not disponibles:
        console.print("[yellow]Aucun téléphone disponible en stock.[/yellow]")
        return

    # Afficher les disponibles
    table = Table(box=box.SIMPLE, header_style="bold magenta")
    table.add_column("ID", style="dim")
    table.add_column("Marque")
    table.add_column("Modèle")
    table.add_column("Couleur")
    table.add_column("Stockage")
    table.add_column("État")
    table.add_column("Qté dispo", justify="center", style="green")
    table.add_column("Prix vente", justify="right", style="green")

    for r in disponibles:
        table.add_row(
            str(r["id"]),
            r["marque"],
            r["modele"],
            r["couleur"] or "-",
            r["stockage"] or "-",
            r["etat"],
            str(r["quantite"]),
            formater_montant(r["prix_vente"]),
        )
    console.print(table)

    id_tel = saisir_int("ID du téléphone à vendre")
    telephone = next((r for r in disponibles if r["id"] == id_tel), None)
    if not telephone:
        console.print("[red]Téléphone introuvable ou indisponible.[/red]")
        return

    console.print(f"\n[cyan]{telephone['marque']} {telephone['modele']}[/cyan] — stock : {telephone['quantite']}")
    quantite = saisir_int("Quantité à vendre", defaut=1)
    if quantite > telephone["quantite"]:
        console.print(f"[red]Stock insuffisant (disponible : {telephone['quantite']})[/red]")
        return

    prix_unitaire = saisir_float("Prix de vente unitaire (FCFA)", defaut=telephone["prix_vente"])
    imei = Prompt.ask("IMEI vendu (optionnel)", default=telephone["imei"] or "").strip() or None
    client_nom = Prompt.ask("Nom du client (optionnel)", default="").strip() or None
    client_tel = Prompt.ask("Téléphone client (optionnel)", default="").strip() or None
    mode_paiement = choisir_parmi(MODES_PAIEMENT, "Mode de paiement (numéro)")
    notes = Prompt.ask("Notes (optionnel)", default="").strip() or None

    prix_total = prix_unitaire * quantite
    cout_achat = telephone["prix_achat"] * quantite
    benefice = prix_total - cout_achat

    console.print(f"\n[bold]Récapitulatif :[/bold]")
    console.print(f"  Article    : [cyan]{telephone['marque']} {telephone['modele']}[/cyan]")
    console.print(f"  Quantité   : {quantite}")
    console.print(f"  Prix unit. : {formater_montant(prix_unitaire)}")
    console.print(f"  Total      : [green bold]{formater_montant(prix_total)}[/green bold]")
    console.print(f"  Bénéfice   : [green]{formater_montant(benefice)}[/green]")
    console.print(f"  Paiement   : {mode_paiement}")

    if not Confirm.ask("\nConfirmer la vente ?"):
        console.print("[yellow]Vente annulée.[/yellow]")
        return

    with get_connection() as conn:
        conn.execute(
            """INSERT INTO ventes
               (telephone_id, marque, modele, imei, quantite, prix_unitaire, prix_total,
                cout_achat, benefice, date_vente, client_nom, client_telephone, mode_paiement, notes)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (id_tel, telephone["marque"], telephone["modele"], imei, quantite,
             prix_unitaire, prix_total, cout_achat, benefice, maintenant(),
             client_nom, client_tel, mode_paiement, notes)
        )
        conn.commit()

    decrementer_stock(id_tel, quantite)
    console.print(f"\n[green bold]✓ Vente enregistrée ! Montant encaissé : {formater_montant(prix_total)}[/green bold]")


def historique_ventes(date_debut: str | None = None, date_fin: str | None = None, silent: bool = False) -> list:
    with get_connection() as conn:
        if date_debut and date_fin:
            rows = conn.execute(
                """SELECT * FROM ventes WHERE date(date_vente) BETWEEN ? AND ?
                   ORDER BY date_vente DESC""",
                (date_debut, date_fin)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM ventes ORDER BY date_vente DESC").fetchall()

    if not silent:
        _afficher_tableau_ventes(rows, f"HISTORIQUE DES VENTES{' (' + date_debut + ' → ' + date_fin + ')' if date_debut else ''}")
    return list(rows)


def _afficher_tableau_ventes(rows: list, titre: str = "VENTES"):
    table = Table(title=f"[bold]{titre}[/bold]", box=box.ROUNDED, show_lines=True, header_style="bold magenta")
    table.add_column("ID", style="dim", width=4)
    table.add_column("Date")
    table.add_column("Marque")
    table.add_column("Modèle")
    table.add_column("IMEI", style="dim")
    table.add_column("Qté", justify="center")
    table.add_column("Prix unit.", justify="right")
    table.add_column("Total", justify="right", style="green")
    table.add_column("Bénéfice", justify="right", style="yellow")
    table.add_column("Paiement")
    table.add_column("Client")

    for r in rows:
        table.add_row(
            str(r["id"]),
            r["date_vente"][:16],
            r["marque"],
            r["modele"],
            r["imei"] or "-",
            str(r["quantite"]),
            formater_montant(r["prix_unitaire"]),
            formater_montant(r["prix_total"]),
            formater_montant(r["benefice"]),
            r["mode_paiement"],
            r["client_nom"] or "-",
        )

    console.print()
    console.print(table)

    if rows:
        total_ca = sum(r["prix_total"] for r in rows)
        total_ben = sum(r["benefice"] for r in rows)
        console.print(f"[bold]CA total : [green]{formater_montant(total_ca)}[/green]  |  Bénéfice total : [yellow]{formater_montant(total_ben)}[/yellow][/bold]")


def rechercher_vente():
    terme = Prompt.ask("Rechercher par client, marque ou modèle").strip().lower()
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT * FROM ventes WHERE
               lower(client_nom) LIKE ? OR lower(marque) LIKE ? OR lower(modele) LIKE ?
               ORDER BY date_vente DESC""",
            (f"%{terme}%", f"%{terme}%", f"%{terme}%")
        ).fetchall()
    _afficher_tableau_ventes(rows, f"Résultats pour « {terme} »")


def annuler_vente():
    console.print("[dim]Affichage des 20 dernières ventes...[/dim]")
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM ventes ORDER BY date_vente DESC LIMIT 20").fetchall()
    _afficher_tableau_ventes(rows, "DERNIÈRES VENTES")

    id_vente = saisir_int("ID de la vente à annuler")
    with get_connection() as conn:
        vente = conn.execute("SELECT * FROM ventes WHERE id=?", (id_vente,)).fetchone()
        if not vente:
            console.print("[red]Vente introuvable.[/red]")
            return

        console.print(f"\n[yellow]Annulation de la vente #{id_vente} : {vente['marque']} {vente['modele']} — {formater_montant(vente['prix_total'])}[/yellow]")
        if not Confirm.ask("Confirmer l'annulation et remettre en stock ?"):
            return

        # Remettre en stock
        if vente["telephone_id"]:
            conn.execute(
                "UPDATE telephones SET quantite = quantite + ? WHERE id=?",
                (vente["quantite"], vente["telephone_id"])
            )
        conn.execute("DELETE FROM ventes WHERE id=?", (id_vente,))
        conn.commit()
    console.print("[green]✓ Vente annulée et stock restauré.[/green]")
