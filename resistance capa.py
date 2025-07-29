# -*- coding: utf-8 -*-
"""
Created on Fri May 23 12:03:52 2025

@author: User
"""
import os
#import mysql.connector
import pandas as pd
"""
user='Vanvan'
password='VoltR99!'


conn = mysql.connector.connect(
    host="34.77.226.40",
    user=user,
    password=password,
    database="cellules_batteries_cloud",
    auth_plugin='mysql_native_password'
) 
"""
dossier=r"C:\Users\User\Desktop\cellules slatr17072025"

colonnes = ['numero_serie', 'capa', 'resi']
df = pd.DataFrame(columns=colonnes)

for fichier in os.listdir(dossier):#Traite chaque fichier dans le dossier 
    if fichier.endswith('.xlsx') or fichier.endswith('.xls'):#Verifie si le fichier est de type excel
    
        chemin_fichier = os.path.join(dossier, fichier) #Création du chemin vers le fichier 
        numero_serie_cellule = os.path.splitext(os.path.basename(chemin_fichier))[0] #Obtenir le nom du fichier puis retirer l'extension '.xls'
           
        print(numero_serie_cellule)       
                
        #Capacité
        
        data = pd.read_excel(chemin_fichier, sheet_name='step') #Extraction des donnees de la sheet 'step'
        Etape = data['Step Type'] #Extraire la colonne STEP Type
        
        target = ['CV DChg', 'CC DChg'] #L'etape que l'on cherche est celle de decharge, le nom peut changer selon le type de test 
        indice = -1
        
        #Boucle qui parcours Etape et cherche la premiere occurence de l'etape de decharge
        for i in range(len(Etape)):
          if Etape[i] in target:    
                indice = i  # Première occurrence trouvée
                break  # Sortir de la boucle 
        
        #Si l'occurence est trouvé, on extrait la valeur de la capacité correpondante dans Capa   
        if indice != -1:
            Capa = data['Capacity(Ah)'][indice]
        
        #Resistance 
        
        #Extraire de la feuille 'record' les données d'interet enregistrées
        data = pd.read_excel(chemin_fichier, sheet_name='record')

        etape = data['Step Type'].tolist() #Type d'etape 
        
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
      
        DeltaCourant=abs(Courant[0])

        #calcul de la variation de tension 
        DeltaTension=abs(Tension.tail(1).values[0]-Tension[0])
        #gestion du cas ou la variation de courant est nulle
    
        
        #Calcule de la Resistance en mOhm
        Resistance = (DeltaTension/DeltaCourant)*1000
        
        capacite_decharge=float(Capa)
        resistance_interne=float(Resistance)
        
        nouvelle_ligne = {'numero_serie': numero_serie_cellule, 'capa': capacite_decharge, 'resi':  resistance_interne}
        df = pd.concat([df, pd.DataFrame([nouvelle_ligne])], ignore_index=True)
        
df.to_excel("results_C3.xlsx", sheet_name="Sheet1")