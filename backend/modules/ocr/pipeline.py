"""
pipeline.py
============
Cœur du système — contient toutes les fonctions de traitement
et les appelle dans l'ordre correct.

Ordre d'exécution pour chaque image :
  1. detect_marker(img)          → trouve l'ID et les coins du marqueur
  2. compute_rois(corners, cfg)  → calcule les coordonnées pixel de chaque cellule
  3. extract_table(img, rois)    → OCR cellule par cellule → dict champ:valeur

Note : pas d'homographie — on travaille directement dans le repère
de l'image originale en utilisant le coin TL du marqueur comme ancre.
"""

import cv2
from cv2 import aruco
import numpy as np
import re
import json
import os
from typing import Optional
from .config import ARUCO_DICT, ARUCO_PARAMS, ROI_CONFIGS, FORMULAIRES

# ── Constantes ──────────────────────────────────────────────────────────────
# Patterns DMS pour latitude (N/S) et longitude (E/W) séparés
# La latitude max 2 chiffres (0-90), la longitude max 3 chiffres (0-180)
# Patterns DMS plus flexibles : le symbole ° est optionnel, on accepte espaces, virgules ou symboles
LATITUDE_DMS_PATTERN = re.compile(
    r"(\d{1,2})\s*°\s*(\d{1,2})\s*['\u2019]\s*(\d{1,2}(?:[.,]\d+)?)\s*[\"\u201d]?\s*([NS])",
    re.IGNORECASE
)
LONGITUDE_DMS_PATTERN = re.compile(
    r"(\d{1,3})\s*°\s*(\d{1,2})\s*['\u2019]\s*(\d{1,2}(?:[.,]\d+)?)\s*[\"\u201d]?\s*([EW])",
    re.IGNORECASE
)
# Pattern générique pour la conversion DMS → DD (très flexible)
DMS_GENERIC = re.compile(
    r"(\d{1,3})\s*[°\s,]*\s*(\d{1,2})\s*['\s,]*\s*(\d{1,2}(?:[.,]\d+)?)\s*[\"\s,]*\s*([NSEW])",
    re.IGNORECASE
)

# Patterns pour détection de format
PATTERN_DM = re.compile(
    r"(\d{1,3})\s*°\s*(\d{1,2}\.\d{2,})\s*['\s]*\s*([NSEW])",
    re.IGNORECASE
)
PATTERN_DD = re.compile(
    r"^[-+]?(\d{1,3})(\.\d+)?\s*([NSEW])?$",
    re.IGNORECASE
)
CHAMPS_LAT = {"latitude_dms", "latitude"}
CHAMPS_LON = {"longitude_dms", "longitude"}
CHAMPS_NUM = {
    "numero", "altitude_terrain", "diametre_rotor", "hauteur_moyeu",
    "hauteur_eolienne", "altitude_totale", "hauteur_mat",
    "hauteur_structure", "hauteur_antenne", "hauteur_grue",
}

# Singleton PaddleOCR — chargé une seule fois
_ocr = None


def _get_ocr():
    global _ocr
    if _ocr is None:
        print("[OCR] Chargement du modèle PaddleOCR (première fois)…")
        from paddleocr import PaddleOCR
        _ocr = PaddleOCR(use_textline_orientation=True, lang='fr')
        print("[OCR] Modèle prêt.")
    return _ocr


# ════════════════════════════════════════════════════════
# ÉTAPE 1 — DÉTECTION DU MARQUEUR
# ════════════════════════════════════════════════════════

