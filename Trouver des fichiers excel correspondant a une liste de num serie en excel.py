# Script simple et linéaire pour vérifier qu'il existe un Excel par n° de série (12 chiffres)
# Dépendances : pandas, openpyxl
#   pip install pandas openpyxl

from pathlib import Path
import re
import pandas as pd

# === À RENSEIGNER ============================================================
INPUT_XLSX   = r"C:\Users\User\Desktop\MJ1\MJ1_non_test.xlsx"     # Excel d'entrée: colonne A = n° série
SCAN_FOLDER  = r"G:\Drive partagés\VoltR\4_Production\5_Cyclage\1_Résultats de cyclage\Fichiers de cyclage pre migration serveur\13_Résultats cycleurs\Resultats de test"       # Dossier contenant les fichiers Excel
OUTPUT_XLSX  = r"C:\Users\User\Desktop\MJ1\rapport.xlsx"     # Chemin du rapport de sortie
RECURSIVE    = True                                # Parcourir récursivement les sous-dossiers ?
EXTS   = (".xlsx", ".xls", ".xlsm", ".xlsb") # Extensions prises en compte


# 1) lire les numéros de série (colonne A)
df = pd.read_excel(INPUT_XLSX, header=None, dtype=str, engine="openpyxl")
serials = (
    df.iloc[:, 0].astype(str).str.strip()
)
serials = [s for s in serials if s]                  # enlève vides
serials = list(dict.fromkeys(serials))               # déduplication en gardant l'ordre
serials_set = set(serials)

print(f"Nb n° série lus (uniques): {len(serials)}")

# 2) lister les fichiers excel du dossier
base = Path(SCAN_FOLDER)
files = [p for p in base.iterdir() if p.is_file() and p.suffix.lower() in EXTS]

print(f"Nb fichiers Excel scannés: {len(files)}")

# 3) construire un index: prefixe_12 -> liste de fichiers
prefix_to_files = {}
for f in files:
    prefix12 = f.stem[:12]  # <=== LES 12 PREMIERS CARACTÈRES DU NOM DE FICHIER
    prefix_to_files.setdefault(prefix12, []).append(f.name)

# 4) pour chaque n° de série, vérifier la présence
rows = []
for s in serials:
    files_for_s = prefix_to_files.get(s, [])
    status = "FOUND" if len(files_for_s) >= 1 else "MISSING"
    rows.append({
        "numero_serie_cellule": s,
        "status": status,
        "match_count": len(files_for_s),
        "files": "; ".join(files_for_s)
    })

report = pd.DataFrame(rows)

# 5) sauvegarde + affichage court
report.to_excel(OUTPUT_XLSX, index=False)
missing = report[report["status"] == "MISSING"]["numero_serie_cellule"].tolist()

print("\n=== RÉSUMÉ ===")
print(f"Total: {len(report)}")
print(f"FOUND: {int((report['match_count'] >= 1).sum())}")
print(f"MISSING: {len(missing)}")

if missing:
    print("\nNuméros sans fichier correspondant:")
    for s in missing:
        print(" -", s)

print(f"\nRapport: {OUTPUT_XLSX}")
