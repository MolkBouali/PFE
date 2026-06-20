"""
Interface saisie parametres etude technique DEA.
Champs : aeroport, type surface, type obstacle, altitudes, distance piste.
Affiche le diagnostic de conformite calcule automatiquement.
Accessible uniquement si coordonnees valides (pas de complement en attente).
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QComboBox
from client.api_client.decision_client import DecisionClient

class EtudeView(QWidget):
    def __init__(self, token: str, dossier_id: int):
        super().__init__()
        self.token = token
        self.dossier_id = dossier_id
        self.client = DecisionClient(token)
        self.setWindowTitle("Système de gestion de demandes d'avis OACA -- Etude technique DEA")
        self.resize(700, 500)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        self.combo_aeroport = QComboBox()
        self.combo_aeroport.setPlaceholderText("Selectionner l aeroport")
        self.combo_surface = QComboBox()
        self.combo_surface.addItems(["piste", "approche", "transition"])
        self.input_alt_sol = QLineEdit(placeholderText="Altitude sol (m)")
        self.input_alt_finale = QLineEdit(placeholderText="Altitude finale (m)")
        self.input_hauteur = QLineEdit(placeholderText="Hauteur demandee (m)")
        self.input_distance = QLineEdit(placeholderText="Distance piste (m)")
        self.lbl_resultat = QLabel("")
        self.btn_analyser = QPushButton("Lancer calcul")
        self.btn_analyser.clicked.connect(self._on_analyser)
        for w in [self.combo_aeroport, self.combo_surface, self.input_alt_sol,
                  self.input_alt_finale, self.input_hauteur, self.input_distance,
                  self.btn_analyser, self.lbl_resultat]:
            layout.addWidget(w)

    def _on_analyser(self):
        data = {"aeroport": self.combo_aeroport.currentText(),
                "type_surface": self.combo_surface.currentText(),
                "type_objet": "obstacle",
                "altitude_sol": float(self.input_alt_sol.text() or 0),
                "altitude_finale": float(self.input_alt_finale.text() or 0),
                "hauteur_demandee": float(self.input_hauteur.text() or 0),
                "distance_piste": float(self.input_distance.text() or 0) or None}
        result = self.client.analyse(self.dossier_id, data)
        if result:
            self.lbl_resultat.setText(
                f"Resultat : {result.get('type_avis')} | Hauteur max : {result.get('hauteur_max_autorisee')} m")