def detect_marker(img: np.ndarray) -> tuple:
    """
    Détecte le marqueur ArUco dans l'image.

    Retourne (marker_id, corners) si trouvé,
             (None, None)         sinon.

    corners : ndarray (4,2) dans l'ordre TL, TR, BR, BL
    coin TL (index 0) = ancre de référence pour tous les calculs ROI.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    gray = np.uint8(gray)

    # Try without parameters first to isolate if ARUCO_PARAMS is the cause
    all_corners, all_ids, _ = aruco.detectMarkers(gray, ARUCO_DICT)

    if all_ids is None or len(all_ids) == 0:
        return None, None

    # Si plusieurs marqueurs détectés : prendre le plus grand (le plus proche)
    best = max(range(len(all_ids)),
               key=lambda i: float(np.linalg.norm(
                   all_corners[i][0][2] - all_corners[i][0][0])))

    marker_id = int(all_ids[best][0])
    corners   = all_corners[best][0]   # (4, 2)

    print(f"  ✓ Marqueur détecté : ID={marker_id} "
          f"({FORMULAIRES.get(marker_id, 'inconnu')})")
    print(f"    TL=({corners[0][0]:.0f},{corners[0][1]:.0f})  "
          f"TR=({corners[1][0]:.0f},{corners[1][1]:.0f})  "
          f"BR=({corners[2][0]:.0f},{corners[2][1]:.0f})  "
          f"BL=({corners[3][0]:.0f},{corners[3][1]:.0f})")

    return marker_id, corners


# ════════════════════════════════════════════════════════
# ÉTAPE 2 — CALCUL DES ROI
# ════════════════════════════════════════════════════════

def compute_rois(corners: np.ndarray, config: dict) -> list:
    """
    Calcule les coordonnées pixel absolues de chaque cellule du tableau.

    Méthode :
      - coin TL du marqueur = origine (x0, y0)
      - taille du marqueur M = moyenne des 4 côtés (en pixels)
      - position de chaque cellule = (x0 + col.dx*M,  y0 + (premiere_dy + row_i * h_ligne)*M)

    Retourne une liste de listes :
      rois[ligne][colonne] = dict {champ, x, y, w, h}
    """
    # Coin TL = ancre
    x0, y0 = float(corners[0][0]), float(corners[0][1])

    # Taille du marqueur = moyenne des 4 côtés
    sides = [np.linalg.norm(corners[(i+1) % 4] - corners[i]) for i in range(4)]
    M     = float(np.mean(sides))

    print(f"  Ancre TL = ({x0:.0f}, {y0:.0f})  |  M = {M:.1f} px")

    all_rois = []
    for row_idx in range(config["nb_lignes_max"]):
        dy   = config["premiere_ligne_dy"] + row_idx * config["hauteur_ligne"]
        row  = []
        for col in config["colonnes"]:
            row.append({
                "champ": col["champ"],
                "ligne": row_idx + 1,
                "x":     int(x0 + col["dx"] * M),
                "y":     int(y0 + dy         * M),
                "w":     int(col["w"]         * M),
                "h":     int(config["hauteur_ligne"] * M),
            })
        all_rois.append(row)

    return all_rois


# ════════════════════════════════════════════════════════
# ÉTAPE 3 — OCR PAR CELLULE
# ════════════════════════════════════════════════════════

def _preprocess_cell(cell: np.ndarray, scale: float = 3.0) -> np.ndarray:
    """
    Prétraite une cellule avant OCR :
      Agrandissement et conversion en gris.
      On retire le seuillage d'Otsu qui peut supprimer du texte si le contraste est faible.
    """
    h, w = cell.shape[:2]
    if h < 2 or w < 2:
        return cell

    big = cv2.resize(cell, (int(w * scale), int(h * scale)),
                     interpolation=cv2.INTER_CUBIC)
    
    # On garde une image simple en BGR pour PaddleOCR
    return big


def _ocr_cell(img: np.ndarray, roi: dict) -> dict:
    """
    Découpe la cellule, applique PaddleOCR, retourne le texte brut + confiance.
    """
    H_img, W_img = img.shape[:2]
    x = max(0, min(roi["x"], W_img - 1))
    y = max(0, min(roi["y"], H_img - 1))
    w = min(roi["w"], W_img - x)
    h = min(roi["h"], H_img - y)

    if w < 5 or h < 5:
        return {"raw": "", "conf": 0.0}

    cell = img[y:y+h, x:x+w]
    proc = _preprocess_cell(cell)

    # DIAGNOSTIC: Save the cropped cell to see what is being OCR'd
    diag_dir = "results/diag_cells"
    os.makedirs(diag_dir, exist_ok=True)
    if not hasattr(_ocr_cell, "counter"):
        _ocr_cell.counter = 0
    if _ocr_cell.counter < 20:
        cv2.imwrite(f"{diag_dir}/cell_{_ocr_cell.counter}.png", proc)
        _ocr_cell.counter += 1

    res = _get_ocr().ocr(proc, cls=False)

    raw, conf = "", 0.0
    if res and res[0]:
        parts = [item[1][0] for item in res[0]]
        confs = [item[1][1] for item in res[0]]
        raw   = " ".join(parts).strip()
        conf  = float(np.mean(confs)) if confs else 0.0

    return {"raw": raw, "conf": round(conf, 3)}


def _clean(text: str, champ: str) -> Optional[str]:
    """Valide et nettoie la valeur selon le type du champ."""
    text = text.strip()
    if not text:
        return None

    if champ in CHAMPS_LAT or champ in CHAMPS_LON:
        return valider_dms(text, champ)

    if champ in CHAMPS_NUM:
        return _parse_num(text, champ)

    return text


def normaliser_dms(texte: str) -> str:
    """
    Nettoie et normalise une chaîne DMS.
    Corrections OCR courantes avant parsing.
    """
    texte = texte.replace('*', '°')      # * → ° (Correction OCR courante)
    texte = texte.replace('O', '0')      # O → 0
    texte = texte.replace('o', '0')      # o → 0
    texte = texte.replace('l', '1')      # l → 1
    texte = texte.replace('I', '1')      # I → 1
    texte = texte.replace(';', "'")      # ; → '
    texte = texte.replace('`', "'")      # ` → '
    texte = texte.replace('"', '"')      # uniformiser guillemets
    # Supprimer les espaces superflus
    texte = re.sub(r'\s+', ' ', texte).strip()
    return texte


def detecter_format(texte: str) -> str:
    """
    Analyse le texte pour déterminer le format des coordonnées.
    Retourne 'DMS', 'DM', 'DD', ou 'Inconnu'.
    """
    if not texte:
        return "Inconnu"
    t = normaliser_dms(texte).strip()
    
    # 1. DM first — decimal minutes like 9°6.1160'E
    dm = re.search(
        r'\d{1,3}\s*°\s*\d{1,2}\.\d+\s*[\']\s*[NSEW]',
        t, re.IGNORECASE
    )
    if dm:
        return "DM"
    
    # 2. DMS — integer minutes + seconds
    if LATITUDE_DMS_PATTERN.search(t) or LONGITUDE_DMS_PATTERN.search(t):
        return "DMS"
    
    # 3. DD
    if PATTERN_DD.search(t):
        return "DD"
    
    return "Inconnu"


def valider_dms(texte: str, champ: str) -> Optional[str]:
    """
    Vérifie si le texte est une coordonnée DMS valide.
    Nettoie d'abord avec normaliser_dms(), puis valide le format et les plages.

    Retourne la chaîne DMS normalisée si valide, None sinon.
    """
    texte = normaliser_dms(texte)
    if not texte:
        return None

    # Detect and reject DM format before DMS parsing
    dm_match = re.search(
        r'(\d{1,3})\s*°\s*(\d{1,2}\.\d+)\s*[\'′]\s*([NSEW])',
        texte, re.IGNORECASE
    )
    if dm_match:
        return None  # DM format — reject explicitly

    # Sélection du pattern selon le type de champ
    if champ in CHAMPS_LAT:
        pat = LATITUDE_DMS_PATTERN
    elif champ in CHAMPS_LON:
        pat = LONGITUDE_DMS_PATTERN
    else:
        return None

    m = pat.search(texte)
    if not m:
        return None

    deg = int(m.group(1))
    minutes = int(m.group(2))
    secondes = float(m.group(3).replace(',', '.'))
    
    # Direction optionnelle : défaut N pour Lat, E pour Lon
    dir_group = m.group(4)
    if dir_group:
        direction = dir_group.upper()
    else:
        direction = 'N' if champ in CHAMPS_LAT else 'E'

    # Validation des plages
    if direction in ('N', 'S') and deg > 90:
        return None
    if direction in ('E', 'W') and deg > 180:
        return None
    if minutes >= 60:
        return None
    if secondes >= 60:
        return None

    # Reconstruction propre (formatte secondes pour garantir la cohérence)
    sec_str = f"{secondes:.2f}" if isinstance(secondes, float) else str(secondes)
    return f"{deg}°{minutes}'{sec_str}\"{direction}"


def _parse_dms(text: str, pat) -> Optional[str]:
    """Tente de parser le texte comme une coordonnée DMS (compatibilité)."""
    # Déterminer le type de champ à partir du pattern passé
    if "latitude" in str(pat) or "lat" in str(pat).lower():
        return valider_dms(text, "latitude_dms")
    elif "longitude" in str(pat) or "lon" in str(pat).lower():
        return valider_dms(text, "longitude_dms")
    else:
        # Fallback : pattern générique
        m = DMS_GENERIC.search(normaliser_dms(text))
        if not m:
            return None
        sec = m.group(3)
        return f"{m.group(1)}°{m.group(2)}'{sec}\"{m.group(4).upper()}"


def _parse_num(text: str, champ: str) -> Optional[str]:
    """Extrait un nombre et vérifie sa plausibilité."""
    cleaned = re.sub(r'[^\d.,]', '', text).replace(',', '.')
    parts   = cleaned.split('.')
    if len(parts) > 2:
        cleaned = parts[0] + '.' + ''.join(parts[1:])
    try:
        val = float(cleaned)
    except ValueError:
        return None
    if champ == "numero"       and not (1 <= val <= 1000): return None
    if "altitude" in champ     and not (0 <= val <= 6000): return None
    if "hauteur"  in champ     and not (0 <= val <= 600):  return None
    if "diametre" in champ     and not (0 <= val <= 300):  return None
    return str(int(val)) if val == int(val) else str(round(val, 2))


def _dms_to_dd(dms: str) -> Optional[float]:
    """Convertit DMS → degrés décimaux."""
    m = DMS_GENERIC.search(dms)
    if not m:
        return None
    sec = float(m.group(3).replace(',', '.'))
    dd  = float(m.group(1)) + float(m.group(2))/60 + sec/3600
    if m.group(4).upper() in ('S', 'W'):
        dd = -dd
    return round(dd, 8)


def extract_table(img: np.ndarray, all_rois: list) -> list:
    """
    Applique l'OCR sur chaque ROI et retourne les données structurées.

    Pour chaque ligne du tableau :
      • Lit chaque cellule avec PaddleOCR
      • Nettoie et valide la valeur selon le type du champ
      • Calcule les degrés décimaux pour les coordonnées DMS
      • Arrête dès qu'une ligne est entièrement vide (fin du tableau)

    Retourne une liste de dicts, un par ligne non vide :
      [{ "ligne":1, "numero":"1", "latitude_dms":"36°52'28.42\"N",
          "latitude_dd":36.874, "longitude_dms":"9°04'26.35\"E",
          "longitude_dd":9.074, "altitude_terrain":"522", ... }, ...]
    """
    rows = []

    for rois_ligne in all_rois:
        row        = {"ligne": rois_ligne[0]["ligne"]}
        all_empty  = True

        for roi in rois_ligne:
            ocr_res = _ocr_cell(img, roi)
            cleaned = _clean(ocr_res["raw"], roi["champ"])

            # If cleaning failed (None), we keep the raw text so the user can see/edit it in the UI
            row[roi["champ"]]           = cleaned if cleaned is not None else ocr_res["raw"]
            row[roi["champ"] + "_raw"]  = ocr_res["raw"]
            row[roi["champ"] + "_conf"] = ocr_res["conf"]

            # DEBUG: print exactly what OCR sees in each cell
            print(f"    [{roi['champ']}] Raw: '{ocr_res['raw']}' Conf: {ocr_res['conf']} -> Cleaned: {cleaned}")

            if cleaned is not None:
                all_empty = False

        # Fin du tableau : ligne entièrement vide
        if all_empty:
            print(f"  → Fin tableau ligne {rois_ligne[0]['ligne']}")
            break

        # Degrés décimaux (on cherche n'importe quel champ de coordonnée reconnu)
        lat_val = row.get("latitude_dms") or row.get("latitude")
        lon_val = row.get("longitude_dms") or row.get("longitude")

        if lat_val:
            row["latitude_dd"] = _dms_to_dd(lat_val)
        if lon_val:
            row["longitude_dd"] = _dms_to_dd(lon_val)

        rows.append(row)
        print(f"  Ligne {row['ligne']:2d} | "
              f"N°={row.get('numero','?')} | "
              f"Lat={row.get('latitude_dms','?')} | "
              f"Lon={row.get('longitude_dms','?')} | "
              f"AltT={row.get('altitude_totale','?')}")

    print("\n--- FINAL EXTRACTION RESULTS ---")
    print(json.dumps(rows, indent=2, ensure_ascii=False))
    print("--------------------------------\n")

    return rows