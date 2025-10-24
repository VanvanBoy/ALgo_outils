# -*- coding: utf-8 -*-
"""
Created on Mon Aug 18 17:46:31 2025

@author: User
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pymysql
import matplotlib.pyplot as plt

# ================================
# Paramètres généraux
# ================================
DB_CONFIG = dict(
    host="34.77.226.40",
    user="Vanvan",
    password="VoltR99!",
    database="cellules_batteries_cloud",
    cursorclass=pymysql.cursors.DictCursor
)

START_DATE = pd.Timestamp('2024-10-12')   # borne inf du calendrier global
END_DATE   = pd.Timestamp('2025-06-04')   # borne sup du calendrier global

# Montée en cadence
RAMP_START = pd.Timestamp('2025-03-01')  # début ramp-up
CAP_BEFORE = 15               # capacité/jour avant RAMP_START
CAP_AFTER  = 30                  # capacité/jour à partir de RAMP_START

# Règles de fenêtre
OFFSET_AFTER_LOT = pd.Timedelta(days=5)  # min = date_lot + 3 semaines
OFFSET_BEFORE_CY = pd.Timedelta(days=3)   # max = min_date_cyclage - 7 jours

RNG_SEED = 42  # reproductibilité


# ================================
# Connexion MySQL
# ================================
conn = pymysql.connect(**DB_CONFIG)

# Étape 1 : batteries sans date_de_demantelement
with conn.cursor() as cursor:
    cursor.execute("""
        SELECT numero_serie_batterie
        FROM batterie
        WHERE etape_processus = 'demantelee' AND date_de_demantelement IS NULL
    """)
    df_batt = pd.DataFrame(cursor.fetchall())

# Si aucune batterie concernée, on peut s'arrêter proprement
if df_batt.empty:
    print("Aucune batterie à mettre à jour (déjà démantelées ou non concernées).")
    conn.close()
    raise SystemExit

# Étape 2 : date de cyclage min par batterie
with conn.cursor() as cursor:
    cursor.execute("""
        SELECT numero_serie_batterie, MIN(date_cyclage) AS min_date_cyclage
        FROM cellule
        GROUP BY numero_serie_batterie
    """)
    df_dates = pd.DataFrame(cursor.fetchall())

# Étape 3 : date du lot
with conn.cursor() as cursor:
    cursor.execute("""
        SELECT b.numero_serie_batterie, r.date AS date_lot
        FROM batterie b
        JOIN ref_lot r ON b.num_lot = r.num_lot
        WHERE b.etape_processus = 'demantelee' AND b.date_de_demantelement IS NULL
    """)
    df_lots = pd.DataFrame(cursor.fetchall())

# ================================
# Fusion & préparation
# ================================
df = df_batt.merge(df_dates, on='numero_serie_batterie', how='left')
df = df.merge(df_lots, on='numero_serie_batterie', how='left')

# Cast des colonnes en datetime
for col in ['min_date_cyclage', 'date_lot']:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

# Fenêtres mini / maxi
df['min_window'] = np.where(df['date_lot'].notna(),
                            df['date_lot'] + OFFSET_AFTER_LOT,
                            START_DATE)
df['max_window'] = np.where(df['min_date_cyclage'].notna(),
                            df['min_date_cyclage'] - OFFSET_BEFORE_CY,
                            END_DATE)

df['min_window'] = pd.to_datetime(df['min_window']).dt.normalize()
df['max_window'] = pd.to_datetime(df['max_window']).dt.normalize()
df['window_days'] = (df['max_window'] - df['min_window']).dt.days

# Diagnostics de base
nb_impossibles = (df['window_days'] < 0).sum()
print(f"Fenêtres impossibles (max < min) : {nb_impossibles} / {len(df)}")

# ================================
# Calendrier quotidien avec capacité/jour
# ================================
calendar = pd.DataFrame({
    'date': pd.date_range(START_DATE, END_DATE, freq='D')
})
calendar['capacity_left'] = np.where(calendar['date'] < RAMP_START, CAP_BEFORE, CAP_AFTER)

# ================================
# Attribution : tri par fenêtres les plus étroites
# ================================
rng = np.random.default_rng(RNG_SEED)
df_sorted = df.copy().sort_values(['window_days', 'min_window'], na_position='last').reset_index(drop=True)

assigned = [pd.NaT] * len(df_sorted)

for i, row in df_sorted.iterrows():
    mn, mx = row['min_window'], row['max_window']
    if pd.isna(mn) or pd.isna(mx) or (mx < mn):
        continue  # fenêtre impossible ou manquante
    mask = (calendar['date'] >= mn) & (calendar['date'] <= mx) & (calendar['capacity_left'] > 0)
    idxs = np.flatnonzero(mask.values)
    if idxs.size:
        pick_idx = int(rng.choice(idxs))     # choix aléatoire parmi les jours disponibles
        assigned[i] = calendar.at[pick_idx, 'date']
        calendar.at[pick_idx, 'capacity_left'] -= 1

df_sorted['new_date_de_demantelement'] = assigned

# Restaure l'ordre initial des batteries
df = df_sorted.sort_index()

# ================================
# Contrôles finaux
# ================================
nb_non_attrib = df['new_date_de_demantelement'].isna().sum()
print(f"Batteries attribuées : {len(df) - nb_non_attrib} / {len(df)}")
print(f"Batteries non attribuées (fenêtre vide ou capacité insuffisante) : {nb_non_attrib}")

# ================================
# Visualisation répartition (par mois)
# ================================
df_valid = df[df["new_date_de_demantelement"].notnull()].copy()
if not df_valid.empty:
    df_valid["mois"] = df_valid["new_date_de_demantelement"].dt.to_period("M")
    repartition = df_valid["mois"].value_counts().sort_index()

    plt.figure(figsize=(10, 5))
    repartition.plot(kind='bar')
    plt.title("Répartition des dates de démantèlement par mois (capacité/jour respectée)")
    plt.xlabel("Mois")
    plt.ylabel("Nombre de batteries")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.grid(True, axis='y', linestyle='--', alpha=0.6)
    plt.show()
else:
    print("Aucune date attribuée, graphique non généré.")

# ================================
# Export & Mise à jour BDD
# ================================
df_valid_update = df[df["new_date_de_demantelement"].notnull()].copy()

# Update SQL
with conn.cursor() as cursor:
    for _, row in df_valid_update.iterrows():
        cursor.execute(
            "UPDATE batterie SET date_de_demantelement = %s WHERE numero_serie_batterie = %s",
            (row["new_date_de_demantelement"].strftime('%Y-%m-%d'),
             row["numero_serie_batterie"])
        )

print(f"{len(df_valid_update)} batteries seront mises à jour (prêtes à commit).")

conn.commit()
conn.close()
