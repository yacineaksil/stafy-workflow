"""
Stafy – Assistante Exécutive Email

Usage:
    python main.py serve          # Lancer le dashboard web
    python main.py refresh        # Analyser les emails maintenant
    python main.py setup          # Configurer l'authentification Gmail
    python main.py demo           # Charger des données de démo (sans Gmail)
"""
import sys
import argparse


def cmd_serve(args):
    import uvicorn
    from src.storage.database import init_db
    from config import settings
    from rich.console import Console

    console = Console()
    init_db()
    console.print(f"\n[bold green]Stafy démarre...[/bold green]")
    console.print(f"[blue]Dashboard : http://localhost:{settings.DASHBOARD_PORT}[/blue]\n")

    uvicorn.run(
        "src.dashboard.app:app",
        host=settings.DASHBOARD_HOST,
        port=settings.DASHBOARD_PORT,
        reload=False,
        log_level="warning",
    )


def cmd_refresh(args):
    from src.storage.database import init_db
    from src.connectors.gmail import GmailConnector
    from src.agent.email_agent import EmailAgent
    from rich.console import Console

    console = Console()
    init_db()

    console.print("\n[bold]Connexion à Gmail...[/bold]")
    gmail = GmailConnector()
    gmail.authenticate()
    console.print(f"[green]✓ Connecté en tant que : {gmail.user_email}[/green]")

    query = args.query or "is:unread"
    console.print(f"\n[bold]Récupération des emails (filtre: {query})...[/bold]")
    emails = gmail.get_messages(query=query)
    console.print(f"[green]✓ {len(emails)} emails récupérés[/green]")

    agent = EmailAgent()
    analyses, briefing = agent.run(emails)

    if briefing:
        console.print(f"\n[bold blue]Briefing :[/bold blue]")
        console.print(briefing.executive_summary)
        console.print(f"\n[green]✓ Analyse terminée. Lancez 'python main.py serve' pour voir le dashboard.[/green]\n")


def cmd_setup(args):
    import setup_oauth
    setup_oauth.setup()


