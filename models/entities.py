from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Product:
    product_id: str
    name: str
    category: str
    brand: str


@dataclass(frozen=True)
class Offer:
    product_id: str
    product_name: str
    store: str
    price: float
    available: bool
    availability: str
    source_name: str
    source_row: str = ""


@dataclass(frozen=True)
class HistoryPoint:
    date: str
    store: str
    product_id: str
    price: float


@dataclass(frozen=True)
class Comparison:
    product_id: str
    product_name: str
    prices: dict
    cheapest_store: str
    cheapest_price: float
    spread_fcfa: float
    spread_percent: float
