"""
Service extraction automatique des coordonnees.
Orchestration du pipeline complet :
1. Sauvegarde formulaire scanné sur le systeme de fichiers
2. Detection marqueurs ArUco (type + orientation du formulaire)
3. Decoupe des regions d interet (ROI)
4. Extraction OCR via PaddleOCR
5. Validation format WGS84 DMS de chaque coordonnee
6. Persistance des points de mesure en base de donnees
7. Generation automatique du fichier KMZ
"""
import os
from typing import List, Dict, Any, Optional
import cv2
import numpy as np
from sqlalchemy.orm import Session
from backend.modules.ocr import pipeline, pdfToImage, config
from backend.modules.ocr.pipeline import valider_dms, _dms_to_dd, detecter_format
from backend.models.dossier import Dossier
from backend.models.formulaire import FormulaireNumerise
from backend.models.point_mesure import PointMesure
from backend.schemas.extraction_schema import (
    ExtractionResult, DonneePointDTO, CoordonneesDTO, StatistiquesDTO
)
from backend.core.config import settings
from backend.services.kmz_service import KMZService
import datetime


# Noms de champs qui représentent un numéro de ligne (peuvent varier selon config)
CHAMPS_NUMERO = {"numero", "numero_eolienne", "numero_pylone", "numéro"}

# Champs internes à exclure de donnees_specifiques
CHAMPS_INTERNES = {"ligne", "latitude_dms", "longitude_dms",
                   "latitude_dd", "longitude_dd",
                   "latitude", "longitude",
                   "_table"}