def cmd_demo(args):
    """Charge des données de démonstration pour tester le dashboard sans Gmail."""
    from datetime import datetime
    from src.storage.database import init_db, save_email, save_analysis, save_briefing
    from src.models.email import Email, EmailAnalysis, DailyBriefing, EmailCategory, Priority
    from rich.console import Console

    console = Console()
    init_db()

    demo_emails = [
        Email(
            id="demo_001", thread_id="t001",
            subject="URGENT : Panne serveur production - Site inaccessible",
            sender="Jean Dupont", sender_email="j.dupont@client-premium.com",
            recipient="vous@company.com", date=datetime.now(),
            body="Bonjour,\n\nNotre site de production est inaccessible depuis 30 minutes. Nous perdons environ 5000€ par heure. Avez-vous constaté un incident de votre côté ?\n\nMerci de traiter cela en urgence absolue.\n\nCordialement,\nJean Dupont, DSI Client Premium",
            snippet="Notre site de production est inaccessible depuis 30 minutes...",
        ),
        Email(
            id="demo_002", thread_id="t002",
            subject="Proposition de partenariat stratégique Q3 2026",
            sender="Marie Laurent", sender_email="m.laurent@partner-corp.fr",
            recipient="vous@company.com", date=datetime.now(),
            body="Bonjour,\n\nSuite à notre rencontre lors du Forum BPO Paris, je souhaitais vous soumettre une proposition de partenariat qui pourrait générer 200K€ de revenus additionnels pour les deux parties.\n\nJe serais disponible pour un call cette semaine. Que pensez-vous de jeudi 14h ?\n\nCordialement,\nMarie Laurent\nDirectrice Développement – PartnerCorp",
            snippet="Suite à notre rencontre lors du Forum BPO Paris...",
        ),
        Email(
            id="demo_003", thread_id="t003",
            subject="Rapport mensuel mai 2026 – KPI et résultats",
            sender="Sophie Martin", sender_email="s.martin@company.com",
            recipient="vous@company.com", date=datetime.now(),
            body="Bonjour,\n\nVeuillez trouver ci-joint le rapport mensuel de mai 2026. Les KPI sont en hausse de 12% par rapport à l'objectif. Points notables : taux de satisfaction client à 94%, délai moyen de traitement réduit de 15%.\n\nBonne lecture.\n\nSophie",
            snippet="Rapport mensuel mai 2026 disponible. KPI en hausse de 12%...",
        ),
        Email(
            id="demo_004", thread_id="t004",
            subject="[Newsletter] Les tendances BPO & IA – Juin 2026",
            sender="BPO Insights", sender_email="newsletter@bpo-insights.fr",
            recipient="vous@company.com", date=datetime.now(),
            body="Ce mois-ci dans BPO Insights : L'IA générative révolutionne les centres de contact, automatisation des processus RPA en hausse...",
            snippet="Ce mois-ci dans BPO Insights : L'IA générative révolutionne...",
        ),
        Email(
            id="demo_005", thread_id="t005",
            subject="Relance : Facture impayée #F2026-0489 – Échéance dépassée",
            sender="Comptabilité Fournisseur", sender_email="compta@fournisseur-it.com",
            recipient="vous@company.com", date=datetime.now(),
            body="Madame, Monsieur,\n\nNous constatons que la facture #F2026-0489 d'un montant de 8 750€ TTC n'a pas été réglée à l'échéance du 31 mai 2026.\n\nNous vous demandons de procéder au règlement dans les 48 heures sous peine de pénalités de retard.\n\nCordialement,\nService Comptabilité",
            snippet="Facture #F2026-0489 de 8 750€ impayée, échéance dépassée...",
        ),
    ]

    demo_analyses = [
        EmailAnalysis(
            email_id="demo_001", category=EmailCategory.URGENT, priority=Priority.CRITIQUE,
            sentiment="urgent",
            summary="Panne de production critique chez Client Premium. Perte financière en cours (5000€/h).",
            key_points=["Site inaccessible depuis 30 min", "Perte de 5000€/heure", "Client Premium affecté"],
            action_required=True,
            action_description="Contacter l'équipe technique immédiatement et informer le client d'un délai de résolution",
            deadline="Immédiat",
            draft_reply="Bonjour Jean,\n\nNous avons bien pris en compte votre signalement et notre équipe technique est mobilisée en ce moment même pour identifier et résoudre l'incident.\n\nJe vous tiendrai informé dans les 15 prochaines minutes sur l'état d'avancement.\n\nToutes mes excuses pour la gêne occasionnée.\n\nCordialement,",
        ),
        EmailAnalysis(
            email_id="demo_002", category=EmailCategory.IMPORTANT, priority=Priority.HAUTE,
            sentiment="positif",
            summary="Proposition de partenariat à 200K€ potentiel de la part de PartnerCorp. Relance suite Forum BPO Paris.",
            key_points=["Potentiel 200K€ pour les deux parties", "Demande de call jeudi 14h", "Contexte Forum BPO Paris"],
            action_required=True,
            action_description="Confirmer ou proposer un autre créneau pour le call avec Marie Laurent",
            deadline="Cette semaine",
            draft_reply="Bonjour Marie,\n\nMerci pour votre message et cette opportunité de partenariat qui semble très prometteuse.\n\nJeudi 14h me convient parfaitement. Je vous envoie une invitation de calendrier.\n\nDans l'intervalle, n'hésitez pas à me faire parvenir votre proposition en amont afin que je puisse l'étudier.\n\nCordialement,",
        ),
        EmailAnalysis(
            email_id="demo_003", category=EmailCategory.NORMAL, priority=Priority.MOYENNE,
            sentiment="positif",
            summary="Rapport mensuel mai 2026 disponible avec des résultats positifs : +12% sur les KPI, 94% satisfaction client.",
            key_points=["KPI +12% vs objectif", "Satisfaction client 94%", "Délai traitement -15%"],
            action_required=False,
            draft_reply=None,
        ),
        EmailAnalysis(
            email_id="demo_004", category=EmailCategory.NEWSLETTER, priority=Priority.NEGLIGEABLE,
            sentiment="neutre",
            summary="Newsletter mensuelle BPO Insights sur les tendances IA et RPA.",
            key_points=["Tendances IA générative", "Automatisation RPA"],
            action_required=False,
            draft_reply=None,
        ),
        EmailAnalysis(
            email_id="demo_005", category=EmailCategory.URGENT, priority=Priority.HAUTE,
            sentiment="négatif",
            summary="Relance facture impayée de 8 750€ avec menace de pénalités. Échéance du 31/05 dépassée.",
            key_points=["Montant: 8 750€ TTC", "Facture #F2026-0489", "Menace de pénalités sous 48h"],
            action_required=True,
            action_description="Transmettre à la comptabilité pour paiement urgent ou contacter le fournisseur si erreur",
            deadline="2026-06-15",
            draft_reply="Madame, Monsieur,\n\nNous avons bien pris note de votre relance concernant la facture #F2026-0489.\n\nNous procédons à une vérification immédiate et vous confirmons le règlement dans les 48 heures.\n\nVeuillez nous excuser pour ce retard.\n\nCordialement,",
        ),
    ]

    demo_briefing = DailyBriefing(
        total_emails=5,
        urgent_count=2,
        important_count=1,
        action_required_count=3,
        executive_summary="Journée à haute intensité : 2 dossiers urgents requièrent votre attention immédiate. Une panne de production chez Client Premium génère des pertes financières en temps réel, et une facture impayée de 8 750€ doit être régularisée sous 48h. Par ailleurs, une opportunité de partenariat à 200K€ mérite d'être saisie rapidement.",
        priority_list=[
            "Résoudre la panne de production Client Premium (perte 5 000€/h en cours)",
            "Transmettre la facture #F2026-0489 à la comptabilité pour paiement sous 48h",
            "Confirmer le rendez-vous avec Marie Laurent de PartnerCorp – jeudi 14h",
        ],
        alerts=[
            "CRITIQUE : Incident de production en cours – client impacté financièrement",
            "Pénalités de retard imminentes sur la facture #F2026-0489",
        ],
    )

    for email in demo_emails:
        save_email(email)
    for analysis in demo_analyses:
        save_analysis(analysis)
    save_briefing(demo_briefing)

    console.print("[green]✓ Données de démo chargées avec succès[/green]")
    console.print("[blue]Lancez 'python main.py serve' pour voir le dashboard[/blue]")


def main():
    parser = argparse.ArgumentParser(
        description="Stafy – Assistante Exécutive Email",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command")

    serve_parser = subparsers.add_parser("serve", help="Lancer le dashboard web")

    refresh_parser = subparsers.add_parser("refresh", help="Analyser les emails Gmail")
    refresh_parser.add_argument("--query", default="is:unread", help="Filtre Gmail (défaut: is:unread)")

    subparsers.add_parser("setup", help="Configurer l'authentification Gmail")
    subparsers.add_parser("demo", help="Charger des données de démo")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    commands = {
        "serve": cmd_serve,
        "refresh": cmd_refresh,
        "setup": cmd_setup,
        "demo": cmd_demo,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
