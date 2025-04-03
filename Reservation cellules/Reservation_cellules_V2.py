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
          insert_query = "INSERT INTO reservation (reservation, reference_cellule, nombre_cellule_originel, project, capacite_min_cellule) VALUES (%s, %s, %s, %s, %s)"
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

          # Compléter le nouveau numéro avec des zéros pour obtenir 9 chiffres
          new_number_padded = str(new_number).zfill(9)

          # Concaténer 
          new_serie = 'R' + new_number_padded
          
          # Insérer le nouveau numéro de série dans la table batteries_recep
          insert_query = "INSERT INTO reservation (reservation, reference_cellule, nombre_cellule_originel, project, capacite_min_cellule) VALUES (%s, %s, %s, %s, %s)"
          insert_params = (new_serie, ref_cell,nbc,projet,capacite_cell)
          cursor.execute(insert_query, insert_params)
          
          new_series_generated.append(new_serie)
          
        connection.commit()
        popup_text = "\n".join(new_series_generated)
        messagebox.showinfo("Réservation effectuée !", popup_text)
        
    except Exception as e:
        line_number = sys.exc_info()[2].tb_lineno
        error_message = f"Une erreur s'est produite à la ligne {line_number}: {str(e)}"
        messagebox.showerror("Erreur", error_message)

# Nouvelle fonctionnalité : Sélection d'une réservation et mise à jour de l'état
def load_reservation_data(event):
    reservation_selected = reservation_combobox.get()
    query = "SELECT project, nombre_cellule_restant, nombre_cellule_originel, etat_reservation FROM reservation WHERE reservation = %s"
    cursor.execute(query, (reservation_selected,))
    result = cursor.fetchone()

    if result:
        projet_label_var.set(f"Projet : {result[0]}")
        nombre_cell_rest_label_var.set(f"Cellules restantes : {result[1]}")
        nombre_cell_orig_label_var.set(f"Cellules originelles : {result[2]}")
        etat_reservation_combobox.set(result[3])

        # Exclure l'état actuel des options
        options = ["en cours", "clos", "bloque", "annule"]
        options.remove(result[3])
        etat_reservation_combobox['values'] = options
    else:
        messagebox.showerror("Erreur", "Réservation non trouvée")

def update_reservation_status():
    reservation_selected = reservation_combobox.get()
    new_status = etat_reservation_combobox.get()
    
    if not new_status:
        messagebox.showerror("Erreur", "Veuillez sélectionner un nouvel état.")
        return

    try:
        update_query = "UPDATE reservation SET etat_reservation = %s WHERE reservation = %s"
        cursor.execute(update_query, (new_status, reservation_selected))
        connection.commit()
        messagebox.showinfo("Succès", "État de la réservation mis à jour.")
    except Exception as e:
        line_number = sys.exc_info()[2].tb_lineno
        error_message = f"Une erreur s'est produite à la ligne {line_number}: {str(e)}"
        messagebox.showerror("Erreur", error_message)

# Connectez-vous à la base de données
user, password = get_db_credentials()

connection = mysql.connector.connect(
    host="localhost",
    user='root',
    password='VoltR99!',
    port=3306,
    database="cellules_batteries_cloud",
    auth_plugin='mysql_native_password'
)

cursor = connection.cursor()

# Fenêtre principale
window = tk.Tk()
window.title("Reservation cellules")
window.geometry("900x600")

main_frame = tk.Frame(window)
main_frame.pack(pady=20, padx=20)

# Création de deux frames pour séparer les sections gauche et droite
left_frame = tk.Frame(main_frame)
left_frame.grid(row=0, column=0, padx=50, pady=10)  # Ajustez les marges ici

# Partie gauche (Création de réservation)
projet_label = tk.Label(left_frame, text="Projet :", font=('Arial', 12))
projet_label.pack(pady=10)
cursor.execute(("SELECT project_name FROM project where etat = %s"),("en cours",))    
result_nom_proj = cursor.fetchall()
mots_possibles_proj= result_nom_proj
projet_combobox = ttk.Combobox(left_frame, values=mots_possibles_proj, font=('Arial', 12))
projet_combobox.pack()
projet_combobox.bind("<<ComboboxSelected>>", on_combobox_select)

