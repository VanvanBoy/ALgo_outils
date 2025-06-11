# -*- coding: utf-8 -*-
"""
Created on Fri May 23 11:59:14 2025

@author: User
"""

import os
import pandas as pd

# Charger la table de correspondance
df = pd.read_excel(r"C:\Users\User\Desktop\test guy\GUY-VS REEL.xlsx")  

# Remplacer par le chemin réel du dossier contenant les fichiers
folder_path = r"C:\Users\User\Desktop\test guy\cellules"

# Boucle sur les lignes de la table pour renommer les fichiers
for _, row in df.iterrows():
    original = str(row['FICHIER'])
    new_name = str(row['NUMERO_SERIE_CELLULE'])
    
    # Chemins complets
    original_path = os.path.join(folder_path, original)
    new_path = os.path.join(folder_path, new_name + '.xlsx')  # En ajoutant l'extension .xlsx
    
    if os.path.exists(original_path):
        os.rename(original_path, new_path)
        print(f"Renommé: {original} -> {new_name}.xlsx")
    else:
        print(f"Fichier non trouvé: {original}")
