from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box

from database import get_connection
from utils import (
    console, aujourd_hui, saisir_float, saisir_int,
    saisir_date, choisir_parmi, formater_montant, maintenant
)

STATUTS = ["en_attente", "en_cours", "terminé", "livré", "non_réparable"]

STATUT_COULEURS = {
    "en_attente": "yellow",
    "en_cours": "blue",
    "terminé": "green",
    "livré": "dim",
    "non_réparable": "red",
}

STATUT_LABELS = {
    "en_attente": "En attente",
    "en_cours": "En cours",
    "terminé": "Terminé",
    "livré": "Livré",
    "non_réparable": "Non réparable",
}


def menu_reparations():
    while True:
        console.print("\n[bold yellow]═══ GESTION DES RÉPARATIONS ═══[/bold yellow]")
        console.print("  [cyan]1[/cyan]. Déposer un téléphone (nouveau dépôt)")
        console.print("  [cyan]2[/cyan]. Voir toutes les réparations")
        console.print("  [cyan]3[/cyan]. Réparations en attente / en cours")
        console.print("  [cyan]4[/cyan]. Mettre à jour le statut")
        console.print("  [cyan]5[/cyan]. Livrer un téléphone réparé")
        console.print("  [cyan]6[/cyan]. Rechercher une réparation")
        console.print("  [cyan]7[/cyan]. Supprimer une réparation")
        console.print("  [cyan]0[/cyan]. Retour")

        choix = Prompt.ask("\n[bold]Votre choix[/bold]")
        if choix == "1":
            deposer_telephone()
        elif choix == "2":
            afficher_reparations()
        elif choix == "3":
            afficher_reparations(filtrer_actives=True)
        elif choix == "4":
            mettre_a_jour_statut()
        elif choix == "5":
            livrer_telephone()
        elif choix == "6":
            rechercher_reparation()
        elif choix == "7":
            supprimer_reparation()
        elif choix == "0":
            break