archi_label = tk.Label(left_frame, text="Architecture batterie", font=('Arial', 12))
archi_label.pack(pady=10)
archi_entry = tk.Entry(left_frame, font=('Arial', 12))
archi_entry.pack()
archi_entry.config(state=tk.DISABLED)

nb_batt_label = tk.Label(left_frame, text="Nombre de batterie", font=('Arial', 12))
nb_batt_label.pack(pady=10)
nb_batt_entry = tk.Entry(left_frame, font=('Arial', 12))
nb_batt_entry.pack()
nb_batt_entry.config(state=tk.DISABLED)

nbc_label = tk.Label(left_frame, text="Nombre cellules", font=('Arial', 12))
nbc_label.pack(pady=10)
nbc_entry = tk.Entry(left_frame, font=('Arial', 12))
nbc_entry.pack()
nbc_entry.config(state=tk.DISABLED)

ref_cell_label = tk.Label(left_frame, text="Référence cellule", font=('Arial', 12))
ref_cell_label.pack(pady=10)
cursor.execute("SELECT reference_cellule FROM bibliotheque")    
result_nom_cell= cursor.fetchall()
mots_possibles_cell= result_nom_cell
ref_cell_combobox = ttk.Combobox(left_frame, values=mots_possibles_cell, font=('Arial', 12))
ref_cell_combobox.pack()

capacite_label = tk.Label(left_frame, text="Capacité minimale cellule (Ah)", font=('Arial', 12))
capacite_label.pack(pady=10)
capacite_entry = tk.Entry(left_frame, font=('Arial', 12))
capacite_entry.pack()

submit_button = tk.Button(left_frame, text="Créer Réservation", command=main, font=('Arial', 12), bg='blue', fg='white')
submit_button.pack(pady=20)


# Partie droite (Sélection de réservation et mise à jour de l'état)
right_frame = tk.Frame(main_frame)
right_frame.grid(row=0, column=1, padx=50, pady=10)  # Ajustez les marges ici

# Partie droite (Sélection de réservation et mise à jour de l'état)
reservation_label = tk.Label(right_frame, text="Sélectionner Réservation :", font=('Arial', 12))
reservation_label.pack(pady=10)
cursor.execute("SELECT reservation FROM reservation")
result_reservation = cursor.fetchall()
mots_possibles_reservation = [res[0] for res in result_reservation]
reservation_combobox = ttk.Combobox(right_frame, values=mots_possibles_reservation, font=('Arial', 12))
reservation_combobox.pack()
reservation_combobox.bind("<<ComboboxSelected>>", load_reservation_data)

# Afficher les informations de la réservation sélectionnée
projet_label_var = tk.StringVar()
projet_label = tk.Label(right_frame, textvariable=projet_label_var, font=('Arial', 12))
projet_label.pack(pady=10)

nombre_cell_rest_label_var = tk.StringVar()
nombre_cell_rest_label = tk.Label(right_frame, textvariable=nombre_cell_rest_label_var, font=('Arial', 12))
nombre_cell_rest_label.pack(pady=10)

nombre_cell_orig_label_var = tk.StringVar()
nombre_cell_orig_label = tk.Label(right_frame, textvariable=nombre_cell_orig_label_var, font=('Arial', 12))
nombre_cell_orig_label.pack(pady=10)

etat_reservation_label = tk.Label(right_frame, text="État de la réservation :", font=('Arial', 12))
etat_reservation_label.pack(pady=10)
etat_reservation_combobox = ttk.Combobox(right_frame, font=('Arial', 12))
etat_reservation_combobox.pack()

update_button = tk.Button(right_frame, text="Mettre à jour l'état", command=update_reservation_status, font=('Arial', 12), bg='green', fg='white')
update_button.pack(pady=20)

# Configurez la méthode on_closing pour être appelée quand la fenêtre est fermée
window.protocol("WM_DELETE_WINDOW", on_closing)

# Execution
window.mainloop()
