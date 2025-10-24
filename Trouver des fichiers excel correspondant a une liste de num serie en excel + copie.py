# -*- coding: utf-8 -*-
"""
Created on Tue Sep 23 10:02:24 2025

@author: User
"""

from pathlib import Path
import shutil
import pandas as pd

# === À RENSEIGNER ============================================================
INPUT_XLSX   = r"C:\Users\User\Desktop\MJ1\MJ1_non_test.xlsx"  # Excel d'entrée: colonne A = n° série
SCAN_FOLDER  = r"G:\Drive partagés\VoltR\4_Production\5_Cyclage\1_Résultats de cyclage\Fichiers de cyclage pre migration serveur\13_Résultats cycleurs\Resultats de test"  # Dossier contenant les fichiers Excel
OUTPUT_XLSX  = r"C:\Users\User\Desktop\MJ1\rapport.xlsx"       # Chemin du rapport de sortie
RECURSIVE    = True                                            # Parcourir récursivement les sous-dossiers ?
EXTS         = (".xlsx", ".xls", ".xlsm", ".xlsb")             # Extensions prises en compte

# Dossier de destination pour les copies
DEST_FOLDER  = r"C:\Users\User\Desktop\MAJ_TEST\Resultats"

# === Utilitaires =============================================================
def iter_excel_files(base: Path, recursive: bool, exts: tuple[str, ...]):
    if recursive:
        for p in base.rglob("*"):
            if p.is_file() and p.suffix.lower() in exts:
                yield p
    else:
        for p in base.iterdir():
            if p.is_file() and p.suffix.lower() in exts:
                yield p

def safe_copy(src: Path, dst_dir: Path) -> Path:
    """
    Copie src dans dst_dir en évitant d'écraser.
    Si un fichier existe déjà, ajoute ' (n)' avant l'extension.
    Retourne le chemin final de la copie.
    """
    dst_dir.mkdir(parents=True, exist_ok=True)
    target = dst_dir / src.name
    if not target.exists():
        shutil.copy2(src, target)
        return target

    stem, suffix = src.stem, src.suffix
    n = 1
    while True:
        candidate = dst_dir / f"{stem} ({n}){suffix}"
        if not candidate.exists():
            shutil.copy2(src, candidate)
            return candidate
        n += 1

# === 1) Lire les numéros de série (colonne A) ================================
df = pd.read_excel(INPUT_XLSX, header=None, dtype=str, engine="openpyxl")
serials = df.iloc[:, 0].astype(str).str.strip()
serials = [s for s in serials if s]         # enlève vides
serials = list(dict.fromkeys(serials))      # déduplication en gardant l'ordre
serials_set = set(serials)
print(f"Nb n° série lus (uniques): {len(serials)}")

# === 2) Lister les fichiers Excel du dossier ================================
base = Path(SCAN_FOLDER)
files = list(iter_excel_files(base, RECURSIVE, EXTS))
print(f"Nb fichiers Excel scannés: {len(files)}")

# === 3) Construire un index: prefixe_12 -> liste de chemins complets ========
prefix_to_files: dict[str, list[Path]] = {}
for f in files:
    prefix12 = f.stem[:12]  # 12 premiers caractères du nom de fichier (sans extension)
    prefix_to_files.setdefault(prefix12, []).append(f)

# === 4) Pour chaque n° de série, vérifier la présence =======================
rows = []
matched_file_paths: set[Path] = set()  # pour la copie des uniques
for s in serials:
    files_for_s = prefix_to_files.get(s, [])
    status = "FOUND" if len(files_for_s) >= 1 else "MISSING"
    rows.append({
        "numero_serie_cellule": s,
        "status": status,
        "match_count": len(files_for_s),
        "files": "; ".join(str(p.relative_to(base)) if p.is_relative_to(base) else p.name
                           for p in files_for_s)
    })
    for p in files_for_s:
        matched_file_paths.add(p)

report = pd.DataFrame(rows)

# === 5) Sauvegarde du rapport ===============================================
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

# === 6) Copier tous les fichiers trouvés vers DEST_FOLDER ====================
dest_dir = Path(DEST_FOLDER)
copied = 0
for src in sorted(matched_file_paths):
    _ = safe_copy(src, dest_dir)
    copied += 1

print(f"\nCopies effectuées: {copied} fichier(s) vers {dest_dir}")
