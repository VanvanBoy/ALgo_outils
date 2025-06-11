# -*- coding: utf-8 -*-
"""
Created on Wed Oct  2 11:55:58 2024

@author: VanvanBoy
"""
from mysql.connector import Error
import pandas as pd
import numpy as np
import mysql.connector
from datetime import datetime
import statistics  # Non utlisé mais permet de verifier qu'aucune connection n'est etablie 
                       # dans l'onglet grace au warning
                       
def extraire_batteries_a_traiter(connection):

    query = (
            "SELECT "
                "batt.Numero_serie_batterie, "
                "batt.num_lot, "
                "batt.reference_batterie_voltr, "
                "nl.fournisseur, "
                "bb.reference_cellule "
            "FROM "
                "batteries_recep as batt "
            "JOIN "
                "numero_lot as nl ON batt.num_lot = nl.lot "
            "JOIN "
                "bibliotheque_batteries as bb ON batt.reference_batterie_voltr = bb.reference_voltr "
            "WHERE batt.etape_processus = %s "
            "AND previsionnel_calcule is null "
            "AND exutoire is null"
            )   

            
    df = pd.read_sql(query, connection,params=('a demanteler',))
    

    grouped = df.groupby(['num_lot', 'reference_batterie_voltr'])

    # Créer une liste de DataFrames, un pour chaque groupe
    list_of_dfs = [group for _, group in grouped]
            
    return list_of_dfs
            
# Fonction pour se connecter à la base de données
def connecter_bdd(host, user, password, database):
    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            auth_plugin='mysql_native_password'
        )
        if connection.is_connected():
            print("Connexion réussie à la base de données")
            return connection
    except Error as e:
        print(f"Erreur lors de la connexion à la base de données : {e}")
        return None

# Fonction pour se déconnecter de la base de données
def deconnecter_bdd(connection):
    if connection.is_connected():
        connection.close()
        print("Déconnexion de la base de données réussie")
    else:
        print("La connexion était déjà fermée")

