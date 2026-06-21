"""
Interface consultation archives.
Liste filtrable des dossiers traites.
Clic sur N° Dossier -> detail du dossier + telechargement avis PDF.
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                                QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                                QComboBox, QLabel, QAbstractItemView, QFrame, QSizePolicy)
from PySide6.QtWidgets import QHeaderView
from client.api_client.dossier_client import DossierClient

# Palette de couleurs pour cohérence avec dossier_view.py
COLOR_PRIMARY = "#1B3A5C"
COLOR_PRIMARY_HL = "#234876"
COLOR_INPUT_BORDER_FOCUS = "#1B3A5C"
COLOR_BG = "#F4F6F9"
COLOR_TEXT_MAIN = "#1A1A2E"
COLOR_TEXT_MUTED = "#6B7A99"
COLOR_BORDER = "#D0D7E2"

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
        color: #B0BAC9;
    }}
"""

class ArchivesView(QWidget):
    dossier_selected = Signal(int)

    STATUTS_GLOBAUX = {
        "en_cours": "En cours",
        "traite": "Traité",
        "en attente": "En attente"
    }
    RESULTATS_AVIS = {
        "FAVORABLE": "Favorable",
        "DEFAVORABLE": "Défavorable",
        "non_genere": "--"
    }
    STATUTS_COMPLEMENT = {
        "aucun": "--",
        "en_attente": "En attente",
    }

    def __init__(self, token: str):
        super().__init__()
        self.token = token
        self.client = DossierClient(token)
        self.setWindowTitle("Système de gestion de demandes d'avis OACA -- Archives")
        self.resize(1200, 600)
        self._build_ui()
        self._load_archives()

    def _build_ui(self):
        self.setStyleSheet(f"background-color: {COLOR_BG};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 20)
        layout.setSpacing(0)

        # Titre section
        title = QLabel("Consultation des Archives")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet(f"color: {COLOR_TEXT_MAIN};")
        layout.addWidget(title)

        layout.addSpacing(6)

        subtitle = QLabel("Recherchez et consultez les dossiers traités dans le système")
        subtitle.setFont(QFont("Arial", 9))
        subtitle.setStyleSheet(f"color: {COLOR_PRIMARY};")
        layout.addWidget(subtitle)

        layout.addSpacing(24)

        # Filter section
        filtres_container = QFrame()
        filtres_container.setStyleSheet(f"background: white; border: 1px solid {COLOR_BORDER}; border-radius: 8px;")

        def create_label(text):
            lbl = QLabel(text)
            lbl.setStyleSheet(
                "color: #64748b; font-size: 10px; font-weight: bold; "
                "background: transparent; border: none;"
            )
            lbl.setFixedWidth(70)
            return lbl

        self.input_numero = QLineEdit(placeholderText="Numéro dossier")
        self.input_numero.setStyleSheet("""
            QLineEdit {
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                padding: 2px 10px;
                font-size: 12px;
                background: white;
                color: #1F3864;
            }
            QLineEdit:focus {
                border: 1px solid #1F3864;
            }
        """)
        self.input_numero.setFixedHeight(32)
        self.input_numero.setMinimumWidth(0)
        self.input_numero.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.input_deposant = QLineEdit(placeholderText="Déposant")
        self.input_deposant.setStyleSheet("""
            QLineEdit {
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                padding: 2px 10px;
                font-size: 12px;
                background: white;
                color: #1F3864;
            }
            QLineEdit:focus {
                border: 1px solid #1F3864;
            }
        """)
        self.input_deposant.setFixedHeight(32)
        self.input_deposant.setMinimumWidth(0)
        self.input_deposant.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Statut Filter
        self.combo_statut = QComboBox()
        self.combo_statut.addItem("Tous")
        for key, value in self.STATUTS_GLOBAUX.items():
            self.combo_statut.addItem(value, key)
        self.combo_statut.setStyleSheet("""
            QComboBox {
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                padding: 2px 10px;
                font-size: 12px;
                background: white;
                color: #1F3864;
            }
            QComboBox::drop-down { border: none; }
        """)
        self.combo_statut.setFixedHeight(32)
        self.combo_statut.setMinimumWidth(0)
        self.combo_statut.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        btn_search = QPushButton("Rechercher")
        btn_search.setFixedHeight(32)
        btn_search.setFixedWidth(120)
        btn_search.setStyleSheet(f"""
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
        btn_search.clicked.connect(self._load_archives)

        filtres_layout = QHBoxLayout(filtres_container)
        filtres_layout.setContentsMargins(16, 10, 16, 10)
        filtres_layout.setSpacing(12)

        # Field 1
        lbl_dossier = create_label("N° DOSSIER")
        filtres_layout.addWidget(lbl_dossier)
        filtres_layout.addWidget(self.input_numero, stretch=2)

        # Separator space
        filtres_layout.addSpacing(8)

        # Field 2
        lbl_deposant = create_label("DÉPOSANT")
        filtres_layout.addWidget(lbl_deposant)
        filtres_layout.addWidget(self.input_deposant, stretch=2)

        # Separator space
        filtres_layout.addSpacing(8)

        # Field 3
        lbl_statut = create_label("STATUT")
        filtres_layout.addWidget(lbl_statut)
        filtres_layout.addWidget(self.combo_statut, stretch=2)

        # Push button to the right
        filtres_layout.addSpacing(16)
        filtres_layout.addWidget(btn_search)
        
        layout.addWidget(filtres_container)
        layout.addSpacing(20)

        # Table setup
        self.table = QTableWidget()
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: white;
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                gridline-color: {COLOR_BORDER};
            }}
            QHeaderView::section {{
                background-color: {COLOR_PRIMARY};
                color: white;
                padding: 6px;
                border: none;
                font-weight: bold;
            }}
        """)
        self.table.verticalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #E2E8F0;
                color: #64748B;
                border: 1px solid #D0D7E2;
                font-weight: normal;
            }
        """)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "N° Dossier", "Déposant", "Type Demande", "Région", 
            "Statut", "Avis", "Complément", "Date"
        ])
        
        # Responsive table: stretch columns to fill space
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        
        # Make table read-only
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # Connect single click for redirection
        self.table.cellClicked.connect(self._on_cell_clicked)
        
        layout.addWidget(self.table)

    def _load_archives(self):
        # Get filter values
        params = {
            "numero": self.input_numero.text().strip(),
            "demandeur": self.input_deposant.text().strip(),
            "statut": self.combo_statut.currentData() if self.combo_statut.currentData() else None
        }
        # Remove empty filters
        params = {k: v for k, v in params.items() if v}

        data = self.client.get_all(params=params) or []
        
        # Sort by date descending (most recent first)
        data.sort(key=lambda x: x.get("date_depot", ""), reverse=True)
        
        self.table.setRowCount(len(data))
        
        # Store IDs for each row
        self.row_ids = [d.get("id") for d in data]
        
        for i, d in enumerate(data):
            # Mapping for the visual display
            statut_mapped = self.STATUTS_GLOBAUX.get(d.get("statut"), d.get("statut", ""))
            avis_mapped = self.RESULTATS_AVIS.get(d.get("avis"), d.get("avis", ""))
            complement_mapped = self.STATUTS_COMPLEMENT.get(d.get("complement"), d.get("complement", ""))
            
            row_data = [
                d.get("numero_dossier", ""),
                d.get("nom_demandeur", ""),
                d.get("type_demande", ""),
                d.get("region", ""),
                statut_mapped,
                avis_mapped,
                complement_mapped,
                d.get("date_depot", "")
            ]
            
            for j, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                # Additional protection to make item read-only
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(i, j, item)

    def _on_cell_clicked(self, row, column):
        # Only the 'Num Dossier' column (column 0) is clickable for redirection
        if column == 0:
            dossier_id = self.row_ids[row] if row < len(self.row_ids) else None
            if dossier_id:
                self.dossier_selected.emit(dossier_id)