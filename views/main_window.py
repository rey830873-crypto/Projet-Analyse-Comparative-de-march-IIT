from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QStackedWidget, QTableWidget, QTableWidgetItem, QTextEdit, QFileDialog,
                             QFrame, QGridLayout, QHeaderView, QMessageBox, QComboBox)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Comparateur de marché | Abidjan")
        self.resize(1250, 820)
        self.setMinimumSize(980, 680)
        self.setStyleSheet("""
            QMainWindow, QWidget { background:#f7f7f6; color:#302d29; font-family:'Segoe UI'; font-size:10pt; }
            QLabel#title { font-size:24pt; font-weight:700; color:#30271f; }
            QLabel#subtitle { color:#77716b; font-size:10.5pt; }
            QPushButton { background:#d77a32; color:white; border:0; border-radius:8px; padding:10px 16px; font-weight:600; }
            QPushButton:hover { background:#bd6828; }
            QPushButton#secondary { background:#eeeae5; color:#514940; }
            QFrame#sidebar { background:#ffffff; border:1px solid #e9e7e3; border-radius:14px; }
            QLabel#brand { color:#bd6b2f; font-size:14pt; font-weight:800; padding:12px 10px 18px; }
            QPushButton#nav { background:transparent; color:#625e59; text-align:left; border-radius:8px; padding:12px 13px; }
            QPushButton#nav:hover { background:#f6f3ef; color:#7b4f2b; }
            QPushButton#nav:checked { background:#f1ede8; color:#784c28; font-weight:700; }
            QStackedWidget { background:#ffffff; border:1px solid #e9e7e3; border-radius:14px; }
            QTableWidget { background:white; alternate-background-color:#faf9f8; gridline-color:#eceae7; border:0; selection-background-color:#f2e9df; }
            QHeaderView::section { background:#f2efeb; color:#514b44; padding:9px; border:0; font-weight:700; }
            QTextEdit, QComboBox { background:white; border:1px solid #e2ded9; border-radius:7px; padding:8px; }
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
        self.data_source.setStyleSheet("color:#77716b;padding:2px;")
        outer.addWidget(self.data_source)
        self.status = QLabel("Prêt. Choisissez le dossier si nécessaire, puis lancez l’analyse.")
        self.status.setStyleSheet("color:#687990; padding:3px;")
        outer.addWidget(self.status)
        body=QHBoxLayout(); body.setSpacing(14); outer.addLayout(body,1)
        sidebar=QFrame(); sidebar.setObjectName("sidebar"); sidebar.setFixedWidth(205)
        side_layout=QVBoxLayout(sidebar); side_layout.setContentsMargins(12,14,12,14); side_layout.setSpacing(5)
        brand=QLabel("●  COMPARATEUR"); brand.setObjectName("brand"); side_layout.addWidget(brand)
        section=QLabel("ESPACE D’ANALYSE"); section.setStyleSheet("color:#aa9a8a;font-size:8pt;font-weight:700;padding:8px 12px 4px;"); side_layout.addWidget(section)
        body.addWidget(sidebar)
        self.pages=QStackedWidget(); body.addWidget(self.pages,1)
        self.nav_buttons=[]
        self.dashboard = QWidget(); self._add_page(side_layout,"⌂   Vue d’ensemble",self.dashboard)
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
        self.basket_total=QLabel("Meilleur panier complet : —"); self.basket_total.setStyleSheet("font-size:14pt;font-weight:700;color:#80512e;padding:8px;"); bl.addWidget(self.basket_total)
        bl.addWidget(QLabel("Détail des articles")); bl.addWidget(self.basket_table,1); self._add_page(side_layout,"▣   Panier de rentrée",basket_page)
        self.history_table=self._table(["Enseigne","Moyenne annuelle","Semaine Black Friday","Écart BF / année","Lignes année","Lignes BF"])
        hist_page=QWidget(); hl=QVBoxLayout(hist_page); hl.setContentsMargins(20,20,20,20); hl.addWidget(self.history_table); note=QLabel("Période Black Friday : du 24 au 30 novembre 2025. L'historique utilise les prix affichés et exclut les données invalides."); note.setWordWrap(True); hl.addWidget(note); self._add_page(side_layout,"◷   Historique",hist_page)
        self.journal=QTextEdit(); self.journal.setReadOnly(True)
        log_page=QWidget(); ll=QVBoxLayout(log_page); ll.setContentsMargins(20,20,20,20); ll.addWidget(self.journal); self._add_page(side_layout,"☷   Journal de nettoyage",log_page)
        side_layout.addStretch()
        foot=QLabel("Projet pédagogique\nDonnées fictives · FCFA"); foot.setStyleSheet("color:#8a837c;font-size:8pt;padding:10px;"); side_layout.addWidget(foot)
        self.nav_buttons[0].setChecked(True)
        self._build_dashboard()

    def _add_page(self, layout, label, page):
        button=QPushButton(label); button.setObjectName("nav"); button.setCheckable(True); button.setAutoExclusive(True)
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
        self.insight=QLabel("Les données ne sont pas encore chargées. Cliquez sur « Lancer l’analyse » pour commencer."); self.insight.setWordWrap(True); self.insight.setStyleSheet("background:#f7f5f2;border-left:4px solid #d77a32;padding:16px;border-radius:5px;font-size:11pt;"); layout.addWidget(self.insight)
        self.top_table=self._table(["Rang","Produit","Prix minimum","Écart à comparer"]); layout.addWidget(QLabel("Les plus fortes économies potentielles")); layout.addWidget(self.top_table,1)

    def _table(self, headers):
        table=QTableWidget(0,len(headers)); table.setHorizontalHeaderLabels(headers); table.setAlternatingRowColors(True); table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers); table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows); table.verticalHeader().setVisible(False); table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents); table.horizontalHeader().setStretchLastSection(True); return table

    @staticmethod
    def money(value):
        return "—" if value is None else f"{value:,.0f}".replace(",", " ") + " FCFA"

    def fill_table(self, table, rows):
        table.setRowCount(len(rows))
        for r, values in enumerate(rows):
            for c, value in enumerate(values):
                item=QTableWidgetItem(str(value)); item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | (Qt.AlignmentFlag.AlignLeft if c == 1 else Qt.AlignmentFlag.AlignCenter))
                if c == 0: item.setForeground(QColor("#62718a"))
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
