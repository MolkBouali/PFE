"""
config.py — Configuration centrale partagée par tous les modules.

Contient :
  - FORMULAIRES   : mapping marker_id → nom du formulaire
  - ROI_CONFIGS   : définition des colonnes/lignes pour chaque formulaire


Les ROI sont exprimées en unités relatives à la taille du marqueur (M).
  dx, dy = décalage depuis le coin TL du marqueur
  w, h   = dimensions de la cellule
  Toutes les valeurs sont multipliées par M (pixels) au moment du calcul.

COMMENT CALIBRER VOS ROI :
  1. Imprimer le formulaire avec son marqueur
  2. Le scanner à 300 DPI
  3. Exécuter : python main.py votre_scan.png --debug
  4. Regarder l'image results/debug_rois_*.png
  5. Ajuster dx, dy, w, h dans ce fichier jusqu'à ce que
     les rectangles tombent bien sur chaque cellule
"""
import cv2
from cv2 import aruco 
ARUCO_DICT = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
ARUCO_PARAMS = aruco.DetectorParameters()

# ── Formulaires : marker_id → nom ──────────────────────────────────────────
FORMULAIRES = {
    0: "eolienne",
    1: "eolienne",
    2: "eolienne",
    10: "ligne_electrique", #pylone
    20: "batiment",
    30: "base_telephonie",
    40: "grue",
    
}

# ── ROI par formulaire ──────────────────────────────────────────────────────
# Toutes les valeurs sont en unités M (taille du marqueur en pixels).
# premiere_ligne_dy : distance Y du coin TL du marqueur à la 1ère ligne de données.
# hauteur_ligne     : hauteur d'une ligne du tableau.
# colonnes[i].dx    : distance X du coin TL du marqueur au début de la colonne i.
# colonnes[i].w     : largeur de la colonne i.

