import logging
from pathlib import Path

import pandas as pd
from services.analysis_service import AnalysisService, BASKET
from services.data_loader import DataLoader, STORES
from services.output_writer import OutputWriter


class MainController:
    def __init__(self, view):
        self.view=view
        self.loader=None
        self.analysis=None
        self.view.data_dir=Path(__file__).resolve().parents[1]/"Data"
        self.view.data_source.setText(f"Source de données : dossier {self.view.data_dir.name}")
        self.view.export_button.setEnabled(False)
        self.view.browse_button.clicked.connect(self.view.choose_folder)
        self.view.refresh_button.clicked.connect(self.load_data)
        self.view.export_button.clicked.connect(self.export_csv)

    def load_data(self):
        data_dir=self.view.data_dir or Path(__file__).resolve().parents[1]/"Data"
        self.view.data_dir=data_dir
        self.view.data_source.setText(f"Chargement depuis le dossier : {data_dir.name}")
        try:
            project_dir=data_dir.parent
            logs_dir=project_dir/"logs"
            logs_dir.mkdir(parents=True,exist_ok=True)
            logging.basicConfig(filename=logs_dir/"nettoyage.log",level=logging.INFO,encoding="utf-8",format="%(asctime)s | %(levelname)s | %(message)s")
            self.loader=DataLoader(data_dir).load()
            writer=OutputWriter(project_dir)
            writer.write_cleaned_data(self.loader)
            writer.write_journal(self.loader.journal)
            self.analysis=AnalysisService(self.loader).run()
            self.render()
        except Exception as exc:
            self.view.status.setText("Les données n'ont pas pu être chargées.")
            self.view.show_error(f"{exc}\n\nVérifiez le dossier Data et les noms/colonnes des fichiers.")

    def render(self):
        a=self.analysis; l=self.loader
        wins, averages, top=a.summary()
        cards=[("Produits de référence",str(len(l.catalog))), ("Offres lues",str(len(l.offers))), ("Produits comparables",str(len(a.comparisons))), ("Temps index + comparatif",f"{a.elapsed_seconds*1000:.2f} ms")]
        while self.view.cards.count():
            item=self.view.cards.takeAt(0); widget=item.widget()
            if widget: widget.deleteLater()
        from PyQt6.QtWidgets import QFrame,QVBoxLayout,QLabel
        for i,(label,value) in enumerate(cards):
            card=QFrame(); card.setStyleSheet("QFrame{background:white;border:1px solid #e9e7e3;border-radius:10px;}")
            box=QVBoxLayout(card); lab=QLabel(label); lab.setStyleSheet("color:#817467;"); val=QLabel(value); val.setStyleSheet("font-size:21pt;font-weight:700;color:#ed7d22;"); box.addWidget(lab); box.addWidget(val)
            self.view.cards.addWidget(card,0,i)
        comparison_rows=[]
        for row in a.comparisons:
            prices=[self.view.money(row.prices.get(s)) if s in row.prices else "—" for s in STORES]
            values=[row.product_id,row.product_name,*prices,row.cheapest_store,self.view.money(row.spread_fcfa),f"{row.spread_percent:.1f} %"]
            comparison_rows.append((l.catalog[row.product_id].category,values))
        self.view.set_comparison_rows(comparison_rows)
        self.view.export_button.setEnabled(True)
        self.view.fill_table(self.view.top_table,[[i+1,r.product_name,self.view.money(r.cheapest_price),f"{self.view.money(r.spread_fcfa)} ({r.spread_percent:.1f} %)"] for i,r in enumerate(top)])
        basket, best, items=a.basket(); basket_rows=[]
        for pid,qty in BASKET.items():
            p=l.catalog.get(pid); costs=[]
            for store in STORES:
                offers=[o for o in l.offers if o.product_id==pid and o.store==store and o.available and o.price>0]
                costs.append(self.view.money(min((o.price for o in offers),default=None)))
            chosen=next((f"{s} · {self.view.money(price)}" for item,quantity,s,price in items if item==pid),"Indisponible")
            basket_rows.append([p.name if p else pid,qty,*costs,chosen])
        self.view.fill_table(self.view.basket_table,basket_rows)
        summary_rows=[]
        for store in STORES:
            info=basket[store]
            if info["missing"]:
                missing_names=[l.catalog[pid].name for pid in info["missing"]]
                summary_rows.append([store,"—","Incomplet · "+", ".join(missing_names)])
            else:
                summary_rows.append([store,self.view.money(info["total"]),"Complet"])
        self.view.fill_table(self.view.basket_summary_table,summary_rows)
        unavailable=[pid for pid,qty,store,price in items if store=="Indisponible"]
        best_label="Panier optimisé : " if not unavailable else "Panier optimisé (partiel) : "
        if unavailable:
            best_label += self.view.money(best)+" · manquant : "+", ".join(l.catalog[pid].name for pid in unavailable)
        else:
            best_label += self.view.money(best)
        self.view.basket_total.setText(best_label)
        h=a.history_summary(); hist_rows=[]
        for store in STORES:
            item=h[store]; pct="—" if item["difference_pct"] is None else f"{item['difference_pct']:+.2f} %"
            hist_rows.append([store,self.view.money(item["annual"]),self.view.money(item["black_friday"]),pct,item["rows"],item["bf_rows"]])
        self.view.fill_table(self.view.history_table,hist_rows)
        self.view.journal.setPlainText("\n".join(f"• {line}" for line in l.journal) or "Aucun problème détecté.")
        if l.unmatched:
            self.view.journal.append(f"\nRapprochements à vérifier : {len(l.unmatched)}. Ces lignes sont exclues des comparaisons.")
        leaders=", ".join(f"{s} ({wins[s]} produits)" for s in STORES)
        gap_text=", ".join(f"{s} : {averages[s]:.1f} %" if averages[s] is not None else f"{s} : aucune donnée" for s in STORES)
        self.view.insight.setText(f"Prix minimum observé le plus souvent : {leaders}.\nÉcart moyen au prix le plus bas, parmi les produits comparables : {gap_text}.\nLe prix de Baobab inclut la livraison; celui du Comptoir tient compte de la remise. La disponibilité est appliquée avant de choisir le moins cher.")
        self.view.status.setText(f"Analyse terminée · {len(l.history):,} lignes d'historique · {len(l.unmatched)} rapprochement(s) à vérifier · fichiers nettoyés enregistrés.".replace(","," "))

    def export_csv(self):
        if not self.analysis:
            self.view.show_error("Chargez les données avant d'exporter."); return
        path=self.view.choose_export()
        if not path: return
        columns=["produit_id","produit","marche_lagune_fcfa","baobab_shop_fcfa","comptoir_ivoire_fcfa","enseigne_moins_chere","prix_min_fcfa","ecart_fcfa","ecart_pct"]
        records=[]
        for row in self.analysis.comparisons:
            records.append({"produit_id":row.product_id,"produit":row.product_name,
                            "marche_lagune_fcfa":row.prices.get(STORES[0]),
                            "baobab_shop_fcfa":row.prices.get(STORES[1]),
                            "comptoir_ivoire_fcfa":row.prices.get(STORES[2]),
                            "enseigne_moins_chere":row.cheapest_store,"prix_min_fcfa":row.cheapest_price,
                            "ecart_fcfa":row.spread_fcfa,"ecart_pct":round(row.spread_percent,2)})
        pd.DataFrame(records,columns=columns).to_csv(path,index=False,sep=";",encoding="utf-8-sig",decimal=",")
        self.view.status.setText(f"Comparatif exporté : {path}")
