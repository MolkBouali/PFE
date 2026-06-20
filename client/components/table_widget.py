"""
Widget tableau generique reutilisable.
Tri par colonne, redimensionnement, selection de ligne.
Signal row_double_clicked(int) emis au double-clic.
Utilise dans ArchivesView et StatsView.
"""
from PySide6.QtWidgets import QTableWidget, QHeaderView
from PySide6.QtCore import Signal

class TableWidget(QTableWidget):
    row_double_clicked = Signal(int)

    def __init__(self, columns: list, parent=None):
        super().__init__(parent)
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cellDoubleClicked.connect(lambda r, c: self.row_double_clicked.emit(r))
