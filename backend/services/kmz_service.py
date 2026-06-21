"""
Service generation fichier KMZ.
- Recupere les coordonnees WGS84 validees depuis la base
- Convertit les coordonnees DMS en degres decimaux
- Cree le fichier KMZ avec les placemarks pour Google Earth
- Sauvegarde et enregistre le document genere en base
"""
import os, datetime
from typing import Any
import simplekml
from sqlalchemy.orm import Session
from backend.models.point_mesure import PointMesure
from backend.models.formulaire import FormulaireNumerise
from backend.models.document_genere import DocumentGenere
from backend.core.config import settings
import re

class KMZService:
    def __init__(self, db: Session):
        self.db = db

    def generate(self, dossier_id: int, points_override: list = None) -> str:
        """
        Genere le fichier KMZ a partir des points de mesure.
        
        Si points_override est fourni, utilise ces objets PointMesure
        (deja en memoire) au lieu de faire une requete DB.
        """
        try:
            if points_override is not None:
                points = points_override
            else:
                points = self.db.query(PointMesure).join(FormulaireNumerise).filter(
                    FormulaireNumerise.dossier_id == dossier_id,
                    PointMesure.coordonnee_valide == True
                ).all()

            # Don't regenerate if KMZ already exists and no valid points are found
            if points_override is None and len(points) == 0:
                kmz_dir = os.path.join(settings.STORAGE_PATH, "kmz")
                existing_kmz = os.path.join(kmz_dir, f"localisation_{dossier_id}.kmz")
                if os.path.exists(existing_kmz):
                    print(f"  → KMZ already exists at {existing_kmz}, returning existing file")
                    return existing_kmz
                print(f"  ! No valid points found for dossier {dossier_id}")
                raise ValueError(f"Aucun point valide pour le dossier {dossier_id}")

            print(f"\n>>> [KMZService] Generating KMZ for dossier {dossier_id}")
            print(f"    Points count: {len(points)}")

            for pt in points:
                coords = getattr(pt, 'coordinates', {}) or {}
                print(f"    Point {getattr(pt, 'numero_ligne', '?')}: "
                      f"coordinates={coords}, "
                      f"coordonnee_valide={getattr(pt, 'coordonnee_valide', '?')}")

            kml = simplekml.Kml()
            for pt in points:
                # On s'assure que pt a bien un attribut coordinates
                coords = getattr(pt, 'coordinates', {}) or {}
                if not isinstance(coords, dict):
                    coords = {}

                # Use pre-computed DD values if available
                lat_dd = coords.get("lat_dd")
                lon_dd = coords.get("lon_dd")

                if lat_dd is not None and lon_dd is not None:
                    lat = float(lat_dd)
                    lon = float(lon_dd)
                else:
                    # Fallback: convert from DMS string
                    lat = self._dms_to_dd(coords.get("lat", ""))
                    lon = self._dms_to_dd(coords.get("lon", ""))

                # Skip invalid points
                if lat == 0.0 and lon == 0.0:
                    print(f"  ! Skipping point {getattr(pt, 'numero_ligne', '?')} — invalid coordinates")
                    continue

                print(f"  → Point {getattr(pt, 'numero_ligne', '?')}: lat={lat}, lon={lon}")
                
                try:
                    pnt = kml.newpoint(
                        name=str(getattr(pt, 'numero_ligne', 'N/A')),
                    )
                    pnt.coords = [(lon, lat)]
                    spec = getattr(pt, 'donnees_specifiques', {}) or {}
                    desc_lines = [f"Latitude DMS: {coords.get('lat','')}",
                                  f"Longitude DMS: {coords.get('lon','')}"]
                    for k, v in spec.items():
                        if not k.startswith("_") and k != "erreur_coordonnee":
                            desc_lines.append(f"{k}: {v}")
                    pnt.description = "\n".join(desc_lines)
                    print(f"  ✓ Added point {getattr(pt, 'numero_ligne', '?')} at ({lat:.6f}, {lon:.6f})")
                except Exception as e:
                    print(f"  ! Failed to add point: {e}")
                    continue

            # Gestion sécurisée du répertoire et du fichier
            try:
                kmz_dir = os.path.join(settings.STORAGE_PATH, "kmz")
                os.makedirs(kmz_dir, exist_ok=True)
                output_path = os.path.join(kmz_dir, f"localisation_{dossier_id}.kmz")
                kml.savekmz(output_path)
            except (OSError, IOError) as e:
                print(f"Erreur système lors de l'écriture du KMZ: {e}")
                raise RuntimeError(f"Impossible d'écrire le fichier KMZ sur le disque: {str(e)}")

            # After building KML, print point count
            print(f"    Output path: {output_path}")

            # Sauvegarder la reference en base
            doc_db = DocumentGenere(
                dossier_id=dossier_id,
                nom_fichier=os.path.basename(output_path),
                type_document="KMZ",
                chemin_stockage=output_path,
                date_creation=datetime.datetime.now()
            )
            self.db.add(doc_db)
            # Note : le commit est fait par l'appelant (confirm_extraction)
            return output_path
            
        except Exception as e:
            print(f"Erreur critique lors de la génération KMZ pour dossier {dossier_id}: {e}")
            # On relance l'exception pour qu'elle soit capturée par l'API
            raise e

    def _dms_to_dd(self, dms: Any) -> float:
        """
        Convertit une coordonnée en degrés décimaux.
        Gère les formats :
        - Float/Int : retourné tel quel.
        - String numérique : converti en float.
        - String DMS : converti via regex.
        """
        if dms is None:
            return 0.0

        # 1. Si c'est déjà un nombre
        if isinstance(dms, (int, float)):
            return float(dms)

        if not isinstance(dms, str):
            return 0.0

        dms_stripped = dms.strip()
        if not dms_stripped:
            return 0.0

        # 2. Tentative de conversion directe en float (cas DD)
        try:
            # On remplace la virgule par un point pour le float()
            return float(dms_stripped.replace(',', '.'))
        except ValueError:
            pass

        # 3. Conversion DMS via le pattern du pipeline
        from backend.modules.ocr.pipeline import DMS_GENERIC
        
        # On teste avec et sans espaces pour maximiser le match
        t_no_space = dms_stripped.replace(' ', '')
        m = DMS_GENERIC.search(t_no_space)
        if not m:
            m = DMS_GENERIC.search(dms_stripped)
            
        if not m:
            return 0.0
                
        try:
            deg = float(m.group(1))
            mn  = float(m.group(2))
            sec = float(m.group(3).replace(',', '.'))
            direction = m.group(4).upper()
            
            dd = deg + mn/60 + sec/3600
            return -dd if direction in ('S', 'W') else dd
        except (ValueError, IndexError):
            return 0.0
