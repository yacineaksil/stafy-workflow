# Stafy — Gestion de Boutique Téléphone

Système de gestion complet pour une boutique de téléphones, en Python, avec interface terminal colorée.

## Fonctionnalités

| Module | Fonctionnalités |
|---|---|
| **Stock** | Ajouter / modifier / supprimer des téléphones, réapprovisionnement, valeur du stock |
| **Ventes** | Enregistrer une vente, historique, recherche, annulation avec remise en stock |
| **Réparations** | Dépôt, suivi du statut, livraison, gestion des avances |
| **Finances** | Rapport journalier, mensuel, par période, chiffre d'affaires, dépenses |
| **Tableau de bord** | Résumé instantané : stock, CA du jour, résultat du mois, réparations en cours |

## Installation

```bash
pip install rich
```

## Lancement

```bash
python main.py
```

## Structure des fichiers

```
main.py          — Point d'entrée, menu principal
database.py      — Initialisation SQLite (boutique_data.db)
stock.py         — Gestion du stock / entrées
ventes.py        — Gestion des ventes / sorties
reparations.py   — Gestion des réparations
finances.py      — Rapports financiers et dépenses
utils.py         — Fonctions utilitaires communes
```

## Base de données

Stockage local dans `boutique_data.db` (SQLite, aucun serveur requis).

Tables : `telephones`, `ventes`, `reparations`, `depenses`
