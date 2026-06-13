#!/usr/bin/env python3
"""
Cron job Stafy – à appeler via cPanel :
  cd /home/USERNAME/stafy-workflow && python3 cron_refresh.py >> logs/cron.log 2>&1

Fréquence recommandée : toutes les 30 minutes (*/30 * * * *)
"""
import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

FLAG_FILE = Path("refresh.flag")
LOGS_DIR  = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def main():
    log("=== Stafy cron démarré ===")

    flag_triggered = FLAG_FILE.exists()
    if flag_triggered:
        log("Flag de refresh détecté depuis le dashboard")

    try:
        from src.storage.database import init_db
        from src.connectors.gmail import GmailConnector
        from src.agent.email_agent import EmailAgent

        init_db()

        log("Connexion à Gmail...")
        gmail = GmailConnector()
        gmail.authenticate()
        log(f"Connecté : {gmail.user_email}")

        emails = gmail.get_messages(query="is:unread newer_than:1d")
        log(f"{len(emails)} emails non lus récupérés")

        if not emails:
            log("Aucun email à analyser.")
        else:
            agent = EmailAgent()
            analyses, briefing = agent.run(emails)
            log(f"✓ {len(analyses)} emails analysés")
            if briefing:
                log(f"Briefing : {briefing.urgent_count} urgents, {briefing.important_count} importants")

    except FileNotFoundError as e:
        log(f"ERREUR : {e}")
        log("Lancez 'python setup_oauth.py' depuis votre machine locale pour configurer Gmail.")
        sys.exit(1)
    except Exception as e:
        log(f"ERREUR : {e}")
        sys.exit(1)
    finally:
        if flag_triggered and FLAG_FILE.exists():
            FLAG_FILE.unlink()
            log("Flag de refresh supprimé")

    log("=== Stafy cron terminé ===")


if __name__ == "__main__":
    main()
