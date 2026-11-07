import json
import logging
import re
import unicodedata
from dataclasses import replace
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

from models.entities import HistoryPoint, Offer, Product

STORES = ("Marché Lagune", "Baobab Shop", "Comptoir Ivoire")
LOG = logging.getLogger("comparateur")


def clean_text(value):
    value = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def match_key(value):
    """Normalise les variantes d'unités, de langue et de saisie du catalogue."""
    key = clean_text(value)
    key = re.sub(r"\b(\d{2,3})\s*gb\b", r"\1 go", key)
    key = re.sub(r"\b(\d+)\s*tb\b", r"\1 to", key)
    key = re.sub(r"\b(\d+(?:\s+\d+)?)\s*hp\b", r"\1 cv", key)
    aliases = {
        "samsun": "samsung", "fridge": "refrigerateur", "refrigerator": "refrigerateur",
        "frigo": "refrigerateur", "dd externe": "disque dur externe", "clim": "climatiseur",
        "blender": "mixeur", "electric kettle": "bouilloire electrique",
        "air conditioner": "climatiseur", "steam iron": "fer a repasser",
        "microwave": "micro ondes", "wireless mouse": "souris sans fil",
        "inch": "pouces", "inches": "pouces", "expansion": "",
    }
    for source, target in aliases.items():
        key = re.sub(rf"\b{re.escape(source)}\b", target, key)
    return re.sub(r"\s+", " ", key).strip()


def number(value):
    if value is None or str(value).strip() == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    raw = str(value).replace("\u202f", "").replace("\xa0", "").replace(" ", "")
    raw = re.sub(r"(?i)fcfa|xof|f cfa", "", raw).replace(",", ".")
    raw = re.sub(r"[^0-9.+-]", "", raw)
    try:
        return float(raw) if raw else None
    except ValueError:
        return None


