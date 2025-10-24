# -*- coding: utf-8 -*-
"""
Created on Wed Oct  1 12:14:34 2025

@author: User
"""

import pandas as pd
import mysql.connector

sequence_maxyver=[1, 17, 33, 49, 65, 81, 97, 113, 129, 145, 161, 177, 193, 209, 225, 241, 242, 226, 210, 194, 178, 162, 146, 130, 114, 98, 82, 66, 50, 34, 18, 2, 3, 19, 35, 51, 67, 83, 99, 115, 131, 147, 163, 179, 195, 211, 227, 243, 244, 228, 212, 196, 180, 164, 148, 132, 116, 100, 84, 68, 52, 36, 20, 4, 5, 21, 37, 53, 69, 85, 101, 117, 133, 149, 165, 181, 197, 213, 229, 245, 246, 230, 214, 198, 182, 166, 150, 134, 118, 102, 86, 70, 54, 38, 22, 6, 7, 23, 39, 55, 71, 87, 103, 119, 135, 151, 167, 183, 199, 215, 231, 247, 248, 232, 216, 200, 184, 168, 152, 136, 120, 104, 88, 72, 56, 40, 24, 8, 9, 25, 41, 57, 73, 89, 105, 121, 137, 153, 169, 185, 201, 217, 233, 249, 250, 234, 218, 202, 186, 170, 154, 138, 122, 106, 90, 74, 58, 42, 26, 10, 11, 27, 43, 59, 75, 91, 107, 123, 139, 155, 171, 187, 203, 219, 235, 251, 252, 236, 220, 204, 188, 172, 156, 140, 124, 108, 92, 76, 60, 44, 28, 12, 13, 29, 45, 61, 77, 93, 109, 125, 141, 157, 173, 189, 205, 221, 237, 253, 254, 238, 222, 206, 190, 174, 158, 142, 126, 110, 94, 78, 62, 46, 30, 14, 15, 31, 47, 63, 79, 95, 111, 127, 143, 159, 175, 191, 207, 223, 239, 255, 256, 240, 224, 208, 192, 176, 160, 144, 128, 112, 96, 80, 64, 48, 32, 16]
sequence_plateau=['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10', 'A11', 'A12', 'A13', 'A14', 'A15', 'A16', 'B16', 'B15', 'B14', 'B13', 'B12', 'B11', 'B10', 'B9', 'B8', 'B7', 'B6', 'B5', 'B4', 'B3', 'B2', 'B1', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'C11', 'C12', 'C13', 'C14', 'C15', 'C16', 'D16', 'D15', 'D14', 'D13', 'D12', 'D11', 'D10', 'D9', 'D8', 'D7', 'D6', 'D5', 'D4', 'D3', 'D2', 'D1', 'E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8', 'E9', 'E10', 'E11', 'E12', 'E13', 'E14', 'E15', 'E16', 'F16', 'F15', 'F14', 'F13', 'F12', 'F11', 'F10', 'F9', 'F8', 'F7', 'F6', 'F5', 'F4', 'F3', 'F2', 'F1', 'G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8', 'G9', 'G10', 'G11', 'G12', 'G13', 'G14', 'G15', 'G16', 'H16', 'H15', 'H14', 'H13', 'H12', 'H11', 'H10', 'H9', 'H8', 'H7', 'H6', 'H5', 'H4', 'H3', 'H2', 'H1', 'I1', 'I2', 'I3', 'I4', 'I5', 'I6', 'I7', 'I8', 'I9', 'I10', 'I11', 'I12', 'I13', 'I14', 'I15', 'I16', 'J16', 'J15', 'J14', 'J13', 'J12', 'J11', 'J10', 'J9', 'J8', 'J7', 'J6', 'J5', 'J4', 'J3', 'J2', 'J1', 'K1', 'K2', 'K3', 'K4', 'K5', 'K6', 'K7', 'K8', 'K9', 'K10', 'K11', 'K12', 'K13', 'K14', 'K15', 'K16', 'L16', 'L15', 'L14', 'L13', 'L12', 'L11', 'L10', 'L9', 'L8', 'L7', 'L6', 'L5', 'L4', 'L3', 'L2', 'L1', 'M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8', 'M9', 'M10', 'M11', 'M12', 'M13', 'M14', 'M15', 'M16', 'N16', 'N15', 'N14', 'N13', 'N12', 'N11', 'N10', 'N9', 'N8', 'N7', 'N6', 'N5', 'N4', 'N3', 'N2', 'N1', 'O1', 'O2', 'O3', 'O4', 'O5', 'O6', 'O7', 'O8', 'O9', 'O10', 'O11', 'O12', 'O13', 'O14', 'O15', 'O16', 'P16', 'P15', 'P14', 'P13', 'P12', 'P11', 'P10', 'P9', 'P8', 'P7', 'P6', 'P5', 'P4', 'P3', 'P2', 'P1']

connexion = mysql.connector.connect(
    host="34.77.226.40",     
    user="Vanvan",
    password="VoltR99!",
    database="cellules_batteries_cloud"
)

curseur = connexion.cursor()

#Extraction en df du excel de picking format manuelle
df_vide=pd.read_excel(r"G:\Drive partagés\VoltR\4_Production\8_Picking\Fichiers pickings\Pickings en cours\SF_20102025_P17to28+37to40.xlsx")

for i in range(0,len(df_vide)):
    num_cell=df_vide["Numero_serie_cellule"][i]
    query_emp="select code_emplacement from emplacement where numero_serie= %s"
    param_emp=(num_cell,)
    curseur.execute(query_emp,param_emp)
    row = curseur.fetchone()                 
    code = str(row[0]) if row else None   
    plateau='P'+ code.split('-')[0]
    emplacement=code.split('-')[1]
    emplacement_num = sequence_maxyver[sequence_plateau.index(emplacement)]
    df_vide.loc[i, ["N°plateau", "N°emplacement"]] = [plateau, emplacement_num]
    
df_final=df_vide
# df existe déjà et contient la colonne 'num_produit_bdd'
df_final["N°Emplacement batt"] = df_final.groupby("num_produit_bdd").cumcount() + 1
df_final = df_final.rename(columns={'num_produit_bdd': 'N°Batt'})
df_final = df_final.rename(columns={'Numero_serie_cellule': 'N°cell'})

cols_a_supprimer = ['reference_cellule', 'capacite', 'resistance','module','etat_picking']  # exemple

ordre = ["N°cell", "N°plateau", "N°emplacement", "N°Emplacement batt", "N°Batt"]
df_final = df_final.reindex(columns = ordre + [c for c in df_final.columns if c not in ordre])
df_final["Statut"] = pd.NA

df_final = df_final.drop(columns=cols_a_supprimer, errors='ignore')

#Sauvegarde sous excel du fichier de picking format machine 
df_final.to_excel(r"G:\Drive partagés\VoltR\4_Production\8_Picking\Fichiers pickings\Pickings en cours\Fichier post trait tom\SF_20102025_P17to28+37to40_post.xlsx",
    index=False)
    
curseur.close()
connexion.close()


    
    