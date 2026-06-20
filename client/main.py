"""
Point d entree PySide6.
Initialise l application Qt, applique la feuille de style,
affiche la fenetre de connexion en premier.
"""
import sys
import os

# Add the project root to sys.path to allow absolute imports starting with 'client'
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from PySide6.QtWidgets import QApplication
from client.views.login_view import LoginView

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Systeme OACA")
    try:
        with open("client/assets/styles.qss", "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        pass
    window = LoginView()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