class DataLoader:
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.catalog = {}
        self.catalog_by_name = {}
        self.offers = []
        self.history = []
        self.unmatched = []
        self.journal = []

    def note(self, message):
        self.journal.append(message)
        LOG.info(message)

    def load(self):
        self.catalog = self._load_catalog()
        self.catalog_by_name = {match_key(p.name): p for p in self.catalog.values()}
        self.offers = []
        self.unmatched = []
        self._load_lagune()
        self._load_baobab()
        self._load_comptoir()
        self._flag_extreme_prices()
        self.history = self._load_history()
        return self

    def _flag_extreme_prices(self):
        """Écarte les écarts manifestes de saisie entre offres du même produit."""
        by_product = {}
        for offer in self.offers:
            if offer.price > 0:
                by_product.setdefault(offer.product_id, []).append(offer)
        rejected = set()
        for pid, offers in by_product.items():
            distinct = {o.store: o.price for o in offers}
            if len(distinct) < 2:
                continue
            ordered = sorted(distinct.values())
            median = ordered[len(ordered)//2] if len(ordered) % 2 else (ordered[len(ordered)//2-1] + ordered[len(ordered)//2]) / 2
            for offer in offers:
                if offer.price > median * 3:
                    rejected.add(id(offer))
                    self.note(f"{offer.store} ligne {offer.source_row} : prix {offer.price:,.0f} FCFA supérieur à 3 fois la médiane des enseignes pour {pid}; offre écartée comme anomalie probable.".replace(",", " "))
        if rejected:
            self.offers = [replace(o, available=False, availability="Prix suspect — à vérifier") if id(o) in rejected else o for o in self.offers]

    def _required(self, name):
        path = self.data_dir / name
        if not path.exists():
            raise FileNotFoundError(f"Fichier requis introuvable : {path}")
        return path

    def _load_catalog(self):
        path = self._required("catalogue_reference.csv")
        result = {}
        frame = pd.read_csv(path, encoding="utf-8-sig", dtype=str, keep_default_na=False)
        for row in frame.to_dict(orient="records"):
            pid = (row.get("produit_id") or "").strip().upper()
            if not pid or pid in result:
                self.note(f"Catalogue : identifiant vide ou dupliqué ignoré ({pid or 'vide'}).")
                continue
            result[pid] = Product(pid, row.get("nom", "").strip(), row.get("categorie", "").strip(), row.get("marque", "").strip())
        self.note(f"Catalogue chargé : {len(result)} produits.")
        return result

    def _match(self, name, explicit_id=""):
        if explicit_id and explicit_id.strip().upper() in self.catalog:
            return explicit_id.strip().upper()
        key = match_key(name)
        if key in self.catalog_by_name:
            return self.catalog_by_name[key].product_id
        # Les noms source contiennent souvent capacité, marque ou ordre des mots différents.
        candidates = []
        tokens = set(key.split())
        for normalized, product in self.catalog_by_name.items():
            ptokens = set(normalized.split())
            overlap = len(tokens & ptokens)
            coverage = overlap / max(1, min(len(tokens), len(ptokens)))
            similarity = SequenceMatcher(None, key, normalized).ratio()
            score = 0.8 * coverage + 0.2 * similarity
            candidates.append((score, product.product_id))
        candidates.sort(reverse=True)
        if candidates and candidates[0][0] >= 0.65 and (len(candidates) == 1 or candidates[0][0] - candidates[1][0] >= 0.1):
            return candidates[0][1]
        return None

    def _add_offer(self, store, name, raw_price, available, availability, source, row, explicit_id=""):
        price = number(raw_price)
        pid = self._match(name, explicit_id)
        if not pid:
            self.unmatched.append({"enseigne": store, "article": str(name), "ligne": str(row)})
            self.note(f"{store} ligne {row} : rapprochement non fiable pour « {name} »; exclu des calculs.")
            return
        if price is None or price <= 0:
            self.note(f"{store} ligne {row} : prix absent ou invalide; offre conservée sans prix exploitable.")
        self.offers.append(Offer(pid, self.catalog[pid].name, store, price or 0, bool(available and price and price > 0), availability, source, str(row)))

    def _load_lagune(self):
        path = self._required("marche_lagune.csv")
        rows = pd.read_csv(path, sep=";", encoding="utf-8-sig", dtype=str, keep_default_na=False).to_dict(orient="records")
        for i, r in enumerate(rows, 2):
            name = r.get("designation", "")
            availability = (r.get("disponibilite") or "").strip()
            price = number(r.get("prix"))
            old = number(r.get("ancien_prix"))
            if old and price and old < price:
                self.note(f"Marché Lagune ligne {i} : ancien prix inférieur au prix actuel; ancien prix ignoré.")
            if not availability:
                self.note(f"Marché Lagune ligne {i} : disponibilité manquante; offre écartée.")
            self._add_offer(STORES[0], name, price, availability.casefold() != "rupture" and bool(availability), availability or "Inconnue", path.name, i)
        self.note(f"Marché Lagune : {len(rows)} lignes lues (CSV séparé par point-virgule).")

    def _load_baobab(self):
        path = self._required("baobab_shop.json")
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        items = data.get("items", [])
        for i, item in enumerate(items, 1):
            pricing = item.get("pricing") or {}
            currency = str(pricing.get("currency", data.get("currency", "XOF"))).upper()
            if currency not in ("XOF", "FCFA", "CFA"):
                self.note(f"Baobab Shop article {i} : devise {currency} non prise en charge; prix écarté.")
                amount = None
            else:
                amount = number(pricing.get("amount"))
                delivery = number(pricing.get("delivery_fee")) or 0
                amount = amount + delivery if amount is not None else None
            stock = number(item.get("stock")) or 0
            self._add_offer(STORES[1], item.get("title", ""), amount, stock > 0, f"Stock : {int(stock)}", path.name, i, item.get("sku", ""))
        self.note(f"Baobab Shop : {len(items)} articles lus (livraison ajoutée au prix).")

    def _load_comptoir(self):
        path = self._required("comptoir_ivoire.xlsx")
        workbook = load_workbook(path, read_only=True, data_only=True)
        sheet = workbook["Tarifs octobre 2026"] if "Tarifs octobre 2026" in workbook.sheetnames else workbook.active
        header_row = 3
        headers = [str(c or "").strip() for c in next(sheet.iter_rows(min_row=header_row, max_row=header_row, values_only=True))]
        normalized = [clean_text(h) for h in headers]
        def col(*terms):
            return next((i for i, h in enumerate(normalized) if all(t in h for t in terms)), None)
        ix = {"code": col("code"), "name": col("article"), "price": col("prix"), "discount": col("remise"), "stock": col("quantite")}
        if ix["name"] is None or ix["price"] is None:
            raise ValueError("En-têtes Excel introuvables à la ligne 3 (Article, Prix catalogue).")
        count = 0
        for row_no, row in enumerate(sheet.iter_rows(min_row=4, values_only=True), 4):
            if not row or not row[ix["name"]]:
                continue
            catalog_price = number(row[ix["price"]])
            discount = number(row[ix["discount"]]) if ix["discount"] is not None else 0
            stock = number(row[ix["stock"]]) if ix["stock"] is not None else 1
            price = catalog_price * (1 - (discount or 0) / 100) if catalog_price else None
            self._add_offer(STORES[2], row[ix["name"]], price, (stock or 0) > 0, f"Quantité : {int(stock or 0)}", path.name, row_no, str(row[ix["code"]] or "") if ix["code"] is not None else "")
            count += 1
        workbook.close()
        self.note(f"Comptoir Ivoire : {count} lignes lues; remise appliquée, retrait en boutique.")

    def _load_history(self):
        path = self._required("historique_prix.csv")
        result = []
        names = {clean_text(s): s for s in STORES}
        aliases = {"marche lagune": STORES[0], "baobab shop": STORES[1], "comptoir ivoire": STORES[2]}
        frame = pd.read_csv(path, encoding="utf-8-sig", dtype=str, keep_default_na=False)
        for row_no, row in enumerate(frame.to_dict(orient="records"), 2):
            store = aliases.get(clean_text(row.get("source", "")))
            price = number(row.get("prix_fcfa"))
            pid = str(row.get("produit_id", "")).strip().upper()
            date = str(row.get("date", "")).strip()
            if not store or pid not in self.catalog or price is None or price <= 0:
                self.note(f"Historique ligne {row_no} : source, produit ou prix invalide; ligne ignorée.")
                continue
            result.append(HistoryPoint(date, store, pid, price))
        self.note(f"Historique chargé : {len(result):,} lignes valides (indexation en mémoire).".replace(",", " "))
        return result
