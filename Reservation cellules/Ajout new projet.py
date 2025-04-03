# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 12:43:31 2024

@author: User
"""

import pandas as pd
import mysql.connector


# Remplacez les informations suivantes par les vôtres
excel_file = "G:/.shortcut-targets-by-id/1IBkpO9vKkNoJkb1g0dz_fPdYNxx0ZGj7/VOLTR/14_Interface Sales   Dev   Prod/Proposition nomenclature interne VoltR.xlsx"
sheet_name = 'Vente de batterie'

# Lire les données depuis le fichier Excel
df = pd.read_excel(excel_file, sheet_name=sheet_name, usecols=['Client', 'Nom du projet'])
df.columns = ['client', 'project_name']  # Renommer les colonnes pour correspondre à la table SQL
df = df.dropna()
"""
# Connexion à la base de données MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="VoltR99!",
    port=3306,
    database="cellules_batteries_cloud",
    auth_plugin='mysql_native_password'
)
"""

# Connectez-vous à la base de données
conn = mysql.connector.connect(
    host="34.77.226.40",
    user="Vanvan",
    password="VoltR99!",
    database="cellules_batteries_cloud",
    auth_plugin='mysql_native_password'
)

cursor = conn.cursor()

# Préparer l'insertion des données
insert_query = "INSERT INTO project (client, project_name, etat) VALUES (%s, %s, %s)"

# Insérer les données ligne par ligne
for index, row in df.iterrows():
    
    project_id = row["project_name"] 
    cursor.execute("SELECT COUNT(*) FROM project WHERE project_name = %s", (project_id,))
    result = cursor.fetchone()
        
    if result[0] == 0:
        cursor.execute(insert_query, (row['client'], row['project_name'],'en cours'))

# Valider les transactions
conn.commit()

# Fermer la connexion
cursor.close()
conn.close()

print("Données insérées avec succès dans la table 'project'")
