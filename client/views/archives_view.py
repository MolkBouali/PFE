"""
Interface consultation archives.
Liste filtrable des dossiers traites.
Clic sur N° Dossier -> detail du dossier + telechargement avis PDF.
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                               QComboBox, QLabel, QAbstractItemView)
from PySide6.QtWidgets import QHeaderView
from client.api_client.dossier_client import DossierClient

class ArchivesView(QWidget):
    dossier_selected = Signal(int)

    STATUTS_GLOBAUX = {
        "en_cours": "En cours",
        "traite": "Traité"
    }
    RESULTATS_AVIS = {
        "favorable": "Favorable",
        "favorable_balisage": "Favorable avec balisage",
        "defavorable": "Défavorable",
        "non_genere": "--"
    }
    STATUTS_COMPLEMENT = {
        "aucun": "--",
        "en_attente": "En attente",
        "recu": "Reçu",
        "traite": "Traité"
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
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Filter section
        filtres = QHBoxLayout()
        filtres.setSpacing(10)

        self.input_numero = QLineEdit(placeholderText="Numéro dossier")
        self.input_deposant = QLineEdit(placeholderText="Déposant")
        
        # Statut Filter
        self.combo_statut = QComboBox()
        self.combo_statut.addItem("Tous")
        for key, value in self.STATUTS_GLOBAUX.items():
            self.combo_statut.addItem(value, key)

        btn_search = QPushButton("Rechercher")
        btn_search.clicked.connect(self._load_archives)

        filtres.addWidget(QLabel("N°:"))
        filtres.addWidget(self.input_numero)
        filtres.addWidget(QLabel("Déposant:"))
        filtres.addWidget(self.input_deposant)
        filtres.addWidget(QLabel("Statut:"))
        filtres.addWidget(self.combo_statut)
        filtres.addWidget(btn_search)
        
        layout.addLayout(filtres)

        # Table setup
        self.table = QTableWidget()
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