def deposer_telephone():
    console.print("\n[bold yellow]── Dépôt de téléphone pour réparation ──[/bold yellow]")
    client_nom = Prompt.ask("Nom du client").strip()
    client_tel = Prompt.ask("Téléphone du client").strip()
    marque = Prompt.ask("Marque du téléphone").strip()
    modele = Prompt.ask("Modèle du téléphone").strip()
    imei = Prompt.ask("IMEI (optionnel)", default="").strip() or None
    probleme = Prompt.ask("Description du problème").strip()
    cout = saisir_float("Coût estimé de réparation (0 si inconnu)", defaut=0)
    avance = saisir_float("Avance reçue (FCFA)", defaut=0)
    date_depot = saisir_date("Date de dépôt", defaut=aujourd_hui())
    date_prevu = saisir_date("Date de rendu prévue (optionnel)", defaut="") if Confirm.ask("Définir une date de rendu prévue ?") else None
    technicien = Prompt.ask("Technicien assigné (optionnel)", default="").strip() or None
    notes = Prompt.ask("Notes (optionnel)", default="").strip() or None

    with get_connection() as conn:
        conn.execute(
            """INSERT INTO reparations
               (client_nom, client_telephone, marque_telephone, modele_telephone, imei,
                probleme, cout_reparation, avance_recue, date_depot, date_rendu_prevu,
                technicien, notes)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (client_nom, client_tel, marque, modele, imei, probleme,
             cout if cout > 0 else None, avance, date_depot, date_prevu, technicien, notes)
        )
        conn.commit()
        rep_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    console.print(f"\n[green]✓ Dépôt enregistré (réparation #{rep_id}).[/green]")
    if avance > 0:
        console.print(f"[green]  Avance encaissée : {formater_montant(avance)}[/green]")


def afficher_reparations(filtrer_actives: bool = False, silent: bool = False) -> list:
    with get_connection() as conn:
        if filtrer_actives:
            rows = conn.execute(
                "SELECT * FROM reparations WHERE statut IN ('en_attente','en_cours') ORDER BY date_depot DESC"
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM reparations ORDER BY date_depot DESC").fetchall()

    if not silent:
        titre = "RÉPARATIONS EN COURS" if filtrer_actives else "TOUTES LES RÉPARATIONS"
        _afficher_tableau_reparations(rows, titre)
    return list(rows)


def _afficher_tableau_reparations(rows: list, titre: str = "RÉPARATIONS"):
    table = Table(title=f"[bold]{titre}[/bold]", box=box.ROUNDED, show_lines=True, header_style="bold magenta")
    table.add_column("ID", style="dim", width=4)
    table.add_column("Client")
    table.add_column("Tél. client")
    table.add_column("Marque / Modèle")
    table.add_column("Problème")
    table.add_column("Coût", justify="right")
    table.add_column("Avance", justify="right", style="yellow")
    table.add_column("Reste", justify="right", style="red")
    table.add_column("Dépôt")
    table.add_column("Rendu prévu")
    table.add_column("Statut")

    for r in rows:
        cout = r["cout_reparation"] or 0
        avance = r["avance_recue"] or 0
        reste = cout - avance
        statut = r["statut"]
        couleur = STATUT_COULEURS.get(statut, "white")
        label = STATUT_LABELS.get(statut, statut)

        table.add_row(
            str(r["id"]),
            r["client_nom"],
            r["client_telephone"],
            f"{r['marque_telephone']} {r['modele_telephone']}",
            r["probleme"][:40] + ("..." if len(r["probleme"]) > 40 else ""),
            formater_montant(cout) if cout else "-",
            formater_montant(avance) if avance else "-",
            formater_montant(reste) if reste > 0 else "-",
            r["date_depot"],
            r["date_rendu_prevu"] or "-",
            f"[{couleur}]{label}[/{couleur}]",
        )

    console.print()
    console.print(table)
    console.print(f"[bold]Total : {len(rows)} réparation(s)[/bold]")


def mettre_a_jour_statut():
    afficher_reparations(filtrer_actives=True)
    id_rep = saisir_int("ID de la réparation à mettre à jour")
    with get_connection() as conn:
        rep = conn.execute("SELECT * FROM reparations WHERE id=?", (id_rep,)).fetchone()
        if not rep:
            console.print("[red]Réparation introuvable.[/red]")
            return

        console.print(f"\n[cyan]{rep['marque_telephone']} {rep['modele_telephone']}[/cyan] de [cyan]{rep['client_nom']}[/cyan]")
        console.print(f"Statut actuel : [{STATUT_COULEURS.get(rep['statut'],'white')}]{STATUT_LABELS.get(rep['statut'],rep['statut'])}[/]")

        nouveau_statut = choisir_parmi(STATUTS, "Nouveau statut (numéro)")

        nouveau_cout = None
        nouvelles_pieces = None
        if nouveau_statut in ("terminé", "livré"):
            if rep["cout_reparation"] is None:
                nouveau_cout = saisir_float("Coût final de réparation (FCFA)")
            nouvelles_pieces = Prompt.ask("Pièces utilisées (optionnel)", default=rep["pieces_utilisees"] or "").strip() or None

        technicien = Prompt.ask("Technicien (optionnel)", default=rep["technicien"] or "").strip() or None
        notes = Prompt.ask("Notes (optionnel)", default=rep["notes"] or "").strip() or None

        updates = {"statut": nouveau_statut, "technicien": technicien, "notes": notes}
        if nouveau_cout is not None:
            updates["cout_reparation"] = nouveau_cout
        if nouvelles_pieces is not None:
            updates["pieces_utilisees"] = nouvelles_pieces

        set_clause = ", ".join(f"{k}=?" for k in updates)
        conn.execute(
            f"UPDATE reparations SET {set_clause} WHERE id=?",
            list(updates.values()) + [id_rep]
        )
        conn.commit()
    console.print("[green]✓ Statut mis à jour.[/green]")


def livrer_telephone():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM reparations WHERE statut='terminé' ORDER BY date_depot DESC"
        ).fetchall()

    if not rows:
        console.print("[yellow]Aucune réparation terminée en attente de livraison.[/yellow]")
        return

    _afficher_tableau_reparations(rows, "RÉPARATIONS TERMINÉES — À LIVRER")
    id_rep = saisir_int("ID de la réparation à livrer")

    with get_connection() as conn:
        rep = conn.execute("SELECT * FROM reparations WHERE id=?", (id_rep,)).fetchone()
        if not rep or rep["statut"] != "terminé":
            console.print("[red]Réparation introuvable ou pas encore terminée.[/red]")
            return

        cout = rep["cout_reparation"] or 0
        avance = rep["avance_recue"] or 0
        reste = cout - avance

        console.print(f"\n[bold]Livraison — {rep['marque_telephone']} {rep['modele_telephone']}[/bold]")
        console.print(f"  Client      : {rep['client_nom']} ({rep['client_telephone']})")
        console.print(f"  Coût total  : {formater_montant(cout)}")
        console.print(f"  Avance payée: {formater_montant(avance)}")
        console.print(f"  Reste à payer: [bold red]{formater_montant(reste)}[/bold red]")

        complement = saisir_float("Montant complémentaire reçu", defaut=reste)

        if not Confirm.ask("Confirmer la livraison ?"):
            return

        conn.execute(
            """UPDATE reparations
               SET statut='livré', date_rendu_reel=?, avance_recue=avance_recue+?
               WHERE id=?""",
            (aujourd_hui(), complement, id_rep)
        )
        conn.commit()

    console.print(f"[green]✓ Téléphone livré ! Montant encaissé : {formater_montant(complement)}[/green]")


def rechercher_reparation():
    terme = Prompt.ask("Rechercher (nom client, marque, modèle)").strip().lower()
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT * FROM reparations WHERE
               lower(client_nom) LIKE ? OR lower(marque_telephone) LIKE ? OR lower(modele_telephone) LIKE ?
               OR client_telephone LIKE ?
               ORDER BY date_depot DESC""",
            (f"%{terme}%", f"%{terme}%", f"%{terme}%", f"%{terme}%")
        ).fetchall()
    _afficher_tableau_reparations(rows, f"Résultats pour « {terme} »")


def supprimer_reparation():
    id_rep = saisir_int("ID de la réparation à supprimer")
    with get_connection() as conn:
        rep = conn.execute("SELECT * FROM reparations WHERE id=?", (id_rep,)).fetchone()
        if not rep:
            console.print("[red]Réparation introuvable.[/red]")
            return
        if Confirm.ask(f"Supprimer la réparation #{id_rep} de {rep['client_nom']} ?"):
            conn.execute("DELETE FROM reparations WHERE id=?", (id_rep,))
            conn.commit()
            console.print("[green]✓ Réparation supprimée.[/green]")


def get_recettes_reparations(date_debut: str | None = None, date_fin: str | None = None) -> float:
    with get_connection() as conn:
        if date_debut and date_fin:
            rows = conn.execute(
                """SELECT avance_recue FROM reparations
                   WHERE statut='livré' AND date(date_rendu_reel) BETWEEN ? AND ?""",
                (date_debut, date_fin)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT avance_recue FROM reparations WHERE statut='livré'"
            ).fetchall()
    return sum(r["avance_recue"] for r in rows if r["avance_recue"])
