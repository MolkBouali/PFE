"""
ExtractionView — Interface résultats extraction OCR
Flux : POST /extract/{dossier_id} → tableau éditable → POST /extraction/confirm

Intégration dans DossierView :
    view = ExtractionView(token, dossier_id, file_path) 
    view.confirmed.connect(self._on_extraction_confirmed)
"""

import os
import requests
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QStackedWidget, QProgressBar, QSizePolicy, QFileDialog
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QColor, QFont, QBrush


# ── Couleurs cohérentes avec DossierView ─────────────────────────────────────
PRIMARY    = "#1e3a5f"
SUCCESS    = "#166534"
SUCCESS_BG = "#f0fdf4"
SUCCESS_BD = "#bbf7d0"
DANGER     = "#991b1b"
DANGER_BG  = "#fee2e2"
DANGER_BD  = "#fecaca"
WARN_BG    = "#fef9c3"
WARN_BD    = "#fde68a"
BORDER     = "#e2e8f0"
TEXT_MAIN  = "#1a1a2e"
TEXT_SUB   = "#64748b"
TEXT_MUTED = "#94a3b8"
BG         = "#f0f2f5"
CARD       = "#ffffff"


# ── Worker threads ───────────────────────────────────────────────────────────

class ExtractionWorker(QThread):
    finished = Signal(dict)   # résultat JSON
    failed   = Signal(str)    # message d'erreur

    def __init__(self, token: str, dossier_id: int, file_path: str):
        super().__init__()
        self.token      = token
        self.dossier_id = dossier_id
        self.file_path  = file_path

    def run(self):
        try:
            with open(self.file_path, "rb") as f:
                ext  = os.path.splitext(self.file_path)[1].lower()
                mime = "application/pdf" if ext == ".pdf" else "image/png"
                resp = requests.post(
                    f"http://localhost:8000/extraction/extract/{self.dossier_id}",
                    files={"file": (os.path.basename(self.file_path), f, mime)},
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=120
                )
            if resp.status_code == 200:
                self.finished.emit(resp.json())
            else:
                self.failed.emit(f"Erreur serveur ({resp.status_code}) : {resp.text}")
        except Exception as e:
            self.failed.emit(f"Impossible de contacter le serveur : {str(e)}")

class ValidationWorker(QThread):
    finished = Signal(dict)
    failed   = Signal(str)

    def __init__(self, token: str, points: list):
        super().__init__()
        self.token = token
        self.points = points

    def run(self):
        try:
            resp = requests.post(
                "http://localhost:8000/extraction/validate",
                json={"points": self.points},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=30,
            )
            if resp.status_code == 200:
                self.finished.emit(resp.json())
            elif resp.status_code == 422:
                self.failed.emit(f"Erreur de format (422): {resp.json().get('detail')}")
            else:
                self.failed.emit(f"Erreur serveur ({resp.status_code}): {resp.text}")
        except Exception as e:
            self.failed.emit(str(e))


# ── Étape pipeline visuelle ───────────────────────────────────────────────────
class PipelineStep(QFrame):
    def __init__(self, label: str, status: str = "wait", parent=None):
        super().__init__(parent)
        self.setStyleSheet("QFrame { background: transparent; border: none; }")
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 3, 0, 3)
        row.setSpacing(10)

        icons  = {"done": "✓", "active": "⟳", "wait": "○", "error": "✗"}
        colors = {
            "done":   (SUCCESS_BG, SUCCESS_BD, SUCCESS),
            "active": ("#eff6ff", "#bfdbfe", "#1e40af"),
            "wait":   ("#f8fafc", BORDER, TEXT_MUTED),
            "error":  (DANGER_BG, DANGER_BD, DANGER),
        }
        bg, bd, fg = colors.get(status, colors["wait"])

        dot = QLabel(icons.get(status, "○"))
        dot.setFixedSize(24, 24)
        dot.setAlignment(Qt.AlignCenter)
        dot.setFont(QFont("Segoe UI", 10, QFont.Bold))
        dot.setStyleSheet(
            f"background:{bg}; border:1px solid {bd}; border-radius:12px; color:{fg};"
        )

        lbl = QLabel(label)
        lbl.setFont(QFont("Segoe UI", 11))
        lbl.setStyleSheet(
            f"color:{PRIMARY if status=='active' else TEXT_MAIN if status=='done' else TEXT_MUTED};"
            f"{'font-weight:bold;' if status=='active' else ''}"
            "border:none; background:transparent;"
        )

        row.addWidget(dot)
        row.addWidget(lbl)
        row.addStretch()


