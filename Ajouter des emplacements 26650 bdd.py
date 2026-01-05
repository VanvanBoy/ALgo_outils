# -*- coding: utf-8 -*-
"""
Created on Tue Dec 16 14:54:45 2025

@author: User
"""

import itertools
import string
from typing import Iterable, List, Tuple
import mysql.connector


# ========= Paramètres de connexion =========
DB_CONFIG = {
    "user": "Vanvan",
    "password": "VoltR99!",
    "host": "34.77.226.40",
    "database": "cellules_batteries_cloud",
    "auth_plugin": "mysql_native_password",  # adapte si besoin
}

# ========= Paramètres plateau =========
# Plateaux à (re)créer : 1–16, 37–47, 59–99 (plateau 17 conservé tel quel)
PLATEAU_RANGES = [(101, 114)]
N_LIGNES = 9   # A..P
N_COLONNES = 14   # 1..16

# Si True : on efface d'abord tout ce qui existe pour ces plateaux, avant de réinsérer proprement
DELETE_EXISTING_FIRST = True

# Taille des batchs pour executemany
BATCH_SIZE = 2000


def iter_plateau_ids(ranges: List[Tuple[int, int]]) -> Iterable[int]:
    """Génère tous les plateau_id des intervalles inclusifs."""
    for a, b in ranges:
        for p in range(a, b + 1):
            yield p


def build_rows_for_plateau(plateau_id: int) -> List[Tuple[int, int, int, str, int, None, None]]:
    """
    Construit les 256 lignes (16x16) pour un plateau donné.
    Retourne une liste de tuples correspondant aux colonnes :
    (plateau_id, ligne, colonne, code_emplacement, est_occupe, numero_serie, date_attribution)
    """
    letters = string.ascii_uppercase[:N_LIGNES]  # 'A'.. 'P'
    rows = []
    for ligne in range(1, N_LIGNES + 1):
        letter = letters[ligne - 1]
        for colonne in range(1, N_COLONNES + 1):
            code = f"{plateau_id}-{letter}{colonne}"
            rows.append((plateau_id, ligne, colonne, code, 0, None, None))
    return rows


def ensure_connection():
    return mysql.connector.connect(**DB_CONFIG)

def insert_rows(cursor, rows: List[Tuple[int, int, int, str, int, None, None]]) -> None:
    """Insère en batch les lignes construites."""
    sql = (
        "INSERT INTO emplacement "
        "(plateau_id, ligne, colonne, code_emplacement, est_occupe, numero_serie, date_attribution) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)"
    )
    # Batch pour éviter des requêtes trop grosses
    for i in range(0, len(rows), BATCH_SIZE):
        cursor.executemany(sql, rows[i : i + BATCH_SIZE])


def count_by_plateau(cursor, plateau_ids: List[int]) -> List[Tuple[int, int]]:
    """Retourne [(plateau_id, nb_lignes), ...] pour contrôle."""
    if not plateau_ids:
        return []
    placeholders = ", ".join(["%s"] * len(plateau_ids))
    sql = (
        f"SELECT plateau_id, COUNT(*) AS n FROM emplacement "
        f"WHERE plateau_id IN ({placeholders}) GROUP BY plateau_id ORDER BY plateau_id"
    )
    cursor.execute(sql, tuple(plateau_ids))
    return list(cursor.fetchall())


def main():
    plateau_ids = list(iter_plateau_ids(PLATEAU_RANGES))
    # Ne pas toucher au plateau 17 (non inclus dans nos ranges)
    print(f"Plateaux ciblés : {plateau_ids[0]}…{plateau_ids[-1]} (total {len(plateau_ids)})")

    conn = ensure_connection()
    conn.autocommit = False
    try:
        cur = conn.cursor()


        # Construction et insertion
        print("Construction des grilles 16×16 et insertion…")
        total_rows = 0
        for p in plateau_ids:
            rows = build_rows_for_plateau(p)
            insert_rows(cur, rows)
            total_rows += len(rows)

        print(f"Insertion terminée. {total_rows} lignes insérées (attendu {len(plateau_ids) * N_LIGNES * N_COLONNES}).")

        # Contrôle
        print("Contrôle des comptes par plateau :")
        for plateau_id, n in count_by_plateau(cur, plateau_ids):
            status = "OK" if n == N_LIGNES * N_COLONNES else f"ATTENTION ({n})"
            print(f"  - Plateau {plateau_id}: {n} lignes -> {status}")

        # Commit final
        conn.commit()
        print("Commit effectué ✅")

        # Conseils d’indexes (facultatif, à exécuter une seule fois si non présents) :
        print(
            "\nConseil (facultatif) : ajoute des index uniques pour éviter tout doublon futur :\n"
            "  ALTER TABLE emplacement ADD UNIQUE KEY ux_plateau_ligne_col (plateau_id, ligne, colonne);\n"
            "  ALTER TABLE emplacement ADD UNIQUE KEY ux_plateau_code (plateau_id, code_emplacement);\n"
            "Exécute ces requêtes manuellement une seule fois."
        )

    except Exception as e:
        conn.rollback()
        print("Erreur, rollback effectué ❌")
        raise
    finally:
        try:
            cur.close()
        except Exception:
            pass
        conn.close()


if __name__ == "__main__":
    main()