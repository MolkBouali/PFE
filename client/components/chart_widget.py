"""
Widget graphique pour les statistiques.
Graphique en barres ou camembert selon les donnees.
Utilise dans StatsView pour repartition avis et evolution mensuelle.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout

class ChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

    def set_bar_data(self, title: str, categories: list, data: dict):
        """Affiche un graphique en barres. Implementation via QtCharts."""
        pass