ROI_CONFIGS = {

    
    # ═══════════════════════════════════════════════════════════════════
    # ID 0 : TABLEAU EOLIENNE - PAGE 1
    # ═══════════════════════════════════════════════════════════════════
    0: {
        "nom_formulaire": "Eolienne - Page 1",
        "type_tableau": "eolienne",
        "nb_lignes_max": 15,           
        "premiere_ligne_dy": 3.2,
        "hauteur_ligne": 0.38,
        "colonnes": [
            {"champ": "numero_eolienne",           "dx": 0.10, "w": 0.55},
            {"champ": "latitude_dms",              "dx": 0.72, "w": 2.80},
            {"champ": "longitude_dms",             "dx": 3.60, "w": 2.80},
            {"champ": "altitude_terrain",          "dx": 6.50, "w": 1.10},
            {"champ": "diametre_rotor",            "dx": 7.70, "w": 1.00},
            {"champ": "hauteur_moyeu",             "dx": 8.80, "w": 1.00},
            {"champ": "hauteur_eolienne",          "dx": 9.90, "w": 1.10},
            {"champ": "altitude_totale_eolienne",  "dx": 11.10, "w": 1.10},
        ],
    },

    # ═══════════════════════════════════════════════════════════════════
    # ID 1 : TABLEAU EOLIENNE - (suite)
    # ═══════════════════════════════════════════════════════════════════
    1: {
        "nom_formulaire": "Eolienne - suite",
        "type_tableau": "eolienne",
        "nb_lignes_max": 15,           # 15 lignes supplémentaires
        "premiere_ligne_dy": 2.5,      # ⚠️ Position différente de la page 1 !
        "hauteur_ligne": 0.38,
        "colonnes": [
            {"champ": "numero_eolienne",           "dx": 0.10, "w": 0.55},
            {"champ": "latitude_dms",              "dx": 0.72, "w": 2.80},
            {"champ": "longitude_dms",             "dx": 3.60, "w": 2.80},
            {"champ": "altitude_terrain",          "dx": 6.50, "w": 1.10},
            {"champ": "diametre_rotor",            "dx": 7.70, "w": 1.00},
            {"champ": "hauteur_moyeu",             "dx": 8.80, "w": 1.00},
            {"champ": "hauteur_eolienne",          "dx": 9.90, "w": 1.10},
            {"champ": "altitude_totale_eolienne",  "dx": 11.10, "w": 1.10},
        ],
    },

    # ═══════════════════════════════════════════════════════════════════
    # ID 2 : TABLEAU MÂT DE MESURE
    # ═══════════════════════════════════════════════════════════════════
    2: {
        "nom_formulaire": "Mât de mesure",
        "type_tableau": "mat_mesure",
        "nb_lignes_max": 12,
        "premiere_ligne_dy": 3.818,
        "hauteur_ligne": 0.643,
        "colonnes": [
            {"champ": "numero",                   "dx": 0.692, "w": 0.922},
            {"champ": "latitude_dms",              "dx": 3.802, "w": 2.144},
            {"champ": "longitude_dms",             "dx": 1.572, "w": 2.187},
            {"champ": "altitude_terrain",          "dx": 5.967, "w": 0.9},
            {"champ": "hauteur_mat",               "dx": 6.867, "w": 0.922},
            {"champ": "altitude_totale_mat",       "dx": 7.811, "w": 0.943},
        ],
    },
   

    # ID 10 — ligne_electrique
    10: {
        "nb_lignes_max":     10, #plusieuuuuurs
        "premiere_ligne_dy": 3.2,
        "hauteur_ligne":     0.38,
        "colonnes": [
            {"champ": "numero_pylone",           "dx": 0.10, "w": 0.55},
            {"champ": "latitude_dms",     "dx": 0.72, "w": 2.80},
            {"champ": "longitude_dms",    "dx": 3.60, "w": 2.80},
            {"champ": "hauteur", "dx": 6.50, "w": 1.10},
            {"champ": "altitude_du_sol",      "dx": 7.70, "w": 1.00},
            {"champ": "altitude_finale",  "dx": 8.80, "w": 1.10},
        ],
    },

    # ID 20 — BÂTIMENT
    20: {
        "nb_lignes_max":     16,
        "premiere_ligne_dy": 3.508,
        "hauteur_ligne":     0.62,
        "colonnes": [
            {"champ": "hauteur (m)",            "dx": -0.279, "w": 1.24},
            {"champ": "altitude_terrain (m)",      "dx": 0.939, "w": 1.218},
            {"champ": "altitude_finale (m)",     "dx": 2.157, "w": 1.24},
            {"champ": "latitude",  "dx": 3.419, "w": 3.101},
            {"champ": "longitude", "dx": 6.542, "w": 3.034},
        ],
    },

    # ID 30 — base_telephonie
    30: {
        "tableau_lignes_electriques": {
            "nb_lignes_max":     5,
            "premiere_ligne_dy": 3.2,
            "hauteur_ligne":     0.38,
            "colonnes": [
                {"champ": "hauteur (m)",           "dx": 0.10, "w": 0.55},
                {"champ": "altitude_terrain (m)",     "dx": 0.72, "w": 2.80},
                {"champ": "altitude_finale (m)",    "dx": 3.60, "w": 2.80},
                {"champ": "latitude", "dx": 6.50, "w": 1.10},
                {"champ": "longitude",  "dx": 7.70, "w": 1.00},
            ], 
        },

        "tableau_emission": {
            "nb_lignes_max": 3,
            "premiere_ligne_dy": 8.5,
            "hauteur_ligne": 0.45,
            "colonnes": [
                {"champ": "Puissance_emission","dx": 0.10, "w": 1.50},
                {"champ": "fréquences",     "dx": 1.70, "w": 1.20},  
            ],
        },
    },

    # ID 40 — GRUE  ############################################
    40: {
        "nb_lignes_max":     5,
        "premiere_ligne_dy": 3.2,
        "hauteur_ligne":     0.38,
        "colonnes": [
            {"champ": "numero",           "dx": 0.10, "w": 0.55},
            {"champ": "latitude_dms",     "dx": 0.72, "w": 2.80},
            {"champ": "longitude_dms",    "dx": 3.60, "w": 2.80},
            {"champ": "altitude_terrain", "dx": 6.50, "w": 1.10},
            {"champ": "hauteur_grue",     "dx": 7.70, "w": 1.00},
            {"champ": "altitude_totale",  "dx": 8.80, "w": 1.10},
        ],
    },
}