def determiner_tot_rebus_batterie(fournisseur,num_lot,ref_value_voltr,cursor):
    
    index_clos=[]
    df_rebus = pd.DataFrame(columns=['numero_lot', 'total_batterie', 'total recyclé','taux_rebus'])

    query = '''
    SELECT 

        (SUM(CASE WHEN etape_processus = 'a demanteler' AND exutoire IS NULL THEN 1 ELSE 0 END) / COUNT(*)) * 100 AS pourcentage_non_traitees
    FROM 
        batteries_recep
    WHERE 
        num_lot = %s
    '''

    # Exécuter la requête avec le paramètre
    cursor.execute(query, (num_lot,))

    # Récupérer le résultat
    taux_non_traite = float(cursor.fetchone()[0])
    
    if taux_non_traite < 80 :
        cursor.execute('SELECT num_lot, COUNT(*) AS total_batteries, SUM(CASE WHEN exutoire = %s THEN 1 ELSE 0 END) AS total_recyclees,(SUM(CASE WHEN exutoire = %s THEN 1 ELSE 0 END) / COUNT(*)) AS taux_rebus FROM batteries_recep WHERE num_lot = %s GROUP BY num_lot',('recyclage','recyclage',num_lot))
        rebus_lot=cursor.fetchall()[0]
        df = pd.DataFrame([rebus_lot], columns=['numero_lot', 'total_batterie', 'total recyclé','taux_rebus'])
        taux_rebus_lot=df['taux_rebus']
        return float(taux_rebus_lot[0])
        
    else:
        cursor.execute('select lot, etat from numero_lot where fournisseur =%s',(fournisseur,))
        
        carac_lot=cursor.fetchall()
        df_lots=pd.DataFrame(carac_lot)
        df_lots.reset_index(drop=True, inplace=True)
    
        for index, row in df_lots.iterrows():
            Numero_lot=row[0]
            etat_lot=row[1]
            if etat_lot == 'Clos' or etat_lot=='clos':
                index_clos.append(index)
            
        if index_clos:
            numeros_lots=df_lots[0]
             
        #if len(num_lots) != 1 or (len(num_lots) ==1 and num_lots[0] != num_lot):
        
            for i in index_clos:
                num_lot=numeros_lots[i]
                cursor.execute('SELECT num_lot, COUNT(*) AS total_batteries, SUM(CASE WHEN exutoire = %s THEN 1 ELSE 0 END) AS total_recyclees,(SUM(CASE WHEN exutoire = %s THEN 1 ELSE 0 END) / COUNT(*)) AS taux_rebus FROM batteries_recep WHERE num_lot = %s GROUP BY num_lot',('recyclage','recyclage',num_lot))
                rebus_lot_b=cursor.fetchall()
                if rebus_lot_b:
                    rebus_lot=rebus_lot_b[0]
                    df = pd.DataFrame([rebus_lot], columns=['numero_lot', 'total_batterie', 'total recyclé','taux_rebus'])
                    
                    df_rebus=pd.concat([df_rebus,df], ignore_index=True)
              
            moyenne_fournisseur = df_rebus['taux_rebus'].mean()
        
            return moyenne_fournisseur
        
        else :
             query = """
                 SELECT numero_serie_batterie 
                 FROM batteries_recep 
                 WHERE reference_batterie_voltr = %s
                 
             """
             
             # Exécution de la requête combinée
             param=(ref_value_voltr,)
             cursor.execute(query, param)
             num_serie_batteries = cursor.fetchall()
             
             # Vérification que num_serie_batteries n'est pas vide
             if num_serie_batteries:
                 num_serie_batteries = [row[0] for row in num_serie_batteries]
                 total_batts = len(num_serie_batteries)
    
                 format_strings = ','.join(['%s'] * len(num_serie_batteries))
                 cursor.execute(f"""
                     SELECT COUNT(*) 
                     FROM batteries_recep 
                     WHERE numero_serie_batterie IN ({format_strings}) 
                     AND exutoire = 'recyclage'
                 """, tuple(num_serie_batteries))
                 
                 recycled_batt_count = cursor.fetchone()[0]
             
                 # Calculer le taux de rebus
                 taux_rebus_ref = (recycled_batt_count / total_batts) 
                 
                 return taux_rebus_ref
             else:
                 cursor.execute("select count(*) from batteries_recep")
                 nombre_tot_batt=cursor.fetchall()[0][0]
                 cursor.execute("select count(*) from batteries_recep where exutoire is not null")
                 nombre_bat_recyclage=cursor.fetchall()[0][0]
                 taux_rebus_glob=float(nombre_bat_recyclage/nombre_tot_batt)
                 return taux_rebus_glob
             

        
