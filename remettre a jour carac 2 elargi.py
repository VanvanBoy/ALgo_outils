# -*- coding: utf-8 -*-
"""
Created on Fri Jul 18 11:26:07 2025

@author: User
"""

import os
import mysql.connector
import pandas as pd

DOSSIER_PRINCIPAL = r"G:\Drive partagés\VoltR\4_Production\5_Cyclage\1_Résultats de cyclage\Fichiers traités"

def calculer_resistance_depuis_excel(fichier_excel, numero_serie_cellule):
    print(numero_serie_cellule)
    data = pd.read_excel(fichier_excel, sheet_name='record')

    df_7_last = data[data["Step Index"] == 7].tail(1)
    df_8_last = data[data["Step Index"] == 8].tail(1)
    df_tot = pd.concat([df_7_last, df_8_last]).sort_index()

    Tension = df_tot["Voltage(V)"].reset_index(drop=True)
    Courant = df_tot["Current(A)"].reset_index(drop=True)

    DeltaCourant = abs(Courant[1])
    DeltaTension = abs(Tension[1] - Tension[0])

    Resistance = (DeltaTension / DeltaCourant) * 1000
    return float(Resistance)

# Connexion à la BDD
conn = mysql.connector.connect(
    host="34.77.226.40",
    user='Vanvan',
    password='VoltR99!',
    database="cellules_batteries_cloud",
    auth_plugin='mysql_native_password'
)
cursor = conn.cursor(dictionary=True)

cursor.execute("""
    SELECT numero_serie_cellule, reference_cellule
    FROM cellule
    WHERE type_carac = 'A.0.2' AND disponibilite = 'dispo' AND commentaire IS NULL
""")
cellules = cursor.fetchall()

for cellule in cellules:
    numero_serie = cellule["numero_serie_cellule"]
    reference = cellule["reference_cellule"]
    fichier_trouve = None

    # Recherche dans le dossier bien rangé
    dossier_ref = os.path.join(DOSSIER_PRINCIPAL, reference)
    if os.path.isdir(dossier_ref):
        for f in os.listdir(dossier_ref):
            if f.startswith(numero_serie) and f.endswith(('.xlsx', '.xls')):
                fichier_trouve = os.path.join(dossier_ref, f)
                break

    # Si toujours rien trouvé, recherche dans tous les sous-dossiers
    if not fichier_trouve:
        for root, _, files in os.walk(DOSSIER_PRINCIPAL):
            for f in files:
                if f.startswith(numero_serie) and f.endswith(('.xlsx', '.xls')):
                    fichier_trouve = os.path.join(root, f)
                    print(f"[INFO] Fichier mal rangé trouvé pour {numero_serie} : {fichier_trouve}")
                    break
            if fichier_trouve:
                break

    if not fichier_trouve:
        print(f"[WARN] Aucun fichier trouvé pour {numero_serie}")
        continue

    try:
        resistance = calculer_resistance_depuis_excel(fichier_trouve, numero_serie)
        print(f"[OK] Résistance calculée pour {numero_serie} : {resistance:.4f}")

        cursor.execute("""
            UPDATE cellule
            SET resistance_interne_cyclee = %s, commentaire = %s
            WHERE numero_serie_cellule = %s
        """, (resistance, 'mal_rangé' if reference not in fichier_trouve else 'test', numero_serie))
        conn.commit()
    except Exception as e:
        print(f"[ERROR] Erreur pour {numero_serie} : {e}")

cursor.close()
conn.close()
print("✅ Mise à jour terminée.")
