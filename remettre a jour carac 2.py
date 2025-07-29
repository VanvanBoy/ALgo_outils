# -*- coding: utf-8 -*-
"""
Created on Thu Jul 17 17:54:29 2025

@author: User
"""

import os
import mysql.connector
import pandas as pd

DOSSIER_PRINCIPAL = r"G:\Drive partagés\VoltR\4_Production\5_Cyclage\1_Résultats de cyclage\Fichiers traités"


def calculer_resistance_depuis_excel(fichier_excel,numero_serie_cellule):
    # Exemple fictif : moyenne d'une colonne 'Résistance'
    print(numero_serie_cellule)       
    
    #Resistance 
    
    #Extraire de la feuille 'record' les données d'interet enregistrées
    data = pd.read_excel(fichier_excel, sheet_name='record')
    
    # Dernière ligne où 'Step Index' == 6
    df_7_last = data[data["Step Index"] == 7].tail(1)
    
    # Toutes les lignes où 'Step Index' == 7
    df_8_last = data[data["Step Index"] == 8].tail(1)
    
    # Combiner
    df_tot = pd.concat([df_7_last,df_8_last])
    
    # Pour conserver l’ordre d’origine (si nécessaire) :
    df_tot = df_tot.sort_index()
    
    Tension= df_tot["Voltage(V)"]
    Tension.reset_index(drop=True, inplace=True)
    
    Courant=df_tot["Current(A)"]
    Courant.reset_index(drop=True, inplace=True)
  
    DeltaCourant=abs(Courant[1])

    #calcul de la variation de tension 
    DeltaTension=abs(Tension.tail(1).values[0]-Tension[0])
    #gestion du cas ou la variation de courant est nulle

    
    #Calcule de la Resistance en mOhm
    Resistance = (DeltaTension/DeltaCourant)*1000
    
    resistance_interne=float(Resistance)
    
    return resistance_interne


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
    WHERE type_carac = 'A.0.2' AND disponibilite = 'dispo' AND commentaire is null
""")
cellules = cursor.fetchall()


for cellule in cellules:
    numero_serie = cellule["numero_serie_cellule"]
    reference = cellule["reference_cellule"]

    dossier_ref = os.path.join(DOSSIER_PRINCIPAL, reference)

    if not os.path.isdir(dossier_ref):
        print(f"[WARN] Dossier introuvable pour {reference}")
        continue

    fichier_trouve = None
    for f in os.listdir(dossier_ref):
        if f.startswith(numero_serie) and f.endswith(('.xlsx', '.xls')):
            fichier_trouve = os.path.join(dossier_ref, f)
            break

    if not fichier_trouve:
        print(f"[WARN] Aucun fichier trouvé pour {numero_serie}")
        continue

    try:
        resistance = calculer_resistance_depuis_excel(fichier_trouve,numero_serie)
        print(f"[OK] Résistance calculée pour {numero_serie} : {resistance:.4f}")

        cursor.execute("""
            UPDATE cellule
            SET resistance_interne_cyclee = %s, commentaire=%s
            WHERE numero_serie_cellule = %s
        """, (resistance,'test', numero_serie))
        conn.commit()
    except Exception as e:
        print(f"[ERROR] Erreur pour {numero_serie} : {e}")

cursor.close()
conn.close()
print("✅ Mise à jour terminée.")
