"""
Interface authentification.
Formulaire connexion (identifiant + mot de passe).
Succes -> redirige vers StatsView. Echec -> message d erreur.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel
from PySide6.QtCore import Qt
from client.api_client.auth_client import AuthClient

class LoginView(QWidget):
    def __init__(self):
        super().__init__()
        self.client = AuthClient()
        self.setWindowTitle("Système de gestion de demandes d'avis OACA -- Connexion")
        self.setFixedSize(400, 300)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)
        self.lbl_title = QLabel("Système de gestion de demandes d'avis OACA")
        self.lbl_error = QLabel("")
        self.lbl_error.setStyleSheet("color: red;")
        self.input_id = QLineEdit(placeholderText="Identifiant")
        self.input_pwd = QLineEdit(placeholderText="Mot de passe")
        self.input_pwd.setEchoMode(QLineEdit.Password)
        self.btn_login = QPushButton("Se connecter")
        self.btn_login.clicked.connect(self._on_login)
        for w in [self.lbl_title, self.input_id, self.input_pwd, self.lbl_error, self.btn_login]:
            layout.addWidget(w)

    def _on_login(self):
        result = self.client.login(self.input_id.text(), self.input_pwd.text())
        if result:
            from client.views.stats_view import StatsView
            self.stats = StatsView(token=result.get("access_token"))
            self.stats.showMaximized()
            self.close()
        else:
            self.lbl_error.setText("Identifiant ou mot de passe incorrect")
