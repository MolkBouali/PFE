"""
Widget depot de fichiers (drag & drop + bouton parcourir).
Accepte PNG, JPG, PDF.
Signal file_selected(path) emis a la selection.
Utilise dans DossierView pour l upload du formulaire scanne.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog
from PySide6.QtCore import Signal, Qt

class FileUploadWidget(QWidget):
    file_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        layout = QVBoxLayout(self)
        self.lbl = QLabel("Deposez le formulaire scanne ici ou")
        self.lbl.setAlignment(Qt.AlignCenter)
        self.btn = QPushButton("Parcourir...")
        self.btn.clicked.connect(self._browse)
        layout.addWidget(self.lbl)
        layout.addWidget(self.btn)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "Selectionner un fichier", "",
                                               "Formulaires (*.png *.jpg *.jpeg *.pdf)")
        if path:
            self.lbl.setText(f"{path.split('/')[-1]}")
            self.file_selected.emit(path)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        path = event.mimeData().urls()[0].toLocalFile()
        self.lbl.setText(path.split("/")[-1])
        self.file_selected.emit(path)
