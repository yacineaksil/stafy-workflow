"""
Script de configuration OAuth Google pour accès Gmail.

Prérequis :
1. Créer un projet Google Cloud : https://console.cloud.google.com
2. Activer l'API Gmail
3. Créer des identifiants OAuth 2.0 (type: Application de bureau)
4. Télécharger le fichier JSON et le renommer en 'credentials.json'
5. Lancer ce script : python setup_oauth.py
"""
import sys
from pathlib import Path

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
except ImportError:
    print("Installez d'abord les dépendances : pip install -r requirements.txt")
    sys.exit(1)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
]

CREDENTIALS_FILE = Path("credentials.json")
TOKEN_FILE = Path("token.json")


def setup():
    if not CREDENTIALS_FILE.exists():
        print(f"\n[ERREUR] Fichier '{CREDENTIALS_FILE}' introuvable.")
        print("\nSteps :")
        print("  1. Allez sur https://console.cloud.google.com")
        print("  2. Créez un projet ou sélectionnez un projet existant")
        print("  3. APIs & Services > Activer APIs > cherchez 'Gmail API' > Activer")
        print("  4. APIs & Services > Identifiants > Créer des identifiants > ID client OAuth")
        print("  5. Choisissez 'Application de bureau'")
        print("  6. Téléchargez le JSON et renommez-le 'credentials.json'")
        print("  7. Placez-le dans le répertoire du projet et relancez ce script")
        sys.exit(1)

    print("\nOuverture du navigateur pour l'authentification Google...")
    print("(Un onglet va s'ouvrir dans votre navigateur)")

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
    creds = flow.run_local_server(port=0)

    TOKEN_FILE.write_text(creds.to_json())
    print(f"\n[OK] Token sauvegardé dans '{TOKEN_FILE}'")
    print("Vous pouvez maintenant lancer Stafy : python main.py serve")


if __name__ == "__main__":
    setup()
