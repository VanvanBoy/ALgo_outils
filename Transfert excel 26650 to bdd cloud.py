# -*- coding: utf-8 -*-
"""
Created on Tue Dec 16 14:57:57 2025

@author: User
"""

import pandas as pd
from datetime import datetime
import mysql.connector
from mysql.connector import Error

def connect_to_db_prod():
    """ Connect to MySQL production database """
    try:
        connection = mysql.connector.connect(
            host='34.77.226.40',
            user='Vanvan',
            password='VoltR99!',
            database='cellules_batteries_cloud',
            port=3306,
            auth_plugin='mysql_native_password'
        )
        if connection.is_connected():
            db_info = connection.get_server_info()
            print("Connected to MySQL Server version ", db_info)
            return connection
    except Error as e:
        print("Error while connecting to MySQL", e)
        return None

# Chargement du fichier Excel
df = pd.read_excel(r"G:\Drive partagés\VoltR\4_Production\8_Picking\Fichiers pickings\Pickings en cours\Fichier post trait tom\Cellules 26650 Vanvan 291225.xlsx", header=None)

# Ligne des plateaux (index 2 car Python commence à 0)
plateau_names = df.iloc[2]

# Données sous les plateaux (à partir de la ligne 4 → index 3)
data = df.iloc[3:]

# Dictionnaire {nom_plateau: DataFrame}
dfs_plateaux = {}

for col_idx, plateau in plateau_names.items():
    if pd.notna(plateau):
        # Récupérer la colonne et supprimer les NaN
        elements = data[col_idx].dropna().reset_index(drop=True)

        # Créer le DataFrame
        dfs_plateaux[plateau] = pd.DataFrame({
            "numero_serie": elements
        })


dfs_plateaux = {
    plateau: df
    for plateau, df in dfs_plateaux.items()
    if not df.empty
}

positions_df = list(range(1, 127))  # index + 1
positions_plateau = [
    'A1','B1','C1','D1','E1','F1','G1','H1','I1',
    'I2','H2','G2','F2','E2','D2','C2','B2','A2',
    'A3','B3','C3','D3','E3','F3','G3','H3','I3',
    'I4','H4','G4','F4','E4','D4','C4','B4','A4',
    'A5','B5','C5','D5','E5','F5','G5','H5','I5',
    'I6','H6','G6','F6','E6','D6','C6','B6','A6',
    'A7','B7','C7','D7','E7','F7','G7','H7','I7',
    'I8','H8','G8','F8','E8','D8','C8','B8','A8',
    'A9','B9','C9','D9','E9','F9','G9','H9','I9',
    'I10','H10','G10','F10','E10','D10','C10','B10','A10',
    'A11','B11','C11','D11','E11','F11','G11','H11','I11',
    'I12','H12','G12','F12','E12','D12','C12','B12','A12',
    'A13','B13','C13','D13','E13','F13','G13','H13','I13',
    'I14','H14','G14','F14','E14','D14','C14','B14','A14'
]

index_to_plateau_pos = dict(zip(positions_df, positions_plateau))

date_insert = datetime.now()

conn=connect_to_db_prod()

prod_cursor=conn.cursor()

for plateau_name, df_plateau in dfs_plateaux.items():

    # Extraire l'ID plateau (ex: "Plateau 101" → 101)
    plateau_id = int(plateau_name.split()[-1])

    for idx, row in df_plateau.iterrows():

        # index + 1 → position logique
        pos_df = idx + 1

        # Sécurité si dépassement
        if pos_df not in index_to_plateau_pos:
            continue

        bdd_emplacement_num = index_to_plateau_pos[pos_df]
        code_emplacement = f"{plateau_id}-{bdd_emplacement_num}"

        numero_cellule = row["numero_serie"]

        query = """
            UPDATE emplacement
            SET est_occupe = %s,
                numero_serie = %s,
                date_attribution = %s,
                tension_plateau = %s
            WHERE code_emplacement = %s
        """

        params = (
            1,
            numero_cellule,
            date_insert,
            3.1,
            code_emplacement
            
        )

        prod_cursor.execute(query, params)
        print(f"{numero_cellule} -> {code_emplacement}")
        prod_cursor.execute("update cellule set tension_plateau =%s where numero_serie_cellule =%s",(3.1,numero_cellule))
        
        
conn.commit()
prod_cursor.close()
conn.close()

