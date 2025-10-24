import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import mysql.connector
import matplotlib.pyplot as plt

# Connexion MySQL
conn = mysql.connector.connect(
    host="34.77.226.40",
    user="Vanvan",
    password="VoltR99!",
    database="bdd_29072025",
    auth_plugin='mysql_native_password',
    use_pure=True 
)
cursor = conn.cursor(dictionary=True,buffered=True)

# Étape 1 : Batteries concernées
cursor.execute("""
    SELECT b.numero_serie_batterie
    FROM batterie b
    WHERE b.etape_processus = 'demantelee' AND b.date_de_demantelement IS NULL
""")
df_batt = pd.DataFrame(cursor.fetchall())

# Étape 2 : Dates de cyclage min
cursor.execute("""
    SELECT c.numero_serie_batterie, MIN(c.date_cyclage) AS min_date_cyclage
    FROM cellule c
    GROUP BY c.numero_serie_batterie
""")
df_dates = pd.DataFrame(cursor.fetchall())

# Étape 3 : Date de lot

cursor.execute("""
    SELECT b.numero_serie_batterie, r.date AS date_lot
    FROM batterie b
    JOIN ref_lot r ON b.num_lot = r.num_lot
    WHERE b.etape_processus = 'demantelee' AND b.date_de_demantelement IS NULL
""")


df_lots = pd.DataFrame(cursor.fetchall())
df_lots["date_lot"] = pd.to_datetime(df_lots["date_lot"], errors='coerce')
# Fusion
df = df_batt.merge(df_dates, on="numero_serie_batterie", how="left")
df = df.merge(df_lots, on="numero_serie_batterie", how="left")

# Étape 4 : Génération de dates
start_date = datetime(2024, 10, 12)
end_date = datetime(2025, 6, 4)
n = len(df)
dates_2024 = pd.date_range(start_date, datetime(2024, 12, 31), periods=int(n * 0.4))
dates_2025 = pd.date_range(datetime(2025, 1, 1), end_date, periods=n - len(dates_2024))
all_dates = pd.to_datetime(np.concatenate([dates_2024, dates_2025])).to_pydatetime()
np.random.shuffle(all_dates)

# Étape 5 : Attribution avec contraintes
final_dates = []
for i, row in df.iterrows():
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

# Étape 6 : Visualisation
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

# Étape 7 : Mise à jour BDD
for _, row in df.iterrows():
    if row["new_date_de_demantelement"]:
        cursor.execute(
            "UPDATE batterie SET date_de_demantelement = %s WHERE numero_serie_batterie = %s",
            (row["new_date_de_demantelement"].strftime('%Y-%m-%d'), row["numero_serie_batterie"])
        )

#conn.commit()
cursor.close()
conn.close()