# ── Page 1 : animation pipeline en cours ─────────────────────────────────────
class PipelinePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._progress = 0
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setFixedWidth(450)
        card.setStyleSheet(f"""
            QFrame {{
                background:{CARD};
                border:1px solid {BORDER};
                border-radius:12px;
            }}
        """)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(30, 30, 30, 30)
        cl.setSpacing(12)

        title = QLabel("Pipeline d'extraction en cours...")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title.setStyleSheet(f"color:{PRIMARY}; border:none; background:transparent;")
        cl.addWidget(title)

        sub = QLabel("Le serveur analyse le formulaire scanné.\nCette opération peut prendre quelques secondes.")
        sub.setAlignment(Qt.AlignCenter)
        sub.setFont(QFont("Segoe UI", 10))
        sub.setStyleSheet(f"color:{TEXT_SUB}; border:none; background:transparent;")
        sub.setWordWrap(True)
        cl.addWidget(sub)
        cl.addSpacing(10)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setFixedHeight(6)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background:{BORDER};
                border-radius:3px;
                border:none;
            }}
            QProgressBar::chunk {{
                background:{PRIMARY};
                border-radius:3px;
            }}
        """)
        cl.addWidget(self.progress)

        layout.addWidget(card)


# ── Page 2 : tableau résultats ────────────────────────────────────────────────
class ResultsPage(QWidget):
    validated = Signal(object)

    def __init__(self, token: str, dossier_id: int, result: dict, parent=None):
        super().__init__(parent)
        self.token      = token
        self.dossier_id = dossier_id
        self.result     = result
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        donnees      = self.result.get("donnees", [])
        stats        = self.result.get("statistiques", {})
        type_form    = self.result.get("type_formulaire", "—")
        statut       = self.result.get("statut_extraction", "inconnu")
        taux_succes  = self.result.get("taux_succes", 0)

        total_lignes   = stats.get("total_lignes", len(donnees))
        # Calculer le nombre total de cellules de coordonnées invalides (Lat + Lon)
        nb_invalides = 0
        for pt in donnees:
            coords = pt.get("coordonnees", {})
            if not coords.get("latitude_valide", False): nb_invalides += 1
            if not coords.get("longitude_valide", False): nb_invalides += 1
        
        # Conserver lignes_valides pour l'affichage du ratio (x/y)
        lignes_valides = stats.get("lignes_valides", 0)

        # ── Bandeau statut ────────────────────────────────────────────────────
        # On vérifie si au moins une coordonnée n'est pas au format DMS
        any_non_dms = False
        for pt in donnees:
            coords = pt.get("coordonnees", {})
            fmt = coords.get("format_detecte", "Inconnu")
            if fmt != "DMS":
                any_non_dms = True
                break

        # Priorisation : Si nb_invalides > 0 ou format non DMS, on ne peut PAS être en vert
        if nb_invalides == 0 and total_lignes > 0 and not any_non_dms:
            banner_bg = SUCCESS_BG
            banner_bd = SUCCESS_BD
            banner_fg = SUCCESS
            banner_tx = f"✓  Toutes les coordonnées sont valides et au format DMS ({lignes_valides}/{total_lignes}) — vous pouvez continuer."
        elif any_non_dms:
            banner_bg = WARN_BG
            banner_bd = WARN_BD
            banner_fg = "#92400e"
            banner_tx = f"⚠  Le format détecté n'est pas DMS. Veuillez générer un complément ou corriger les données."
        elif 0 < nb_invalides < (total_lignes * 2):
            banner_bg = WARN_BG
            banner_bd = WARN_BD
            banner_fg = "#92400e"
            banner_tx = f"⚠  Certaines coordonnées sont invalides — veuillez les corriger avant de confirmer."
        elif nb_invalides >= (total_lignes * 2) or total_lignes == 0 or statut == "echec":
            banner_bg = DANGER_BG
            banner_bd = DANGER_BD
            banner_fg = DANGER
            banner_tx = "✗  Aucune coordonnée valide extraite — vérifiez la qualité du scan ou le format du document."
        else:
            banner_bg = DANGER_BG
            banner_bd = DANGER_BD
            banner_fg = DANGER
            banner_tx = "✗  Erreur lors de la validation des coordonnées."

        self.banner = QLabel(banner_tx)
        self.banner.setFont(QFont("Segoe UI", 11))
        self.banner.setStyleSheet(
            f"background:{banner_bg}; border:1px solid {banner_bd}; "
            f"border-radius:6px; color:{banner_fg}; padding:8px 14px;"
        )
        self.banner.setWordWrap(True)
        layout.addWidget(self.banner)

        # ── Infos ─────────────────────────────────────────────────────────────
        message_api = self.result.get("message", "")
        info = QLabel(
            f"Type de formulaire : {type_form}  ·  "
            f"{total_lignes} ligne(s) détectée(s)  ·  "
            f"Taux de succès : {taux_succes}%"
        )
        info.setFont(QFont("Segoe UI", 10))
        info.setStyleSheet(f"color:{TEXT_MUTED}; border:none; background:transparent;")
        layout.addWidget(info)

        if message_api:
            msg2 = QLabel(message_api)
            msg2.setFont(QFont("Segoe UI", 9))
            msg2.setStyleSheet(f"color:{TEXT_MUTED}; border:none; background:transparent;")
            layout.addWidget(msg2)

        # ── Tableau ───────────────────────────────────────────────────────────
        fixed_cols  = ["N°", "Latitude DMS", "Longitude DMS"]

        spec_keys = []
        if donnees:
            spec_keys = [k for k in donnees[0].get("donnees_specifiques", {}).keys()
                         if not k.startswith("_")]

        alt_keys = [k for k in spec_keys if "altitude" in k.lower() or "finale" in k.lower()]
        autres_keys = [k for k in spec_keys if k not in alt_keys]
        spec_keys = autres_keys + alt_keys
        self.spec_keys = spec_keys

        def capitalize_header(key: str) -> str:
            return key[0].upper() + key[1:] if key else key

        all_cols = fixed_cols + [capitalize_header(k) for k in spec_keys]

        self.table = QTableWidget(len(donnees), len(all_cols))
        self.table.setHorizontalHeaderLabels(all_cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setFont(QFont("Segoe UI", 10))
        self.table.setStyleSheet(f"""
            QTableWidget {{
                border:1px solid {BORDER};
                border-radius:6px;
                background:{CARD};
                gridline-color:{BORDER};
            }}
            QHeaderView::section {{
                background:{BG};
                color:{TEXT_SUB};
                font-size:11px;
                font-weight:bold;
                border:none;
                border-bottom:1px solid {BORDER};
                padding:6px;
            }}
            QTableWidget::item:selected {{
                background:#e8f0fe;
                color:{TEXT_MAIN};
            }}
        """)

        for row_i, pt in enumerate(donnees):
            coords = pt.get("coordonnees", {})

            item_n = QTableWidgetItem(str(pt.get("numero_ligne", row_i + 1)))
            item_n.setTextAlignment(Qt.AlignCenter)
            item_n.setFlags(item_n.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_i, 0, item_n)

            item_lat = QTableWidgetItem(coords.get("latitude_dms", ""))
            item_lat.setFont(QFont("Segoe UI", 10))
            item_lat.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_i, 1, item_lat)

            item_lon = QTableWidgetItem(coords.get("longitude_dms", ""))
            item_lon.setFont(QFont("Segoe UI", 10))
            item_lon.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_i, 2, item_lon)

            spec = pt.get("donnees_specifiques", {})
            for col_j, key in enumerate(spec_keys, start=3):
                val = spec.get(key, "")
                if isinstance(val, float):
                    display = f"{val:.1f}" if val == int(val) else str(val)
                else:
                    display = str(val)
                item_s = QTableWidgetItem(display)
                item_s.setFont(QFont("Segoe UI", 10))
                item_s.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_i, col_j, item_s)

        layout.addWidget(self.table)

        # Show extraction result immediately before async validation
        if statut == "echec" or nb_invalides > 0:
            self.banner.setText(
                f"⚠  Coordonnées invalides détectées ({nb_invalides} cellule(s)) "
                f"— format DM ou non reconnu. Corrigez avant de continuer."
            )
            self.banner.setStyleSheet(
                f"background:{WARN_BG}; border:1px solid {WARN_BD}; "
                f"border-radius:6px; color:#92400e; padding:8px 14px;"
            )

        hint = QLabel("Double-cliquez sur une cellule pour la modifier manuellement.")
        hint.setFont(QFont("Segoe UI", 10))
        hint.setStyleSheet(f"color:{TEXT_MUTED}; border:none; background:transparent;")
        layout.addWidget(hint)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_relancer = QPushButton("⟳  Relancer l'extraction")
        btn_relancer.setObjectName("btnSecondary")
        btn_relancer.setFixedHeight(36)
        btn_relancer.setStyleSheet(self._btn_secondary())

        btn_complement = QPushButton("📄  Générer complément")
        btn_complement.setObjectName("btnSecondary")
        btn_complement.setFixedHeight(36)
        btn_complement.setStyleSheet(self._btn_secondary())
        # Le bouton s'affiche si au moins une coordonnée est en DD ou DM
        btn_complement.setVisible(any_non_dms)
        btn_complement.clicked.connect(self._on_generate_complement)

        self.btn_revalider = QPushButton("🔄  Revalider les coordonnées")
        self.btn_revalider.setFixedHeight(38)
        self.btn_revalider.setStyleSheet(self._btn_secondary())
        self.btn_revalider.clicked.connect(self._on_valider)

        self.btn_confirmer = QPushButton("✓  Confirmer et continuer")
        self.btn_confirmer.setFixedHeight(38)
        self.btn_confirmer.setEnabled(False)
        self.btn_confirmer.setStyleSheet(self._btn_secondary())
        self.btn_confirmer.clicked.connect(self._on_confirmer)

        btn_row.addWidget(btn_relancer)
        btn_row.addWidget(btn_complement)
        btn_row.addWidget(self.btn_revalider)
        btn_row.addWidget(self.btn_confirmer)
        layout.addLayout(btn_row)

        btn_relancer.clicked.connect(lambda: self.validated.emit([]))


    def _trigger_validation(self):
        """Lancement de la validation en arrière-plan pour éviter de geler l'UI"""
        original = self.result.get("donnees", [])
        nb_total = self.table.rowCount()
        points_in = []

        for row_i in range(nb_total):
            try:
                num = int(self.table.item(row_i, 0).text())
            except (ValueError, AttributeError):
                num = row_i + 1
            
            lat_texte = self.table.item(row_i, 1).text().strip() if self.table.item(row_i, 1) else ""
            lon_texte = self.table.item(row_i, 2).text().strip() if self.table.item(row_i, 2) else ""
            
            orig_point = next((p for p in original if p.get("numero_ligne") == num), {})
            spec_table = {}
            for col_j, key in enumerate(self.spec_keys, start=3):
                item = self.table.item(row_i, col_j)
                spec_table[key] = item.text().strip() if item else ""
            
            raw_num = orig_point.get("numero")
            numero_val = str(raw_num) if raw_num is not None else None

            point_dict = {
                "numero_ligne": num,
                "coordonnees": {
                    "latitude_dms": lat_texte,
                    "longitude_dms": lon_texte,
                },
                "donnees_specifiques": spec_table,
            }
            if numero_val is not None:
                point_dict["numero"] = numero_val

            points_in.append(point_dict)

        self.val_worker = ValidationWorker(self.token, points_in)
        self.val_worker.finished.connect(self._handle_validation_success)
        self.val_worker.failed.connect(self._handle_validation_error)
        self.val_worker.start()

    def _handle_validation_success(self, validate_result: dict):
        resultats = validate_result.get("resultats", [])
        statut_global = validate_result.get("statut_global", "echec")
        
        self._mettre_a_jour_tableau_avec_resultats(resultats)

        if statut_global != "succes":
            nb_invalides = 0
            for res in resultats:
                coords = res.get("coordonnees", {})
                if not coords.get("latitude_valide", False): nb_invalides += 1
                if not coords.get("longitude_valide", False): nb_invalides += 1
            
            if nb_invalides > 0:
                self.banner.setText(f"⚠  {nb_invalides} coordonnée(s) invalide(s) surlignée(s) en rouge — corrigez-les avant de valider.")
                self.banner.setStyleSheet(f"background:{WARN_BG}; border:1px solid {WARN_BD}; border-radius:6px; color:#92400e; padding:8px 14px;")
            else:
                self.banner.setText("⚠  Aucune coordonnée valide — vérifiez les valeurs saisies.")
                self.banner.setStyleSheet(f"background:{DANGER_BG}; border:1px solid {DANGER_BD}; border-radius:6px; color:{DANGER}; padding:8px 14px;")
            
            self.btn_confirmer.setEnabled(False)
            self.btn_confirmer.setStyleSheet(self._btn_secondary())
        else:
            self.btn_confirmer.setEnabled(True)
            self.btn_confirmer.setStyleSheet(self._btn_primary())
            self.banner.setText("✓  Toutes les coordonnées sont valides — cliquez sur Confirmer pour continuer.")
            self.banner.setStyleSheet(f"background:{SUCCESS_BG}; border:1px solid {SUCCESS_BD}; border-radius:6px; color:{SUCCESS}; padding:8px 14px;")

    def _handle_validation_error(self, error_msg: str):
        QMessageBox.critical(self, "Erreur de Validation", f"Le serveur a renvoyé une erreur :\n{error_msg}")

    def _on_valider(self):
        self._trigger_validation()

    def _mettre_a_jour_cellule_validation(self, row_i: int, lat_valide: bool, lon_valide: bool):
        err_bg = QColor(DANGER_BG)
        err_fg = QColor(DANGER)
        ok_bg  = QColor(SUCCESS_BG)
        ok_fg  = QColor(SUCCESS)

        item_lat = self.table.item(row_i, 1)
        if item_lat:
            if lat_valide:
                item_lat.setBackground(QBrush(ok_bg))
                item_lat.setForeground(QBrush(ok_fg))
            else:
                item_lat.setBackground(QBrush(err_bg))
                item_lat.setForeground(QBrush(err_fg))

        item_lon = self.table.item(row_i, 2)
        if item_lon:
            if lon_valide:
                item_lon.setBackground(QBrush(ok_bg))
                item_lon.setForeground(QBrush(ok_fg))
            else:
                item_lon.setBackground(QBrush(err_bg))
                item_lon.setForeground(QBrush(err_fg))

    def _mettre_a_jour_tableau_avec_resultats(self, resultats: list):
        for row_i, pt in enumerate(resultats):
            coords = pt.get("coordonnees", {})
            lat_valide = coords.get("latitude_valide", False)
            lon_valide = coords.get("longitude_valide", False)
            self._mettre_a_jour_cellule_validation(row_i, lat_valide, lon_valide)

    def _on_generate_complement(self):
        from PySide6.QtWidgets import QApplication
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            url = f"http://localhost:8000/extraction/generate-complement/{self.dossier_id}"
            resp = requests.post(
                url,
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=30
            )
            if resp.status_code == 200:
                filename = f"Complement_Dossier_{self.dossier_id}.docx"
                path, _ = QFileDialog.getSaveFileName(
                    self, "Sauvegarder le document", filename, "Document Word (*.docx)"
                )
                if path:
                    with open(path, "wb") as f:
                        f.write(resp.content)
                    QMessageBox.information(self, "Succès", "Le document a été généré avec succès.")
            else:
                QMessageBox.critical(
                    self, "Erreur", 
                    f"Le serveur n'a pas pu générer le document ({resp.status_code}) :\n{resp.text}"
                )
        except Exception as e:
            QMessageBox.critical(self, "Erreur réseau", f"Impossible de générer le document : {str(e)}")
        finally:
            QApplication.restoreOverrideCursor()


    def _on_confirmer(self):
        from PySide6.QtWidgets import QApplication

        formulaire_id = self.result.get("formulaire_id")
        if not formulaire_id:
            QMessageBox.critical(self, "Erreur", "Identifiant de formulaire manquant.")
            return

        # Recover points from table to ensure final state is saved
        original = self.result.get("donnees", [])
        nb_total = self.table.rowCount()
        points_to_confirm = []
        
        for row_i in range(nb_total):
            try:
                num = int(self.table.item(row_i, 0).text())
            except (ValueError, AttributeError):
                num = row_i + 1
            
            lat_texte = self.table.item(row_i, 1).text().strip() if self.table.item(row_i, 1) else ""
            lon_texte = self.table.item(row_i, 2).text().strip() if self.table.item(row_i, 2) else ""
            
            orig_point = next((p for p in original if p.get("numero_ligne") == num), {})
            
            spec_table = {}
            for col_j, key in enumerate(self.spec_keys, start=3):
                item = self.table.item(row_i, col_j)
                spec_table[key] = item.text().strip() if item else ""
            
            raw_num = orig_point.get("numero")
            numero_val = str(raw_num) if raw_num is not None else None

            point_dict = {
                "numero_ligne": num,
                "coordonnees": {
                    "latitude_dms": lat_texte,
                    "longitude_dms": lon_texte,
                },
                "donnees_specifiques": spec_table,
            }
            if numero_val is not None:
                point_dict["numero"] = numero_val

            points_to_confirm.append(point_dict)

        payload = {"formulaire_id": formulaire_id, "points": points_to_confirm}
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            resp = requests.post(
                "http://localhost:8000/extraction/confirm",
                json=payload,
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=30,
            )
            QApplication.restoreOverrideCursor()
            if resp.status_code == 200:
                confirm_result = resp.json()
                self.validated.emit(confirm_result)
            else:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'enregistrement ({resp.status_code}) :\n{resp.text}")
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "Erreur réseau", str(e))

    @staticmethod
    def _btn_primary():
        return (
            f"QPushButton {{ background:{PRIMARY}; color:white; border:none; "
            f"border-radius:6px; padding:0 20px; font-size:12px; font-weight:bold; }}"
            f"QPushButton:hover {{ background:#2d5282; }}"
        )

    @staticmethod
    def _btn_secondary():
        return (
            f"QPushButton {{ background:#e2e8f0; color:#475569; border:none; "
            f"border-radius:6px; padding:0 16px; font-size:12px; }}"
            f"QPushButton:hover {{ background:#cbd5e1; }}"
        )