def determiner_tot_rebus_cellule(num_lot,fournisseur,reference_cell, cursor):
    
    df_rebus = pd.DataFrame(columns=['numero_lot', 'total_cells', 'total recyclé','taux_rebus'])
    
    
    query = '''
    SELECT 
        (SUM(CASE WHEN etape_processus = 'demantelee' AND exutoire IS NULL THEN 1 ELSE 0 END) / COUNT(*)) * 100 AS pourcentage_non_traitees
    FROM 
        cellules
    WHERE 
        num_lot = %s
    '''

    # Exécuter la requête avec le paramètre
    cursor.execute(query, (num_lot,))
    result =cursor.fetchone()
    if result is None or result[0] is None:
        taux_non_traite = 100
    else :
        taux_non_traite = float(result[0])
    
    if taux_non_traite < 80 :
        cursor.execute('SELECT num_lot, COUNT(*) AS total_cellules, SUM(CASE WHEN exutoire = %s THEN 1 ELSE 0 END) AS total_recyclees,(SUM(CASE WHEN exutoire = %s THEN 1 ELSE 0 END) / COUNT(*)) AS taux_rebus FROM cellules WHERE num_lot = %s GROUP BY num_lot',('recyclage','recyclage',num_lot))
        rebus_lot=cursor.fetchall()[0]
        df = pd.DataFrame([rebus_lot], columns=['numero_lot', 'total_cells', 'total recyclé','taux_rebus'])
        taux_rebus_lot=df['taux_rebus']
        return float(taux_rebus_lot[0])
    
    cursor.execute("Select lot from numero_lot where fournisseur=%s",(fournisseur,))
    nums_lots_cells=cursor.fetchall()
    if nums_lots_cells:
        for num_lot_cell in nums_lots_cells:
            num_lot_act=num_lot_cell[0]
            cursor.execute('Select count(*) FROM cellules where num_lot=%s',(num_lot_act,))
            nb_cell_lot=cursor.fetchall()[0][0]
            if nb_cell_lot !=0:
                cursor.execute('SELECT num_lot, COUNT(*) AS total_cells, SUM(CASE WHEN exutoire = %s THEN 1 ELSE 0 END) AS total_recyclees,(SUM(CASE WHEN exutoire = %s THEN 1 ELSE 0 END) / COUNT(*)) AS taux_rebus FROM cellules WHERE num_lot = %s GROUP BY num_lot',('recyclage','recyclage',num_lot_act))
                rebus_lot=cursor.fetchall()[0]
                
                df = pd.DataFrame([rebus_lot], columns=['numero_lot', 'total_cells', 'total recyclé','taux_rebus'])
                
                df_rebus=pd.concat([df_rebus,df], ignore_index=True)
            
         
                taux_rebus_fournisseur = df_rebus['taux_rebus'].mean()
                
                return taux_rebus_fournisseur
            
            else :
                
                cursor.execute("Select Capacite_nominale_cellule, Courant_de_charge_max from bibliotheque where reference_cellule =%s ",(reference_cell,))
                capa_nom,c_max_dch=cursor.fetchall()[0]
                if capa_nom:
                    capa_nom=float(capa_nom)
                else:
                    capa_nom=0
                    
                if c_max_dch:
                    c_max_dch=float(c_max_dch)
                else :
                    c_max_dch=0
                cursor.execute("SELECT numero_serie_cellule FROM cellules WHERE reference_cellule IN (SELECT reference_cellule FROM bibliotheque WHERE Capacite_nominale_cellule BETWEEN %s AND %s AND Courant_de_charge_max BETWEEN %s AND %s)", (capa_nom*0.9, capa_nom*1.1, c_max_dch*0.9, c_max_dch*1.1))
                numero_series_cells_dom = cursor.fetchall()
                if numero_series_cells_dom:   
      
                     numero_series_cells_dom = [num[0] for num in numero_series_cells_dom]
                 
                     
                     total_cells = len(numero_series_cells_dom)
                 
                    
                     format_strings = ','.join(['%s'] * len(numero_series_cells_dom))
                     cursor.execute(f"""
                         SELECT COUNT(*) 
                         FROM cellules 
                         WHERE numero_serie_cellule IN ({format_strings}) 
                         AND exutoire = 'recyclage'
                     """, tuple(numero_series_cells_dom))
                     
                     recycled_cells_count = cursor.fetchone()[0]
                 
                     # Calculer le taux de rebus
                     taux_rebus_dom = float((recycled_cells_count / total_cells))
                     
                     return taux_rebus_dom
                else :
                    cursor.execute("select count(*) from cellules")
                    nombre_tot_cell=cursor.fetchall()[0][0]
                    cursor.execute("select count(*) from cellules where exutoire is not null")
                    nombre_cell_recyclage=cursor.fetchall()[0][0]
                    taux_rebus_glob=float(nombre_cell_recyclage/nombre_tot_cell)
                    return taux_rebus_glob

        
    else :
        
        cursor.execute("Select Capacite_nominale_cellule, Courant_de_charge_max from bibliotheque where reference_cellule =%s ",(reference_cell,))
        capa_nom,c_max_dch=cursor.fetchall()[0]
        capa_nom=float(capa_nom)
        c_max_dch=float(c_max_dch)
        cursor.execute("SELECT numero_serie_cellule FROM cellules WHERE reference_cellule IN (SELECT reference_cellule FROM bibliotheque WHERE Capacite_nominale_cellule BETWEEN %s AND %s AND Courant_de_charge_max BETWEEN %s AND %s)", (capa_nom*0.9, capa_nom*1.1, c_max_dch*0.9, c_max_dch*1.1))
        numero_series_cells_dom = cursor.fetchall()
        if numero_series_cells_dom:
             
             numero_series_cells_dom = [num[0] for num in numero_series_cells_dom]
         
             
             total_cells = len(numero_series_cells_dom)
         
            
             format_strings = ','.join(['%s'] * len(numero_series_cells_dom))
             cursor.execute(f"""
                 SELECT COUNT(*) 
                 FROM cellules 
                 WHERE numero_serie_cellule IN ({format_strings}) 
                 AND exutoire = 'recyclage'
             """, tuple(numero_series_cells_dom))
             
             recycled_cells_count = cursor.fetchone()[0]
         
             # Calculer le taux de rebus
             taux_rebus_dom = (recycled_cells_count / total_cells)
             
             return taux_rebus_dom
        else :
            cursor.execute("select count(*) from batteries_recep")
            nombre_tot_batt=cursor.fetchall()[0][0]
            cursor.execute("select count(*) from batteries_recep where exutoire is not null")
            nombre_bat_recyclage=cursor.fetchall()[0][0]
            taux_rebus_glob=float(nombre_bat_recyclage/nombre_tot_batt)
            return taux_rebus_glob
            
            

