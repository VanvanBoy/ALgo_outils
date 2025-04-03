# -*- coding: utf-8 -*-
"""
Created on Tue Jul  2 13:54:37 2024

@author: Vanvan
"""

import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog
import mysql.connector
from tkinter import messagebox
import sys

def on_closing():
    if cursor:
        cursor.close()
    if connection:
        connection.close()
    window.destroy()
    

def on_combobox_select(event):
     proj=projet_combobox.get()
     if proj[:3]=='VRC':
         archi_entry.config(state=tk.DISABLED)
         nbc_entry.config(state=tk.NORMAL)
         nb_batt_entry.config(state=tk.DISABLED)
         
     else:
         archi_entry.config(state=tk.NORMAL)
         nbc_entry.config(state=tk.DISABLED)
         nb_batt_entry.config(state=tk.NORMAL)
         
def get_db_credentials():
    # Fonction pour obtenir les informations d'identification de l'utilisateur
    user = simpledialog.askstring("Login", "Enter your MySQL username:")
    password = simpledialog.askstring("Login", "Enter your MySQL password:", show='*')
    return user, password

def main():
    
    archi = archi_entry.get().upper()
    capacite = float(capacite_entry.get()) if capacite_entry.get() else 0
    ref_cell=ref_cell_combobox.get()
    projet=projet_combobox.get()
    
    if archi:
        nb_batt=int(nb_batt_entry.get())
        indice_s = archi.find("S")
        nbs = int(archi[:indice_s])
        indice_p = archi.find("P")
        nbp = int(archi[indice_s + 1:indice_p])
        nbc=nbs*nbp*nb_batt
        capacite_cell= capacite
    else : 
        nbc=nbc_entry.get()
        capacite_cell=capacite
    try:
        
        new_series_generated = []
        
        query = "SELECT reservation FROM reservation"
        cursor.execute(query)
        existing_series = [resa[0] for resa in cursor.fetchall()] 
     
        if not existing_series:
          new_serie = 'R' + '000000001'
          # Insérer le nouveau numéro de série dans la table batteries_recep
          insert_query = "INSERT INTO reservation (reservation, reference_cellule, nombre_cellule, project, capacite_min_cellule) VALUES (%s, %s, %s, %s, %s)"
          insert_params = (new_serie, ref_cell,nbc,projet,capacite_cell)
          cursor.execute(insert_query, insert_params)

          new_series_generated.append(new_serie) #Ajouter le nouveau numero de serie a la liste 
          
        else:
          # Trier la liste des numéros de série existants dans l'ordre décroissant
          existing_series.sort(reverse=True)

          # Extraire le dernier numéro de série existant 
          last_serie = existing_series[0]
          
          # Extraire le nombre après id_batterie et convertir en entier
          last_number = int(last_serie[len('R'):])

          # Générer le nouveau numéro de série en incrémentant de 1 le dernier numéro
          new_number = last_number + 1

          # Compléter le nouveau numéro avec des zéros pour obtenir 6 chiffres
          new_number_padded = str(new_number).zfill(9)

          # Concaténer 
          new_serie = 'R' + new_number_padded
          
          # Insérer le nouveau numéro de série dans la table batteries_recep
          insert_query = "INSERT INTO reservation (reservation, reference_cellule, nombre_cellule, project, capacite_min_cellule) VALUES (%s, %s, %s, %s, %s)"
          insert_params = (new_serie, ref_cell,nbc,projet,capacite_cell)
          cursor.execute(insert_query, insert_params)
          
          new_series_generated.append(new_serie)
          
         
        
        connection.commit()
        popup_text = "\n".join(new_series_generated)
        messagebox.showinfo("Réservation effectuée !", popup_text)
        
    except Exception as e:
        # Obtenir le numéro de ligne où l'erreur s'est produite
        line_number = sys.exc_info()[2].tb_lineno
        
        # Afficher un message d'erreur avec le numéro de ligne
        error_message = f"Une erreur s'est produite à la ligne {line_number}: {str(e)}"
        messagebox.showerror("Erreur", error_message)

# Connectez-vous à la base de données
user, password = get_db_credentials()

connection = mysql.connector.connect(
     host="localhost",
     user="root",
     password="VoltR99!",
     port=3306,
     database="cellules_batteries_cloud",
     auth_plugin='mysql_native_password'
 )

cursor = connection.cursor()

# Fenetre principale
window = tk.Tk()
window.title("Reservation cellules")
window.geometry("900x500")
# Labels et entrees

projet_label = tk.Label(window, text=" Projet :", font=('Arial', 12))
projet_label.pack(pady=10)
cursor.execute(("SELECT project_name FROM project where etat = %s"),("en cours",))    
result_nom_proj = cursor.fetchall()
mots_possibles_proj= result_nom_proj
projet_combobox = ttk.Combobox(window, values=mots_possibles_proj, font=('Arial', 12))
projet_combobox.pack()
projet_combobox.bind("<<ComboboxSelected>>", on_combobox_select)

archi_label = tk.Label(window, text="Architrecture batterie", font=('Arial', 12))
archi_label.pack(pady=10)
archi_entry = tk.Entry(window, font=('Arial', 12))
archi_entry.pack()
archi_entry.config(state=tk.DISABLED)

nb_batt_label = tk.Label(window, text="Nombre de batterie", font=('Arial', 12))
nb_batt_label.pack(pady=10)
nb_batt_entry = tk.Entry(window, font=('Arial', 12))
nb_batt_entry.pack()
nb_batt_entry.config(state=tk.DISABLED)

nbc_label = tk.Label(window, text="Nombre cellules", font=('Arial', 12))
nbc_label.pack(pady=10)
nbc_entry = tk.Entry(window, font=('Arial', 12))
nbc_entry.pack()
nbc_entry.config(state=tk.DISABLED)

ref_cell_label = tk.Label(window, text="Reference cellule", font=('Arial', 12))
ref_cell_label.pack(pady=10)
cursor.execute("SELECT reference_cellule FROM bibliotheque")    
result_nom_cell= cursor.fetchall()
mots_possibles_cell= result_nom_cell
ref_cell_combobox = ttk.Combobox(window, values=mots_possibles_cell, font=('Arial', 12))
ref_cell_combobox.pack()

capacite_label = tk.Label(window, text="Capacité minimale (Ah)", font=('Arial', 12))
capacite_label.pack(pady=10)
capacite_entry = tk.Entry(window, font=('Arial', 12))
capacite_entry.pack()
#capacite_entry.insert(0, "5.2")  

# Sauvegarde
save_label = tk.Label(window, text="", font=('Arial', 12))
save_label.pack(pady=10)
submit_button = tk.Button(window, text="Start", command=main, font=('Arial', 12), bg='blue', fg='white')
submit_button.pack()  # Vous pouvez ajuster la position et le nombre de colonnes au besoin
"""
if cursor:
    cursor.close()
if connection:
    connection.close()
"""

# Configurez la méthode on_closing pour être appelée quand la fenêtre est fermée
window.protocol("WM_DELETE_WINDOW", on_closing)
# Execution
window.mainloop()
