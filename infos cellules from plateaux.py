# -*- coding: utf-8 -*-
"""
Created on Mon Sep 22 11:22:30 2025

@author: User
"""

import pandas as pd
import mysql.connector

# Connexion à la base de données MySQL

connexion = mysql.connector.connect(
    host="34.77.226.40",     
    user="Vanvan",
    password="VoltR99!",
    database="cellules_batteries_cloud"
)

curseur = connexion.cursor()

query_emp="select numero_serie from emplacement where plateau_id between %s and %s"
params_emp=(37,40) #intervalle de plateau 
curseur.execute(query_emp,params_emp)
rows=curseur.fetchall()
list_num_serie = [r[0] for r in rows] 
    
# Exécution de la requête pour chaque numéro de série
data = []
for num_serie in list_num_serie:
    requete = """
        SELECT date_cyclage,
               etape_processus,
               capacite_cyclee,
               exutoire,
               reference_cellule,
               type_carac,
               disponibilite,
               affectation_produit,
               soh_cycle,
               resistance_interne_cyclee
        FROM cellule
        WHERE numero_serie_cellule = %s
    """
    curseur.execute(requete, (num_serie,))
    resultats = curseur.fetchall()

    # Pour chaque enregistrement retourné, on l'ajoute dans la liste 'data'
    for (date_test, etape_processus, capacite_decharge, exutoire, reference_cellule,type_carac,disponibilite,affectation_produit,soh,resistance) in resultats:
        data.append([
            num_serie,
            date_test,
            etape_processus,
            capacite_decharge,
            exutoire,
            reference_cellule,
            type_carac,
            disponibilite,
            affectation_produit,
            soh,
            resistance
            
        ])

#Construction du DataFrame final
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
        "affectation_produit",
        "soh",
        "resistance"
    ]
)

print(df_final)

# Fermeture de la connexion
curseur.close()
connexion.close()