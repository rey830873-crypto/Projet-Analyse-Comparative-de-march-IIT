from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QStackedWidget, QTableWidget, QTableWidgetItem, QTextEdit, QFileDialog,
                             QFrame, QGridLayout, QHeaderView, QMessageBox, QComboBox, QScrollArea)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Comparateur de marché | Abidjan")
        self.resize(1280, 820)
        self.setMinimumSize(1000, 680)
        self.setStyleSheet("""
            QMainWindow, QWidget { background:#F8F5EF; color:#2B2B2B; font-family:'Segoe UI'; font-size:10pt; }
            QLabel#title { font-size:24pt; font-weight:700; color:#252525; }
            QLabel#subtitle { color:#6F6A64; font-size:10.5pt; }
            QPushButton { background:#C65D2E; color:#FFFDF8; border:0; border-radius:8px; padding:10px 16px; font-weight:600; }
            QPushButton:hover { background:#A94B25; }
            QPushButton#secondary { background:#EEEAE3; color:#333333; }
            QFrame#sidebar { background:#FFFDF8; border:1px solid #E5DED4; border-radius:14px; }
            QLabel#brand { color:#B75126; font-size:14pt; font-weight:800; padding:12px 10px 18px; }
            QPushButton#nav { background:transparent; color:#414141; text-align:left; border-radius:8px; padding:12px 13px; }
            QPushButton#nav:hover { background:#F1ECE4; color:#A94B25; }
            QPushButton#nav:checked { background:#F4E5D8; color:#9B461F; font-weight:700; }
            QStackedWidget { background:#FFFDF8; border:1px solid #E5DED4; border-radius:14px; }
            QTableWidget { background:#FFFDF8; alternate-background-color:#F4F0E9; gridline-color:#E3DDD3; border:0; selection-background-color:#F2E0D5; }
            QHeaderView::section { background:#EEEAE3; color:#333333; padding:9px; border:0; font-weight:700; }
            QTextEdit, QComboBox { background:#FFFDF8; border:1px solid #E5DED4; border-radius:7px; padding:8px; }
            QTextEdit:focus, QComboBox:focus { border:1px solid #C65D2E; }
        """)
        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(26, 22, 26, 22)
        outer.setSpacing(16)
        top = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Analyse comparative de marché")
        title.setObjectName("title")
        subtitle = QLabel("Trois enseignes · une décision éclairée · prix en FCFA")
        subtitle.setObjectName("subtitle")
        title_box.addWidget(title); title_box.addWidget(subtitle)
        top.addLayout(title_box); top.addStretch()
        self.data_dir = None
        self.browse_button = QPushButton("Choisir le dossier")
        self.browse_button.setObjectName("secondary")
        top.addWidget(self.browse_button)
        self.refresh_button = QPushButton("Lancer l’analyse")
        top.addWidget(self.refresh_button)
        outer.addLayout(top)
        self.data_source = QLabel("Données : dossier Data du projet")
        self.data_source.setStyleSheet("color:#6F6A64;padding:2px;")
        self.data_source.setWordWrap(True)
        outer.addWidget(self.data_source)
        self.status = QLabel("Prêt. Choisissez le dossier si nécessaire, puis lancez l’analyse.")
        self.status.setStyleSheet("color:#4B4A48; padding:3px;")
        self.status.setWordWrap(True)
        outer.addWidget(self.status)
        body=QHBoxLayout(); body.setSpacing(14); outer.addLayout(body,1)
        sidebar=QFrame(); sidebar.setObjectName("sidebar"); sidebar.setFixedWidth(220)
        side_layout=QVBoxLayout(sidebar); side_layout.setContentsMargins(12,14,12,14); side_layout.setSpacing(5)
        brand=QLabel("●  COMPARATEUR"); brand.setObjectName("brand"); side_layout.addWidget(brand)
        section=QLabel("ESPACE D’ANALYSE"); section.setStyleSheet("color:#77716A;font-size:8pt;font-weight:700;padding:8px 12px 4px;"); side_layout.addWidget(section)
        body.addWidget(sidebar)
        self.pages=QStackedWidget(); body.addWidget(self.pages,1)
        self.nav_buttons=[]
        self.dashboard = QWidget(); self.dashboard_scroll=QScrollArea(); self.dashboard_scroll.setWidgetResizable(True); self.dashboard_scroll.setFrameShape(QFrame.Shape.NoFrame); self.dashboard_scroll.setWidget(self.dashboard); self._add_page(side_layout,"▤   Synthèse générale",self.dashboard_scroll)
        self.compare_table = self._table(["ID", "Produit", "Marché Lagune", "Baobab Shop", "Comptoir Ivoire", "Moins cher", "Écart FCFA", "Écart %"])
        compare_page = QWidget(); l = QVBoxLayout(compare_page); l.setContentsMargins(18,18,18,18)
        filter_row=QHBoxLayout(); filter_row.addWidget(QLabel("Afficher une catégorie :"))
        self.category_filter=QComboBox(); self.category_filter.addItems(["Toutes les catégories","Smartphone","Informatique","Électroménager"]); self.category_filter.setMinimumWidth(210)
        self.category_filter.setCurrentIndex(1)
        filter_row.addWidget(self.category_filter); filter_row.addStretch(); l.addLayout(filter_row); l.addWidget(self.compare_table,1)
        exp_row=QHBoxLayout(); self.export_button=QPushButton("Exporter le comparatif en CSV"); exp_row.addStretch(); exp_row.addWidget(self.export_button); l.addLayout(exp_row)
        self._add_page(side_layout,"▤   Comparatif des prix",compare_page)
        self.comparison_rows=[]
        self.category_filter.currentTextChanged.connect(self.filter_comparisons)
        self.basket_table = self._table(["Produit", "Qté", "Marché Lagune", "Baobab Shop", "Comptoir Ivoire", "Meilleur choix"])
        basket_page=QWidget(); bl=QVBoxLayout(basket_page); bl.setContentsMargins(20,20,20,20); bl.setSpacing(12)
        self.basket_summary_table=self._table(["Enseigne","Coût du panier","Disponibilité"]); bl.addWidget(self.basket_summary_table)
        self.basket_total=QLabel("Meilleur panier complet : —"); self.basket_total.setWordWrap(True); self.basket_total.setStyleSheet("font-size:14pt;font-weight:700;color:#B75126;padding:8px;"); bl.addWidget(self.basket_total)
        bl.addWidget(QLabel("Détail des articles")); bl.addWidget(self.basket_table,1); self._add_page(side_layout,"▣   Panier de rentrée",basket_page)
        self.history_table=self._table(["Enseigne","Moyenne annuelle","Semaine Black Friday","Écart BF / année","Lignes année","Lignes BF"])
        hist_page=QWidget(); hl=QVBoxLayout(hist_page); hl.setContentsMargins(20,20,20,20); hl.addWidget(self.history_table); note=QLabel("Période Black Friday : du 24 au 30 novembre 2025. L'historique utilise les prix affichés et exclut les données invalides."); note.setWordWrap(True); hl.addWidget(note); self._add_page(side_layout,"◷   Historique",hist_page)
        self.journal=QTextEdit(); self.journal.setReadOnly(True)
        log_page=QWidget(); ll=QVBoxLayout(log_page); ll.setContentsMargins(20,20,20,20); ll.addWidget(self.journal); self._add_page(side_layout,"☷   Journal de nettoyage",log_page)
        side_layout.addStretch()
        foot=QLabel("Projet pédagogique\nDonnées fictives · FCFA"); foot.setStyleSheet("color:#6F6A64;font-size:8pt;padding:10px;"); foot.setWordWrap(True); side_layout.addWidget(foot)
        self.nav_buttons[0].setChecked(True)
        self._build_dashboard()

    def _add_page(self, layout, label, page):
        button=QPushButton(label); button.setObjectName("nav"); button.setCheckable(True); button.setAutoExclusive(True); button.setMinimumHeight(42); button.setToolTip(label)
        index=self.pages.addWidget(page)
        button.clicked.connect(lambda checked=False, page_index=index: self.pages.setCurrentIndex(page_index))
        layout.addWidget(button); self.nav_buttons.append(button)

    def set_comparison_rows(self, rows):
        self.comparison_rows=rows
        self.filter_comparisons(self.category_filter.currentText())

    def filter_comparisons(self, category):
        rows=[values for row_category,values in self.comparison_rows
              if category == "Toutes les catégories" or row_category == category]
        self.fill_table(self.compare_table,rows)

    def _build_dashboard(self):
        layout=QVBoxLayout(self.dashboard); layout.setContentsMargins(20,20,20,20); layout.setSpacing(18)
        self.cards=QGridLayout(); self.cards.setSpacing(14); layout.addLayout(self.cards)
        self.insight=QLabel("La synthèse rassemble les principaux résultats : enseignes les moins chères, écarts moyens et meilleures occasions. Cliquez sur « Lancer l’analyse » pour la calculer."); self.insight.setWordWrap(True); self.insight.setStyleSheet("background:#F1ECE4;border-left:4px solid #C65D2E;padding:14px;border-radius:5px;font-size:10.5pt;"); layout.addWidget(self.insight)
        store_title=QLabel("Résultats par enseigne"); store_title.setStyleSheet("font-weight:700;font-size:11pt;color:#333333;"); layout.addWidget(store_title)
        self.store_summary_table=self._table(["Enseigne","Victoires","Part des comparables gagnés","Écart moyen au minimum","Offres sur produits comparables"])
        self.store_summary_table.setMaximumHeight(190); layout.addWidget(self.store_summary_table)
        top_title=QLabel("Les trois plus fortes économies potentielles"); top_title.setStyleSheet("font-weight:700;font-size:11pt;color:#333333;"); layout.addWidget(top_title)
        top_note=QLabel("Classées selon l'écart en pourcentage entre l'offre la plus basse et la plus élevée."); top_note.setStyleSheet("color:#6F6A64;"); top_note.setWordWrap(True); layout.addWidget(top_note)
        self.top_table=self._table(["Rang","Produit","Enseigne la moins chère","Prix minimum","Écart max./min."]); self.top_table.setMaximumHeight(175); layout.addWidget(self.top_table)

    def _table(self, headers):
        table=QTableWidget(0,len(headers)); table.setHorizontalHeaderLabels(headers); table.setAlternatingRowColors(True); table.setWordWrap(True); table.setTextElideMode(Qt.TextElideMode.ElideNone); table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded); table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers); table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows); table.verticalHeader().setVisible(False); table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents); table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents); table.horizontalHeader().setStretchLastSection(True); return table

    @staticmethod
    def money(value):
        return "—" if value is None else f"{value:,.0f}".replace(",", " ") + " FCFA"

    def fill_table(self, table, rows):
        table.setRowCount(len(rows))
        for r, values in enumerate(rows):
            for c, value in enumerate(values):
                item=QTableWidgetItem(str(value)); item.setToolTip(str(value)); item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | (Qt.AlignmentFlag.AlignLeft if c == 1 else Qt.AlignmentFlag.AlignCenter))
                if c == 0: item.setForeground(QColor("#6F6A64"))
                table.setItem(r,c,item)
        table.resizeRowsToContents()

    def show_error(self, message):
        QMessageBox.critical(self, "Erreur de chargement", message)

    def choose_folder(self):
        start=str(self.data_dir) if self.data_dir else ""
        path=QFileDialog.getExistingDirectory(self,"Choisir le dossier des données",start)
        if path:
            from pathlib import Path
            self.data_dir=Path(path)
            self.data_source.setText(f"Dossier choisi : {self.data_dir.name} · Cliquez sur « Lancer l’analyse » pour continuer.")

    def choose_export(self):
        from pathlib import Path
        export_dir=(self.data_dir.parent/"exports") if self.data_dir else Path.cwd()/"exports"
        export_dir.mkdir(parents=True,exist_ok=True)
        path,_=QFileDialog.getSaveFileName(self,"Exporter le comparatif",str(export_dir/"comparatif_prix.csv"),"CSV (*.csv)")
        return path
