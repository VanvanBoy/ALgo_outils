# -*- coding: utf-8 -*-
"""
Created on Tue Dec 10 19:36:31 2024

@author: User
"""
import re
import pandas as pd
import mysql.connector
from mysql.connector import Error
import numpy as np
from tkinter import messagebox
from datetime import datetime
"""
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
"""
def selection_fut(type_produit,numero_serie,cursor):
        
        cursor.execute("SELECT bib.poids FROM ref_cellule AS bib JOIN cellule AS cell ON bib.reference_cellule = cell.reference_cellule WHERE cell.numero_serie_cellule = %s",(numero_serie,))
        poids = cursor.fetchall()[0][0]
        poids= float(poids)
        type_fut="eco_org_pap"
        cursor.execute("SELECT id_fut from fut_recyclage WHERE exutoire=%s and etat_fut=%s limit 1",(type_fut,"en cours"))
        fut=cursor.fetchall()

        if not fut : 
            messagebox.showerror("Erreur !", "Aucun fut d'exutoire Screlec n'est ouvert")
        
        else :
            cursor.execute("SELECT id_fut,poids from fut_recyclage WHERE exutoire=%s and etat_fut=%s limit 1",(type_fut,"en cours"))
            data_fut=cursor.fetchall()
            fut,poids_fut=data_fut[0]
            poids_tot= poids_fut + poids 
            cursor.execute("UPDATE fut_recyclage SET poids=%s where id_fut=%s",(poids_tot,fut))
            
            emplacement = 'fut'+' '+str(fut)
            
            return emplacement, fut, type_fut
        
# Function to read Excel file
def lire_excel(fichier_excel):
    return pd.read_excel(fichier_excel)

# Function to connect to the MySQL database
def connecter_bdd(host, database, user, password):
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            auth_plugin='mysql_native_password'
        )
        if conn.is_connected():
            print("Connexion réussie à la base de données MySQL")
            return conn
    except Error as e:
        print(f"Erreur de connexion à MySQL: {e}")
        return None

# Function to find a replacement for a given cell
def trouver_remplacement(cellule, df_disponibles,capa_origine,resi_origine):
    #df_filtre = df_disponibles[df_disponibles['capacite_decharge_cellule_mesuree'] >= capa_origine]
    df_filtre = df_disponibles
    df_filtre['ecart_capacite'] = np.abs(df_filtre['capacite_cyclee'] - capa_origine)
    df_filtre['ecart_resistance'] = np.abs(df_filtre['resistance_interne_cyclee'] - resi_origine)
    df_filtre['ecart_total'] = 50*df_filtre['ecart_capacite'] + df_filtre['ecart_resistance']
    meilleure_cellule = df_filtre.loc[df_filtre['ecart_total'].idxmin()]
    return meilleure_cellule

# Function to update the 'cellules' table
def maj_bdd_origine(conn, id_cellule,commentaire=None):
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE cellule SET disponibilite = %s, affectation_produit = NULL, commentaire = %s WHERE numero_serie_cellule = %s",
            ("NON DISPO", commentaire, id_cellule)
        )
        conn.commit()
    except Error as e:
        print(f"Erreur lors de la mise à jour de la BDD: {e}")
    finally:
        cursor.close()
        
def maj_bdd_remplaçante(conn, id_cellule, produit, commentaire=None):
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE cellule SET disponibilite = %s, affectation_produit = %s, commentaire = %s WHERE numero_serie_cellule = %s",
            ("NON DISPO",produit, commentaire, id_cellule)
        )
        conn.commit()
    except Error as e:
        print(f"Erreur lors de la mise à jour de la BDD: {e}")
    finally:
        cursor.close()

# Function to insert into 'remplacement' table
def inserer_remplacement(conn, origine, remplaçante, produit, cause, tension=None):
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO remplacement (numero_serie_cellule_origine, numero_serie_cellule_remplaçante, produit_voltr, cause, tension) VALUES (%s, %s, %s, %s, %s)",
            (origine, remplaçante, produit, cause, tension)
        )
        conn.commit()
    except Error as e:
        print(f"Erreur lors de l'insertion dans la BDD: {e}")
    finally:
        cursor.close()

# Function to insert into 'recyclage_dechet' table
def inserer_recyclage(conn, numero_serie):
    cursor = conn.cursor()
    date_du_jour=datetime.now()
    try:
        fut,num_fut,type_fut=selection_fut("Cellule",numero_serie,cursor)
        insert_query = "INSERT INTO recyclage (numero_serie,type_objet,sur_site,date_rebut,id_fut) VALUES (%s,%s,%s,%s,%s)"
        cursor.execute(insert_query, (numero_serie,"Cellule",'oui',date_du_jour,num_fut))
        cursor.execute("UPDATE cellule SET disponibilite=%s, exutoire=%s WHERE numero_serie_cellule = %s", ("NON DISPO","recyclage",numero_serie))  
        conn.commit()
    except Error as e:
        print(f"Erreur lors de l'insertion dans la BDD: {e}")
    finally:
        cursor.close()

