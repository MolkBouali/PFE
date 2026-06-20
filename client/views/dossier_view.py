"""
dossier_view.py — Vue de création/traitement d'un dossier OACA
Étapes : 1-Informations → 2-Extraction → 3-Validation → 4-Étude DEA → 5-Avis PDF
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QProgressBar, QSizePolicy, QScrollArea,
    QStackedWidget, QApplication, QMessageBox
)
from PySide6.QtCore import Qt, QSize, QTimer, Signal, QThread, QObject
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QIcon, QCursor
import sys
import os
from client.api_client.http_client import HTTPClient


# ──────────────────────────────────────────────
#  Palette de couleurs
# ──────────────────────────────────────────────
COLOR_PRIMARY    = "#1B3A5C"   # bleu marine foncé
COLOR_PRIMARY_HL = "#234876"   # bleu marine hover
COLOR_SUCCESS    = "#28A745"   # vert
COLOR_SUCCESS_BG = "#F0FFF4"   # fond vert clair
COLOR_SUCCESS_BD = "#B2DFBD"   # bordure vert
COLOR_BORDER     = "#D0D7E2"
COLOR_BG         = "#F4F6F9"
COLOR_TEXT_MAIN  = "#1A1A2E"
COLOR_TEXT_MUTED = "#6B7A99"
COLOR_STEP_DONE  = "#28A745"
COLOR_STEP_CURR  = COLOR_PRIMARY
COLOR_STEP_NEXT  = "#B0BAC9"
COLOR_INPUT_BORDER_FOCUS = "#1B3A5C"
COLOR_RED_CELL   = "#DC3545"
COLOR_GREEN_CELL = "#1B8A3C"


# ──────────────────────────────────────────────
#  Worker pour l'extraction autonome
# ──────────────────────────────────────────────
class ExtractionWorker(QThread):
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, client: HTTPClient, data: dict, dossier_id: int = None):
        super().__init__()
        self.client = client
        self.data = data
        self.dossier_id = dossier_id

    def run(self):
        try:
            # 1. Création du dossier si nécessaire
            if self.dossier_id is None:
                # Préparer les données pour le backend (DossierCreate)
                payload = {
                    "nom_demandeur": self.data.get("nom", ""),
                    "identifiant_depositaire": self.data.get("identifiant", ""),
                    "type_demande": self.data.get("type", ""),
                    "region": self.data.get("region", ""),
                }
                res = self.client.post("/dossiers/", json=payload)
                if res and "id" in res:
                    self.dossier_id = res["id"]
                else:
                    self.error.emit("Erreur lors de la création du dossier sur le serveur.")
                    return

            # 2. Extraction des coordonnées
            file_path = self.data.get("formulaire")
            if not file_path or not os.path.exists(file_path):
                self.error.emit("Fichier formulaire introuvable pour l'extraction.")
                return

            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f, "application/pdf")}
                # L'endpoint est /extraction/extract/{dossier_id}
                path = f"/extraction/extract/{self.dossier_id}"
                extract_res = self.client.post(path, files=files)

            if extract_res:
                # S'assurer que l'ID du dossier est transmis au signal finished
                if isinstance(extract_res, dict):
                    extract_res["dossier_id"] = self.dossier_id
                self.finished.emit(extract_res)
            else:
                self.error.emit("L'extraction a échoué ou le serveur n'a pas répondu.")

        except Exception as e:
            self.error.emit(f"Erreur technique : {str(e)}")

# ──────────────────────────────────────────────
#  Widget Stepper horizontal
# ──────────────────────────────────────────────
class StepperWidget(QWidget):
    STEPS = ["Informations", "Extraction", "Validation", "Étude DEA", "Avis PDF"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current = 0          # 0-based
        self._done    = set()
        self.setFixedHeight(80)
        self.setStyleSheet("background: white;")

    def set_current(self, index: int):
        """index 0-based"""
        self._current = index
        self._done = set(range(index))
        self.update()

    def mark_done(self, index: int):
        self._done.add(index)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        n = len(self.STEPS)
        w = self.width()
        h = self.height()
        circle_r = 16
        step_w = w // n
        cy = h // 2 - 6

        for i in range(n):
            cx = step_w * i + step_w // 2

            # Ligne de connexion (avant le cercle)
            if i > 0:
                prev_cx = step_w * (i - 1) + step_w // 2
                if i <= self._current:
                    color = QColor(COLOR_SUCCESS)
                else:
                    color = QColor(COLOR_STEP_NEXT)
                pen = QPen(color, 2)
                painter.setPen(pen)
                painter.drawLine(prev_cx + circle_r, cy, cx - circle_r, cy)

            # Cercle
            if i in self._done:
                # Vert avec coche
                painter.setBrush(QBrush(QColor(COLOR_SUCCESS)))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(cx - circle_r, cy - circle_r, circle_r * 2, circle_r * 2)
                pen = QPen(QColor("white"), 2)
                painter.setPen(pen)
                # Coche simple
                painter.drawLine(cx - 6, cy, cx - 2, cy + 5)
                painter.drawLine(cx - 2, cy + 5, cx + 6, cy - 5)
            elif i == self._current:
                # Cercle bleu marine
                painter.setBrush(QBrush(QColor(COLOR_PRIMARY)))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(cx - circle_r, cy - circle_r, circle_r * 2, circle_r * 2)
                painter.setPen(QPen(QColor("white")))
                font = QFont("Arial", 9, QFont.Bold)
                painter.setFont(font)
                painter.drawText(cx - circle_r, cy - circle_r, circle_r * 2, circle_r * 2,
                                 Qt.AlignCenter, str(i + 1))
            else:
                # Cercle gris
                painter.setBrush(QBrush(QColor("white")))
                painter.setPen(QPen(QColor(COLOR_STEP_NEXT), 2))
                painter.drawEllipse(cx - circle_r, cy - circle_r, circle_r * 2, circle_r * 2)
                painter.setPen(QPen(QColor(COLOR_STEP_NEXT)))
                font = QFont("Arial", 9)
                painter.setFont(font)
                painter.drawText(cx - circle_r, cy - circle_r, circle_r * 2, circle_r * 2,
                                 Qt.AlignCenter, str(i + 1))

            # Label
            label_y = cy + circle_r + 6
            if i in self._done:
                painter.setPen(QPen(QColor(COLOR_TEXT_MUTED)))
                font = QFont("Arial", 8)
            elif i == self._current:
                painter.setPen(QPen(QColor(COLOR_PRIMARY)))
                font = QFont("Arial", 8, QFont.Bold)
            else:
                painter.setPen(QPen(QColor(COLOR_STEP_NEXT)))
                font = QFont("Arial", 8)
            painter.setFont(font)
            painter.drawText(cx - 50, label_y, 100, 20, Qt.AlignCenter, self.STEPS[i])

        painter.end()


# ──────────────────────────────────────────────
#  Zone de dépôt de fichier (drag & drop)
# ──────────────────────────────────────────────
class DropZone(QFrame):
    file_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._filepath = None
        self.setAcceptDrops(True)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setMinimumHeight(120)
        self.setStyleSheet(f"""
            QFrame {{
                border: 2px dashed {COLOR_BORDER};
                border-radius: 8px;
                background: #FAFBFD;
            }}
            QFrame:hover {{
                border-color: {COLOR_PRIMARY};
                background: #F0F4FA;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(6)

        # Icône trombone (unicode)
        self.icon_label = QLabel("📎")
        self.icon_label.setAlignment(Qt.AlignCenter)
        font_icon = QFont("Arial", 28)
        self.icon_label.setFont(font_icon)
        layout.addWidget(self.icon_label)

        self.text_label = QLabel("Déposez le formulaire ici ou cliquez pour parcourir")
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; border: none; background: transparent;")
        font_txt = QFont("Arial", 9)
        self.text_label.setFont(font_txt)
        layout.addWidget(self.text_label)

        self.hint_label = QLabel("Formats acceptés : PNG, JPG, PDF — Taille max : 10 Mo")
        self.hint_label.setAlignment(Qt.AlignCenter)
        self.hint_label.setStyleSheet(f"color: {COLOR_STEP_NEXT}; font-size: 8pt; border: none; background: transparent;")
        layout.addWidget(self.hint_label)

    def mousePressEvent(self, event):
        self._open_dialog()

    def _open_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choisir le formulaire scanné", "",
            "Images et PDF (*.png *.jpg *.jpeg *.pdf)"
        )
        if path:
            self._set_file(path)

    def _set_file(self, path):
        self._filepath = path
        filename = os.path.basename(path)
        self.text_label.setText(f"✅  {filename}")
        self.text_label.setStyleSheet(f"color: {COLOR_SUCCESS}; border: none; background: transparent;")
        self.hint_label.hide()
        self.icon_label.hide()
        self.file_selected.emit(path)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            self._set_file(urls[0].toLocalFile())

    def get_filepath(self):
        return self._filepath

    def reset(self):
        self._filepath = None
        self.icon_label.show()
        self.hint_label.show()
        self.text_label.setText("Déposez le formulaire ici ou cliquez pour parcourir")
        self.text_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; border: none; background: transparent;")


# ──────────────────────────────────────────────
#  Page 1 — Informations (Créer un nouveau dossier)
# ──────────────────────────────────────────────
class InformationsPage(QWidget):
    submitted = Signal(dict)   # émet les données du formulaire
    cancelled = Signal()

    FIELD_STYLE = f"""
        QLineEdit, QComboBox {{
            border: 1.5px solid {COLOR_BORDER};
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 10pt;
            color: {COLOR_TEXT_MAIN};
            background: white;
        }}
        QLineEdit:focus, QComboBox:focus {{
            border-color: {COLOR_INPUT_BORDER_FOCUS};
        }}
        QLineEdit::placeholder {{
            color: {COLOR_STEP_NEXT};
        }}
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 30, 40, 20)
        root.setSpacing(0)

        # Titre
        title = QLabel("Créer un nouveau dossier")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet(f"color: {COLOR_TEXT_MAIN};")
        root.addWidget(title)

        root.addSpacing(6)

        subtitle = QLabel("Renseignez les informations du déposant et uploadez le formulaire scanné")
        subtitle.setFont(QFont("Arial", 9))
        subtitle.setStyleSheet(f"color: {COLOR_PRIMARY};")
        root.addWidget(subtitle)

        root.addSpacing(24)

        def field_label(text):
            lbl = QLabel(text)
            lbl.setFont(QFont("Arial", 8, QFont.Bold))
            lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; letter-spacing: 0.5px;")
            return lbl

        # NOM DU DÉPOSANT
        root.addWidget(field_label("NOM DU DÉPOSANT *"))
        root.addSpacing(4)
        self.nom_input = QLineEdit()
        self.nom_input.setPlaceholderText("Ex : Société Éolienne du Nord")
        self.nom_input.setStyleSheet(self.FIELD_STYLE)
        self.nom_input.setFixedHeight(42)
        root.addWidget(self.nom_input)

        root.addSpacing(14)

        # IDENTIFIANT DÉPOSANT
        root.addWidget(field_label("IDENTIFIANT DÉPOSANT *"))
        root.addSpacing(4)
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("Ex : SEN-2024-112")
        self.id_input.setStyleSheet(self.FIELD_STYLE)
        self.id_input.setFixedHeight(42)
        root.addWidget(self.id_input)

        root.addSpacing(14)

        # TYPE DE DEMANDE
        root.addWidget(field_label("TYPE DE DEMANDE *"))
        root.addSpacing(4)
        self.type_combo = QComboBox()
        self.type_combo.addItems([""] + ["Bâtiment", "Éolienne", "Grue", "Pylône", "Station mobile"])
        self.type_combo.setStyleSheet(self.FIELD_STYLE + """
            QComboBox::drop-down { border: none; width: 30px; }
            QComboBox::down-arrow { image: none; border: none; }
        """)
        self.type_combo.setFixedHeight(42)
        root.addWidget(self.type_combo)

        root.addSpacing(14)

        # RÉGION
        root.addWidget(field_label("RÉGION *"))
        root.addSpacing(4)
        self.region_combo = QComboBox()
        self.region_combo.addItems([""] + ["Tunis", "Enfidha", "Monastir", "Djerba", "Sfax", "Tozeur", "Gafsa", "Tabarka", "Gabès", "Borj El Amri"])
        self.region_combo.setStyleSheet(self.FIELD_STYLE + """
            QComboBox::drop-down { border: none; width: 30px; }
            QComboBox::down-arrow { image: none; border: none; }
        """)
        self.region_combo.setFixedHeight(42)
        root.addWidget(self.region_combo)

        root.addSpacing(14)

        # FORMULAIRE SCANNÉ
        root.addWidget(field_label("FORMULAIRE SCANNÉ *"))
        root.addSpacing(6)
        self.drop_zone = DropZone()
        root.addWidget(self.drop_zone)

        root.addStretch(1)

        # Boutons
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)

        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.setFixedHeight(40)
        self.btn_cancel.setFixedWidth(110)
        self.btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background: white;
                border: 1.5px solid {COLOR_BORDER};
                border-radius: 6px;
                font-size: 10pt;
                color: {COLOR_TEXT_MAIN};
            }}
            QPushButton:hover {{
                background: #F0F0F0;
            }}
        """)
        self.btn_cancel.clicked.connect(self.cancelled.emit)
        btn_row.addWidget(self.btn_cancel)

        btn_row.addSpacing(10)

        self.btn_submit = QPushButton("Créer le dossier  →")
        self.btn_submit.setFixedHeight(40)
        self.btn_submit.setFixedWidth(180)
        self.btn_submit.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_PRIMARY};
                border: none;
                border-radius: 6px;
                font-size: 10pt;
                font-weight: bold;
                color: white;
            }}
            QPushButton:hover {{
                background: {COLOR_PRIMARY_HL};
            }}
        """)
        self.btn_submit.clicked.connect(self._on_submit)
        btn_row.addWidget(self.btn_submit)

        root.addLayout(btn_row)

    def _on_submit(self):
        nom = self.nom_input.text().strip()
        identifiant = self.id_input.text().strip()
        type_demande = self.type_combo.currentText()
        region = self.region_combo.currentText()
        formulaire = self.drop_zone.get_filepath()

        # Validation
        missing = []
        if not nom: missing.append("Nom du déposant")
        if not identifiant: missing.append("Identifiant déposant")
        if not type_demande: missing.append("Type de demande")
        if not region: missing.append("Région")
        if not formulaire: missing.append("Formulaire scanné")

        if missing:
            QMessageBox.warning(self, "Champs manquants", 
                                f"Veuillez remplir les champs suivants :\n\n" + "\n".join(missing))
            return

        data = {
            "nom": nom,
            "identifiant": identifiant,
            "type": type_demande,
            "region": region,
            "formulaire": formulaire,
        }
        self.submitted.emit(data)

    def reset(self):
        self.nom_input.clear()
        self.id_input.clear()
        self.region_combo.setCurrentIndex(0)
        self.type_combo.setCurrentIndex(0)
        self.drop_zone.reset()


# ──────────────────────────────────────────────
#  Page 2a — Extraction en cours (loading)
# ──────────────────────────────────────────────
class ExtractionLoadingPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 40, 40, 40)
        root.setAlignment(Qt.AlignCenter)

        # Carte centrale
        card = QFrame()
        card.setFixedWidth(460)
        card.setFixedHeight(180)
        card.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 12px;
                border: 1px solid #E0E6EF;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 30, 40, 30)
        card_layout.setSpacing(10)
        card_layout.setAlignment(Qt.AlignCenter)

        title = QLabel("Pipeline d'extraction en cours...")
        title.setFont(QFont("Arial", 13, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"color: {COLOR_TEXT_MAIN}; border: none; background: transparent;")
        card_layout.addWidget(title)

        desc = QLabel("Le serveur analyse le formulaire scanné.\nCette opération peut prendre quelques secondes.")
        desc.setFont(QFont("Arial", 9))
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; border: none; background: transparent;")
        card_layout.addWidget(desc)

        card_layout.addSpacing(8)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)   # indéterminé
        self.progress.setFixedHeight(8)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background: #E0E6EF;
                border-radius: 4px;
                border: none;
            }}
            QProgressBar::chunk {{
                background: {COLOR_PRIMARY};
                border-radius: 4px;
            }}
        """)
        card_layout.addWidget(self.progress)

        root.addStretch(1)
        h = QHBoxLayout()
        h.addStretch(1)
        h.addWidget(card)
        h.addStretch(1)
        root.addLayout(h)
        root.addStretch(1)

    def start(self):
        self.progress.setRange(0, 0)

    def set_progress(self, value: int, maximum: int = 100):
        self.progress.setRange(0, maximum)
        self.progress.setValue(value)