def determiner_soh(num_lot,nb_cells,ref_cell,cursor):
    cursor.execute('select numero_serie_cellule, SOH_cellule_determine,reference_cellule, num_lot from cellules where etape_processus =%s and num_lot=%s',('Testee',num_lot))
    cell_test=cursor.fetchall()   
    if cell_test :
        df = pd.DataFrame(cell_test, columns=['numero_serie_cellule', 'SOH_cellule_determine', 'reference_cellule','num_lot'])
        soh_cell_test = df['SOH_cellule_determine'].tolist()
        # Calculer la moyenne et l'écart-type de toute la liste
        mean = np.mean(soh_cell_test)
        std_dev = np.std(soh_cell_test)
        
        # Générer une nouvelle liste de 50 éléments selon une distribution normale avec les paramètres calculés
        new_soh = np.random.normal(loc=mean, scale=std_dev, size=nb_cells)
        soh_m= statistics.mean(new_soh)
        return new_soh,soh_m
    cursor.execute('Select lot from numero_lot where fournisseur in (select fournisseur from numero_lot where lot=%s)',(num_lot,))
    lots_fournisseur = cursor.fetchall()[0]
    if lots_fournisseur:
        for lot in lots_fournisseur:
            cursor.execute('select numero_serie_cellule, SOH_cellule_determine,reference_cellule, num_lot from cellules where etape_processus =%s and num_lot=%s',('Testee',lot))
            cell_test=cursor.fetchall()   
            if cell_test :
                df = pd.DataFrame(cell_test, columns=['numero_serie_cellule', 'SOH_cellule_determine', 'reference_cellule','num_lot'])
                soh_cell_test= df['SOH_cellule_determine'].tolist()
                # Calculer la moyenne et l'écart-type de toute la liste
                mean = np.mean(soh_cell_test)
                std_dev = np.std(soh_cell_test)
                
                # Générer une nouvelle liste de 50 éléments selon une distribution normale avec les paramètres calculés
                new_soh = np.random.normal(loc=mean, scale=std_dev, size=nb_cells)
                soh_m= statistics.mean(new_soh)
                return new_soh,soh_m
    cursor.execute('Select fournisseur from numero_lot where lot=%s',(num_lot,))
    fournisseur=cursor.fetchall()[0][0] 
    if fournisseur:
        cursor.execute('select numero_serie_cellule, SOH_cellule_determine,reference_cellule, num_lot from cellules where etape_processus =%s and num_lot in ( select lot from numero_lot where fournisseur =%s)',('Testee',fournisseur))
        cell_test=cursor.fetchall()   
        if cell_test :
            df = pd.DataFrame(cell_test, columns=['numero_serie_cellule', 'SOH_cellule_determine', 'reference_cellule','num_lot'])
            soh_cell_test = df['SOH_cellule_determine'].tolist()
            # Calculer la moyenne et l'écart-type de toute la liste
            mean = np.mean(soh_cell_test)
            std_dev = np.std(soh_cell_test)
            
            # Générer une nouvelle liste de 50 éléments selon une distribution normale avec les paramètres calculés
            new_soh = np.random.normal(loc=mean, scale=std_dev, size=nb_cells)
            soh_m= statistics.mean(new_soh)
            return new_soh,soh_m
        else :
            cursor.execute("Select Capacite_nominale_cellule, Courant_de_charge_max from bibliotheque where reference_cellule =%s ",(ref_cell,))
            capa_nom,c_max_dch=cursor.fetchall()[0]
            if capa_nom:
                capa_nom=float(capa_nom)
            else:
                capa_nom=0
                
            if c_max_dch:
                c_max_dch=float(c_max_dch)
            else :
                c_max_dch=0
            cursor.execute('''
    SELECT numero_serie_cellule, SOH_cellule_determine, reference_cellule,num_lot
    FROM cellules 
    WHERE etape_processus = %s 
    AND reference_cellule IN (
        SELECT reference_cellule 
        FROM bibliotheque 
        WHERE capacite_nominale_cellule BETWEEN %s AND %s 
        AND courant_de_charge_max BETWEEN %s AND %s
    )
''', ('Testee', capa_nom * 0.9, capa_nom * 1.1, c_max_dch * 0.9, c_max_dch * 1.1))

            cell_ref = cursor.fetchall()

            if cell_ref:
                df = pd.DataFrame(cell_ref, columns=['numero_serie_cellule', 'SOH_cellule_determine', 'reference_cellule','num_lot'])
                soh_cell_test = df['SOH_cellule_determine'].tolist()
                soh_cell_test = [x for x in soh_cell_test if not pd.isna(x)]
                
                # Calculer la moyenne et l'écart-type de toute la liste
                mean = np.mean(soh_cell_test)
                std_dev = np.std(soh_cell_test)
                
                # Générer une nouvelle liste de 50 éléments selon une distribution normale avec les paramètres calculés
                new_soh = np.random.normal(loc=mean, scale=std_dev, size=nb_cells)
                soh_m= statistics.mean(new_soh)
                return new_soh,soh_m
            else :
                cursor.execute('select numero_serie_cellule, SOH_cellule_determine,reference_cellule, num_lot from cellules where etape_processus =%s',('Testee',))
                cell_test_glob=cursor.fetchall()  
                df = pd.DataFrame(cell_test_glob, columns=['numero_serie_cellule', 'SOH_cellule_determine', 'reference_cellule','num_lot'])
                df = df.dropna(subset=['SOH_cellule_determine'])
                soh_cell_test = df['SOH_cellule_determine'].tolist()
                # Calculer la moyenne et l'écart-type de toute la liste
                mean = np.mean(soh_cell_test)
                std_dev = np.std(soh_cell_test)
                
                # Générer une nouvelle liste de 50 éléments selon une distribution normale avec les paramètres calculés
                new_soh = np.random.normal(loc=mean, scale=std_dev, size=nb_cells)
                soh_m= statistics.mean(new_soh)
                return new_soh,soh_m
                
                
                

