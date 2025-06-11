# -*- coding: utf-8 -*-
"""
Created on Wed Apr 23 16:27:37 2025

@author: User
"""


import shutil
from pathlib import Path
import pandas as pd


EXCEL_FILE = Path(r"G:\Drive partagés\VoltR\11_Data\AssoV4\Population 200 cells de test\MH1 96_soh_2%.xlsx")
SOURCE_DIR = Path(r"G:\Drive partagés\VoltR\4_Production\5_Cyclage\1_Résultats de cyclage\Fichiers traités")
DEST_DIR   = Path(r"G:\Drive partagés\VoltR\11_Data\AssoV4\Population 200 cells de test\MH1 96_soh_2%")


def main() -> None:
   
    serials = (
        pd.read_excel(EXCEL_FILE, usecols=[0], dtype=str)   # ne garde que la 1ᵉʳᵉ colonne
          .iloc[:, 0]                                       # Series
          .dropna()                                         # enlève les cellules vides
          .str.strip()                                      # supprime espaces \t \n en trop
    )

    # --- 2. préparation du dossier de destination ---
    DEST_DIR.mkdir(parents=True, exist_ok=True)

    # --- 3. boucle de copie ---
    n_total = 0
    for serial in serials:
        # Attention : sur Linux/macOS la recherche est sensible à la casse.
        for f in SOURCE_DIR.glob(f"{serial}*"):
            if f.is_file():
                target = DEST_DIR / f.name
                # copy2 → conserve date & heure d’origine
                shutil.copy2(f, target)
                n_total += 1

    print(f"✓ {n_total} fichier(s) copié(s) dans : {DEST_DIR}")

if __name__ == "__main__":
    main()
