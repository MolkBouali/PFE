"""
Widget notification temporaire (toast).
Succes (vert) ou erreur (rouge), disparait apres 3 secondes.
Reutilise dans toutes les vues.
"""
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import QTimer, Qt

class NotificationWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.hide()

    def show_success(self, message: str):
        self.setText(f"OK {message}")
        self.setStyleSheet("background:#d4edda;color:#155724;padding:8px;border-radius:4px;")
        self._show_temp()

    def show_error(self, message: str):
        self.setText(f"Erreur : {message}")
        self.setStyleSheet("background:#f8d7da;color:#721c24;padding:8px;border-radius:4px;")
        self._show_temp()

    def _show_temp(self):
        self.show()
        QTimer.singleShot(3000, self.hide)
