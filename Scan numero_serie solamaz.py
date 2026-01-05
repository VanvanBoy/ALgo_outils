# -*- coding: utf-8 -*-
"""
Created on Mon Dec 29 11:50:09 2025

@author: User
"""

import tkinter as tk
from tkinter import ttk
import mysql.connector
from mysql.connector import Error

# --- Connexion BDD (déjà existante chez toi) ---
def connect_to_db_prod():
    """ Connect to MySQL production database """
    try:
        connection = mysql.connector.connect(
            host='34.77.226.40',
            user='Vanvan',
            password='VoltR99!',
            database='cellules_batteries_cloud',
            port=3306,
            auth_plugin='mysql_native_password'
        )
        if connection.is_connected():
            db_info = connection.get_server_info()
            print("Connected to MySQL Server version ", db_info)
            return connection
    except Error as e:
        print("Error while connecting to MySQL", e)
        return None

# --- Application ---
class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Recherche cellule")
        self.geometry("400x200")

        ttk.Label(self, text="Numéro de série (12 caractères)").pack(pady=10)

        self.entry_sn = ttk.Entry(self, width=30)
        self.entry_sn.pack()
        self.entry_sn.bind("<KeyRelease>", self.check_length)

        self.result_label = ttk.Label(self, text="", font=("Arial", 12, "bold"))
        self.result_label.pack(pady=20)

    def check_length(self, event=None):
        numero_serie = self.entry_sn.get().strip()

        if len(numero_serie) == 12:
            self.search_db(numero_serie)
        else:
            self.result_label.config(text="")

    def search_db(self, numero_serie):
        try:
            conn = connect_to_db_prod()
            cursor = conn.cursor()

            query = """
                SELECT affectation_produit
                FROM cellule
                WHERE numero_serie_cellule = %s
            """
            cursor.execute(query, (numero_serie,))
            result = cursor.fetchone()

            if result:
                self.result_label.config(text=f"Batterie : {result[0]}")
            else:
                self.result_label.config(text="Aucune donnée trouvée")

        except Exception as e:
            self.result_label.config(text="Erreur BDD")
            print(e)

        finally:
            if conn:
                conn.close()

# --- Lancement ---
if __name__ == "__main__":
    app = App()
    app.mainloop()
