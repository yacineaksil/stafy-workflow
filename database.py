import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "boutique_data.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS telephones (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        marque          TEXT    NOT NULL,
        modele          TEXT    NOT NULL,
        imei            TEXT    UNIQUE,
        couleur         TEXT,
        stockage        TEXT,
        prix_achat      REAL    NOT NULL,
        prix_vente      REAL    NOT NULL,
        quantite        INTEGER NOT NULL DEFAULT 0,
        etat            TEXT    NOT NULL DEFAULT 'neuf',
        date_ajout      TEXT    NOT NULL,
        notes           TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS ventes (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        telephone_id    INTEGER,
        marque          TEXT    NOT NULL,
        modele          TEXT    NOT NULL,
        imei            TEXT,
        quantite        INTEGER NOT NULL DEFAULT 1,
        prix_unitaire   REAL    NOT NULL,
        prix_total      REAL    NOT NULL,
        cout_achat      REAL    NOT NULL,
        benefice        REAL    NOT NULL,
        date_vente      TEXT    NOT NULL,
        client_nom      TEXT,
        client_telephone TEXT,
        mode_paiement   TEXT    NOT NULL DEFAULT 'espèces',
        notes           TEXT,
        FOREIGN KEY (telephone_id) REFERENCES telephones(id)
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS reparations (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        client_nom          TEXT    NOT NULL,
        client_telephone    TEXT    NOT NULL,
        marque_telephone    TEXT    NOT NULL,
        modele_telephone    TEXT    NOT NULL,
        imei                TEXT,
        probleme            TEXT    NOT NULL,
        cout_reparation     REAL,
        avance_recue        REAL    NOT NULL DEFAULT 0,
        date_depot          TEXT    NOT NULL,
        date_rendu_prevu    TEXT,
        date_rendu_reel     TEXT,
        statut              TEXT    NOT NULL DEFAULT 'en_attente',
        technicien          TEXT,
        pieces_utilisees    TEXT,
        notes               TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS depenses (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        description     TEXT    NOT NULL,
        montant         REAL    NOT NULL,
        categorie       TEXT    NOT NULL DEFAULT 'divers',
        date_depense    TEXT    NOT NULL,
        notes           TEXT
    )
    """)

    conn.commit()
    conn.close()
