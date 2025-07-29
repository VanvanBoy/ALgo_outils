import pandas as pd
import os
import mysql.connector
import datetime

date_now=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
# Connexion à la base de données MySQL
conn=mysql.connector.connect(
    host="34.77.226.40",
    user="Vanvan",
    password="VoltR99!",
    database="cellules_batteries_cloud",
    auth_plugin='mysql_native_password'
)

cursor=conn.cursor()

# Récupération des numéros de série des cellules d'origine
query = "SELECT numero_serie_cellule_origine FROM remplacement "
cursor.execute(query)
cellules_origine = [row[0] for row in cursor.fetchall()]

#récupération des cellules au recyclage 
query = "SELECT numero_serie FROM recyclage where type_objet= %s " 
param=("cellule",)
cursor.execute(query, param)
cellules_recyclage = [row[0] for row in cursor.fetchall()]

#Maj remplacement 
excel_path_dos=r"C:\Users\User\Desktop\Pb remplacement"
for file in os.listdir(excel_path_dos):
    if file.endswith('.xlsx'):
        excel_path = os.path.join(excel_path_dos, file)
        df=pd.read_excel(excel_path)
        for roww in df.iterrows():
            row=roww[1]
            cell_or=row["cellules d'origine"]
            cell_r=row["cellule remplaçante"]
            produit=row["produit_voltr"]
            if cell_or not in cellules_origine:
                query_insert = "INSERT INTO remplacement (numero_serie_cellule_origine, numero_serie_cellule_remplaçante, produit_voltr,date_remplacement) VALUES (%s, %s, %s,%s)"
                param=(cell_or, cell_r, produit, date_now)
                cursor.execute(query_insert, param)

                query_update = "Update cellule set disponibilite =%s, affectation_produit =%s where numero_serie_cellule =%s"
                param_update = ("non dispo", produit, cell_r)

                query_update2 = "Update cellule set disponibilite =%s, affectation_produit =%s where numero_serie_cellule =%s"
                param_update2 = ("non dispo", None, cell_or)

                if cell_or not in cellules_recyclage:
                    query_recyclage ='INSERT INTO recyclage (numero_serie, type_objet, date_rebut,cause,sur_site) VALUES (%s, %s, %s,%s,%s)'
                    param_recyclage = (cell_or, "cellule", date_now, "autres", "oui")
                    cursor.execute(query_recyclage, param_recyclage)

                cursor.execute(query_update, param_update)
                cursor.execute(query_update2, param_update2)
                conn.commit()
                print(f"Remplacement effectué pour {cell_or} avec {cell_r} pour le produit {produit}.")
            else:
                print(f"Le remplacement pour {cell_or} avec {cell_r} pour le produit {produit} a déjà été effectué.")
    
# Fermeture de la connexion
cursor.close()
conn.close()
print("Mise à jour des remplacements terminée.")












