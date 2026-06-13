"""
Stafy – Assistante Exécutive Email

Usage:
    python main.py serve       Démarre le serveur + scheduler automatique
    python main.py refresh     Analyse les emails maintenant (one-shot)
    python main.py demo        Charge des données de démo
    python main.py check       Vérifie la configuration (IMAP, LLM)
"""
import logging
import sys
import typer
from rich.console import Console
from rich.table import Table

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/stafy.log", encoding="utf-8"),
    ],
)

app_cli = typer.Typer(help="Stafy – Assistante Exécutive Email", add_completion=False)
console = Console()


@app_cli.command()
def serve(
    host: str = typer.Option(None, help="Host d'écoute"),
    port: int = typer.Option(None, help="Port d'écoute"),
    no_scheduler: bool = typer.Option(False, "--no-scheduler", help="Désactiver le refresh automatique"),
):
    """Démarre le dashboard web + scheduler de refresh automatique."""
    import uvicorn
    from src.storage.database import init_db
    from src.dashboard.app import app as fastapi_app, start_scheduler
    from config import settings

    init_db()

    if not no_scheduler:
        start_scheduler()

    _host = host or settings.DASHBOARD_HOST
    _port = port or settings.DASHBOARD_PORT

    console.print(f"\n[bold green]Stafy démarre[/bold green]")
    console.print(f"[blue]→ http://localhost:{_port}[/blue]")
    console.print(f"[dim]Refresh auto toutes les {settings.REFRESH_INTERVAL_MINUTES} min[/dim]\n")

    uvicorn.run(fastapi_app, host=_host, port=_port, log_level="warning")


@app_cli.command()
def refresh(
    query_folder: str = typer.Option("INBOX", "--folder", "-f", help="Dossier IMAP"),
    all_emails: bool = typer.Option(False, "--all", help="Inclure les emails déjà lus"),
):
    """Récupère et analyse les nouveaux emails maintenant."""
    from src.storage.database import init_db
    from src.connectors.imap import IMAPConnector
    from src.agent.email_agent import EmailAgent
    from config import settings

    if not settings.IMAP_HOST:
        console.print("[red]IMAP_HOST non configuré. Éditez votre fichier .env[/red]")
        raise typer.Exit(1)

    init_db()

    console.print(f"\n[bold]Connexion IMAP → {settings.IMAP_HOST}...[/bold]")
    with IMAPConnector() as imap:
        console.print(f"[green]✓ Connecté ({settings.IMAP_USERNAME})[/green]")
        emails = imap.get_messages(folder=query_folder, unread_only=not all_emails)

    console.print(f"[green]✓ {len(emails)} emails récupérés[/green]")

    if not emails:
        console.print("[yellow]Aucun email à analyser.[/yellow]")
        return

    agent = EmailAgent()
    analyses, briefing = agent.run(emails)

    if briefing:
        console.print(f"\n[bold blue]Briefing :[/bold blue] {briefing.executive_summary[:200]}")

    console.print(f"\n[green]✓ Terminé. Lancez 'python main.py serve' pour le dashboard.[/green]\n")


@app_cli.command()
def check():
    """Vérifie que la configuration est correcte."""
    from config import settings

    table = Table(title="Configuration Stafy", show_header=True)
    table.add_column("Paramètre", style="cyan")
    table.add_column("Valeur", style="white")
    table.add_column("Statut", style="green")

    checks = [
        ("LLM Provider",    settings.LLM_PROVIDER,    "✓"),
        ("IMAP Host",       settings.IMAP_HOST or "⚠ NON DÉFINI", "✓" if settings.IMAP_HOST else "✗"),
        ("IMAP Username",   settings.IMAP_USERNAME or "⚠ NON DÉFINI", "✓" if settings.IMAP_USERNAME else "✗"),
        ("IMAP Password",   "***" if settings.IMAP_PASSWORD else "⚠ NON DÉFINI", "✓" if settings.IMAP_PASSWORD else "✗"),
        ("Dashboard Port",  str(settings.DASHBOARD_PORT), "✓"),
        ("DB Path",         settings.STAFY_DB_PATH, "✓"),
    ]

    if settings.LLM_PROVIDER == "anthropic":
        checks.append(("Anthropic Key", "***" if settings.ANTHROPIC_API_KEY else "⚠ NON DÉFINI",
                        "✓" if settings.ANTHROPIC_API_KEY else "✗"))
    else:
        checks.append(("Ollama Host", settings.OLLAMA_HOST, "✓"))
        checks.append(("Ollama Model", settings.OLLAMA_MODEL, "✓"))

    for name, value, status in checks:
        table.add_row(name, str(value), status)

    console.print(table)

    # Test connexion IMAP
    if settings.IMAP_HOST:
        console.print("\n[bold]Test IMAP…[/bold]")
        try:
            from src.connectors.imap import IMAPConnector
            with IMAPConnector() as imap:
                console.print(f"[green]✓ IMAP OK ({settings.IMAP_USERNAME})[/green]")
        except Exception as e:
            console.print(f"[red]✗ IMAP ERREUR : {e}[/red]")

    # Test LLM
    console.print("[bold]Test LLM…[/bold]")
    try:
        from src.llm import get_llm_client
        llm = get_llm_client()
        console.print(f"[green]✓ LLM OK ({llm.name})[/green]")
    except Exception as e:
        console.print(f"[red]✗ LLM ERREUR : {e}[/red]")