# ──────────────────────────────────────────────
#  Page 2b — Résultats de l'extraction
# ──────────────────────────────────────────────
class ExtractionResultPage(QWidget):
    relancer = Signal()
    valider  = Signal(list)   # émet les lignes validées

    HEADERS = ["N°", "Latitude DMS", "Longitude DMS",
               "Hauteur_mat", "Altitude_terrain", "Altitude_totale_mat"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows = []
        self.client = None
        self._build_ui()

    def set_client(self, client):
        self.client = client

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 20, 30, 20)
        root.setSpacing(10)

        # Bandeau succès
        self.banner = QFrame()
        self.banner.setFixedHeight(46)
        self.banner.setStyleSheet(f"""
            QFrame {{
                background: {COLOR_SUCCESS_BG};
                border: 1.5px solid {COLOR_SUCCESS_BD};
                border-radius: 8px;
            }}
        """)
        banner_lay = QHBoxLayout(self.banner)
        banner_lay.setContentsMargins(16, 0, 16, 0)
        self.banner_label = QLabel("✓  Toutes les coordonnées sont valides (4/4) — vous pouvez continuer.")
        self.banner_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.banner_label.setStyleSheet(f"color: {COLOR_SUCCESS}; background: transparent; border: none;")
        banner_lay.addWidget(self.banner_label)
        root.addWidget(self.banner)

        # Sous-titre
        self.subtitle = QLabel("Type de formulaire : eolienne  ·  4 ligne(s) détectée(s)  ·  Taux de succès : 100.0%")
        self.subtitle.setFont(QFont("Arial", 8))
        self.subtitle.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")
        root.addWidget(self.subtitle)

        self.detail = QLabel("4 lignes extraites, 4 coordonnées valides")
        self.detail.setFont(QFont("Arial", 8))
        self.detail.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")
        root.addWidget(self.detail)

        # Tableau
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.DoubleClicked)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(False)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                font-size: 9pt;
                background: white;
                gridline-color: {COLOR_BORDER};
            }}
            QHeaderView::section {{
                background: white;
                color: {COLOR_TEXT_MAIN};
                font-weight: bold;
                font-size: 9pt;
                border: none;
                border-bottom: 2px solid {COLOR_BORDER};
                padding: 8px 4px;
            }}
            QTableWidget::item {{
                padding: 6px 8px;
            }}
        """)
        root.addWidget(self.table)

        # Hint
        hint = QLabel("Double-cliquez sur une cellule pour la modifier manuellement.")
        hint.setFont(QFont("Arial", 8))
        hint.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")
        root.addWidget(hint)

        root.addStretch(1)

        # Boutons
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)

        self.btn_relancer = QPushButton("↻  Relancer l'extraction")
        self.btn_relancer.setFixedHeight(40)
        self.btn_relancer.setFixedWidth(190)
        self.btn_relancer.setStyleSheet(f"""
            QPushButton {{
                background: white;
                border: 1.5px solid {COLOR_BORDER};
                border-radius: 6px;
                font-size: 9pt;
                color: {COLOR_TEXT_MUTED};
            }}
            QPushButton:hover {{ background: #F0F0F0; }}
        """)
        self.btn_relancer.clicked.connect(self.relancer.emit)
        btn_row.addWidget(self.btn_relancer)

        btn_row.addSpacing(10)

        self.btn_valider = QPushButton("Valider les coordonnées  →")
        self.btn_valider.setFixedHeight(40)
        self.btn_valider.setFixedWidth(220)
        self.btn_valider.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_PRIMARY};
                border: none;
                border-radius: 6px;
                font-size: 10pt;
                font-weight: bold;
                color: white;
            }}
            QPushButton:hover {{
                background: {COLOR_PRIMARY_HL};
            }}
        """)
        self.btn_valider.clicked.connect(self._on_valider)
        btn_row.addWidget(self.btn_valider)

        root.addLayout(btn_row)

    def load_data(self, rows: list, type_formulaire: str = "eolienne",
                   n_detected: int = None, success_rate: float = 100.0,
                   n_valid: int = None):
        """
        rows: liste de DonneePointDTO (dicts avec coordonnées et donnees_specifiques)
        """
        self._rows = rows
        n = len(rows)
        nd = n_detected if n_detected is not None else n
        
        # Calcul du nombre d'entités valides (Lat et Lon séparément)
        total_entities = n * 2
        valid_entities = 0
        for row in rows:
            coords = row.get("coordonnees", {})
            v_lat = coords.get("latitude_valide", row.get("valid_lat", row.get("valid", False)))
            v_lon = coords.get("longitude_valide", row.get("valid_lon", row.get("valid", False)))
            if v_lat: valid_entities += 1
            if v_lon: valid_entities += 1

        # Bandeau
        all_valid = (valid_entities == total_entities)
        if all_valid:
            self.banner.setStyleSheet(f"""
                QFrame {{
                    background: {COLOR_SUCCESS_BG};
                    border: 1.5px solid {COLOR_SUCCESS_BD};
                    border-radius: 8px;
                }}
            """)
            self.banner_label.setText(
                f"✓  Toutes les coordonnées sont valides ({valid_entities}/{total_entities}) — vous pouvez continuer."
            )
            self.banner_label.setStyleSheet(f"color: {COLOR_SUCCESS}; background: transparent; border: none;")
        else:
            self.banner.setStyleSheet("""
                QFrame {
                    background: #FFF3CD;
                    border: 1.5px solid #FFEAA7;
                    border-radius: 8px;
                }
            """)
            self.banner_label.setText(
                f"⚠  {valid_entities}/{total_entities} coordonnées valides — vérifiez les cellules en rouge."
            )
            self.banner_label.setStyleSheet("color: #856404; background: transparent; border: none;")

        self.subtitle.setText(
            f"Type de formulaire : {type_formulaire}  ·  {nd} ligne(s) détectée(s)  ·  Taux de succès : {success_rate:.1f}%"
        )
        self.detail.setText(f"{nd} lignes extraites, {valid_entities} entités valides sur {total_entities}")

        # Remplir tableau
        self.table.setRowCount(n)
        for i, row in enumerate(rows):
            coords = row.get("coordonnees", {})
            v_lat = coords.get("latitude_valide", row.get("valid_lat", row.get("valid", False)))
            v_lon = coords.get("longitude_valide", row.get("valid_lon", row.get("valid", False)))

            def cell(text, colored=False, is_valid=True):
                item = QTableWidgetItem(str(text))
                item.setTextAlignment(Qt.AlignCenter)
                if colored:
                    color = COLOR_GREEN_CELL if is_valid else COLOR_RED_CELL
                    item.setForeground(QColor(color))
                    f = QFont("Arial", 9, QFont.Bold)
                    item.setFont(f)
                return item

            # Extraction des données selon la structure DonneePointDTO
            coords = row.get("coordonnees", {})
            specs = row.get("donnees_specifiques", {})
            
            num = row.get("numero") or row.get("numero_ligne", i + 1)
            lat = coords.get("latitude_dms", "")
            lon = coords.get("longitude_dms", "")
            h = specs.get("hauteur_mat", "")
            alt_t = specs.get("altitude_terrain", "")
            alt_tot = specs.get("altitude_totale_mat", "")

            self.table.setItem(i, 0, cell(num))
            self.table.setItem(i, 1, cell(lat, colored=True, is_valid=v_lat))
            self.table.setItem(i, 2, cell(lon, colored=True, is_valid=v_lon))
            self.table.setItem(i, 3, cell(h))
            self.table.setItem(i, 4, cell(alt_t))
            self.table.setItem(i, 5, cell(alt_tot))

        # Bouton toujours activé
        self.btn_valider.setEnabled(True)
        self.btn_valider.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_PRIMARY};
                border: none;
                border-radius: 6px;
                font-size: 10pt;
                font-weight: bold;
                color: white;
            }}
            QPushButton:hover {{
                background: {COLOR_PRIMARY_HL};
            }}
        """)

    def _on_valider(self):
        if not self.client:
            QMessageBox.critical(self, "Erreur", "Client API non configuré.")
            return

        # 1. Récupérer les données actuelles du tableau
        current_data = self.get_table_data()
        
        # 2. Préparer la requête pour /validate
        # Le backend attend un objet ValidationRequest avec une liste de PointValidationInput
        points = []
        for i, row in enumerate(current_data):
            points.append({
                "numero_ligne": i + 1,
                "numero": row["n"] if row["n"] else None,
                "coordonnees": {
                    "latitude_dms": row["lat"],
                    "longitude_dms": row["lon"]
                },
                "donnees_specifiques": {
                    "hauteur_mat": row["hauteur"],
                    "altitude_terrain": row["alt_terrain"],
                    "altitude_totale_mat": row["alt_totale"]
                }
            })
        
        payload = {"points": points}
        
        try:
            # 3. Appel backend
            res = self.client.post("/extraction/validate", json=payload)
            if not res:
                raise Exception("Le serveur n'a pas répondu.")
            
            # Le backend retourne la clé 'resultats'
            validation_results = res.get("resultats", [])
            
            if len(validation_results) != len(current_data):
                raise Exception("Erreur de correspondance entre les données et les résultats de validation.")

            # 4. Mise à jour des données locales et de l'UI
            updated_rows = []
            total_entities = len(current_data) * 2
            valid_entities = 0

            for i, row_data in enumerate(current_data):
                v_res = validation_results[i]
                # Le backend renvoie la validité dans l'objet 'coordonnees'
                coords_res = v_res.get("coordonnees", {})
                v_lat = coords_res.get("latitude_valide", False)
                v_lon = coords_res.get("longitude_valide", False)
                
                if v_lat: valid_entities += 1
                if v_lon: valid_entities += 1

                # Reconstruction d'une ligne pour load_data
                updated_rows.append({
                    "numero": row_data["n"],
                    "coordonnees": {"latitude_dms": row_data["lat"], "longitude_dms": row_data["lon"]},
                    "donnees_specifiques": {
                        "hauteur_mat": row_data["hauteur"],
                        "altitude_terrain": row_data["alt_terrain"],
                        "altitude_totale_mat": row_data["alt_totale"]
                    },
                    "valid_lat": v_lat,
                    "valid_lon": v_lon
                })

            # On rafraîchit l'affichage avec les nouvelles validités
            # On conserve le type_formulaire etc. si disponible, sinon on utilise des valeurs par défaut
            self.load_data(updated_rows, type_formulaire="eolienne")

            # 5. Décision : Passage à l'étape suivante ?
            if valid_entities == total_entities:
                self.valider.emit(updated_rows)
            else:
                QMessageBox.warning(self, "Validation incomplète", 
                                   f"Il reste des coordonnées invalides ({valid_entities}/{total_entities}).\n"
                                   "Veuillez corriger les cellules en rouge avant de continuer.")

        except Exception as e:
            QMessageBox.critical(self, "Erreur de validation", f"Impossible de valider les coordonnées : {str(e)}")

    def get_table_data(self):
        """Retourne les données actuelles du tableau (après éditions manuelles)."""
        rows = []
        for i in range(self.table.rowCount()):
            rows.append({
                "n":          self.table.item(i, 0).text() if self.table.item(i, 0) else "",
                "lat":        self.table.item(i, 1).text() if self.table.item(i, 1) else "",
                "lon":        self.table.item(i, 2).text() if self.table.item(i, 2) else "",
                "hauteur":    self.table.item(i, 3).text() if self.table.item(i, 3) else "",
                "alt_terrain":self.table.item(i, 4).text() if self.table.item(i, 4) else "",
                "alt_totale": self.table.item(i, 5).text() if self.table.item(i, 5) else "",
            })
        return rows


# ──────────────────────────────────────────────
#  Page 4 — Étude DEA
# ──────────────────────────────────────────────
class DEAPage(QWidget):
    submitted = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.kmz_data = None
        self._dea_config = {}
        self._needs_distance = {}
        self._last_dea_result = None
        self._client = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 30, 40, 20)
        root.setSpacing(0)

        title = QLabel("Étude DEA")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet(f"color: {COLOR_TEXT_MAIN};")
        root.addWidget(title)

        root.addSpacing(6)

        subtitle = QLabel("Renseignez les détails de l'étude DEA et téléchargez le fichier KMZ")
        subtitle.setFont(QFont("Arial", 9))
        subtitle.setStyleSheet(f"color: {COLOR_PRIMARY};")
        root.addWidget(subtitle)

        root.addSpacing(24)

        def field_label(text):
            lbl = QLabel(text)
            lbl.setFont(QFont("Arial", 8, QFont.Bold))
            lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; letter-spacing: 0.5px;")
            return lbl

        # KMZ Section
        root.addWidget(field_label("FICHIER KMZ (Généré)"))
        root.addSpacing(4)
        self.kmz_link = QPushButton("⬇  Télécharger le fichier KMZ")
        self.kmz_link.setFixedHeight(40)
        self.kmz_link.setStyleSheet(f"""
            QPushButton {{
                background: white;
                border: 1.5px solid {COLOR_PRIMARY};
                border-radius: 6px;
                color: {COLOR_PRIMARY};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: #F0F4FA;
            }}
        """)
        self.kmz_link.setEnabled(False)
        self.kmz_link.clicked.connect(self._download_kmz)
        root.addWidget(self.kmz_link)

        root.addSpacing(14)

        # Altitude Max Section
        root.addWidget(field_label("ALTITUDE TOTALE MAXIMALE"))
        root.addSpacing(4)
        self.alt_max_display = QLineEdit()
        self.alt_max_display.setReadOnly(True)
        self.alt_max_display.setPlaceholderText("...")
        self.alt_max_display.setStyleSheet(InformationsPage.FIELD_STYLE + "background: #E9ECEF;")
        self.alt_max_display.setFixedHeight(42)
        root.addWidget(self.alt_max_display)

        root.addSpacing(14)

        # Résultat DEA
        root.addWidget(field_label("RÉSULTAT — ALTITUDE MAXIMALE AUTORISÉE"))
        root.addSpacing(4)
        self.alt_autorisee_display = QLineEdit()
        self.alt_autorisee_display.setReadOnly(True)
        self.alt_autorisee_display.setPlaceholderText("Calculée après saisie des paramètres...")
        self.alt_autorisee_display.setStyleSheet(InformationsPage.FIELD_STYLE + "background:#E9ECEF;")
        self.alt_autorisee_display.setFixedHeight(42)
        root.addWidget(self.alt_autorisee_display)

        self.lbl_formule = QLabel("")
        self.lbl_formule.setStyleSheet(f"color:{COLOR_TEXT_MUTED}; font-size:9pt;")
        self.lbl_formule.setWordWrap(True)
        root.addWidget(self.lbl_formule)

        root.addSpacing(16)
        
        # Form DEA
        form_card = QFrame()
        form_card.setStyleSheet(f"QFrame {{ background: white; border: 1px solid {COLOR_BORDER}; border-radius: 8px; }}")
        form_lay = QVBoxLayout(form_card)
        form_lay.setContentsMargins(20, 20, 20, 20)
        form_lay.setSpacing(14)

        # Aéroport
        form_lay.addWidget(field_label("AÉROPORT *"))
        self.aeroport_combo = QComboBox()
        self.aeroport_combo.setStyleSheet(InformationsPage.FIELD_STYLE)
        self.aeroport_combo.setFixedHeight(42)
        form_lay.addWidget(self.aeroport_combo)

        # Surface de protection
        form_lay.addWidget(field_label("SURFACE DE PROTECTION *"))
        self.surface_combo = QComboBox()
        self.surface_combo.setStyleSheet(InformationsPage.FIELD_STYLE)
        self.surface_combo.setFixedHeight(42)
        self.surface_combo.currentTextChanged.connect(self._on_surface_changed)
        form_lay.addWidget(self.surface_combo)

        # Distance D
        self.lbl_distance = QLabel("DISTANCE D (mètres) *")
        self.lbl_distance.setFont(QFont("Arial", 8, QFont.Bold))
        self.lbl_distance.setStyleSheet(f"color:{COLOR_TEXT_MUTED};")
        self.distance_input = QLineEdit()
        self.distance_input.setPlaceholderText("Ex : 1500")
        self.distance_input.setStyleSheet(InformationsPage.FIELD_STYLE)
        self.distance_input.setFixedHeight(42)
        form_lay.addWidget(self.lbl_distance)
        form_lay.addWidget(self.distance_input)

        # Btn calculer
        self.btn_calculer = QPushButton("Calculer l'altitude autorisée")
        self.btn_calculer.setFixedHeight(38)
        self.btn_calculer.setStyleSheet(f"""
            QPushButton {{
                background: white;
                border: 1.5px solid {COLOR_PRIMARY};
                border-radius: 6px;
                color: {COLOR_PRIMARY};
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #F0F4FA; }}
        """)
        self.btn_calculer.clicked.connect(self._on_calculer)
        form_lay.addWidget(self.btn_calculer)

        root.addWidget(form_card)
        root.addStretch(1)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)

        self.btn_submit = QPushButton("Valider l'étude DEA  →")
        self.btn_submit.setFixedHeight(40)
        self.btn_submit.setFixedWidth(180)
        self.btn_submit.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_PRIMARY};
                border: none;
                border-radius: 6px;
                font-size: 10pt;
                font-weight: bold;
                color: white;
            }}
            QPushButton:hover {{
                background: {COLOR_PRIMARY_HL};
            }}
        """)
        self.btn_submit.clicked.connect(self._on_submit)
        self.btn_submit.setEnabled(False)
        btn_row.addWidget(self.btn_submit)
        root.addLayout(btn_row)

    def load_dea_config(self, client):
        """Charge les aéroports et surfaces depuis GET /dea/config"""
        try:
            config = client.get("/dea/config")
            if not config:
                return
            self._dea_config = config
            self._needs_distance = config.get("surface_needs_distance", {})
            
            self.aeroport_combo.clear()
            self.aeroport_combo.addItem("")
            for name in config.get("aeroports", {}).keys():
                self.aeroport_combo.addItem(name)
            
            self.surface_combo.clear()
            self.surface_combo.addItem("")
            for surface in config.get("surfaces", []):
                self.surface_combo.addItem(surface)
        except Exception as e:
            print(f"[DEAPage] Erreur chargement config DEA: {e}")

    def _on_surface_changed(self, surface: str):
        """Masque/affiche le champ distance selon la surface."""
        needs = self._needs_distance.get(surface, True)
        self.lbl_distance.setVisible(needs)
        self.distance_input.setVisible(needs)
        self.alt_autorisee_display.clear()
        self.lbl_formule.setText("")
        self.btn_submit.setEnabled(False)

    def _on_calculer(self):
        """Appelle POST /dea/calculer et affiche le résultat."""
        aeroport = self.aeroport_combo.currentText().strip()
        surface  = self.surface_combo.currentText().strip()
        
        if not aeroport or not surface:
            QMessageBox.warning(self, "Champs manquants", 
                "Veuillez sélectionner un aéroport et une surface.")
            return
        
        distance = None
        if self.distance_input.isVisible():
            txt = self.distance_input.text().strip()
            if not txt:
                QMessageBox.warning(self, "Distance manquante",
                    "La distance D est requise pour cette surface.")
                return
            try:
                distance = float(txt)
            except ValueError:
                QMessageBox.warning(self, "Format invalide",
                    "La distance doit être un nombre (ex: 1500).")
                return
        
        payload = {
            "aeroport": aeroport,
            "surface":  surface,
            "distance_m": distance
        }
        
        try:
            result = self._client.post("/dea/calculer", json=payload)
            if not result or result.get("erreur"):
                err = result.get("erreur") if result else "Erreur serveur"
                QMessageBox.warning(self, "Erreur DEA", err)
                return
            
            alt = result.get("alt_autorisee")
            formule = result.get("formule_appliquee", "")
            
            self.alt_autorisee_display.setText(f"{alt} m")
            self.lbl_formule.setText(f"Formule : {formule}")
            self.btn_submit.setEnabled(True)
            self._last_dea_result = result
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def set_data(self, data: dict, client=None):
        self.kmz_data = data
        if client:
            self._client = client
        self.alt_max_display.setText(
            f"{data.get('altitude_finale_max', 'N/A')} m"
        )
        if data.get("kmz_path"):
            self.kmz_link.setEnabled(True)
        self.alt_autorisee_display.clear()
        self.lbl_formule.setText("")
        self.btn_submit.setEnabled(False)

    def _download_kmz(self):
        """Gere le telechargement du fichier KMZ via l'API."""
        if not self.kmz_data:
            return
            
        try:
            dossier_id = self.kmz_data.get("dossier_id")
            if not dossier_id:
                QMessageBox.critical(self, "Erreur", "ID de dossier manquant pour le téléchargement.")
                return

            content = self._client.get_binary(f"/documents/generate/kmz/{dossier_id}") if self._client else None
            
            if content:
                filename = self.kmz_data.get("kmz_filename", f"localisation_{dossier_id}.kmz")
                save_path, _ = QFileDialog.getSaveFileName(
                    self, "Enregistrer le fichier KMZ", filename, "KMZ files (*.kmz)"
                )
                if save_path:
                    with open(save_path, "wb") as f:
                        f.write(content)
                    QMessageBox.showinfo("Succès", f"Fichier KMZ enregistré sous : {save_path}")
            else:
                QMessageBox.showerror("Erreur", "Échec du téléchargement du fichier KMZ.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue : {str(e)}")

    def _on_submit(self):
        if not hasattr(self, '_last_dea_result') or not self._last_dea_result:
            QMessageBox.warning(self, "Calcul requis",
                "Veuillez d'abord calculer l'altitude autorisée.")
            return
        
        self.submitted.emit({
            "aeroport":      self.aeroport_combo.currentText(),
            "surface":       self.surface_combo.currentText(),
            "distance_m":    self.distance_input.text() if self.distance_input.isVisible() else None,
            "alt_demandee":  self.alt_max_display.text(),
            "alt_autorisee": self.alt_autorisee_display.text(),
            "formule":       self.lbl_formule.text(),
        })
# No changes here, just making sure I don't replace the whole class unless intended. 
# Since I'm rewriting the DEAPage class, I will replace the entire block from "class DEAPage(QWidget):" to the end of its methods.

# ──────────────────────────────────────────────
#  Vue principale : DossierView
# ──────────────────────────────────────────────
class DossierView(QWidget):
    """
    Widget principal orchestrant toutes les pages du workflow dossier.
    Signaux exposés :
      - dossier_created(dict)  : après soumission du formulaire
      - coordonnees_validees(list) : après validation des coordonnées
    """
    dossier_created      = Signal(dict)
    coordonnees_validees = Signal(list)

    # Pages dans le QStackedWidget
    PAGE_INFOS     = 0
    PAGE_LOADING   = 1
    PAGE_RESULTS   = 2
    PAGE_DEA       = 3

    def __init__(self, token: str = None, parent=None):
        super().__init__(parent)
        self.token = token
        self.client = HTTPClient(token=self.token)
        self.current_dossier_id = None
        self.setWindowTitle("Système de gestion de demandes d'avis OACA — Créer un nouveau dossier")
        self.setMinimumSize(900, 620)
        self.setStyleSheet(f"background: {COLOR_BG};")
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Bande blanche du haut avec Stepper ──
        header = QFrame()
        header.setFixedHeight(88)
        header.setStyleSheet("""
            QFrame {
                background: white;
                border-bottom: 1px solid #E0E6EF;
            }
        """)
        header_lay = QVBoxLayout(header)
        header_lay.setContentsMargins(20, 4, 20, 4)

        self.stepper = StepperWidget()
        header_lay.addWidget(self.stepper)
        root.addWidget(header)

        # ── Stack des pages ──
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background: {COLOR_BG};")

        self.page_infos   = InformationsPage()
        self.page_loading = ExtractionLoadingPage()
        self.page_results = ExtractionResultPage()
        self.page_results.set_client(self.client)
        self.page_dea      = DEAPage()
        self.page_dea.load_dea_config(self.client)

        self.stack.addWidget(self.page_infos)    # 0
        self.stack.addWidget(self.page_loading)  # 1
        self.stack.addWidget(self.page_results)  # 2
        self.stack.addWidget(self.page_dea)       # 3

        root.addWidget(self.stack)

        # Connexions internes
        self.page_infos.submitted.connect(self._on_form_submitted)
        self.page_infos.cancelled.connect(self._on_cancel)
        self.page_results.relancer.connect(self._on_relancer)
        self.page_results.valider.connect(self._on_valider)
        self.page_dea.submitted.connect(self._on_dea_submitted)

        # État initial
        self.stepper.set_current(0)
        self.stack.setCurrentIndex(self.PAGE_INFOS)

    # ── Transitions ─────────────────────────────

    def _on_form_submitted(self, data: dict):
        """Lance l'extraction autonome via le Worker."""
        self.stepper.mark_done(0)
        self.stepper.set_current(1)
        self.stack.setCurrentIndex(self.PAGE_LOADING)
        self.page_loading.start()

        # Lancement du worker d'extraction
        self.extraction_worker = ExtractionWorker(self.client, data)
        self.extraction_worker.finished.connect(self._on_extraction_finished)
        self.extraction_worker.error.connect(self._on_extraction_error)
        self.extraction_worker.start()

    def _on_cancel(self):
        """Réinitialise le formulaire."""
        self.page_infos.reset()

    def _on_relancer(self):
        """Relance l'extraction pour le dossier actuel."""
        self.stack.setCurrentIndex(self.PAGE_LOADING)
        self.page_loading.start()

        # On récupère les données du formulaire (si possible) ou on utilise les infos stockées
        # Pour simplifier, on assume que self.page_infos a les données
        data = {
            "nom": self.page_infos.nom_input.text(),
            "identifiant": self.page_infos.id_input.text(),
            "type": self.page_infos.type_combo.currentText(),
            "region": self.page_infos.region_combo.currentText(),
            "formulaire": self.page_infos.drop_zone.get_filepath(),
        }

        self.extraction_worker = ExtractionWorker(self.client, data, dossier_id=self.current_dossier_id)
        self.extraction_worker.finished.connect(self._on_extraction_finished)
        self.extraction_worker.error.connect(self._on_extraction_error)
        self.extraction_worker.start()

    def _on_valider(self, rows: list):
        """
        Valide les coordonnées, confirme l'extraction pour générer le KMZ,
        et passe à l'étape Étude DEA.
        """
        if not self.current_dossier_id:
            QMessageBox.critical(self, "Erreur", "ID de dossier manquant pour la confirmation.")
            return

        try:
            # 1. Appeler /extraction/confirm pour générer le KMZ et obtenir l'altitude max
            # On envoie les coordonnées validées pour confirmation finale
            payload = {"formulaire_id": self.current_dossier_id, "points": rows}
            res = self.client.post("/extraction/confirm", json=payload)

            if not res:
                raise Exception("Le serveur n'a pas répondu à la confirmation.")

            # On attend un objet contenant kmz_path, kmz_filename et altitude_finale_max
            self.page_dea.set_data(res, client=self.client)

            # 2. Mise à jour UI
            self.stepper.mark_done(2)
            self.stepper.set_current(3)
            self.stack.setCurrentIndex(self.PAGE_DEA)
            
            self.coordonnees_validees.emit(rows)
            QMessageBox.information(self, "Succès", "Coordonnées confirmées. Le fichier KMZ a été généré.")

        except Exception as e:
            QMessageBox.critical(self, "Erreur de confirmation", f"Impossible de confirmer les coordonnées : {str(e)}")

    def _on_dea_submitted(self, data: dict):
        """Gère la soumission du formulaire DEA."""
        QMessageBox.information(self, "Étude DEA", "Les données de l'étude DEA ont été enregistrées avec succès.")
        # Transition vers la page finale Avis PDF (PAGE 4) si elle existait
        self.stepper.mark_done(3)
        self.stepper.set_current(4)

    # ── API publique ─────────────────────────────

    def _on_extraction_finished(self, result: dict):
        """Gère la réponse réussie du Worker."""
        # Mettre à jour l'ID du dossier pour les relances
        if "id" in result:
            self.current_dossier_id = result["id"]
        elif self.current_dossier_id is None:
            # On essaie de trouver l'id dans le résultat d'extraction si le backend le renvoie
            self.current_dossier_id = result.get("dossier_id")

        # ExtractionKResult contient 'donnees', 'statistiques', etc.
        rows = result.get("donnees", [])
        stats = result.get("statistiques", {})
        
        self.show_extraction_results(
            rows,
            type_formulaire=result.get("type_formulaire", "Inconnu"),
            n_detected=stats.get("total_lignes", len(rows)),
            success_rate=result.get("taux_succes", 100.0),
            n_valid=stats.get("coordonnees_valides", len(rows))
        )

    def show_extraction_results(self, rows: list, **kwargs):
        """
        Affiche les résultats de l'extraction.
        """
        self.stepper.mark_done(1)
        self.stepper.set_current(2)
        self.page_results.load_data(rows, **kwargs)
        self.stack.setCurrentIndex(self.PAGE_RESULTS)

    def _on_extraction_error(self, message: str):
        """Gère l'erreur du Worker."""
        self.show_extraction_error(message)

    def show_extraction_error(self, message: str):
        """Affiche l'erreur via un QMessageBox et revient à la saisie."""
        QMessageBox.critical(self, "Erreur d'extraction", message)
        self.stack.setCurrentIndex(self.PAGE_INFOS)
        self.stepper.set_current(0)

    def go_to_step(self, step: int):
        """Navigue manuellement vers une étape (0-based)."""
        self.stepper.set_current(step)

    def update_progress(self, value: int, maximum: int = 100):
        """Met à jour la barre de progression (si mode déterminé)."""
        self.page_loading.set_progress(value, maximum)


# ──────────────────────────────────────────────
#  Démo standalone
# ──────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    view = DossierView()

    # Simuler la réponse backend après 2 secondes
    DEMO_ROWS = [
        {"n": 1, "lat": '36°52\'53.30"N', "lon": '9°6\'6.96"E',   "hauteur": "120.0", "alt_terrain": "400.0", "alt_totale": "520.0", "valid": True},
        {"n": 2, "lat": '36°51\'45.99"N', "lon": '9°45\'9.83"E',  "hauteur": "120.0", "alt_terrain": "552.0", "alt_totale": "672.0", "valid": True},
        {"n": 3, "lat": '36°50\'36.05"N', "lon": '9°3\'49.14"E',  "hauteur": "120.0", "alt_terrain": "542.0", "alt_totale": "662.0", "valid": True},
        {"n": 4, "lat": '36°49\'46.82"N', "lon": '9°1\'51.44"E',  "hauteur": "120.0", "alt_terrain": "594.0", "alt_totale": "714.0", "valid": True},
    ]

    def on_dossier_created(data):
        print("Dossier créé :", data)
        QTimer.singleShot(2000, lambda: view.show_extraction_results(
            DEMO_ROWS,
            type_formulaire="eolienne",
            n_detected=4,
            success_rate=100.0,
            n_valid=4,
        ))

    view.dossier_created.connect(on_dossier_created)
    view.coordonnees_validees.connect(lambda rows: print("Coordonnées validées :", rows))

    view.show()
    sys.exit(app.exec())