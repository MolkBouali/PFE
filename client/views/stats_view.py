from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QFrame, QScrollArea, QSpacerItem, QSizePolicy, QPushButton
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QFont

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np
import random

from client.components.stats_components import KpiCard, ChartCard
from client.views.dossier_view import DossierView
from client.views.archives_view import ArchivesView

# Color Palette
PRIMARY = "#1F3864"
SECONDARY = "#2E5FA3"
BG = "#F0F2F5"
CARD_BG = "#FFFFFF"
GREEN = "#27AE60"
ORANGE = "#E67E22"
RED = "#E74C3C"
BLUE_LT = "#AEC6E8"
GREY = "#D5D8DC"
BLUE_MD = "#3498DB"

class StatsView(QWidget):
    def __init__(self, token=None, parent=None):
        super().__init__(parent)
        self.token = token
        self.api_headers = {"Authorization": f"Bearer {token}"} if token else {}
        self.setup_ui()
        self._refresh()

    def setup_ui(self):
        self.setMinimumSize(900, 600)
        self.resize(1120, 860)
        self.setStyleSheet(f"background-color: {BG};")
        
        # Root Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 1. Header Row 1 (Dark Navy Bar)
        self.header_row1 = QFrame()
        self.header_row1.setFixedHeight(70)
        self.header_row1.setStyleSheet(f"background-color: {PRIMARY}; border: none;")
        header1_layout = QHBoxLayout(self.header_row1)
        header1_layout.setContentsMargins(20, 0, 20, 0)

        self.main_title = QLabel("Système de gestion de demandes d'avis OACA")
        self.main_title.setStyleSheet("color: white; font-size: 18px; font-weight: bold; border: none; background: transparent;")
        header1_layout.addWidget(self.main_title)
        header1_layout.addStretch()

        # Action Buttons in Row 1
        buttons_container = QHBoxLayout()
        buttons_container.setSpacing(15)

        self.btn_view_archives = QPushButton("Consulter Archives")
        self.btn_view_archives.setFixedSize(160, 32)
        self.btn_view_archives.setStyleSheet(f"""
            QPushButton {{
                background-color: #4A69BD;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                border: 1px solid #FFFFFF;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY};
            }}
        """)
        self.btn_view_archives.clicked.connect(self._on_view_archives)

        self.btn_create_dossier = QPushButton("+ Nouveau Dossier")
        self.btn_create_dossier.setFixedSize(160, 32)
        self.btn_create_dossier.setStyleSheet(f"""
            QPushButton {{
                background-color: {SECONDARY};
                color: white;
                font-weight: bold;
                border-radius: 5px;
                border: 1px solid #FFFFFF;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY};
            }}
        """)
        self.btn_create_dossier.clicked.connect(self._on_create_dossier)

        buttons_container.addWidget(self.btn_view_archives)
        buttons_container.addWidget(self.btn_create_dossier)
        header1_layout.addLayout(buttons_container)
        self.main_layout.addWidget(self.header_row1)

        # Header Row 2 (White Bar with Breadcrumbs and Filters)
        self.header_row2 = QFrame()
        self.header_row2.setFixedHeight(60)
        self.header_row2.setStyleSheet("background-color: white; border-bottom: 1px solid #E0E0E0;")
        row2_layout = QHBoxLayout(self.header_row2)
        row2_layout.setContentsMargins(20, 0, 20, 0)

        # Left side: Breadcrumbs
        left_side = QHBoxLayout()
        title_lbl = QLabel("Tableau de bord")
        title_lbl.setStyleSheet("color: #1F3864; font-size: 14px; font-weight: bold; background: transparent; border: none;")
        
        separator_lbl = QLabel("|")
        separator_lbl.setStyleSheet("color: #CBD5E1; background: transparent; border: none;")
        
        subtitle_lbl = QLabel("Vue d'ensemble de l'activité du service d'instruction")
        subtitle_lbl.setStyleSheet("color: #64748b; font-size: 11px; background: transparent; border: none;")
        
        left_side.addWidget(title_lbl)
        left_side.addWidget(separator_lbl)
        left_side.addWidget(subtitle_lbl)
        left_side.addStretch()

        # Right side: Integrated Filters
        right_side = QHBoxLayout()
        filter_lbl = QLabel("Filtres statistiques :")
        filter_lbl.setStyleSheet("color: #1F3864; font-weight: bold; font-size: 11px; background: transparent; border: none;")
        
        self.year_combo = QComboBox()
        self.year_combo.addItems(["2025", "2026"])
        self.year_combo.setCurrentText("2026")
        self.year_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 12px;
                background: white;
                color: #1F3864;
                min-width: 70px;
            }
            QComboBox::drop-down { border: none; }
        """)
        
        self.month_combo = QComboBox()
        self.month_combo.addItems(["Toute l'année", "Jan", "Fév", "Mar", "Avr", "Mai", "Jun", "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"])
        self.month_combo.setCurrentText("Jun")
        self.month_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 12px;
                background: white;
                color: #1F3864;
                min-width: 120px;
            }
            QComboBox::drop-down { border: none; }
        """)
 
        self.period_label = QLabel("")
        self.period_label.setStyleSheet("color: #1F3864; font-size: 11px; border: none; background: transparent; margin-left: 10px;")

        self.year_combo.currentTextChanged.connect(self._refresh)
        self.month_combo.currentTextChanged.connect(self._refresh)
 
        right_side.addWidget(filter_lbl)
        right_side.addWidget(self.year_combo)
        right_side.addWidget(self.month_combo)
        right_side.addWidget(self.period_label)

        row2_layout.addLayout(left_side)
        row2_layout.addLayout(right_side)
        self.main_layout.addWidget(self.header_row2)

        # 2. Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background: {BG};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: #B0C4DE;
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)

        # Inner Widget for Scroll Area
        self.inner_widget = QWidget()
        self.inner_widget.setStyleSheet(f"background: {BG};")
        self.content_layout = QVBoxLayout(self.inner_widget)
        self.content_layout.setSpacing(8)
        self.content_layout.setContentsMargins(20, 8, 8, 8)
        
        # 3. KPI Cards row
        self.kpi_row = QHBoxLayout()
        self.kpi_row.setSpacing(12)
        
        self.kpi_total = KpiCard("Total dossiers", PRIMARY, tint="#EEF2F8")
        self.kpi_pending = KpiCard("En attente", ORANGE, tint="#FEF5EC")
        self.kpi_ongoing = KpiCard("En cours", BLUE_MD, tint="#EBF5FB")
        self.kpi_done = KpiCard("Traités", GREEN, tint="#EAFAF1")
        
        for kpi in [self.kpi_total, self.kpi_pending, self.kpi_ongoing, self.kpi_done]:
            kpi.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.kpi_row.addWidget(kpi)
        
        self.content_layout.addLayout(self.kpi_row)

        # 4. Donuts Row
        self.donuts_row = QHBoxLayout()
        self.donuts_row.setSpacing(20)
        
        self.chart_status = ChartCard("Répartition par statut", height=280)
        self.chart_avis = ChartCard("Répartition des avis émis", height=280)
        
        self.donuts_row.addWidget(self.chart_status)
        self.donuts_row.addWidget(self.chart_avis)
        
        self.content_layout.addLayout(self.donuts_row)

        # To ensure a clear separation and push these to the scroll area
        self.content_layout.setSpacing(20)
        
        # 5. Monthly Bar Chart
        self.chart_monthly = ChartCard("Évolution mensuelle — Dossiers déposés", height=250)
        self.content_layout.addWidget(self.chart_monthly)

        # 6. Regional Bar Chart
        self.chart_regions = ChartCard("Distribution par région", height=360)
        self.content_layout.addWidget(self.chart_regions)
        
        # Content stays top-aligned
        self.content_layout.addStretch()

        self.scroll.setWidget(self.inner_widget)
        self.main_layout.addWidget(self.scroll)

    def _on_create_dossier(self):
        """Open the Dossier creation view in a new window"""
        self.dossier_window = DossierView(token=self.token)
        self.dossier_window.showMaximized()
        # Removed self.close() to keep the stats window open

    def _on_view_archives(self):
        """Open the Archives view in a new window"""
        self.archives_window = ArchivesView(token=self.token)
        self.archives_window.showMaximized()
        # Removed self.close() to keep the stats window open

    def _refresh(self):
        year = self.year_combo.currentText()
        month = self.month_combo.currentText()
        month_index = self.month_combo.currentIndex()  # 0=Toute l'année, 1=Jan...
        
        # Update Period Labels
        period_text = f"Période : {year}" if month == "Toute l'année" else f"Période : {month} {year}"
        self.period_label.setText(period_text)

        # --- DATA FETCHING (Mocked for now, will be replaced by API calls) ---
        # In a real scenario, we'd call backend/api/stats.py
        data = self._get_mock_data(year, month, month_index)
        
        # Update KPIs
        self.kpi_total.set_value(data['total'], "Dossiers cumulés")
        self.kpi_pending.set_value(data['pending'], "À traiter")
        self.kpi_ongoing.set_value(data['ongoing'], "En analyse")
        self.kpi_done.set_value(data['done'], "Clôturés")

        # Update Charts
        self._draw_status_donut(data['status_dist'])
        self._draw_avis_donut(data['avis_dist'])
        self._draw_monthly_chart(data['monthly_dist'], month)
        self._draw_regions_chart(data['regions_dist'])

    def _get_mock_data(self, year, month, month_index=0):
        import random
        random.seed(hash(f"{year}{month}"))  # deterministic per filter combo

        MONTHLY_2025 = [8,11,9,14,17,22,18,13,15,10,7,3]
        MONTHLY_2026 = [16,15,17,24,30,41,0,0,0,0,0,0]

        MONTHS_LIST = ["Jan","Fév","Mar","Avr","Mai","Jun",
                       "Jul","Aoû","Sep","Oct","Nov","Déc"]

        monthly = MONTHLY_2025 if year == "2025" else MONTHLY_2026

        if month == "Toute l'année":
            total    = sum(monthly)
            pending  = max(1, int(total * 0.08))
            ongoing  = max(1, int(total * 0.20))
            done     = total - pending - ongoing
            monthly_dist = monthly
            regions_base = [38,14,18,12,10,6,5,4,9,27] if year=="2025" \
                           else [42,18,21,15,12,8,7,6,11,7]
        else:
            idx      = MONTHS_LIST.index(month)
            total    = monthly[idx]
            pending  = max(0, int(total * 0.17)) if idx == 5 and year=="2026" \
                       else max(0, int(total * 0.07))
            ongoing  = max(0, int(total * 0.31)) if idx == 5 and year=="2026" \
                       else max(0, int(total * 0.18))
            done     = max(0, total - pending - ongoing)
            monthly_dist = monthly
            regions_base = [
                max(0, int(v * total / max(sum([42,18,21,15,12,8,7,6,11,7]), 1)))
                for v in [42,18,21,15,12,8,7,6,11,7]
            ]

        REGIONS = ["Tunis","Enfidha","Monastir","Djerba","Sfax",
                   "Tozeur","Gafsa","Tabarka","Gabès","Borj El Amri"]

        favorable     = max(0, int(done * 0.65))
        fav_balisage  = max(0, int(done * 0.22))
        defavorable   = max(0, done - favorable - fav_balisage)

        return {
            'total':   total,
            'pending': pending,
            'ongoing': ongoing,
            'done':    done,
            'status_dist': {
                'En attente': pending,
                'En cours':   ongoing,
                'Traité':     done
            },
            'avis_dist': {
                'Favorable':           favorable,
                'Fav. avec balisage':  fav_balisage,
                'Défavorable':         defavorable
            },
            'monthly_dist': monthly_dist,
            'regions_dist': dict(zip(REGIONS, regions_base))
        }

    def _draw_status_donut(self, dist):
        fig = self.chart_status.get_figure()
        fig.clf()
        ax = fig.add_subplot(111)
        fig.subplots_adjust(left=0.05, right=0.65, top=0.92, bottom=0.12)
        ax.set_aspect('equal')
        
        labels = list(dist.keys())
        values = list(dist.values())
        colors = [ORANGE, BLUE_MD, GREEN]
        
        wedges, texts = ax.pie(values, colors=colors, startangle=90, wedgeprops=dict(width=0.45, edgecolor='w'))
        
        # Center Text
        total = sum(values)
        ax.text(0, 0.1, f"{total}", ha='center', va='center', 
                fontsize=20, fontweight='bold', color=PRIMARY)
        ax.text(0, -0.1, "dossiers", ha='center', va='center', 
                fontsize=12, color=PRIMARY)
        
        ax.legend(wedges, [f"{l} ({v})" for l, v in zip(labels, values)], 
                  loc="center left", bbox_to_anchor=(1.1, 0.5), frameon=False)
        
        ax.axis('off')
        # Fix margins to prevent the circle from moving when legend labels change
        fig.subplots_adjust(left=0.1, right=0.75, top=0.9, bottom=0.1)
        self.chart_status.canvas.draw()

    def _draw_avis_donut(self, dist):
        fig = self.chart_avis.get_figure()
        fig.clf()
        ax = fig.add_subplot(111)
        fig.subplots_adjust(left=0.05, right=0.65, top=0.92, bottom=0.12)
        ax.set_aspect('equal')
        
        labels = list(dist.keys())
        values = list(dist.values())
        colors = [GREEN, ORANGE, RED]
        
        if sum(values) == 0:
            ax.text(0.5, 0.5, "Aucune donnée", ha='center', va='center', fontsize=12, color=GREY)
            ax.axis('off')
            fig.subplots_adjust(left=0.1, right=0.75, top=0.9, bottom=0.1)
            self.chart_avis.canvas.draw()
            return

        wedges, texts = ax.pie(values, colors=colors, startangle=90, wedgeprops=dict(width=0.45, edgecolor='w'))
        
        total = sum(values)
        ax.text(0, 0.1, f"{total}", ha='center', va='center', 
                fontsize=20, fontweight='bold', color=PRIMARY)
        ax.text(0, -0.1, "avis", ha='center', va='center', 
                fontsize=12, color=PRIMARY)
        
        ax.legend(wedges, [f"{l} ({v})" for l, v in zip(labels, values)], 
                  loc="center left", bbox_to_anchor=(1.1, 0.5), frameon=False)
        
        ax.axis('off')
        # Fix margins to prevent the circle from moving when legend labels change
        fig.subplots_adjust(left=0.1, right=0.75, top=0.9, bottom=0.1)
        self.chart_avis.canvas.draw()

    def _draw_monthly_chart(self, monthly_data, selected_month):
        fig = self.chart_monthly.get_figure()
        fig.clf()
        ax = fig.add_subplot(111)
        
        months = ["Jan", "Fév", "Mar", "Avr", "Mai", "Jun", "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"]
        
        # Color logic
        if selected_month == "Toute l'année":
            colors = [SECONDARY] * 12
            legend_labels = ["Total Annuel"]
        else:
            colors = [PRIMARY if m == selected_month else BLUE_LT for m in months]
            legend_labels = ["Mois sélectionné", "Autres mois"]

        bars = ax.bar(months, monthly_data, color=colors, width=0.6)
        
        # Value labels
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.5, 
                        f'{int(height)}', ha='center', va='bottom', fontsize=9, color='#555')

        ax.set_facecolor('none')
        fig.patch.set_facecolor('none')
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.yaxis.grid(True, linestyle='--', alpha=0.7, color=GREY)
        ax.tick_params(axis='both', which='both', length=0)
        ax.set_xticks(range(len(months)))
        ax.set_xticklabels(months, fontsize=10, rotation=0)
        fig.subplots_adjust(bottom=0.22)
        
        # Custom Legend
        from matplotlib.lines import Line2D
        legend_elements = [Line2D([0], [0], color=c, lw=4, label=l) for c, l in zip(
            [PRIMARY, BLUE_LT] if selected_month != "Toute l'année" else [SECONDARY], 
            legend_labels
        )]
        ax.legend(handles=legend_elements, loc='upper right', frameon=False, fontsize=9)

        self.chart_monthly.canvas.draw()

    def _draw_regions_chart(self, region_data):
        fig = self.chart_regions.get_figure()
        fig.clf()
        ax = fig.add_subplot(111)
        
        # Sort descending
        sorted_data = sorted(region_data.items(), key=lambda x: x[1], reverse=True)
        labels = [x[0][:12] + "..." if len(x[0]) > 12 else x[0] for x in sorted_data]
        values = [x[1] for x in sorted_data]
        
        colors = [SECONDARY if v > 0 else GREY for v in values]
        bars = ax.barh(labels, values, color=colors, height=0.65)
        
        # Value labels on bars
        for i, v in enumerate(values):
            text = str(v) if v > 0 else "–"
            color = PRIMARY if v > 0 else '#AAA'
            ax.text(v + 0.5, i, text, va='center', color=color, fontsize=9)

        ax.invert_yaxis() 
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.tick_params(axis='x', labelbottom=False, length=0)
        ax.xaxis.grid(True, linestyle='--', alpha=0.5, color='#D5D8DC')
        ax.set_axisbelow(True)
        ax.yaxis.grid(True, linestyle='--', alpha=0.5, color=GREY)
        ax.tick_params(axis='y', labelsize=10)
        fig.subplots_adjust(left=0.28, right=0.92)
        
        # Custom Legend
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], color=SECONDARY, lw=4, label="Région active"),
            Line2D([0], [0], color=GREY, lw=4, label="Aucun dossier")
        ]
        ax.legend(handles=legend_elements, loc='lower right', frameon=False, fontsize=9)

        self.chart_regions.canvas.draw()