@app_cli.command()
def demo():
    """Charge des données de démo pour tester le dashboard sans email réel."""
    from datetime import datetime
    from src.storage.database import init_db, save_email, save_analysis, save_briefing
    from src.models.email import Email, EmailAnalysis, DailyBriefing, EmailCategory, Priority

    init_db()

    emails = [
        Email(id="demo_001", thread_id="t001", subject="URGENT : Panne serveur production",
              sender="Jean Dupont", sender_email="j.dupont@client.com", recipient="vous@company.com",
              date=datetime.now(), body="Notre site est inaccessible depuis 30 min. Perte de 5000€/h.", snippet="", is_read=False, labels=[]),
        Email(id="demo_002", thread_id="t002", subject="Partenariat stratégique Q3 2026",
              sender="Marie Laurent", sender_email="m.laurent@partner.fr", recipient="vous@company.com",
              date=datetime.now(), body="Suite à notre rencontre, je vous soumets une proposition à 200K€.", snippet="", is_read=False, labels=[]),
        Email(id="demo_003", thread_id="t003", subject="Rapport mensuel mai 2026",
              sender="Sophie Martin", sender_email="s.martin@company.com", recipient="vous@company.com",
              date=datetime.now(), body="KPI en hausse de 12%. Satisfaction client 94%.", snippet="", is_read=False, labels=[]),
        Email(id="demo_004", thread_id="t004", subject="[Newsletter] Tendances BPO Juin 2026",
              sender="BPO Insights", sender_email="news@bpo-insights.fr", recipient="vous@company.com",
              date=datetime.now(), body="Ce mois-ci : IA générative et automatisation...", snippet="", is_read=True, labels=[]),
        Email(id="demo_005", thread_id="t005", subject="Facture impayée #F2026-0489",
              sender="Comptabilité", sender_email="compta@fournisseur.com", recipient="vous@company.com",
              date=datetime.now(), body="Facture de 8750€ impayée. Pénalités sous 48h.", snippet="", is_read=False, labels=[]),
    ]

    analyses = [
        EmailAnalysis(email_id="demo_001", category=EmailCategory.URGENT, priority=Priority.CRITIQUE,
                      sentiment="urgent", summary="Panne critique chez client premium. Perte financière en cours.",
                      key_points=["Site inaccessible 30 min", "5000€/h de pertes", "Client premium"],
                      action_required=True, action_description="Contacter l'équipe technique immédiatement", deadline="Immédiat",
                      draft_reply="Bonjour Jean,\n\nNotre équipe technique est mobilisée. Je vous tiens informé dans 15 minutes.\n\nCordialement,"),
        EmailAnalysis(email_id="demo_002", category=EmailCategory.IMPORTANT, priority=Priority.HAUTE,
                      sentiment="positif", summary="Opportunité partenariat 200K€. Relance Forum BPO Paris.",
                      key_points=["Potentiel 200K€", "Demande de call", "Contexte Forum BPO"],
                      action_required=True, action_description="Confirmer le créneau de rendez-vous", deadline="Cette semaine",
                      draft_reply="Bonjour Marie,\n\nVotre proposition m'intéresse beaucoup. Je confirme notre échange cette semaine.\n\nCordialement,"),
        EmailAnalysis(email_id="demo_003", category=EmailCategory.NORMAL, priority=Priority.MOYENNE,
                      sentiment="positif", summary="Bons résultats mai 2026. KPI +12%, satisfaction 94%.",
                      key_points=["KPI +12%", "Satisfaction 94%", "Délai traitement -15%"],
                      action_required=False, draft_reply=None),
        EmailAnalysis(email_id="demo_004", category=EmailCategory.NEWSLETTER, priority=Priority.NEGLIGEABLE,
                      sentiment="neutre", summary="Newsletter mensuelle BPO Insights.",
                      key_points=["Tendances IA", "Automatisation RPA"],
                      action_required=False, draft_reply=None),
        EmailAnalysis(email_id="demo_005", category=EmailCategory.URGENT, priority=Priority.HAUTE,
                      sentiment="négatif", summary="Facture impayée 8750€. Menace de pénalités sous 48h.",
                      key_points=["8750€ TTC", "Facture #F2026-0489", "Délai 48h"],
                      action_required=True, action_description="Transmettre à la comptabilité pour règlement urgent", deadline="2026-06-15",
                      draft_reply="Madame, Monsieur,\n\nNous procédons à la vérification et confirmons le règlement sous 48h.\n\nCordialement,"),
    ]

    briefing = DailyBriefing(
        total_emails=5, urgent_count=2, important_count=1, action_required_count=3,
        executive_summary="Journée haute intensité : panne de production chez un client premium génère des pertes immédiates, une facture de 8 750€ doit être réglée d'urgence, et une opportunité de partenariat à 200K€ attend votre confirmation.",
        priority_list=["Résoudre la panne production Client Premium (5 000€/h en cours)",
                       "Régler la facture #F2026-0489 sous 48h pour éviter les pénalités",
                       "Confirmer le rendez-vous avec Marie Laurent – partenariat 200K€"],
        alerts=["CRITIQUE : Incident production en cours – client impacté financièrement",
                "Pénalités imminentes sur facture #F2026-0489"],
    )

    for e in emails:
        save_email(e)
    for a in analyses:
        save_analysis(a)
    save_briefing(briefing)

    console.print("[green]✓ Données de démo chargées[/green]")
    console.print("[blue]→ python main.py serve[/blue]")


if __name__ == "__main__":
    app_cli()
