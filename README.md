# Stafy – Assistante Exécutive Email

Agent IA de gestion d'emails avec dashboard exécutif, propulsé par Claude.

## Fonctionnalités

- **Lecture intelligente** – Connexion Gmail OAuth2, récupération automatique
- **Analyse IA** – Catégorisation, priorité 1→5, sentiment, points clés
- **Réponses suggérées** – Brouillons professionnels générés par Claude
- **Briefing exécutif** – Résumé quotidien + actions prioritaires + alertes
- **Dashboard PHP** – Hébergeable sur Hostinger shared hosting

---

## Déploiement Hostinger (hébergement partagé)

### Architecture

```
/home/USERNAME/
├── stafy-workflow/          ← code Python + base de données (hors web)
│   ├── .env                 ← clés API (jamais accessible depuis le web)
│   ├── token.json           ← token Gmail OAuth
│   ├── stafy.db             ← base de données SQLite
│   ├── cron_refresh.py      ← script appelé par le cron Hostinger
│   └── src/
└── public_html/
    └── stafy/               ← dashboard PHP (accessible depuis le web)
        ├── index.php
        ├── email.php
        ├── refresh.php
        └── ...
```

### Étape 1 – Cloner le dépôt sur Hostinger (SSH)

```bash
ssh USERNAME@VOTRE_SERVEUR_HOSTINGER
cd ~
git clone https://github.com/yacineaksil/stafy-workflow.git
cd stafy-workflow
```

### Étape 2 – Installer Python et les dépendances

```bash
pip3 install --user -r requirements.txt
```

### Étape 3 – Configurer les variables d'environnement

```bash
cp .env.example .env
nano .env   # Renseignez ANTHROPIC_API_KEY
```

### Étape 4 – Configurer Gmail OAuth (sur votre machine locale)

```bash
# Sur VOTRE machine (pas le serveur)
pip install -r requirements.txt
python setup_oauth.py    # Ouvre un navigateur pour l'autorisation Google
```

Puis uploadez `token.json` et `credentials.json` sur le serveur :

```bash
scp token.json credentials.json USERNAME@VOTRE_SERVEUR:/home/USERNAME/stafy-workflow/
```

### Étape 5 – Copier le dashboard PHP dans public_html

```bash
# Sur le serveur SSH
mkdir -p ~/public_html/stafy
cp -r ~/stafy-workflow/public/* ~/public_html/stafy/
```

Éditez `~/public_html/stafy/config.php` et remplacez `YOUR_USERNAME` :

```php
define('DB_PATH',      '/home/YOUR_USERNAME/stafy-workflow/stafy.db');
define('REFRESH_FLAG', '/home/YOUR_USERNAME/stafy-workflow/refresh.flag');
define('LOGS_DIR',     '/home/YOUR_USERNAME/stafy-workflow/logs');
```

### Étape 6 – Configurer le cron job (cPanel Hostinger)

Dans cPanel → **Cron Jobs**, ajoutez :

| Champ | Valeur |
|-------|--------|
| Minute | `*/30` |
| Heure | `*` |
| Jour | `*` |
| Mois | `*` |
| Jour sem. | `*` |
| Commande | `cd /home/YOUR_USERNAME/stafy-workflow && python3 cron_refresh.py >> logs/cron.log 2>&1` |

### Étape 7 – Premier test

```bash
# Sur le serveur SSH
cd ~/stafy-workflow
python3 main.py demo    # Charge des données de démonstration
```

Puis visitez : `https://VOTRE_DOMAINE/stafy/`

---

## Développement local

```bash
pip install -r requirements.txt
cp .env.example .env
python main.py demo     # Données de démo sans Gmail
python main.py serve    # Dashboard local → http://localhost:8000
```

Avec Gmail :
```bash
python setup_oauth.py   # OAuth (une seule fois)
python main.py refresh  # Analyser les emails
python main.py serve    # Dashboard
```

---

## Architecture du code

```
src/
├── agent/          # Agent Claude (tool_use loop)
│   ├── email_agent.py   # Orchestration principale
│   ├── tools.py         # Définitions des outils Claude
│   └── prompts.py       # Prompts système
├── connectors/
│   └── gmail.py         # Gmail OAuth2 + API
├── dashboard/
│   └── app.py           # FastAPI (développement local)
├── models/
│   └── email.py         # Modèles Pydantic
└── storage/
    └── database.py      # SQLite (partagé PHP ↔ Python)

public/                  # Dashboard PHP (Hostinger)
├── index.php            # Dashboard principal
├── email.php            # Détail d'un email
├── refresh.php          # Déclencheur de refresh
├── config.php           # Configuration chemins
└── includes/            # Composants réutilisables

cron_refresh.py          # Point d'entrée cron Hostinger
```
