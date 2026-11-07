"""Écrit les résultats intermédiaires produits par le nettoyage."""
from pathlib import Path

import pandas as pd


class OutputWriter:
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.cleaned_dir = self.project_dir / "donnees_nettoyees"
        self.logs_dir = self.project_dir / "logs"

    def write_cleaned_data(self, loader):
        self.cleaned_dir.mkdir(parents=True, exist_ok=True)

        offers = []
        for offer in loader.offers:
            product = loader.catalog[offer.product_id]
            offers.append({
                "produit_id": offer.product_id,
                "produit": offer.product_name,
                "categorie": product.category,
                "marque": product.brand,
                "enseigne": offer.store,
                "prix_fcfa": round(offer.price, 2) if offer.price else "",
                "prix_utilisable": offer.available,
                "disponibilite": offer.availability,
                "fichier_source": offer.source_name,
                "ligne_source": offer.source_row,
            })
        pd.DataFrame(offers, columns=[
            "produit_id", "produit", "categorie", "marque", "enseigne", "prix_fcfa",
            "prix_utilisable", "disponibilite", "fichier_source", "ligne_source",
        ]).to_csv(self.cleaned_dir / "offres_normalisees.csv", index=False, sep=";", encoding="utf-8-sig", decimal=",")

        history = [{
            "date": point.date,
            "source": point.store,
            "produit_id": point.product_id,
            "prix_fcfa": point.price,
        } for point in loader.history]
        pd.DataFrame(history, columns=["date", "source", "produit_id", "prix_fcfa"]).to_csv(
            self.cleaned_dir / "historique_nettoye.csv", index=False, sep=";", encoding="utf-8-sig", decimal=","
        )

    def write_journal(self, messages):
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        journal = list(messages) or ["Aucun problème détecté pendant le nettoyage."]
        pd.DataFrame({"numero": range(1, len(journal) + 1), "message": journal}).to_csv(
            self.logs_dir / "journal_nettoyage.csv", index=False, sep=";", encoding="utf-8-sig"
        )
        text = "JOURNAL DE NETTOYAGE\n" + "=" * 24 + "\n\n"
        text += "\n".join(f"{index}. {message}" for index, message in enumerate(journal, 1))
        (self.logs_dir / "journal_nettoyage.txt").write_text(text, encoding="utf-8")

