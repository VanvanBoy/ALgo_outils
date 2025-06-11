# -*- coding: utf-8 -*-
"""
Created on Tue Apr  8 17:54:07 2025

@author: User
"""

import pandas as pd
import mysql.connector
import re

def extract_long_strings_from_excel(file_path, min_length=12):
    # Charger toutes les feuilles du fichier Excel
    xls = pd.ExcelFile(file_path)
    long_strings = []

    # Parcourir chaque feuille
    for sheet_name in xls.sheet_names:
        # Lire la feuille sous forme de DataFrame
        data = pd.read_excel(file_path, sheet_name=sheet_name)
        # Extraire toutes les valeurs sous forme de texte
        text_data = data.applymap(str).values.flatten()
        # Utiliser une expression régulière pour trouver les chaînes avec min_length ou plus
        pattern = rf'\b\w{{{min_length},}}\b'
        long_strings.extend(
            match.group() for item in text_data for match in re.finditer(pattern, item)
        )
    
    # Supprimer les doublons et retourner les résultats
    return list(set(long_strings))

# 1. Lecture de l'Excel
# Remplacez "votre_fichier.xlsx" par le chemin/noms du fichier Excel
##df_excel = pd.read_excel("C:/Users/User/Desktop/Plateaux NA 08042025/Plateaux ABC.xlsx")
#df_excel = pd.read_excel("C:/Users/User/Downloads/Remplacement cellules NA au 08042025.xlsx")

""" Cas ou le fichier est sous forme de colonnes"""
# Suppose que la première colonne contient les numéros de série
# On retire les doublons éventuels et les valeurs nulles
## list_num_serie = df_excel.iloc[:, 0].dropna().unique().tolist()

""" cas ou le fichier est sous forme de tableaux"""
file_path=r"C:\Users\User\Desktop\NA_23052025\Extraction 35E au 230525.xlsx"
list_num_serie = extract_long_strings_from_excel(file_path, min_length=12)

# 2. Connexion à la base de données MySQL
# Modifiez ces paramètres en fonction de votre configuration
connexion = mysql.connector.connect(
    host="34.77.226.40",      # ou l'IP de votre serveur
    user="Vanvan",
    password="VoltR99!",
    database="cellules_batteries_cloud"
)

curseur = connexion.cursor()

# 3. Exécution de la requête pour chaque numéro de série
data = []
for num_serie in list_num_serie:
    requete = """
        SELECT date_test,
               etape_processus,
               capacite_decharge_cellule_mesuree,
               exutoire,
               reference_cellule,
               type_carac,
               disponibilite,
               affectation_produit
        FROM cellules
        WHERE numero_serie_cellule = %s
    """
    curseur.execute(requete, (num_serie,))
    resultats = curseur.fetchall()

    # Pour chaque enregistrement retourné, on l'ajoute dans la liste 'data'
    for (date_test, etape_processus, capacite_decharge, exutoire, reference_cellule,type_carac,disponibilite,affectation_produit) in resultats:
        data.append([
            num_serie,
            date_test,
            etape_processus,
            capacite_decharge,
            exutoire,
            reference_cellule,
            type_carac,
            disponibilite,
            affectation_produit
            
        ])

# Fermeture de la connexion
curseur.close()
connexion.close()

# 4. Construction du DataFrame final
df_final = pd.DataFrame(
    data,
    columns=[
        "numero_serie_cellule",
        "date_test",
        "etape_processus",
        "capacite_decharge_cellule_mesuree",
        "exutoire",
        "reference_cellule",
        "type_carac",
        "disponibilite",
        "affectation_produit"
    ]
)

print(df_final)
