# -*- coding: utf-8 -*-
"""
Created on Mon Feb  5 14:17:21 2024

@author: Vanvanboy

Cell_ref_choice
"""
import tkinter as tk
from tkinter import ttk
from tkinter import ttk,simpledialog
import mysql.connector
import pandas as pd
import numpy as np
from openpyxl import Workbook
from collections import Counter
from tkinter import filedialog
import math

def get_db_credentials():
    # Fonction pour obtenir les informations d'identification de l'utilisateur
    user = simpledialog.askstring("Login", "Enter your MySQL username:")
    password = simpledialog.askstring("Login", "Enter your MySQL password:", show='*')
    return user, password

def main():
    
    archi = archi_entry.get().upper()
    indice_s = archi.find("S")
    nbs = int(archi[:indice_s])
    indice_p = archi.find("P")
    nbp = int(archi[indice_s + 1:indice_p])
    dim= int(dim_entry.get()) if dim_entry.get() else None
    capacite = float(capacite_entry.get()) if capacite_entry.get() else None
    tension_nom = float(tension_nom_entry.get()) if tension_nom_entry.get() else None
    tension_max = float(tension_max_entry.get()) if tension_max_entry.get() else None
    courant_c_max = float(courant_c_entry.get()) if courant_c_entry.get() else None
    courant_d_max = float(courant_d_entry.get()) if courant_d_entry.get() else None
    courant_d_pic = float(courant_d_pic_entry.get()) if courant_d_pic_entry.get() else None
    duree_pic = float(duree_pic_entry.get()) if duree_pic_entry.get() else None
    temp_min_charge = float(temp_min_charge_entry.get()) if temp_min_charge_entry.get() else None
    temp_max_charge = float(temp_max_charge_entry.get()) if temp_max_charge_entry.get() else None
    temp_min_decharge = float(temp_min_decharge_entry.get()) if temp_min_decharge_entry.get() else None
    temp_max_decharge = float(temp_max_decharge_entry.get()) if temp_max_decharge_entry.get() else None
    
    # Obtenez les informations d'identification de la base de données
    db_user, db_password = get_db_credentials()

    try:
        """
        # Connectez-vous à la base de données
        connection = mysql.connector.connect(
            host="34.77.226.40",
            user=db_user,
            password=db_password,
            database="cellules_batteries_cloud",
            auth_plugin='mysql_native_password'
        )
        """
        
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="VoltR99!",
            port=3306,
            database="cellules_batteries_cloud",
            auth_plugin='mysql_native_password'
        )
        
        cursor = connection.cursor()
        
        # Construisez la requête SQL de base
        sql_query = "SELECT reference_cellule FROM bibliotheque WHERE 1=1"
        values = []
        
        capacite_cellule= (capacite/nbp) -0.01
        
        if capacite:
            sql_query += " AND Capacite_nominale_cellule >= %s"
            values.append(capacite_cellule)
        if dim:
            sql_query += " AND Dimension = %s"
            values.append(dim)            
        if tension_nom:
            sql_query += " AND Tension_nominale >= %s"
            values.append(tension_nom/nbs -0.01)
        if tension_max:
            sql_query += " AND Tension_maximale >= %s"
            values.append(tension_max/nbs -0.01)
        if courant_c_max:
            sql_query += " AND Courant_de_charge_max >= %s"
            values.append(courant_c_max/nbp -0.01)
        if courant_d_max:
            sql_query += " AND Courant_de_decharge_max >= %s"
            values.append(courant_d_max/nbp -0.01)
        if courant_d_pic:
            sql_query += " AND Courant_de_decharge_pic >= %s"
            values.append(courant_d_pic/nbp -0.01)
        if duree_pic:
            sql_query += " AND duree_pic >= %s"
            values.append(duree_pic -0.01)
        if temp_min_charge:
            sql_query += " AND temp_min_charge <= %s"
            values.append(temp_min_charge +0.01)
        if temp_max_charge:
            sql_query += " AND temp_max_charge >= %s"
            values.append(temp_max_charge -0.01)
        if temp_min_decharge:
            sql_query += " AND temp_min_decharge <= %s"
            values.append(temp_min_decharge +0.01)
        if temp_max_decharge:
            sql_query += " AND temp_max_decharge >= %s"
            values.append(temp_max_decharge -0.01)
        
        cursor.execute(sql_query, values)
        
        references = cursor.fetchall()

                # Initialisez la liste des résultats en dehors de la boucle
        results = []
        
        # Pour chaque référence de cellule, effectuez le comptage dans la table "cellules"
        for reference in references:
            
            # Méthode 1 ----------------------------------------------------------------------------------------------------------------------------------------------
            capacite_cellule=math.ceil(capacite_cellule*100)/100
            reference_cellule = reference[0]
            
            cursor.execute("Select Capacite_nominale_cellule from bibliotheque where reference_cellule=%s",(reference_cellule,))
            capacite_datasheet=float(cursor.fetchone()[0])
            """
            borne_60=capacite_datasheet*0.60
            borne_75=capacite_datasheet*0.75
            borne_80=capacite_datasheet*0.80
            borne_85=capacite_datasheet*0.85
            borne_90=capacite_datasheet*0.90
            borne_95=capacite_datasheet*0.95
            """
            
            count_query = f"SELECT COUNT(*) FROM cellules WHERE reference_cellule = '{reference_cellule}' AND disponibilite= 'DISPO' AND bon_cyclage= 'OUI' AND Capacite_decharge_cellule_mesuree > '{capacite_cellule}' "
            cursor.execute(count_query)
            count_tot_result = cursor.fetchone()[0]
            
            # Comptage des cellules dans chaque intervalle de capacité résiduelle
            cursor.execute("""
                SELECT COUNT(*) FROM cellules 
                WHERE reference_cellule = %s AND disponibilite= 'DISPO' AND bon_cyclage= 'OUI' AND Capacite_decharge_cellule_mesuree > %s
                    AND (Capacite_decharge_cellule_mesuree / %s) * 100 BETWEEN %s AND %s
            """, (reference_cellule,capacite_cellule, capacite_datasheet, 60, 75))
            count_interval_60_75 = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM cellules 
                WHERE reference_cellule = %s AND disponibilite= 'DISPO' AND bon_cyclage= 'OUI' AND Capacite_decharge_cellule_mesuree > %s
                    AND (Capacite_decharge_cellule_mesuree / %s) * 100 BETWEEN %s AND %s
            """, (reference_cellule,capacite_cellule, capacite_datasheet, 75, 80))
            count_interval_75_80 = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM cellules 
                WHERE reference_cellule = %s AND disponibilite= 'DISPO' AND bon_cyclage= 'OUI' AND Capacite_decharge_cellule_mesuree > %s
                    AND (Capacite_decharge_cellule_mesuree / %s) * 100 BETWEEN %s AND %s
            """, (reference_cellule,capacite_cellule, capacite_datasheet, 80, 85))
            count_interval_80_85 = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM cellules 
                WHERE reference_cellule = %s AND disponibilite= 'DISPO' AND bon_cyclage= 'OUI' AND Capacite_decharge_cellule_mesuree > %s
                    AND (Capacite_decharge_cellule_mesuree / %s) * 100 BETWEEN %s AND %s
            """, (reference_cellule,capacite_cellule, capacite_datasheet, 85, 90))
            count_interval_85_90 = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM cellules 
                WHERE reference_cellule = %s AND disponibilite= 'DISPO' AND bon_cyclage= 'OUI' AND Capacite_decharge_cellule_mesuree > %s
                    AND (Capacite_decharge_cellule_mesuree / %s) * 100 BETWEEN %s AND %s
            """, (reference_cellule,capacite_cellule, capacite_datasheet, 90, 95))
            count_interval_90_95 = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM cellules 
                WHERE reference_cellule = %s AND disponibilite= 'DISPO' AND bon_cyclage= 'OUI' AND Capacite_decharge_cellule_mesuree > %s
                    AND (Capacite_decharge_cellule_mesuree / %s) * 100 > %s
            """, (reference_cellule,capacite_cellule, capacite_datasheet, 95))
            count_interval_sup_95 = cursor.fetchone()[0]
        
            # Ajoutez le résultat dans une liste pour le tri ultérieur
            results.append((reference_cellule, count_tot_result, count_interval_60_75, count_interval_75_80, count_interval_80_85, count_interval_85_90, count_interval_90_95, count_interval_sup_95))
        
            """        
            # Méthode 2 ----------------------------------------------------------------------------------------------------------------------------------------------
            
            cursor.execute("Select Capacite_nominale_cellule from bibliotheque where reference_cellule=%s",(reference_cellule,))
            capacite_datasheet=float(cursor.fetchone()[0])
            
            count_query = f"SELECT COUNT(*) FROM cellules WHERE reference_cellule = '{reference_cellule}' AND disponibilite= 'DISPO' AND bon_cyclage= 'OUI'"
            cursor.execute(count_query)
            count_tot_result = cursor.fetchone()[0]
            
            # Récupérer les cellules ayant la référence actuelle
            cursor.execute("SELECT Capacite_decharge_cellule_mesuree FROM cellules WHERE reference_cellule = %s", (reference[0],))
            cellules = cursor.fetchall()
        
            # Initialiser les compteurs pour chaque intervalle
            count_intervals = [0] * 6
        
            for cellule in cellules:
                # Calculer SOH
                soh = (cellule[0] /capacite_datasheet) * 100
        
                # Calculer dans quel intervalle se trouve le SOH et incrémenter le compteur correspondant
                if 60 <= soh <= 75:
                    count_intervals[0] += 1
                elif 75 < soh <= 80:
                    count_intervals[1] += 1
                elif 80 < soh <= 85:
                    count_intervals[2] += 1
                elif 85 < soh <= 90:
                    count_intervals[3] += 1
                elif 90 < soh <= 95:
                    count_intervals[4] += 1
                elif soh > 95:
                    count_intervals[5] += 1   
            """
    
        # Triez les résultats par ordre décroissant en fonction du nombre de cellules
        sorted_results = sorted(results, key=lambda x: x[1], reverse=True)
        
        # Affichez le résultat trié dans le Treeview
        for result in sorted_results:
            tree.insert("", "end", values=(result[0],result[1],result[2],result[3],result[4],result[5],result[6],result[7]))

        # Validez la transaction
        #connection.commit()
        
        # Créez un classeur Excel
        workbook = Workbook()
        
        # Créez une feuille dans le classeur
        sheet = workbook.active
        
        # Ajoutez des en-têtes aux colonnes
        sheet['A1'] = 'Référence de cellule'
        sheet['B1'] = 'Nombre de cellules'
        sheet['C1'] = 'SOH : 60%-75%'
        sheet['D1'] = 'SOH : 75%-80%'
        sheet['E1'] = 'SOH : 80%-85%'
        sheet['F1'] = 'SOH : 85%-90%'
        sheet['G1'] = 'SOH : 90%-95%'
        sheet['H1'] = 'SOH > 95%'
        
        
        # Obtenez les données triées du Treeview
        data_to_export = [(result[0], result[1],result[2],result[3],result[4],result[5],result[6],result[7]) for result in sorted_results]
        
        # Ajoutez les données au classeur Excel
        for index, data in enumerate(data_to_export, start=2):
            sheet[f'A{index}'] = data[0]
            sheet[f'B{index}'] = data[1]
            sheet[f'C{index}'] = data[2]
            sheet[f'D{index}'] = data[3]
            sheet[f'E{index}'] = data[4]
            sheet[f'F{index}'] = data[5]
            sheet[f'G{index}'] = data[6]
            sheet[f'H{index}'] = data[7]
          
        # Enregistrez le fichier Excel
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
        if file_path:
            workbook.save(file_path)

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Fermez le curseur et la connexion à la base de données
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return

# Fenetre principale
window = tk.Tk()
window.title("Cell references choice")
window.geometry("1000x600")

# Labels et entrees
archi_label = tk.Label(window, text="Architrecture batterie", font=('Arial', 12))
archi_label.grid(row=0, column=0, pady=10)
archi_entry = tk.Entry(window, font=('Arial', 12))
archi_entry.grid(row=0, column=1)
archi_entry.insert(0, "10S7P")  

# Labels et entrees
dim_label = tk.Label(window, text="Dimension cellule", font=('Arial', 12))
dim_label.grid(row=1, column=0, pady=10)
dim_entry = tk.Entry(window, font=('Arial', 12))
dim_entry.grid(row=1, column=1)
dim_entry.insert(0, "18650")  

capacite_label = tk.Label(window, text="Capacité(Ah)", font=('Arial', 12))
capacite_label.grid(row=2, column=0, pady=10)
capacite_entry = tk.Entry(window, font=('Arial', 12))
capacite_entry.grid(row=2, column=1)
capacite_entry.insert(0, "5.2")  

tension_nom_label = tk.Label(window, text="Tension nominale(V)", font=('Arial', 12))
tension_nom_label.grid(row=3, column=0, pady=10)
tension_nom_entry = tk.Entry(window, font=('Arial', 12))
tension_nom_entry.grid(row=3, column=1)
tension_nom_entry.insert(0, "7.2")  

tension_max_label = tk.Label(window, text="Tension maximale(V)", font=('Arial', 12))
tension_max_label.grid(row=4, column=0, pady=10)
tension_max_entry = tk.Entry(window, font=('Arial', 12))
tension_max_entry.grid(row=4, column=1)
tension_max_entry.insert(0, "8.4")  

courant_c_label = tk.Label(window, text="Courant continu maximal de charge(A)", font=('Arial', 12))
courant_c_label.grid(row=5, column=0, pady=10)
courant_c_entry = tk.Entry(window, font=('Arial', 12))
courant_c_entry.grid(row=5, column=1)
courant_c_entry.insert(0,"2.04")

courant_d_label = tk.Label(window, text="Courant continu max de décharge(A)", font=('Arial', 12))
courant_d_label.grid(row=6, column=0, pady=10)
courant_d_entry = tk.Entry(window, font=('Arial', 12))
courant_d_entry.grid(row=6, column=1)
courant_d_entry.insert(0,"2.6")

courant_d_pic_label = tk.Label(window, text="Courant de décharge en pic(A)", font=('Arial', 12))
courant_d_pic_label.grid(row=7, column=0, pady=10)
courant_d_pic_entry = tk.Entry(window, font=('Arial', 12))
courant_d_pic_entry.grid(row=8, column=0)
#courant_d_pic_entry.insert(0,"5.2")

duree_pic_label = tk.Label(window, text="Durée pic(s)", font=('Arial', 12))
duree_pic_label.grid(row=7, column=1, pady=10)
duree_pic_entry = tk.Entry(window, font=('Arial', 12))
duree_pic_entry.grid(row=8, column=1)
#duree_pic_entry.insert(0,"5.2")

temp_min_charge_label = tk.Label(window, text="Temperature min charge(°C)", font=('Arial', 12))
temp_min_charge_label.grid(row=9, column=0, pady=10)
temp_min_charge_entry = tk.Entry(window, font=('Arial', 12))
temp_min_charge_entry.grid(row=10, column=0)
#temp_min_charge_entry.insert(0,"2.04")

temp_max_charge_label = tk.Label(window, text="Temperature max charge(°C)", font=('Arial', 12))
temp_max_charge_label.grid(row=9, column=1, pady=10)
temp_max_charge_entry = tk.Entry(window, font=('Arial', 12))
temp_max_charge_entry.grid(row=10, column=1)
#temp_max_charge_entry.insert(0,"2.04")

temp_min_decharge_label = tk.Label(window, text="Temperature min decharge (°C)", font=('Arial', 12))
temp_min_decharge_label.grid(row=11, column=0, pady=10)
temp_min_decharge_entry = tk.Entry(window, font=('Arial', 12))
temp_min_decharge_entry.grid(row=12, column=0)
#temp_min_decharge_entry.insert(0,"2.04")

temp_max_decharge_label = tk.Label(window, text="Temperature max decharge (°C)", font=('Arial', 12))
temp_max_decharge_label.grid(row=11, column=1, pady=10)
temp_max_decharge_entry = tk.Entry(window, font=('Arial', 12))
temp_max_decharge_entry.grid(row=12, column=1)
#temp_max_decharge_entry.insert(0,"2.04")

# Création de l'écran (rectangle) à droite
screen_frame = tk.Frame(window, width=200, height=600, bg="white")
screen_frame.grid(row=0, column=2, rowspan=8, padx=10, pady=10, sticky='nsew')
window.grid_columnconfigure(2, weight=1)  # Permet à la colonne 2 de s'étendre horizontalement

# Création du widget Treeview pour afficher les données avec la barre de défilement 
tree = ttk.Treeview(screen_frame, columns=[], show="headings")
tree.pack(fill=tk.BOTH, expand=True)

tree["columns"] = ("col1", "col2","col3","col4","col5","col6","col7","col8")
tree.heading("col1", text="Reference celulle")
tree.heading("col2", text="Total cellules disponibles")
tree.heading("col3", text="SOH 60%-75%")
tree.heading("col4", text="SOH 75%-80%")
tree.heading("col5", text="SOH 80%-85%")
tree.heading("col6", text="SOH 85%-90%")
tree.heading("col7", text="SOH 90%-95%")
tree.heading("col8", text="SOH > 95%")


# Barre horizontale
tree_scroll = ttk.Scrollbar(screen_frame, orient='horizontal', command=tree.xview)
tree_scroll.pack(fill='x')
tree.configure(xscrollcommand=tree_scroll.set)  # Lier le défilement horizontal du Treeview avec le curseur

# Création de la barre de défilement verticale
tree_scroll_y = ttk.Scrollbar(screen_frame, orient='vertical', command=tree.yview)
tree_scroll_y.place(relx=1.0, rely=0, relheight=1.0, anchor='ne')
tree.configure(yscrollcommand=tree_scroll_y.set)

# Sauvegarde
submit_button = tk.Button(window, text="Start", command=main, font=('Arial', 12), bg='blue', fg='white')
submit_button.grid(row=13, column=0, columnspan=2, pady=20)  # Vous pouvez ajuster la position et le nombre de colonnes au besoin

# Execution
window.mainloop()
