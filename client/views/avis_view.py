"""
Interface generation avis officiel PDF.
Cases a cocher : validations DER, DTA, DANA, DNA.
Le type d avis est determine automatiquement selon les validations.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QCheckBox, QTextEdit
from client.api_client.document_client import DocumentClient

class AvisView(QWidget):
    def __init__(self, token: str, dossier_id: int):
        super().__init__()
        self.token = token
        self.dossier_id = dossier_id
        self.client = DocumentClient(token)
        self.setWindowTitle("OACA -- Generation avis officiel")
        self.resize(600, 500)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Validations des directions"))
        self.chk_der = QCheckBox("DER")
        self.chk_dta = QCheckBox("DTA")
        self.chk_dana = QCheckBox("DANA")
        self.chk_dna = QCheckBox("DNA")
        self.txt_justif = QTextEdit(placeholderText="Justification (optionnel)")
        self.btn_generer = QPushButton("Generer l avis officiel PDF")
        self.btn_generer.clicked.connect(self._on_generer)
        self.lbl_status = QLabel("")
        for w in [self.chk_der, self.chk_dta, self.chk_dana, self.chk_dna,
                  self.txt_justif, self.btn_generer, self.lbl_status]:
            layout.addWidget(w)

    def _on_generer(self):
        data = {"validation_der": self.chk_der.isChecked(), "validation_dta": self.chk_dta.isChecked(),
                "validation_dana": self.chk_dana.isChecked(), "validation_dna": self.chk_dna.isChecked(),
                "justification": self.txt_justif.toPlainText()}
        result = self.client.generate_pdf(self.dossier_id, data)
        self.lbl_status.setText("Avis PDF genere avec succes" if result else "Erreur generation")