# Main function for processing replacements
def main(fichier_excel, host, database, user, password, ref_cell,type_carac):
    df_excel = lire_excel(fichier_excel)
    conn = connecter_bdd(host, database, user, password)

    if conn is None:
        return None

    try:
        query = "SELECT numero_serie_cellule, reference_cellule, capacite_cyclee, resistance_interne_cyclee, disponibilite FROM cellule WHERE disponibilite = 'DISPO' and reference_cellule = %s and type_carac= %s"
        df_disponibles = pd.read_sql(query, conn, params=[ref_cell,type_carac])
        """
        file_path="C:/Users/User/Desktop/Plateaux 14042025/DEF.xlsx"
        list_plat=extract_long_strings_from_excel(file_path)
        df_disponibles = df_disponibles[df_disponibles['numero_serie_cellule'].isin(list_plat)]
        """

        remplacements = []

        for _, cellule in df_excel.iterrows():
            
            
            cause = cellule['Motif NC']
            numero_serie = cellule['N° cellule']
            produit = cellule['N° batterie']
            tension = cellule['Tension'] if not pd.isna(cellule['Tension']) else None
            produit = 'VB000'+str(produit)
            cursor=conn.cursor()
            cursor.execute("select capacite_cyclee,resistance_interne_cyclee from cellule where numero_serie_cellule=%s",(numero_serie,))
            data=cursor.fetchall()
            capa_origine=data[0][0]
            resi_origine=data[0][1]
            cursor.close()       
            
            meilleure_cellule = trouver_remplacement(cellule, df_disponibles,capa_origine,resi_origine)
            remplacements.append({
                'cellules d\'origine': numero_serie,
                'cellule remplaçante': meilleure_cellule['numero_serie_cellule'],
                'produit_voltr': produit,
                'capa_cellule_origine': capa_origine,
                'capa_cellule_remplaçante': meilleure_cellule['capacite_cyclee'],
                'resistance_cellule_origine': resi_origine,
                'resistance_cellule_remplaçante': meilleure_cellule['resistance_interne_cyclee']
            })

            if cause == "Non trouvée":
                
                # Update the database for the replacement
                maj_bdd_remplaçante(conn, meilleure_cellule['numero_serie_cellule'], produit)
                # Update the original cell as "introuvable"
                maj_bdd_origine(conn, numero_serie,"introuvable")
                inserer_remplacement(conn, numero_serie, meilleure_cellule['numero_serie_cellule'], produit, "introuvable")

            
            elif cause == "Tension":
                    # Handle tension-related issues
                    maj_bdd_origine(conn, numero_serie,"pb tension, mise de coté")
                    maj_bdd_remplaçante(conn, meilleure_cellule['numero_serie_cellule'], produit)
                    inserer_remplacement(conn, numero_serie, meilleure_cellule['numero_serie_cellule'], produit, "tension", tension)
                    inserer_recyclage(conn, numero_serie) 
            elif cause=='Déformation':
                    # Handle other non-conformity cases
                    maj_bdd_origine(conn, numero_serie,"remplacement non conformité")
                    maj_bdd_remplaçante(conn, meilleure_cellule['numero_serie_cellule'], produit)
                    inserer_remplacement(conn, numero_serie, meilleure_cellule['numero_serie_cellule'], produit, "déformation")
                    inserer_recyclage(conn, numero_serie)

            # Remove the selected replacement from available cells
            df_disponibles = df_disponibles[df_disponibles['numero_serie_cellule'] != meilleure_cellule['numero_serie_cellule']]

        # Generate the final replacement report
        df_remplacements = pd.DataFrame(remplacements)

        # Save the modified Excel file with replacement information
        chemin_rapport = "C:/Users/User/Desktop/Remplacements NA04062025.xlsx"
        df_remplacements.to_excel(chemin_rapport, index=False)

        print(f"Fichier Excel modifié sauvegardé sous {chemin_rapport}")

        # Return the DataFrame for further use
        return df_remplacements

    finally:
        conn.close()

# Use the main function with the uploaded file
#fichier_excel = "G:/Drive partagés/VoltR/4_Production/8_Picking/remplacement/Remplacement en cours/Remplacement NA 14042025.xlsx"
fichier_excel = "C:/Users/User/Desktop/Remplacement NA04062025.xlsx"
"""
host = "localhost"
database = "cellules_batteries_cloud"
user = "root"
password = "VoltR99!"
ref_cell='INR1865030Q'
"""
host = "34.77.226.40"
database = "cellules_batteries_cloud"
user = "Vanvan"
password = "VoltR99!"
ref_cell='INR1865035E'
type_carac="A.0.2"

rapport_final = main(fichier_excel, host, database, user, password, ref_cell,type_carac)

# Show the final report if available
rapport_final.head()