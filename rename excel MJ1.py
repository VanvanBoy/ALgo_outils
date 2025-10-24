# -*- coding: utf-8 -*-
"""
Created on Tue Sep 23 10:15:14 2025

@author: User
"""

from pathlib import Path

# === À RENSEIGNER ============================================================
FOLDER   = r"C:\Users\User\Desktop\MAJ_TEST\Resultats - Copie" # Dossier contenant les Excel
RECURSIVE = False                         # True = parcourt les sous-dossiers
DRY_RUN   = False                          # False pour renommer réellement
EXTS      = {".xlsx", ".xls", ".xlsm", ".xlsb"}
SUFFIX_TO_ADD = "-INR18650MJ1_A.0.0"
# ============================================================================

def target_name(base_stem: str) -> str:
    """
    Si le nom (sans extension) contient >= 4 occurrences de '-',
    couper au 4e '-' (supprimer le 4e et tout ce qui suit),
    puis ajouter le suffixe demandé.
    """
    parts = base_stem.split("-")
    # Avec 4 occurrences, on a 5 segments => len(parts) >= 5
    if len(parts) >= 5:
        kept = "-".join(parts[:4])   # seg1 - seg2 - seg3 - seg4
    else:
        kept = base_stem
    return f"{kept}{SUFFIX_TO_ADD}"

def unique_path(p: Path) -> Path:
    """Évite les collisions en ajoutant ' (1)', ' (2)', ... si besoin."""
    if not p.exists():
        return p
    stem, ext = p.stem, p.suffix
    i = 1
    while True:
        candidate = p.with_name(f"{stem} ({i}){ext}")
        if not candidate.exists():
            return candidate
        i += 1

def iter_files(folder: Path, recursive: bool):
    if recursive:
        yield from (p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in EXTS)
    else:
        yield from (p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in EXTS)

def main():
    root = Path(FOLDER)
    if not root.exists():
        print(f"[ERREUR] Dossier introuvable: {root}")
        return

    changed = 0
    for f in iter_files(root, RECURSIVE):
        new_stem = target_name(f.stem)
        new_path = f.with_name(new_stem + f.suffix)

        # Si le chemin cible existe déjà, trouver un nom unique
        new_path = unique_path(new_path)

        if new_path == f:
            # Déjà conforme (rare, mais possible)
            print(f"[SKIP] {f.name} (aucun changement)")
            continue

        print(f"[RENOMMER] '{f.name}'  ->  '{new_path.name}'")
        if not DRY_RUN:
            try:
                f.rename(new_path)
                changed += 1
            except Exception as e:
                print(f"  [ERREUR] {e}")

    if DRY_RUN:
        print("\n[INFO] DRY_RUN=True : rien n’a été modifié. Passe DRY_RUN à False pour appliquer.")
    else:
        print(f"\n[FINI] Fichiers modifiés: {changed}")

if __name__ == "__main__":
    main()