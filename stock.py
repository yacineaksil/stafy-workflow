from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box

from database import get_connection
from utils import (
    console, aujourd_hui, saisir_float, saisir_int,
    saisir_date, choisir_parmi, formater_montant
)

ETATS = ["neuf", "occasion", "reconditionné"]


def menu_stock():
    while True:
        console.print("\n[bold cyan]═══ GESTION DU STOCK ═══[/bold cyan]")
        console.print("  [cyan]1[/cyan]. Ajouter un téléphone (entrée)")
        console.print("  [cyan]2[/cyan]. Voir le stock complet")
        console.print("  [cyan]3[/cyan]. Rechercher un téléphone")
        console.print("  [cyan]4[/cyan]. Modifier un article")
        console.print("  [cyan]5[/cyan]. Réapprovisionner (ajouter quantité)")
        console.print("  [cyan]6[/cyan]. Supprimer un article")
        console.print("  [cyan]0[/cyan]. Retour")

        choix = Prompt.ask("\n[bold]Votre choix[/bold]")
        if choix == "1":
            ajouter_telephone()
        elif choix == "2":
            afficher_stock()
        elif choix == "3":
            rechercher_telephone()
        elif choix == "4":
            modifier_telephone()
        elif choix == "5":
            reapprovisionner()
        elif choix == "6":
            supprimer_telephone()
        elif choix == "0":
            break


def ajouter_telephone():
    console.print("\n[bold green]── Ajouter un téléphone ──[/bold green]")
    marque = Prompt.ask("Marque").strip()
    modele = Prompt.ask("Modèle").strip()
    imei = Prompt.ask("IMEI (optionnel)", default="").strip() or None
    couleur = Prompt.ask("Couleur (optionnel)", default="").strip() or None
    stockage = Prompt.ask("Stockage ex: 128Go (optionnel)", default="").strip() or None
    etat = choisir_parmi(ETATS, "État (numéro)")
    prix_achat = saisir_float("Prix d'achat (FCFA)")
    prix_vente = saisir_float("Prix de vente (FCFA)")
    quantite = saisir_int("Quantité", defaut=1)
    notes = Prompt.ask("Notes (optionnel)", default="").strip() or None

    with get_connection() as conn:
        try:
            conn.execute(
                """INSERT INTO telephones
                   (marque, modele, imei, couleur, stockage, prix_achat, prix_vente, quantite, etat, date_ajout, notes)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (marque, modele, imei, couleur, stockage, prix_achat, prix_vente, quantite, etat, aujourd_hui(), notes)
            )
            conn.commit()
            console.print(f"\n[green]✓ {marque} {modele} ajouté au stock avec succès.[/green]")
        except Exception as e:
            if "UNIQUE" in str(e):
                console.print("[red]Erreur : cet IMEI existe déjà dans la base.[/red]")
            else:
                console.print(f"[red]Erreur : {e}[/red]")


def afficher_stock(filtrer_disponible: bool = False) -> list:
    with get_connection() as conn:
        if filtrer_disponible:
            rows = conn.execute(
                "SELECT * FROM telephones WHERE quantite > 0 ORDER BY marque, modele"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM telephones ORDER BY marque, modele"
            ).fetchall()

    table = Table(
        title="[bold]STOCK DE TÉLÉPHONES[/bold]",
        box=box.ROUNDED,
        show_lines=True,
        header_style="bold magenta"
    )
    table.add_column("ID", style="dim", width=4)
    table.add_column("Marque", style="cyan")
    table.add_column("Modèle", style="cyan")
    table.add_column("IMEI", style="dim")
    table.add_column("Couleur")
    table.add_column("Stockage")
    table.add_column("État")
    table.add_column("Qté", justify="center")
    table.add_column("Prix achat", justify="right", style="yellow")
    table.add_column("Prix vente", justify="right", style="green")
    table.add_column("Date ajout", style="dim")

    for r in rows:
        qte_style = "green" if r["quantite"] > 0 else "red"
        table.add_row(
            str(r["id"]),
            r["marque"],
            r["modele"],
            r["imei"] or "-",
            r["couleur"] or "-",
            r["stockage"] or "-",
            r["etat"],
            f"[{qte_style}]{r['quantite']}[/{qte_style}]",
            formater_montant(r["prix_achat"]),
            formater_montant(r["prix_vente"]),
            r["date_ajout"],
        )

    console.print()
    console.print(table)

    valeur_stock = sum(r["prix_achat"] * r["quantite"] for r in rows)
    valeur_vente = sum(r["prix_vente"] * r["quantite"] for r in rows)
    total_unites = sum(r["quantite"] for r in rows)

    console.print(f"[bold]Total unités en stock :[/bold] {total_unites}")
    console.print(f"[bold]Valeur d'achat du stock :[/bold] {formater_montant(valeur_stock)}")
    console.print(f"[bold]Valeur de vente du stock :[/bold] {formater_montant(valeur_vente)}")

    return list(rows)


def rechercher_telephone():
    terme = Prompt.ask("Rechercher (marque, modèle ou IMEI)").strip().lower()
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT * FROM telephones
               WHERE lower(marque) LIKE ? OR lower(modele) LIKE ? OR imei LIKE ?
               ORDER BY marque, modele""",
            (f"%{terme}%", f"%{terme}%", f"%{terme}%")
        ).fetchall()

    if not rows:
        console.print("[yellow]Aucun résultat trouvé.[/yellow]")
        return

    table = Table(box=box.SIMPLE, header_style="bold magenta")
    table.add_column("ID", style="dim")
    table.add_column("Marque")
    table.add_column("Modèle")
    table.add_column("IMEI", style="dim")
    table.add_column("État")
    table.add_column("Qté", justify="center")
    table.add_column("Prix vente", justify="right", style="green")

    for r in rows:
        qte_style = "green" if r["quantite"] > 0 else "red"
        table.add_row(
            str(r["id"]),
            r["marque"],
            r["modele"],
            r["imei"] or "-",
            r["etat"],
            f"[{qte_style}]{r['quantite']}[/{qte_style}]",
            formater_montant(r["prix_vente"]),
        )

    console.print(table)


