# Stafy – Assistante Exécutive Email

Agent IA de gestion d'emails avec dashboard exécutif, propulsé par Claude.

## Fonctionnalités

- **Lecture intelligente** – Connexion Gmail OAuth2, récupération automatique des emails
- **Analyse IA** – Catégorisation, priorité (1-5), sentiment, points clés
- **Réponses suggérées** – Brouillons professionnels générés par Claude
- **Briefing exécutif** – Résumé quotidien + liste d'actions prioritaires
- **Dashboard** – Interface web élégante type secrétaire de direction

## Installation

```bash
pip install -r requirements.txt
cp .env.example .env
# Éditez .env avec votre clé API Anthropic
```

## Configuration Gmail

1. Créez un projet Google Cloud : https://console.cloud.google.com
2. Activez l'API Gmail
3. Créez des identifiants OAuth 2.0 (Application de bureau)
4. Téléchargez `credentials.json` dans le répertoire du projet
5. Lancez `python setup_oauth.py`

## Usage

```bash
# Tester avec des données de démo (sans Gmail)
python main.py demo
python main.py serve

# Avec Gmail réel
python main.py setup          # OAuth (une seule fois)
python main.py refresh        # Analyser les emails
python main.py serve          # Dashboard sur http://localhost:8000
```

## Architecture

```
src/
├── agent/          # Agent Claude (tool_use loop)
├── connectors/     # Connecteur Gmail API
├── dashboard/      # Dashboard FastAPI + Jinja2
├── models/         # Modèles Pydantic
└── storage/        # Base SQLite
```