class ErrorPage(QWidget):
    retry = Signal()

    def __init__(self, message: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setStyleSheet(f"QFrame {{ background:{DANGER_BG}; border:1px solid {DANGER_BD}; border-radius:8px; }}")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(24, 20, 24, 20)
        cl.setSpacing(10)

        icon = QLabel("✗")
        icon.setAlignment(Qt.AlignCenter)
        icon.setFont(QFont("Segoe UI", 28))
        icon.setStyleSheet(f"color:{DANGER}; border:none; background:transparent;")

        title = QLabel("Échec de l'extraction")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title.setStyleSheet(f"color:{DANGER}; border:none; background:transparent;")

        msg = QLabel(message)
        msg.setAlignment(Qt.AlignCenter)
        msg.setFont(QFont("Segoe UI", 10))
        msg.setStyleSheet(f"color:#7f1d1d; border:none; background:transparent;")
        msg.setWordWrap(True)

        btn = QPushButton("Réessayer")
        btn.setFixedHeight(36)
        btn.setStyleSheet(f"QPushButton {{ background:{DANGER}; color:white; border:none; border-radius:6px; padding:0 20px; font-weight:bold; }}")
        btn.clicked.connect(self.retry.emit)

        cl.addWidget(icon)
        cl.addWidget(title)
        cl.addWidget(msg)
        cl.addSpacing(8)
        cl.addWidget(btn, alignment=Qt.AlignCenter)
        layout.addWidget(card)


class ExtractionView(QWidget):
    confirmed = Signal(dict)
    relancer  = Signal()

    def __init__(self, token: str, dossier_id: int, file_path: str, parent=None):
        super().__init__(parent)
        self.token      = token
        self.dossier_id = dossier_id
        self.file_path  = file_path
        self.setStyleSheet(f"background:{BG}; font-family:'Segoe UI',Arial;")

        self.stack        = QStackedWidget(self)
        self.pipeline_pg  = PipelinePage()
        self.stack.addWidget(self.pipeline_pg)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self.stack)
        self._launch()

    def _launch(self):
        self.worker = ExtractionWorker(self.token, self.dossier_id, self.file_path)
        self.worker.finished.connect(self._on_success)
        self.worker.failed.connect(self._on_error)
        self.worker.start()

    def _on_success(self, result: dict):
        results_pg = ResultsPage(self.token, self.dossier_id, result)
        results_pg.validated.connect(self._on_validated)
        self.stack.addWidget(results_pg)
        self.stack.setCurrentWidget(results_pg)

    def _on_error(self, message: str):
        error_pg = ErrorPage(message)
        error_pg.retry.connect(self._on_retry)
        self.stack.addWidget(error_pg)
        self.stack.setCurrentWidget(error_pg)

    def _on_validated(self, confirm_result: dict):
        if not confirm_result or confirm_result.get("status") != "success":
            self._on_retry()
        else:
            self.confirmed.emit(confirm_result)

    def _on_retry(self):
        self.stack.setCurrentWidget(self.pipeline_pg)
        self._launch()