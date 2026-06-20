from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout, QWidget
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QPalette
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class KpiCard(QFrame):
    """
    KPI Card with colored left border and decorative circle
    """
    def __init__(self, title, color, tint="#FFFFFF", parent=None):
        super().__init__(parent)
        self.title = title
        self.color = color
        self.tint = tint
        self.setup_ui()

    def setup_ui(self):
        self.setFixedHeight(110)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.tint};
                border-radius: 10px;
                border-left: 6px solid {self.color};
                border-top: 3px solid {self.color};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(2)

        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet("color: #888; font-size: 12px; border: none; background: transparent;")
        
        self.value_label = QLabel("0")
        self.value_label.setStyleSheet(f"color: {self.color}; font-size: 32px; font-weight: bold; border: none; background: transparent;")
        
        self.subtitle_label = QLabel("")
        self.subtitle_label.setStyleSheet("color: #AAA; font-size: 11px; border: none; background: transparent;")

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.subtitle_label)

    def set_value(self, value, subtitle=None):
        self.value_label.setText(str(value))
        if subtitle:
            self.subtitle_label.setText(subtitle)

class ChartCard(QFrame):
    """
    Card container for matplotlib charts
    """
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #E0E0E0;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)

        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(5)

        title_label = QLabel(self.title)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1F3864; border: none; background: transparent;")
        
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #D5D8DC; max-height: 1px;")

        title_layout.addWidget(title_label)
        title_layout.addWidget(separator)

        self.canvas = FigureCanvas(Figure(figsize=(4, 3), dpi=100))
        self.canvas.setStyleSheet("border: none; background: transparent;")
        
        layout.addWidget(title_container)
        layout.addWidget(self.canvas)

    def get_figure(self):
        return self.canvas.figure