# -*- coding: utf-8 -*-
"""
Created on Thu Jul 31 17:04:21 2025

@author: User
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pymysql
import matplotlib.pyplot as plt

# Connexion avec PyMySQL
conn = pymysql.connect(
    host="127.0.0.1",
    user="root",
    password="VoltR99!",
    database="bdd_29072025",
    cursorclass=pymysql.cursors.DictCursor
)

# Étape 1 : batteries sans date_de_demantelement
with conn.cursor() as cursor:
    cursor.execute("""
        SELECT numero_serie_batterie
        FROM batterie
        WHERE etape_processus = 'demantelee' AND date_de_demantelement IS NULL
    """)
    df_batt = pd.DataFrame(cursor.fetchall())

# Étape 2 : date de cyclage min
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

# Fusion
df = df_batt.merge(df_dates, on='numero_serie_batterie', how='left')
df = df.merge(df_lots, on='numero_serie_batterie', how='left')

# Génération de dates
start_date = datetime(2024, 10, 12)
end_date = datetime(2025, 6, 4)
n = len(df)
dates_2024 = pd.date_range(start_date, datetime(2024, 12, 31), periods=int(n * 0.4))
dates_2025 = pd.date_range(datetime(2025, 1, 1), end_date, periods=n - len(dates_2024))
all_dates = pd.to_datetime(np.concatenate([dates_2024, dates_2025])).to_pydatetime()
np.random.shuffle(all_dates)

# Attribution
final_dates = []
for _, row in df.iterrows():
    cyclage = row["min_date_cyclage"]
    lot_date = row["date_lot"]

    max_date = pd.to_datetime(cyclage) - timedelta(days=7) if pd.notnull(cyclage) else end_date
    min_date = pd.to_datetime(lot_date) + timedelta(weeks=3) if pd.notnull(lot_date) else start_date

    valid_dates = [d for d in all_dates if min_date <= d <= max_date]
    if valid_dates:
        chosen = valid_dates[0]
        final_dates.append(chosen)
        all_dates = [d for d in all_dates if d != chosen]
    else:
        final_dates.append(None)

df["new_date_de_demantelement"] = final_dates

# Visualisation
df_valid = df[df["new_date_de_demantelement"].notnull()].copy()
df_valid["mois"] = df_valid["new_date_de_demantelement"].dt.to_period("M")
repartition = df_valid["mois"].value_counts().sort_index()

plt.figure(figsize=(10, 5))
repartition.plot(kind='bar')
plt.title("Répartition des dates de démantèlement par mois")
plt.xlabel("Mois")
plt.ylabel("Nombre de batteries")
plt.xticks(rotation=45)
plt.tight_layout()
plt.grid(True, axis='y', linestyle='--', alpha=0.6)
plt.show()

# Mise à jour en base
df_valid_update = df[df["new_date_de_demantelement"].notnull()]

df_valid_update.to_excel("batteries_demantelees_maj.xlsx", index=False)
print("Fichier Excel exporté : batteries_demantelees_maj.xlsx")

with conn.cursor() as cursor:
    for _, row in df_valid_update.iterrows():
        cursor.execute(
            "UPDATE batterie SET date_de_demantelement = %s WHERE numero_serie_batterie = %s",
            (row["new_date_de_demantelement"].strftime('%Y-%m-%d'), row["numero_serie_batterie"])
        )
        
print(f"{len(df_valid_update)} batteries seront mises à jour.")
#conn.commit()
conn.close()