def modifier_telephone():
    afficher_stock()
    id_tel = saisir_int("ID du téléphone à modifier")
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM telephones WHERE id=?", (id_tel,)).fetchone()
        if not row:
            console.print("[red]Téléphone introuvable.[/red]")
            return

        console.print(f"\nModification de [cyan]{row['marque']} {row['modele']}[/cyan]")
        console.print("[dim](Laissez vide pour conserver la valeur actuelle)[/dim]")

        marque = Prompt.ask("Marque", default=row["marque"])
        modele = Prompt.ask("Modèle", default=row["modele"])
        couleur = Prompt.ask("Couleur", default=row["couleur"] or "")
        stockage = Prompt.ask("Stockage", default=row["stockage"] or "")
        prix_achat = saisir_float("Prix d'achat", defaut=row["prix_achat"])
        prix_vente = saisir_float("Prix de vente", defaut=row["prix_vente"])
        notes = Prompt.ask("Notes", default=row["notes"] or "")

        conn.execute(
            """UPDATE telephones SET marque=?, modele=?, couleur=?, stockage=?,
               prix_achat=?, prix_vente=?, notes=? WHERE id=?""",
            (marque, modele, couleur or None, stockage or None,
             prix_achat, prix_vente, notes or None, id_tel)
        )
        conn.commit()
    console.print("[green]✓ Téléphone mis à jour.[/green]")


def reapprovisionner():
    afficher_stock()
    id_tel = saisir_int("ID du téléphone à réapprovisionner")
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM telephones WHERE id=?", (id_tel,)).fetchone()
        if not row:
            console.print("[red]Téléphone introuvable.[/red]")
            return
        console.print(f"[cyan]{row['marque']} {row['modele']}[/cyan] — stock actuel : {row['quantite']}")
        qte = saisir_int("Quantité à ajouter", defaut=1)
        nouveau_prix_achat = saisir_float("Nouveau prix d'achat (ou Entrée pour garder)", defaut=row["prix_achat"])
        conn.execute(
            "UPDATE telephones SET quantite = quantite + ?, prix_achat=? WHERE id=?",
            (qte, nouveau_prix_achat, id_tel)
        )
        conn.commit()
    console.print(f"[green]✓ {qte} unité(s) ajoutée(s).[/green]")


def supprimer_telephone():
    afficher_stock()
    id_tel = saisir_int("ID du téléphone à supprimer")
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM telephones WHERE id=?", (id_tel,)).fetchone()
        if not row:
            console.print("[red]Téléphone introuvable.[/red]")
            return
        if Confirm.ask(f"Supprimer [red]{row['marque']} {row['modele']}[/red] définitivement ?"):
            conn.execute("DELETE FROM telephones WHERE id=?", (id_tel,))
            conn.commit()
            console.print("[green]✓ Article supprimé.[/green]")


def get_telephones_disponibles() -> list:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM telephones WHERE quantite > 0 ORDER BY marque, modele"
        ).fetchall()


def decrementer_stock(telephone_id: int, quantite: int):
    with get_connection() as conn:
        conn.execute(
            "UPDATE telephones SET quantite = quantite - ? WHERE id=?",
            (quantite, telephone_id)
        )
        conn.commit()
