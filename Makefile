.PHONY: help install check demo serve refresh pull-model up down logs

SHELL := /bin/bash
OLLAMA_MODEL ?= qwen2.5:7b

help:
	@echo ""
	@echo "  Stafy – Assistante Exécutive Email"
	@echo ""
	@echo "  make install       Installer les dépendances Python"
	@echo "  make check         Vérifier la configuration"
	@echo "  make demo          Charger des données de démo"
	@echo "  make serve         Démarrer le serveur local"
	@echo "  make refresh       Analyser les emails maintenant"
	@echo "  make pull-model    Télécharger le modèle Ollama"
	@echo "  make up            Démarrer avec Docker Compose"
	@echo "  make down          Arrêter les containers"
	@echo "  make logs          Voir les logs en temps réel"
	@echo ""

install:
	pip install -r requirements.txt

check:
	python main.py check

demo:
	python main.py demo

serve:
	python main.py serve

refresh:
	python main.py refresh

pull-model:
	ollama pull $(OLLAMA_MODEL)

ssl-cert:
	@mkdir -p nginx/certs
	certbot certonly --standalone -d $(DOMAIN) \
		--cert-path nginx/certs/fullchain.pem \
		--key-path nginx/certs/privkey.pem

up:
	docker compose up -d
	@echo "Stafy démarré → https://localhost"
	@echo "Premier lancement : make pull-model (dans le container ollama)"

down:
	docker compose down

logs:
	docker compose logs -f stafy

model-in-docker:
	docker compose exec ollama ollama pull $(OLLAMA_MODEL)
