# Stafy – Assistante Exécutive Email

Agent IA de gestion d'emails pour dirigeants. Analyse, priorise, rédige des réponses et produit un briefing exécutif quotidien.

**Stack 2026 · Gratuit · Self-hosted · IMAP universel**

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        Votre VM                         │
│                                                         │
│  ┌─────────┐   ┌──────────────┐   ┌─────────────────┐  │
│  │  Nginx  │──▶│  FastAPI     │──▶│  SQLite         │  │
│  │  :443   │   │  + Scheduler │   │  stafy.db       │  │
│  └─────────┘   └──────┬───────┘   └─────────────────┘  │
│                        │                                │
│           ┌────────────┴────────────┐                   │
│           ▼                         ▼                   │
│  ┌──────────────┐         ┌──────────────────┐          │
│  │  IMAP        │         │  Ollama (gratuit)│          │
│  │  Votre mail  │         │  qwen2.5:7b      │          │
│  └──────────────┘         └──────────────────┘          │
└─────────────────────────────────────────────────────────┘
```

**Flux :** Toutes les 30 min → lecture IMAP → Claude/Ollama analyse → briefing → dashboard

---

## Prérequis

| Composant | Minimum | Recommandé |
|-----------|---------|-----------|
| RAM VM | 8 Go | 16 Go |
| CPU | 2 cœurs | 4 cœurs |
| Stockage | 10 Go | 20 Go |
| OS | Ubuntu 22.04+ | Ubuntu 24.04 |
| Python | 3.11+ | 3.12 |
| Docker | 24+ | latest |
| Accès email | IMAP/SSL | IMAP/SSL |

---

## Déploiement VM – Mode Docker (recommandé)

### 1. Cloner et configurer

```bash
git clone https://github.com/yacineaksil/stafy-workflow.git
cd stafy-workflow
cp .env.example .env
nano .env   # Remplir IMAP_* et DASHBOARD_PASSWORD
```

### 2. Générer le SSL (Let's Encrypt)

```bash
# Installer certbot si nécessaire
apt install certbot
make ssl-cert DOMAIN=stafy.votredomaine.com

# Puis éditer nginx/stafy.conf pour mettre votre domaine
```

### 3. Démarrer

```bash
make up
make model-in-docker   # Télécharge qwen2.5:7b dans Ollama (~4 Go)
```

Dashboard : **https://stafy.votredomaine.com**

---

## Déploiement VM – Mode Direct (sans Docker)

```bash
# 1. Installer Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:7b

# 2. Installer les dépendances Python
pip install -r requirements.txt

# 3. Configurer
cp .env.example .env && nano .env

# 4. Vérifier la configuration
make check

# 5. Tester avec des données de démo
make demo

# 6. Démarrer
make serve
```

### Service systemd (démarrage automatique)

```ini
# /etc/systemd/system/stafy.service
[Unit]
Description=Stafy Email Agent
After=network.target ollama.service

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/stafy-workflow
ExecStart=/usr/bin/python3 main.py serve
Restart=always
RestartSec=10
EnvironmentFile=/home/ubuntu/stafy-workflow/.env

[Install]
WantedBy=multi-user.target
```

```bash
systemctl enable --now stafy
```

---

## Configuration `.env`

```env
# LLM – choisir un provider
LLM_PROVIDER=ollama          # gratuit, local
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b

# Email IMAP (fonctionne avec tout fournisseur)
IMAP_HOST=mail.votredomaine.com
IMAP_PORT=993
IMAP_SSL=true
IMAP_USERNAME=vous@votredomaine.com
IMAP_PASSWORD=mot_de_passe

# Dashboard
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD=mot_de_passe_fort
SECRET_KEY=cle-aleatoire-longue-32-caracteres-min

# Agent
REFRESH_INTERVAL_MINUTES=30
MAX_EMAILS_PER_FETCH=50
```

---

## Modèles Ollama recommandés

| Modèle | RAM | Qualité | Usage |
|--------|-----|---------|-------|
| `qwen2.5:7b` | 6 Go | ★★★★ | **Recommandé** |
| `llama3.2:8b` | 6 Go | ★★★★ | Alternative |
| `mistral:7b` | 5 Go | ★★★ | RAM limitée |
| `qwen2.5:14b` | 12 Go | ★★★★★ | VM puissante |

```bash
ollama pull qwen2.5:7b   # Changer OLLAMA_MODEL dans .env
```

---

## Commandes

```bash
make check      # Vérifier config IMAP + LLM
make demo       # Données de démo
make serve      # Serveur local (dev)
make refresh    # Analyser les emails maintenant
make up         # Docker Compose
make logs       # Logs en temps réel
```

---

## Structure du projet

```
stafy-workflow/
├── main.py                    # CLI principal (typer)
├── config.py                  # Configuration (pydantic-settings)
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── nginx/
│   └── stafy.conf             # Config Nginx + SSL
├── src/
│   ├── llm/
│   │   ├── base.py            # Interface abstraite LLM
│   │   ├── factory.py         # Sélection automatique du provider
│   │   ├── ollama_client.py   # Client Ollama (gratuit, local)
│   │   └── anthropic_client.py # Client Anthropic (optionnel)
│   ├── connectors/
│   │   └── imap.py            # Connecteur IMAP universel
│   ├── agent/
│   │   ├── email_agent.py     # Orchestration agent (tool_use loop)
│   │   ├── tools.py           # Définitions outils Claude/Ollama
│   │   └── prompts.py         # Prompts système
│   ├── dashboard/
│   │   ├── app.py             # FastAPI + scheduler APScheduler
│   │   ├── auth.py            # Authentification session cookie
│   │   └── templates/         # Jinja2 (Tailwind CSS)
│   ├── models/
│   │   └── email.py           # Modèles Pydantic
│   └── storage/
│       └── database.py        # SQLite
└── legacy/                    # Code archivé (Gmail, cron)
```