def main():
    conn=connecter_bdd("34.77.226.40", "Vanvan", "VoltR99!", "cellules_batteries_cloud")
    #conn=connecter_bdd("127.0.0.1", "root", "VoltR99!", "cellules_batteries_cloud")
    batteries_par_num_lot=extraire_batteries_a_traiter(conn)
    cursor=conn.cursor()
    for lot in batteries_par_num_lot:
        lot=lot.reset_index(drop=True)
        nb_batt= lot.shape[0]
        fournisseur=lot.loc[0, 'fournisseur']
        numero_lot=lot.loc[0, 'num_lot']
        ref_batt=int(lot.loc[0, 'reference_batterie_voltr'])
        ref_cell=lot.loc[0, 'reference_cellule']
        list_batt=lot['Numero_serie_batterie'].tolist()
        if ref_cell=='INCONNU' or ref_cell == 'cellule_non_verifiee':
            for batt_previ in list_batt:
                cursor.execute("UPDATE batteries_recep SET previsionnel_calcule =%s where numero_serie_batterie=%s",("Ok",batt_previ))
            conn.commit()
            continue
        rebus_batt= determiner_tot_rebus_batterie(fournisseur,numero_lot,ref_batt,cursor)
        nb_batt_previ=round(nb_batt*(1-rebus_batt))
        cursor.execute("SELECT Nombre_cellule,utilisation_premiere_vie,type_cellules FROM bibliotheque_batteries WHERE Reference_voltr=%s",(ref_batt,))
        data_ref_batt=cursor.fetchall()[0]
        nb_cells,usage,typec=data_ref_batt
        nb_cells=int(nb_cells)
        cursor.execute("SELECT Date FROM numero_lot WHERE lot=%s",(numero_lot,))
        date_reception=cursor.fetchall()[0][0]
        rebus_cells=determiner_tot_rebus_cellule(numero_lot, fournisseur, ref_cell, cursor)
        nb_cells_previ=round(nb_cells*(1-rebus_cells))
        soh_ventilation,soh_m=determiner_soh(numero_lot, nb_cells_previ,ref_cell,cursor)
        cursor.execute("Select Capacite_nominale_cellule from bibliotheque where reference_cellule= %s",(ref_cell,))
        capa_ref_cell=cursor.fetchall()[0][0]
        id_boucle=nb_batt_previ
        print(numero_lot)
        print(soh_ventilation)
        print(soh_m)
        print(rebus_cells)
        print(rebus_batt)
        while id_boucle != 0:
            for k in range(nb_cells_previ):
                
                 query = "SELECT numero_serie_cellule FROM cellules_previsionelles WHERE numero_serie_cellule LIKE %s"
                 param = ('CP' + '%', ) #cherche le type de batterie demandé 
                 cursor.execute(query, param)
                 existing_series = [serie[0] for serie in cursor.fetchall()] # Liste de toutes les batterie de ce type
               # Si aucun numéro de série existant, le numéro généré sera id_batterie + 0000001
                 if not existing_series:
                   new_serie_cell = 'CP' + '0000000001'
   
                 else:
                   # Trier la liste des numéros de série existants dans l'ordre décroissant
                   existing_series.sort(reverse=True)
                   # Extraire le dernier numéro de série existant 
                   last_serie = existing_series[0]
                   # Extraire le nombre après id_batterie et convertir en entier
                   last_number = int(last_serie[len('CP'):])
                   # Générer le nouveau numéro de série en incrémentant de 1 le dernier numéro
                   new_number = last_number + 1
                   # Compléter le nouveau numéro avec des zéros pour obtenir 6 chiffres
                   new_number_padded = str(new_number).zfill(10)
                   # Concaténer 
                   new_serie_cell = 'CP' + new_number_padded
                 
                 soh_cell=float(soh_ventilation[k])
                 capa_cell=capa_ref_cell*soh_cell/100
                 print(new_serie_cell)

                 insert_query ="INSERT INTO cellules_previsionelles (Numero_serie_cellule, Num_lot,utilisation_premiere_vie, Date_de_reception, Type_cellule, Reference_cellule,SOH_cellule_determine,reference_batterie) VALUES(%s, %s, %s, %s, %s, %s, %s,%s)"
                 insert_params = (new_serie_cell,numero_lot,usage, date_reception, typec,ref_cell,soh_cell,ref_batt)
                 cursor.execute(insert_query, insert_params)
                 
            id_boucle -= 1
        
        for batt_previ in list_batt:
            cursor.execute("UPDATE batteries_recep SET previsionnel_calcule =%s where numero_serie_batterie=%s",("Ok",batt_previ))
        conn.commit()
    
    cursor.close()
    deconnecter_bdd(conn)
    print("fin du traitement")
    

# Lancer le script
if __name__ == "__main__":
    main()