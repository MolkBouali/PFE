"""
dossier_view.py — Vue de création/traitement d'un dossier OACA
Étapes : 1-Informations → 2-Extraction → 3-Validation → 4-Étude DEA → 5-Avis PDF
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QProgressBar, QSizePolicy, QScrollArea,
    QStackedWidget, QApplication, QMessageBox, QCheckBox
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
COLOR_WARN_BG    = "#fef9c3"   # fond jaune
COLOR_WARN_BD    = "#fde68a"   # bordure jaune
COLOR_WARN_FG    = "#92400e"   # texte orange foncé
COLOR_DANGER     = "#991b1b"   # rouge foncé
COLOR_DANGER_BG  = "#fee2e2"   # fond rouge clair
COLOR_DANGER_BD  = "#fecaca"   # bordure rouge
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
            # 1. Extraction des coordonnées
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
    STEPS = ["Informations", "Extraction", "Validation", "Analyse", "Avis"]

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

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows = []
        self.client = None
        self._dossier_id = None
        self._token = None
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
        self.banner_label = QLabel("Analyse des coordonnées en cours...")
        self.banner_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.banner_label.setStyleSheet(f"color: {COLOR_SUCCESS}; background: transparent; border: none;")
        banner_lay.addWidget(self.banner_label)
        root.addWidget(self.banner)

        # Sous-titre
        self.subtitle = QLabel("Chargement des informations...")
        self.subtitle.setFont(QFont("Arial", 8))
        self.subtitle.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")
        root.addWidget(self.subtitle)

        self.detail = QLabel("Veuillez patienter...")
        self.detail.setFont(QFont("Arial", 8))
        self.detail.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")
        root.addWidget(self.detail)

        # Tableau
        self.table = QTableWidget()
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

        self.btn_complement = QPushButton("📄  Générer complément")
        self.btn_complement.setFixedHeight(40)
        self.btn_complement.setFixedWidth(200)
        self.btn_complement.setStyleSheet(f"""
            QPushButton {{
                background: white;
                border: 1.5px solid {COLOR_BORDER};
                border-radius: 6px;
                font-size: 9pt;
                color: {COLOR_TEXT_MUTED};
            }}
            QPushButton:hover {{ background: #F0F0F0; }}
        """)
        self.btn_complement.setVisible(False)
        self.btn_complement.clicked.connect(self._on_generate_complement)
        btn_row.addWidget(self.btn_complement)

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

    def load_data(self, rows: list, headers: list = None, type_formulaire: str = "eolienne",
                   n_detected: int = None, success_rate: float = 100.0,
                   n_valid: int = None, dossier_id: int = None, token: str = None):
        """
        rows: liste de DonneePointDTO (dicts avec coordonnées et donnees_specifiques)
        headers: liste des entêtes de colonnes
        """
        if dossier_id is not None:
            self._dossier_id = dossier_id
        if token is not None:
            self._token = token
        if headers is None:
            # Fallback to default if no headers provided
            headers = ["N°", "Latitude DMS", "Longitude DMS",
                      "Hauteur_mat", "Altitude_terrain", "Altitude_totale_mat"]

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

        # Détection format non-DMS
        nb_invalides = total_entities - valid_entities
        total_lignes = n
        lignes_valides = sum(
            1 for row in rows
            if row.get("coordonnees", {}).get("latitude_valide", False)
            and row.get("coordonnees", {}).get("longitude_valide", False)
        )
        statut = "succes" if lignes_valides == total_lignes and total_lignes > 0 else "echec"

        any_non_dms = any(
            row.get("coordonnees", {}).get("format_detecte", "DMS") not in ("DMS", None, "")
            for row in rows
            if row.get("coordonnees", {}).get("format_detecte") is not None
        )

        # Bandeau — logique priorisée
        if nb_invalides == 0 and total_lignes > 0 and not any_non_dms:
            banner_bg = COLOR_SUCCESS_BG
            banner_bd = COLOR_SUCCESS_BD
            banner_fg = COLOR_SUCCESS
            banner_tx = f"✓  Toutes les coordonnées sont valides et au format DMS ({lignes_valides}/{total_lignes}) — vous pouvez continuer."
        elif any_non_dms:
            banner_bg = COLOR_WARN_BG
            banner_bd = COLOR_WARN_BD
            banner_fg = COLOR_WARN_FG
            banner_tx = "⚠  Le format détecté n'est pas DMS. Veuillez générer un complément ou corriger les données."
        elif 0 < nb_invalides < (total_lignes * 2):
            banner_bg = COLOR_WARN_BG
            banner_bd = COLOR_WARN_BD
            banner_fg = COLOR_WARN_FG
            banner_tx = "⚠  Certaines coordonnées sont invalides — veuillez les corriger avant de confirmer."
        elif nb_invalides >= (total_lignes * 2) or total_lignes == 0 or statut == "echec":
            banner_bg = COLOR_DANGER_BG
            banner_bd = COLOR_DANGER_BD
            banner_fg = COLOR_DANGER
            banner_tx = "✗  Aucune coordonnée valide extraite — vérifiez la qualité du scan ou le format du document."
        else:
            banner_bg = COLOR_DANGER_BG
            banner_bd = COLOR_DANGER_BD
            banner_fg = COLOR_DANGER
            banner_tx = "✗  Erreur lors de la validation des coordonnées."

        self.banner.setStyleSheet(f"""
            QFrame {{
                background: {banner_bg};
                border: 1.5px solid {banner_bd};
                border-radius: 8px;
            }}
        """)
        self.banner_label.setText(banner_tx)
        self.banner_label.setStyleSheet(f"color: {banner_fg}; background: transparent; border: none;")

        self.subtitle.setText(
            f"Type de formulaire : {type_formulaire}  ·  {nd} ligne(s) détectée(s)  ·  Taux de succès : {success_rate:.1f}%"
        )
        self.detail.setText(f"{nd} lignes extraites, {valid_entities} entités valides sur {total_entities}")

        # Configurer tableau
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
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

            specs = row.get("donnees_specifiques", {})
            
            # Remplissage dynamique basé sur les headers
            # Mappage des headers d'affichage vers les clés techniques du backend
            header_to_key = {
                "Hauteur_mat": "hauteur_mat",
                "Altitude_terrain": "altitude_terrain",
                "Altitude_totale_mat": "altitude_totale_mat"
            }

            for col_idx, header in enumerate(headers):
                if header == "N°":
                    val = row.get("numero") or row.get("numero_ligne", i + 1)
                    self.table.setItem(i, col_idx, cell(val))
                elif header == "Latitude DMS":
                    val = coords.get("latitude_dms", "")
                    self.table.setItem(i, col_idx, cell(val, colored=True, is_valid=v_lat))
                elif header == "Longitude DMS":
                    val = coords.get("longitude_dms", "")
                    self.table.setItem(i, col_idx, cell(val, colored=True, is_valid=v_lon))
                else:
                    # Utilisation du mappage si disponible, sinon recherche par nom exact du header
                    key = header_to_key.get(header, header)
                    val = specs.get(key, "")
                    self.table.setItem(i, col_idx, cell(val))

        # Bouton complément visible si format non-DMS
        self.btn_complement.setVisible(any_non_dms)

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

    def _on_generate_complement(self):
        import requests
        from PySide6.QtWidgets import QApplication
        if not self._dossier_id:
            QMessageBox.warning(self, "Erreur", "Identifiant de dossier manquant.")
            return
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            token = self._token or (self.client.token if self.client else None)
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            resp = requests.post(
                f"http://localhost:8000/extraction/generate-complement/{self._dossier_id}",
                headers=headers,
                timeout=30,
            )
            if resp.status_code == 200:
                filename = f"Complement_Dossier_{self._dossier_id}.docx"
                path, _ = QFileDialog.getSaveFileName(
                    self, "Sauvegarder le document", filename, "Document Word (*.docx)"
                )
                if path:
                    with open(path, "wb") as f:
                        f.write(resp.content)
                    QMessageBox.information(self, "Succès", "Document généré avec succès.")
                    
                    # Reset workflow to prevent duplicate dossier creation
                    # Traverse up to find the main DossierView controller
                    view = self.parent()
                    while view and not hasattr(view, 'current_dossier_id'):
                        view = view.parent()
                    
                    if view:
                        view.current_dossier_id = None
                        view.current_formulaire_id = None
                        view.page_infos.reset()
                        view.stepper.set_current(0)
                        view.stack.setCurrentIndex(view.PAGE_INFOS)
            else:
                QMessageBox.critical(self, "Erreur",
                    f"Le serveur n'a pas pu générer le document ({resp.status_code}).\n{resp.text}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur réseau", f"Impossible de générer le document : {str(e)}")
        finally:
            QApplication.restoreOverrideCursor()

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
                    "numero_ligne": i + 1,
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
            # On peut passer les headers actuels pour conserver la structure du tableau
            current_headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
            self.load_data(updated_rows, headers=current_headers, type_formulaire="eolienne")

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
#  Page 4 — Étude DEA (Saisie)
# ──────────────────────────────────────────────
class DEAPage(QWidget):
    submitted = Signal(dict)
    back_requested = Signal()

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

        # Remove btn_calculer and keep only submit button (renamed)
        root.addWidget(form_card)
        root.addStretch(1)

        # Buttons
        btn_row = QHBoxLayout()
        
        self.btn_back = QPushButton("← Retour")
        self.btn_back.setFixedHeight(40)
        self.btn_back.setFixedWidth(120)
        self.btn_back.setStyleSheet(f"""
            QPushButton {{
                background: white;
                border: 1.5px solid {COLOR_BORDER};
                border-radius: 6px;
                color: {COLOR_TEXT_MAIN};
            }}
            QPushButton:hover {{ background: #F0F0F0; }}
        """)
        self.btn_back.clicked.connect(self.back_requested.emit)
        btn_row.addWidget(self.btn_back)
        
        btn_row.addStretch(1)

        self.btn_submit = QPushButton("Lancer l'analyse →")
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
        self.btn_submit.setEnabled(True)
        btn_row.addWidget(self.btn_submit)
        root.addLayout(btn_row)

    def load_dea_config(self, client):
        """Charge les aéroports et surfaces."""
        # Liste des aéroports officiels
        aeroports = [
            "Aéroport International de Tunis-Carthage",
            "Aéroport International d'Enfidha-Hammamet",
            "Aéroport International de Monastir Habib-Bourguiba",
            "Aéroport International de Djerba-Zarzis",
            "Aéroport International de Sfax-Thyna",
            "Aéroport International de Tozeur-Nefta",
            "Aéroport International de Gafsa-Ksar",
            "Aéroport International de Tabarka-Aïn Draham",
            "Aéroport International de Gabès-Matmata",
            "Aéroport Borj El Amri"
        ]
        # Liste des 5 surfaces
        surfaces = ["Horizontale Intérieure", "Conique", "Approche — 1ère section", "Approche — 2ème section", "Approche — 3ème section","Transition","Montée au Décollage"]
        
        self.aeroport_combo.clear()
        self.aeroport_combo.addItem("Sélectionnez un aéroport...")
        self.aeroport_combo.addItems(aeroports)
        
        self.surface_combo.clear()
        self.surface_combo.addItem("Sélectionnez une surface...")
        self.surface_combo.addItems(surfaces)
        
        # Config pour la visibilité de la distance
        self._needs_distance = {s: True for s in surfaces}
        self._needs_distance["Horizontale Intérieure"] = False

    def _on_surface_changed(self, surface: str):
        """Masque/affiche le champ distance selon la surface."""
        needs = self._needs_distance.get(surface, True)
        self.lbl_distance.setVisible(needs)
        self.distance_input.setVisible(needs)
        


    def set_data(self, data: dict, client=None):
        self.kmz_data = data
        self.dossier_id = data.get("dossier_id")
        if client:
            self._client = client
        self.alt_max_display.setText(
            f"{data.get('altitude_finale_max', 'N/A')} m"
        )
        if data.get("kmz_path"):
            self.kmz_link.setEnabled(True)
        self.btn_submit.setEnabled(True)
        self.btn_submit.setText("Lancer l'analyse →")

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
                    QMessageBox.information(self, "Succès", f"Fichier KMZ enregistré sous : {save_path}")
            else:
                QMessageBox.critical(self, "Erreur", "Échec du téléchargement du fichier KMZ.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue : {str(e)}")

    def _on_submit(self):
        """Effectue le calcul puis transitionne vers la page de résultat."""
        print(">>> _on_submit appelé")
        print(f">>> client: {self._client}")
        
        # 1. Exécuter la logique de calcul
        aeroport = self.aeroport_combo.currentText().strip()
        surface  = self.surface_combo.currentText().strip()
        print(f">>> aeroport: {aeroport}")
        print(f">>> surface: {surface}")
        
        if not aeroport or aeroport == "Sélectionnez un aéroport..." or \
           not surface or surface == "Sélectionnez une surface...":
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
            
            self._last_dea_result = result
            # 2. Transition immédiate vers la page de résultat
            self.submitted.emit(self._last_dea_result)
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

# ──────────────────────────────────────────────
#  Page 5 — Interface de l'Avis
# ──────────────────────────────────────────────
class AvisPage(QWidget):
    back_requested = Signal()
    final_submitted = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_result = {}
        self._alt_finale_max = 0.0
        self._dossier_id = None
        self._client = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 30, 40, 20)
        root.setSpacing(0)

        title = QLabel("Avis OACA")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet(f"color: {COLOR_TEXT_MAIN};")
        root.addWidget(title)

        root.addSpacing(6)
        subtitle = QLabel("Résultat de l'étude DEA et génération de l'avis officiel.")
        subtitle.setFont(QFont("Arial", 9))
        subtitle.setStyleSheet(f"color: {COLOR_PRIMARY};")
        root.addWidget(subtitle)

        root.addSpacing(20)

        # ── Carte résultats (altitude autorisée + écart + badge) ──
        res_card = QFrame()
        res_card.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 2px solid {COLOR_PRIMARY};
                border-radius: 12px;
            }}
        """)
        res_lay = QHBoxLayout(res_card)
        res_lay.setContentsMargins(30, 20, 30, 20)
        res_lay.setSpacing(0)

        # Altitude autorisée
        alt_col = QVBoxLayout()
        alt_col.setAlignment(Qt.AlignCenter)
        lbl_alt_title = QLabel("ALTITUDE AUTORISÉE")
        lbl_alt_title.setAlignment(Qt.AlignCenter)
        lbl_alt_title.setFont(QFont("Arial", 8, QFont.Bold))
        lbl_alt_title.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; border: none; background: transparent;")
        self.alt_val = QLabel("--- m")
        self.alt_val.setAlignment(Qt.AlignCenter)
        self.alt_val.setFont(QFont("Arial", 22, QFont.Bold))
        self.alt_val.setStyleSheet(f"color: {COLOR_PRIMARY}; border: none; background: transparent;")
        self.lbl_formule = QLabel("")
        self.lbl_formule.setAlignment(Qt.AlignCenter)
        self.lbl_formule.setFont(QFont("Arial", 8, italic=True))
        self.lbl_formule.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; border: none; background: transparent;")
        alt_col.addWidget(lbl_alt_title)
        alt_col.addSpacing(6)
        alt_col.addWidget(self.alt_val)
        alt_col.addWidget(self.lbl_formule)
        res_lay.addLayout(alt_col)

        # Séparateur
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet(f"color: {COLOR_BORDER};")
        res_lay.addSpacing(20)
        res_lay.addWidget(sep)
        res_lay.addSpacing(20)

        # Écart
        ecart_col = QVBoxLayout()
        ecart_col.setAlignment(Qt.AlignCenter)
        lbl_ecart_title = QLabel("ÉCART")
        lbl_ecart_title.setAlignment(Qt.AlignCenter)
        lbl_ecart_title.setFont(QFont("Arial", 8, QFont.Bold))
        lbl_ecart_title.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; border: none; background: transparent;")
        self.lbl_ecart = QLabel("--- m")
        self.lbl_ecart.setAlignment(Qt.AlignCenter)
        self.lbl_ecart.setFont(QFont("Arial", 22, QFont.Bold))
        self.lbl_ecart.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; border: none; background: transparent;")
        ecart_col.addWidget(lbl_ecart_title)
        ecart_col.addSpacing(6)
        ecart_col.addWidget(self.lbl_ecart)
        res_lay.addLayout(ecart_col)

        # Séparateur
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.VLine)
        sep2.setStyleSheet(f"color: {COLOR_BORDER};")
        res_lay.addSpacing(20)
        res_lay.addWidget(sep2)
        res_lay.addSpacing(20)

        # Badge avis
        badge_col = QVBoxLayout()
        badge_col.setAlignment(Qt.AlignCenter)
        lbl_badge_title = QLabel("AVIS")
        lbl_badge_title.setAlignment(Qt.AlignCenter)
        lbl_badge_title.setFont(QFont("Arial", 8, QFont.Bold))
        lbl_badge_title.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; border: none; background: transparent;")
        self.lbl_badge = QLabel("---")
        self.lbl_badge.setAlignment(Qt.AlignCenter)
        self.lbl_badge.setFont(QFont("Arial", 14, QFont.Bold))
        self.lbl_badge.setFixedWidth(160)
        self.lbl_badge.setFixedHeight(40)
        self.lbl_badge.setStyleSheet("border-radius: 8px; border: none; background: #E0E0E0; color: #666;")
        badge_col.addWidget(lbl_badge_title)
        badge_col.addSpacing(6)
        badge_col.addWidget(self.lbl_badge, alignment=Qt.AlignCenter)
        res_lay.addLayout(badge_col)

        root.addWidget(res_card)
        root.addSpacing(20)

        # ── Section favorable : cases à cocher ──
        self.section_favorable = QFrame()
        self.section_favorable.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
            }}
        """)
        fav_lay = QVBoxLayout(self.section_favorable)
        fav_lay.setContentsMargins(24, 16, 24, 16)
        fav_lay.setSpacing(10)

        lbl_dir = QLabel("Validation par les directions")
        lbl_dir.setFont(QFont("Arial", 10, QFont.Bold))
        lbl_dir.setStyleSheet(f"color: {COLOR_TEXT_MAIN}; border: none; background: transparent;")
        fav_lay.addWidget(lbl_dir)

        lbl_dir_sub = QLabel("Cochez les directions qui valident le dossier.")
        lbl_dir_sub.setFont(QFont("Arial", 8))
        lbl_dir_sub.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; border: none; background: transparent;")
        fav_lay.addWidget(lbl_dir_sub)

        chk_row = QHBoxLayout()
        chk_style = f"color: {COLOR_TEXT_MAIN}; font-size: 10pt; border: none; background: transparent;"
        self.chk_dna  = QCheckBox("DNA")
        self.chk_dana = QCheckBox("DANA")
        self.chk_der  = QCheckBox("DER")
        self.chk_dta  = QCheckBox("DTA")
        for chk in [self.chk_dna, self.chk_dana, self.chk_der, self.chk_dta]:
            chk.setStyleSheet(chk_style)
            chk_row.addWidget(chk)
        chk_row.addStretch(1)
        fav_lay.addLayout(chk_row)

        self.btn_confirmer = QPushButton("Confirmer les validations")
        self.btn_confirmer.setFixedHeight(38)
        self.btn_confirmer.setFixedWidth(220)
        self.btn_confirmer.setStyleSheet(f"""
            QPushButton {{
                background: white;
                border: 1.5px solid {COLOR_PRIMARY};
                border-radius: 6px;
                color: {COLOR_PRIMARY};
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #F0F4FA; }}
        """)
        self.btn_confirmer.clicked.connect(self._on_confirmer)
        fav_lay.addWidget(self.btn_confirmer, alignment=Qt.AlignLeft)

        self.section_favorable.setVisible(False)
        root.addWidget(self.section_favorable)

        root.addStretch(1)

        # ── Boutons bas ──
        btn_row = QHBoxLayout()
        self.btn_back = QPushButton("← Retour")
        self.btn_back.setFixedHeight(40)
        self.btn_back.setFixedWidth(120)
        self.btn_back.setStyleSheet(f"""
            QPushButton {{
                background: white;
                border: 1.5px solid {COLOR_BORDER};
                border-radius: 6px;
                color: {COLOR_TEXT_MAIN};
            }}
            QPushButton:hover {{ background: #F0F0F0; }}
        """)
        self.btn_back.clicked.connect(self.back_requested.emit)
        btn_row.addWidget(self.btn_back)
        btn_row.addStretch(1)

        self.btn_generer = QPushButton("📄  Générer l'avis officiel")
        self.btn_generer.setFixedHeight(40)
        self.btn_generer.setFixedWidth(220)
        self.btn_generer.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_PRIMARY};
                border: none;
                border-radius: 6px;
                color: white;
                font-weight: bold;
                font-size: 10pt;
            }}
            QPushButton:hover {{ background: {COLOR_PRIMARY_HL}; }}
        """)
        self.btn_generer.setVisible(False)
        self.btn_generer.clicked.connect(self._on_generer_avis)
        btn_row.addWidget(self.btn_generer)

        root.addLayout(btn_row)

    def set_result(self, result: dict, alt_finale_max: float = 0.0,
                   dossier_id: int = None, client=None):
        self._current_result = result
        self._alt_finale_max = alt_finale_max
        self._dossier_id = dossier_id
        self._client = client

        alt_autorisee = result.get("alt_autorisee", 0.0)
        formule = result.get("formule_appliquee", "")

        self.alt_val.setText(f"{alt_autorisee} m")
        self.lbl_formule.setText(f"Formule : {formule}" if formule else "")

        # Calcul écart
        try:
            ecart = float(alt_autorisee) - float(alt_finale_max)
        except (TypeError, ValueError):
            ecart = None

        if ecart is not None:
            signe = "+" if ecart >= 0 else ""
            self.lbl_ecart.setText(f"{signe}{ecart:.2f} m")
            favorable = ecart >= 0
        else:
            self.lbl_ecart.setText("N/A")
            favorable = False

        # Badge
        if favorable:
            self.lbl_badge.setText("✓  FAVORABLE")
            self.lbl_badge.setStyleSheet(f"border-radius: 8px; border: none; background: {COLOR_SUCCESS_BG}; color: {COLOR_SUCCESS}; font-weight: bold;")
            self.section_favorable.setVisible(True)
            self.btn_generer.setVisible(False)
            # Reset cases
            for chk in [self.chk_dna, self.chk_dana, self.chk_der, self.chk_dta]:
                chk.setChecked(False)
        else:
            self.lbl_badge.setText("✗  DÉFAVORABLE")
            self.lbl_badge.setStyleSheet(f"border-radius: 8px; border: none; background: {COLOR_DANGER_BG}; color: {COLOR_DANGER}; font-weight: bold;")
            self.section_favorable.setVisible(False)
            self.btn_generer.setVisible(True)

        self.lbl_ecart.setStyleSheet(
            f"color: {COLOR_SUCCESS}; border: none; background: transparent;" if favorable
            else f"color: {COLOR_DANGER}; border: none; background: transparent;"
        )

    def _on_confirmer(self):
        """Affiche le bouton Générer après confirmation des cases."""
        self.btn_generer.setVisible(True)

    def _on_generer_avis(self):
        """Appelle POST /documents/generate/pdf/{dossier_id} et ouvre le PDF."""
        if not self._dossier_id or not self._client:
            QMessageBox.warning(self, "Erreur", "Informations manquantes.")
            return

        toutes_cochees = all([
            self.chk_dna.isChecked(),
            self.chk_dana.isChecked(),
            self.chk_der.isChecked(),
            self.chk_dta.isChecked(),
        ])

        try:
            from PySide6.QtWidgets import QApplication
            QApplication.setOverrideCursor(Qt.WaitCursor)

            payload = {
                "validation_dna":  self.chk_dna.isChecked(),
                "validation_dana": self.chk_dana.isChecked(),
                "validation_der":  self.chk_der.isChecked(),
                "validation_dta":  self.chk_dta.isChecked(),
                "avis_type": "favorable" if toutes_cochees else "defavorable",
            }
            content = self._client.post_binary(
                f"/documents/generate/pdf/{self._dossier_id}",
                json=payload
            )
            if content:
                import tempfile, os
                from PySide6.QtGui import QDesktopServices
                from PySide6.QtCore import QUrl
                tmp = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".pdf",
                    prefix=f"avis_oaca_{self._dossier_id}_"
                )
                tmp.write(content)
                tmp.close()
                QDesktopServices.openUrl(QUrl.fromLocalFile(tmp.name))
                self.final_submitted.emit(self._current_result)
            else:
                QMessageBox.critical(self, "Erreur", "Le serveur n'a pas retourné de PDF.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de générer l'avis : {str(e)}")
        finally:
            QApplication.restoreOverrideCursor()

    def _on_final(self):
        if hasattr(self, '_current_result'):
            self.final_submitted.emit(self._current_result)

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
    PAGE_AVIS      = 4

    def __init__(self, token: str = None, parent=None):
        super().__init__(parent)
        self.token = token
        self.client = HTTPClient(token=self.token)
        self.current_dossier_id  = None
        self.current_formulaire_id = None
        self.setWindowTitle("Système de gestion de demandes d'avis OACA — Traiter un nouveau dossier")
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
        self.page_avis = AvisPage()

        self.stack.addWidget(self.page_infos)    # 0
        self.stack.addWidget(self.page_loading)  # 1
        self.stack.addWidget(self.page_results) # 2
        self.stack.addWidget(self.page_dea)       # 3
        self.stack.addWidget(self.page_avis) # 4

        root.addWidget(self.stack)

        # Connexions internes
        self.page_infos.submitted.connect(self._on_form_submitted)
        self.page_infos.cancelled.connect(self._on_cancel)
        self.page_results.relancer.connect(self._on_relancer)
        self.page_results.valider.connect(self._on_valider)
        self.page_dea.submitted.connect(self._on_dea_submitted)
        self.page_dea.back_requested.connect(self._on_dea_back_to_validation)
        self.page_avis.back_requested.connect(self._on_dea_back)
        self.page_avis.final_submitted.connect(self._on_dea_final_submitted)

        # État initial
        self.stepper.set_current(0)
        self.stack.setCurrentIndex(self.PAGE_INFOS)

    # ── Transitions ─────────────────────────────

    def _on_form_submitted(self, data: dict):
        """Crée le dossier puis lance l'extraction autonome via le Worker."""
        # Guard: if a dossier already exists for this session, 
        # don't create a new one
        if self.current_dossier_id:
            reply = QMessageBox.question(
                self, "Dossier existant",
                f"Un dossier (ID: {self.current_dossier_id}) est déjà en cours.\n"
                "Voulez-vous continuer avec ce dossier ou en créer un nouveau ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                # Reuse existing dossier — skip creation
                self.stepper.mark_done(0)
                self.stepper.set_current(1)
                self.stack.setCurrentIndex(self.PAGE_LOADING)
                self.page_loading.start()
                self.extraction_worker = ExtractionWorker(
                    self.client, data, 
                    dossier_id=self.current_dossier_id
                )
                self.extraction_worker.finished.connect(self._on_extraction_finished)
                self.extraction_worker.error.connect(self._on_extraction_error)
                self.extraction_worker.start()
                return
            else:
                self.current_dossier_id = None  # Allow new creation

        # 1. Création explicite du dossier avant l'extraction
        payload = {
            "nom_demandeur": data.get("nom", ""),
            "identifiant_depositaire": data.get("identifiant", ""),
            "type_demande": data.get("type", ""),
            "region": data.get("region", ""),
        }
        res = self.client.post("/dossiers/", json=payload)
        
        if not res or "id" not in res:
            QMessageBox.critical(self, "Erreur", "Impossible de créer le dossier sur le serveur. L'extraction ne peut pas démarrer.")
            return

        self.current_dossier_id = res["id"]

        # 2. Transition UI
        self.stepper.mark_done(0)
        self.stepper.set_current(1)
        self.stack.setCurrentIndex(self.PAGE_LOADING)
        self.page_loading.start()

        # 3. Lancement du worker d'extraction avec l'ID créé
        self.extraction_worker = ExtractionWorker(self.client, data, dossier_id=self.current_dossier_id)
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
            formulaire_id = self.current_formulaire_id or self.current_dossier_id
            payload = {"formulaire_id": formulaire_id, "points": rows}
            res = self.client.post("/extraction/confirm", json=payload)
            print(f">>> CONFIRM RESPONSE: {res}")

            if not res:
                raise Exception("Le serveur n'a pas répondu à la confirmation.")

            # On attend un objet contenant kmz_path, kmz_filename et altitude_finale_max
            self._confirm_result = res
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
        """Transition vers la page Avis."""
        alt_finale_max = self._confirm_result.get("altitude_finale_max", 0.0) if hasattr(self, "_confirm_result") else 0.0
        self.page_avis.set_result(
            data,
            alt_finale_max=alt_finale_max,
            dossier_id=self.current_dossier_id,
            client=self.client,
        )
        self.stepper.mark_done(3)
        self.stepper.set_current(4)
        self.stack.setCurrentIndex(self.PAGE_AVIS)

    def _on_dea_back(self):
        """Retourne à la page de saisie DEA."""
        self.stack.setCurrentIndex(self.PAGE_DEA)

    def _on_dea_back_to_validation(self):
        """Retourne à la page de validation des coordonnées."""
        self.stack.setCurrentIndex(self.PAGE_RESULTS)
        self.stepper.set_current(2)

    def _on_dea_final_submitted(self, data: dict):
        """Gère la validation finale de l'étude DEA."""
        QMessageBox.information(self, "Étude DEA", "Les données de l'étude DEA ont été enregistrées avec succès.")
        self.stepper.mark_done(3)
        self.stepper.set_current(4)
        # Transition vers la page finale Avis PDF si implémentée

    # ── API publique ─────────────────────────────

    def _on_extraction_finished(self, result: dict):
        """Gère la réponse réussie du Worker."""
        # Mettre à jour l'ID du dossier pour les relances
        if "id" in result:
            self.current_dossier_id = result["id"]
        elif self.current_dossier_id is None:
            self.current_dossier_id = result.get("dossier_id")
        # Stocker le formulaire_id retourné par le pipeline OCR
        self.current_formulaire_id = result.get("formulaire_id")

        # ExtractionKResult contient 'donnees', 'statistiques', etc.
        rows = result.get("donnees", [])
        stats = result.get("statistiques", {})

        # Dynamic headers from actual extracted data
        fixed = ["N°", "Latitude DMS", "Longitude DMS"]
        if rows:
            spec = rows[0].get("donnees_specifiques", {})
            keys = [k for k in spec.keys()
                    if not k.startswith("_") and k != "erreur_coordonnee"]
            alt  = [k for k in keys if "altitude" in k.lower() or "finale" in k.lower()]
            rest = [k for k in keys if k not in alt]
            headers = fixed + [k[0].upper()+k[1:] for k in rest + alt]
        else:
            headers = fixed

        self.show_extraction_results(
            rows,
            headers=headers,
            type_formulaire=result.get("type_formulaire", "Inconnu"),
            n_detected=stats.get("total_lignes", len(rows)),
            success_rate=result.get("taux_succes", 100.0),
            n_valid=stats.get("coordonnees_valides", len(rows)),
            dossier_id=self.current_dossier_id,
            token=self.token,
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