class ExtractionService:
    def __init__(self, db: Session):
        self.db = db

    # ─── Construction de la réponse normalisée ────────────────────────────────

    def _build_extraction_result(
        self,
        formulaire_id: int,
        form_type: str,
        rows: List[dict],
        marker_id: Optional[int] = None
    ) -> ExtractionResult:
        """
        Transforme les lignes brutes extraites par l'OCR en la structure JSON
        demandée.

        Règles :
          - 'ligne' → numero_ligne
          - Le champ qui correspond à un numéro (numero, numero_eolienne, etc.) → numero
          - latitude_dms / longitude_dms → coordonnees (avec dd et valide)
          - Tout le reste (spécifique au marqueur détecté) → donnees_specifiques
        """
        donnees: List[DonneePointDTO] = []

        for i, row in enumerate(rows):
            ligne_num = row.get("ligne", i + 1)

            # ── Extraire le numero ────────────────────────────────────────────
            numero = None
            for key in CHAMPS_NUMERO:
                val = row.get(key)
                if val is not None and val != "":
                    numero = str(val)
                    break

            # ── Extraire les coordonnées ──────────────────────────────────────
            lat_dms = row.get("latitude_dms") or row.get("latitude") or ""
            lon_dms = row.get("longitude_dms") or row.get("longitude") or ""

            lat_dd = row.get("latitude_dd")
            lon_dd = row.get("longitude_dd")

            # Détection du format pour l'affichage du bouton "Générer Complément"
            format_lat = detecter_format(lat_dms) if lat_dms else "Inconnu"
            format_lon = detecter_format(lon_dms) if lon_dms else "Inconnu"
            format_detecte = format_lat if format_lat != "Inconnu" else format_lon

            # Validation individuelle de chaque coordonnée : doit être présente, avoir un DD et être au format DMS
            lat_valide = bool(lat_dms and lat_dd is not None) and format_lat == "DMS"
            lon_valide = bool(lon_dms and lon_dd is not None) and format_lon == "DMS"

            # Forcer l'invalidité si le format DM est détecté (non accepté)
            if format_detecte == "DM":
                lat_valide = False
                lon_valide = False

            # ── Tout le reste → donnees_specifiques ───────────────────────────
            specifiques = {}
            for key, val in row.items():
                if key in CHAMPS_INTERNES:
                    continue
                if key in CHAMPS_NUMERO:
                    continue
                if key.endswith("_raw") or key.endswith("_conf"):
                    continue
                if val is not None and val != "":
                    try:
                        specifiques[key] = float(str(val).replace(",", "."))
                    except (ValueError, TypeError):
                        specifiques[key] = val

            # Ajouter un message d'erreur détaillé si les coordonnées sont invalides
            if not (lat_valide and lon_valide):
                if format_detecte == "DM":
                    specifiques["erreur_coordonnee"] = (
                        "Format DM détecté : minutes décimales (ex: 9°6.1160'E). "
                        "Le système accepte uniquement le format DMS (ex: 9°06'06.96\"E)."
                    )
                elif format_detecte == "DD":
                    specifiques["erreur_coordonnee"] = (
                        "Format DD détecté. Le système accepte uniquement le format DMS."
                    )
                elif format_detecte == "Inconnu":
                    specifiques["erreur_coordonnee"] = "Coordonnée non reconnue."

            point = DonneePointDTO(
                numero_ligne=ligne_num,
                numero=numero,
                coordonnees=CoordonneesDTO(
                    latitude_dms=lat_dms,
                    longitude_dms=lon_dms,
                    latitude_dd=float(lat_dd) if lat_dd is not None else None,
                    longitude_dd=float(lon_dd) if lon_dd is not None else None,
                    latitude_valide=lat_valide,
                    longitude_valide=lon_valide,
                    format_detecte=format_detecte,
                ),
                donnees_specifiques=specifiques if specifiques else None,
            )
            donnees.append(point)

        # ── Statistiques ─────────────────────────────────────────────────────
        total_lignes = len(donnees)
        lignes_valides = sum(
            1 for d in donnees
            if d.coordonnees.latitude_valide and d.coordonnees.longitude_valide
        )
        taux = round(
            (lignes_valides / total_lignes * 100) if total_lignes > 0 else 0,
            1
        )

        if total_lignes == 0:
            statut = "echec"
            message = "Aucune ligne extraite"
        elif lignes_valides == total_lignes:
            statut = "succes"
            message = f"{total_lignes} lignes extraites, {lignes_valides} coordonnées valides"
        elif lignes_valides > 0:
            statut = "succes_partiel"
            message = f"{total_lignes} lignes extraites, {lignes_valides} coordonnées valides"
        else:
            statut = "echec"
            message = f"{total_lignes} lignes extraites, aucune coordonnée valide"

        return ExtractionResult(
            statut_extraction=statut,
            taux_succes=taux,
            message=message,
            donnees=donnees,
            statistiques=StatistiquesDTO(
                total_lignes=total_lignes,
                lignes_valides=lignes_valides,
                coordonnees_valides=lignes_valides,
                taux_reussite=taux,
            ),
            formulaire_id=formulaire_id,
            type_formulaire=form_type,
        )

    # ─── Validation côté serveur des coordonnées DMS ─────────────────────────

    def validate_dms_points(self, points_data: List[Dict]) -> dict:
        """
        Valide les coordonnées DMS d'une liste de points (sans persistance).
        Utilise le même code regex que le pipeline OCR.

        Retourne un dict avec :
          - resultats : liste de dicts par ligne avec latitude_valide/longitude_valide
          - statut_global : "succes" | "succes_partiel" | "echec"
          - nb_valides : nombre de points entièrement valides
          - nb_total : nombre total de points
        """
        from backend.modules.ocr.pipeline import CHAMPS_LAT, CHAMPS_LON

        resultats = []
        nb_valides = 0

        for pt in points_data:
            coords = pt.get("coordonnees", {})
            lat_dms = coords.get("latitude_dms", "") or coords.get("latitude", "")
            lon_dms = coords.get("longitude_dms", "") or coords.get("longitude", "")

            # Check format FIRST — reject DM/DD/Inconnu before DMS validation
            format_lat = detecter_format(lat_dms) if lat_dms else "Inconnu"
            format_lon = detecter_format(lon_dms) if lon_dms else "Inconnu"

            if format_lat == "DM":
                lat_valide = False
                lat_result = None
                erreur_lat = "Format DM non accepté. Utilisez DMS (ex: 36°52'53.28\"N)"
            elif format_lat != "DMS":
                lat_valide = False
                lat_result = None
                erreur_lat = f"Format {format_lat} non accepté. Utilisez DMS."
            else:
                lat_result = valider_dms(lat_dms, "latitude_dms")
                lat_valide = lat_result is not None
                erreur_lat = None if lat_valide else "Coordonnée DMS invalide (plages WGS84 non respectées)"

            if format_lon == "DM":
                lon_valide = False
                lon_result = None
                erreur_lon = "Format DM non accepté. Utilisez DMS (ex: 9°06'06.96\"E)"
            elif format_lon != "DMS":
                lon_valide = False
                lon_result = None
                erreur_lon = f"Format {format_lon} non accepté. Utilisez DMS."
            else:
                lon_result = valider_dms(lon_dms, "longitude_dms")
                lon_valide = lon_result is not None
                erreur_lon = None if lon_valide else "Coordonnée DMS invalide (plages WGS84 non respectées)"

            # Calcul des DD si valide
            lat_dd = _dms_to_dd(lat_result) if lat_valide else None
            lon_dd = _dms_to_dd(lon_result) if lon_valide else None

            point_valide = lat_valide and lon_valide
            if point_valide:
                nb_valides += 1

            resultats.append({
                "numero_ligne": pt.get("numero_ligne", 1),
                "numero": pt.get("numero"),
                "coordonnees": {
                    "latitude_dms": lat_result if lat_valide else lat_dms,
                    "longitude_dms": lon_result if lon_valide else lon_dms,
                    "latitude_dd": lat_dd,
                    "longitude_dd": lon_dd,
                    "latitude_valide": lat_valide,
                    "longitude_valide": lon_valide,
                },
                "donnees_specifiques": pt.get("donnees_specifiques", {}),
            })

        nb_total = len(points_data)
        if nb_total == 0:
            statut_global = "echec"
        elif nb_valides == nb_total:
            statut_global = "succes"
        elif nb_valides > 0:
            statut_global = "succes_partiel"
        else:
            statut_global = "echec"

        return {
            "status": "ok",
            "resultats": resultats,
            "statut_global": statut_global,
            "nb_valides": nb_valides,
            "nb_total": nb_total,
        }

    # ─── Preview extraction ───────────────────────────────────────────────────

    def preview_extract(self, dossier_id: int, file_content: bytes, filename: str) -> ExtractionResult:
        print(f"\n>>> [ExtractionService] Starting PREVIEW extraction for Dossier ID: {dossier_id}, File: {filename}")
        try:
            dossier = self.db.query(Dossier).filter(Dossier.id == dossier_id).first()
            if not dossier:
                print(f"!!! [ExtractionService] Error: Dossier {dossier_id} not found")
                raise ValueError(f"Dossier {dossier_id} not found")

            now = datetime.datetime.now()
            year = now.strftime("%Y")
            month = now.strftime("%m")

            save_dir = os.path.join(settings.STORAGE_PATH, year, month, dossier.numero_dossier)
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, filename)

            with open(save_path, "wb") as f:
                f.write(file_content)
            print(f"  ✓ File saved to: {save_path}")

            formulaire = self.db.query(FormulaireNumerise).filter(FormulaireNumerise.dossier_id == dossier_id).first()

            if formulaire:
                print(f"  ... Found existing FormulaireNumerise ID: {formulaire.id}. Updating...")
                formulaire.nom_fichier = filename
                formulaire.chemin_stockage = save_path
                formulaire.format = filename.split(".")[-1].upper()
                formulaire.date_upload = datetime.datetime.now()
            else:
                print(f"  ... No existing FormulaireNumerise for Dossier {dossier_id}. Creating new...")
                try:
                    formulaire = FormulaireNumerise(dossier_id=dossier_id, nom_fichier=filename,
                                                     chemin_stockage=save_path,
                                                     format=filename.split(".")[-1].upper(),
                                                     date_upload=datetime.datetime.now())
                    self.db.add(formulaire)
                    self.db.flush()
                except Exception as e:
                    self.db.rollback()
                    print(f"  ! Insertion failed (likely duplicate), retrying as update: {str(e)}")
                    formulaire = self.db.query(FormulaireNumerise).filter(FormulaireNumerise.dossier_id == dossier_id).first()
                    if formulaire:
                        formulaire.nom_fichier = filename
                        formulaire.chemin_stockage = save_path
                        formulaire.format = filename.split(".")[-1].upper()
                        formulaire.date_upload = datetime.datetime.now()
                    else:
                        raise e

            self.db.flush()

            img_path = save_path
            is_pdf = filename.lower().endswith(".pdf")
            if is_pdf:
                print("  ... Converting PDF first page to image")
                tmp_img = os.path.join(save_dir, "temp_ocr_page1.png")
                pdfToImage.convert_pdf_first_page(save_path, output_image=tmp_img)
                img_path = tmp_img

            print(f"  ... Loading image: {img_path}")
            img = cv2.imread(img_path)
            if img is None:
                print(f"!!! [ExtractionService] Error: Could not read image from {img_path}")
                raise ValueError(f"Could not read image from {img_path}")

            print("  ... Detecting ArUco marker")
            marker_id, corners = pipeline.detect_marker(img)
            if marker_id is None:
                print("!!! [ExtractionService] No marker detected.")
                self.db.commit()
                return self._build_extraction_result(
                    formulaire_id=formulaire.id,
                    form_type="Inconnu",
                    rows=[],
                    marker_id=marker_id
                )

            form_type = config.FORMULAIRES.get(marker_id, "Inconnu")
            roi_config = config.ROI_CONFIGS.get(marker_id)
            if not roi_config:
                print(f"!!! [ExtractionService] No ROI config found for marker {marker_id}.")
                self.db.commit()
                return self._build_extraction_result(
                    formulaire_id=formulaire.id,
                    form_type=form_type,
                    rows=[],
                    marker_id=marker_id
                )

            print("  ... Computing ROIs and running OCR pipeline")

            all_rows = []
            if marker_id == 30:
                cfg1 = roi_config.get("tableau_lignes_electriques")
                if cfg1:
                    rois1 = pipeline.compute_rois(corners, cfg1)
                    rows1 = pipeline.extract_table(img, rois1)
                    for r in rows1:
                        r["_table"] = "lignes_electriques"
                    all_rows.extend(rows1)

                cfg2 = roi_config.get("tableau_emission")
                if cfg2:
                    rois2 = pipeline.compute_rois(corners, cfg2)
                    rows2 = pipeline.extract_table(img, rois2)
                    for r in rows2:
                        r["_table"] = "emission"
                    all_rows.extend(rows2)
            else:
                all_rois = pipeline.compute_rois(corners, roi_config)
                all_rows = pipeline.extract_table(img, all_rois)

            print(f"  ✓ Extracted {len(all_rows)} rows")

            dossier.type_demande = form_type
            formulaire.type_formulaire = form_type
            formulaire.marqueur_aruco = marker_id
            self.db.commit()

            if is_pdf and os.path.exists(img_path):
                os.remove(img_path)

            result = self._build_extraction_result(
                formulaire_id=formulaire.id,
                form_type=form_type,
                rows=all_rows,
                marker_id=marker_id
            )

            print(f">>> [ExtractionService] Preview completed for {filename}")
            print(f"    Statut: {result.statut_extraction} | Taux: {result.taux_succes}% | {result.message}")
            return result

        except Exception as e:
            print(f"!!! [ExtractionService] UNEXPECTED ERROR during preview of {filename}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise e

    # ─── Confirmation (sauvegarde en BDD + génération KMZ) ────────────────────

    def confirm_extraction(self, formulaire_id: int, points_data: List[Dict]) -> dict:
        """
        Sauvegarde les points validés en base de données,
        génère automatiquement le fichier KMZ,
        calcule l'altitude finale maximale.

        Retourne un dict avec :
          - status
          - nb_points : nombre de points sauvegardés
          - kmz_path : chemin du fichier KMZ généré
          - kmz_filename : nom du fichier KMZ
          - altitude_finale_max : altitude finale maximale relevée
          - points : la liste des points sauvegardés (avec donnees_specifiques)
        """
        print(f"\n>>> [ExtractionService] Confirming extraction for Formulaire ID: {formulaire_id}")
        try:
            # Récupérer le formulaire pour avoir le dossier_id
            formulaire = self.db.query(FormulaireNumerise).filter(FormulaireNumerise.id == formulaire_id).first()
            if not formulaire:
                raise ValueError(f"Formulaire {formulaire_id} not found")
            dossier_id = formulaire.dossier_id

            saved_points = []
            for pt in points_data:
                num_ligne = pt.get("numero_ligne", 1)
                coords = pt.get("coordonnees", {})
                lat = coords.get("latitude_dms", "")
                lon = coords.get("longitude_dms", "")
                # coordonnee_valide = True for all confirmed points
                # (they passed validation before confirm was called)
                lat_val = True
                lon_val = True
                specifiques = pt.get("donnees_specifiques", {})

                # Upsert: Vérifier si le point existe déjà pour ce formulaire et cette ligne
                existing_point = self.db.query(PointMesure).filter(
                    PointMesure.formulaire_id == formulaire_id,
                    PointMesure.numero_ligne == num_ligne
                ).first()

                lat_dd_val = coords.get("latitude_dd")
                lon_dd_val = coords.get("longitude_dd")

                if existing_point:
                    existing_point.coordinates = {
                        "lat": lat,
                        "lon": lon,
                        "lat_dd": lat_dd_val,
                        "lon_dd": lon_dd_val,
                    }
                    existing_point.coordonnee_valide = True
                    existing_point.corrigee_manuellement = True
                    existing_point.donnees_specifiques = specifiques
                    point_to_save = existing_point
                else:
                    point_to_save = PointMesure(
                        formulaire_id=formulaire_id,
                        numero_ligne=num_ligne,
                        coordinates={
                            "lat": lat,
                            "lon": lon,
                            "lat_dd": lat_dd_val,
                            "lon_dd": lon_dd_val,
                        },
                        coordonnee_valide=True,
                        corrigee_manuellement=True,
                        donnees_specifiques=specifiques,
                        page_source=1
                    )
                    self.db.add(point_to_save)
                
                saved_points.append(point_to_save)

            self.db.flush()  # Récupère les IDs sans commit final

            # ── Calcul de l'altitude finale maximale ──────────────────────────
            altitude_finale_max = 0.0
            for pt in points_data:
                spec = pt.get("donnees_specifiques", {})
                # Chercher les champs d'altitude totale ou finale
                for key, val in spec.items():
                    key_lower = key.lower()
                    if "altitude totale" in key_lower or "altitude finale" in key_lower:
                        try:
                            val_f = float(str(val).replace(",", "."))
                            if val_f > altitude_finale_max:
                                altitude_finale_max = val_f
                        except (ValueError, TypeError):
                            pass

            # ── Génération automatique du KMZ ─────────────────────────────────
            kmz_path = ""
            kmz_filename = ""
            try:
                kmz_service = KMZService(self.db)
                # On passe les points déjà sauvegardés pour éviter une requête
                generated_path = kmz_service.generate(dossier_id, points_override=saved_points)
                kmz_path = generated_path
                kmz_filename = os.path.basename(generated_path)
                print(f"  ✓ KMZ generated: {kmz_path}")
            except Exception as e:
                print(f"  ! KMZ generation failed (non-fatal): {str(e)}")

            self.db.commit()
            print(f"  ✓ Successfully saved {len(points_data)} points to DB\n")

            return {
                "status": "success",
                "dossier_id": dossier_id,
                "nb_points": len(points_data),
                "kmz_path": kmz_path,
                "kmz_filename": kmz_filename,
                "altitude_finale_max": altitude_finale_max,
                "points": points_data
            }

        except Exception as e:
            print(f"!!! [ExtractionService] Error during confirmation: {str(e)}")
            self.db.rollback()
            raise e