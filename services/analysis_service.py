from collections import defaultdict
from datetime import date
from time import perf_counter

from models.entities import Comparison
from services.data_loader import STORES

BASKET = {"P04": 1, "P12": 1, "P14": 2, "P15": 1, "P28": 1}
BLACK_FRIDAY_START = date(2025, 11, 24)
BLACK_FRIDAY_END = date(2025, 11, 30)


class AnalysisService:
    def __init__(self, loader):
        self.loader = loader
        self.comparisons = []
        self.history_index = defaultdict(list)
        self.elapsed_seconds = 0.0

    def run(self):
        start = perf_counter()
        self._index_history()
        self.comparisons = self._compare()
        self.elapsed_seconds = perf_counter() - start
        return self

    def _index_history(self):
        for point in self.loader.history:
            self.history_index[(point.store, point.product_id)].append(point)

    def _compare(self):
        grouped = defaultdict(dict)
        for offer in self.loader.offers:
            if offer.available and offer.price > 0:
                grouped[offer.product_id][offer.store] = min(offer.price, grouped[offer.product_id].get(offer.store, float("inf")))
        results = []
        for pid, prices in grouped.items():
            if len(prices) < 2:
                continue
            low, high = min(prices.values()), max(prices.values())
            winner = next(s for s in STORES if prices.get(s) == low)
            product = self.loader.catalog[pid]
            results.append(Comparison(pid, product.name, prices, winner, low, high - low, ((high-low)/low*100 if low else 0)))
        return sorted(results, key=lambda r: (-r.spread_percent, r.product_id))

    def summary(self):
        wins = {s: 0 for s in STORES}
        gaps = {s: [] for s in STORES}
        for row in self.comparisons:
            wins[row.cheapest_store] += 1
            for store, price in row.prices.items():
                gaps[store].append((price-row.cheapest_price)/row.cheapest_price*100 if row.cheapest_price else 0)
        averages = {s: (sum(gaps[s])/len(gaps[s]) if gaps[s] else None) for s in STORES}
        return wins, averages, self.comparisons[:3]

    def basket(self):
        rows = {s: {"total": 0.0, "missing": []} for s in STORES}
        best_total = 0.0
        best_items = []
        offers_by_pid = defaultdict(list)
        for o in self.loader.offers:
            if o.available and o.price > 0:
                offers_by_pid[o.product_id].append(o)
        for pid, quantity in BASKET.items():
            available = offers_by_pid.get(pid, [])
            for store in STORES:
                offers = [o for o in available if o.store == store]
                if offers:
                    rows[store]["total"] += min(o.price for o in offers)*quantity
                else:
                    rows[store]["missing"].append(pid)
            if available:
                best = min(available, key=lambda o: (o.price, STORES.index(o.store)))
                best_total += best.price*quantity
                best_items.append((pid, quantity, best.store, best.price))
            else:
                best_items.append((pid, quantity, "Indisponible", None))
        return rows, best_total, best_items

    def history_summary(self):
        grouped = defaultdict(list)
        # On récupère chaque série par sa clé (enseigne, produit) dans l'index.
        for store in STORES:
            for product_id in self.loader.catalog:
                grouped[store].extend(self.history_index.get((store, product_id), ()))
        result = {}
        for store in STORES:
            annual = grouped[store]
            bf = [p for p in annual if BLACK_FRIDAY_START <= date.fromisoformat(p.date) <= BLACK_FRIDAY_END]
            annual_avg = sum(p.price for p in annual)/len(annual) if annual else None
            bf_avg = sum(p.price for p in bf)/len(bf) if bf else None
            result[store] = {"annual": annual_avg, "black_friday": bf_avg,
                             "difference_pct": ((bf_avg-annual_avg)/annual_avg*100 if annual_avg and bf_avg is not None else None),
                             "rows": len(annual), "bf_rows": len(bf)}
        return result
