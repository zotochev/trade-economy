"""Стакан и агрессоры вживую: глубина стакана Binance около цены, баланс агрессивных покупок и продаж за последние
часы и вынужденные заявки (ликвидации) против глубины. Публичные эндпоинты бирж, без ключей.

Историю глубины копит trade-news (снимки раз в 5 минут) — пока её нет, здесь только «сейчас».
"""
from typing import Callable

import pandas as pd
import requests

Load = Callable[[str], pd.Series]
VENUES = {"spot": ("https://api.binance.com/api/v3", 5000), "perp": ("https://fapi.binance.com/fapi/v1", 1000)}
BAND = 0.1  # ±% от середины: стакан бессрочного фьючерса Binance (limit=1000) покрывает только около ±0,15%


def depth(venue: str, symbol: str = "BTCUSDT", band: float = BAND) -> dict[str, float]:
    """Середина, спред и сумма заявок на покупку (bids) и продажу (asks) в $ в пределах ±band % от середины."""
    base, limit = VENUES[venue]
    d = requests.get(f"{base}/depth", params={"symbol": symbol, "limit": limit}, timeout=15).json()
    bids = [(float(p), float(q)) for p, q in d["bids"]]
    asks = [(float(p), float(q)) for p, q in d["asks"]]
    mid = (bids[0][0] + asks[0][0]) / 2
    lo, hi = mid * (1 - band / 100), mid * (1 + band / 100)
    return {"mid": mid, "spread": asks[0][0] - bids[0][0],
            "bids": sum(p * q for p, q in bids if p >= lo), "asks": sum(p * q for p, q in asks if p <= hi)}


def taker_share(venue: str, symbol: str = "BTCUSDT") -> dict[int, float]:
    """Доля агрессивных покупок в обороте за последние закрытые 1, 4 и 24 часа (часовые свечи), %."""
    base, _ = VENUES[venue]
    k = requests.get(f"{base}/klines", params={"symbol": symbol, "interval": "1h", "limit": 25},
                     timeout=15).json()[:-1]  # последний час ещё не закрыт — в нём несколько минут, это шум
    vol = [float(x[7]) for x in k]
    buy = [float(x[10]) for x in k]
    return {h: sum(buy[-h:]) / sum(vol[-h:]) * 100 for h in (1, 4, 24)}


def taker_norm(load: Load, venue: str) -> float:
    """Обычная доля агрессивных покупок — медиана дневных значений за прошлый год, %. На Binance она
    чуть ниже 50% и разная у спота и фьючерса, поэтому сравнивать надо с нормой, а не с половиной."""
    v, b = (load("BTC_QVOL"), load("BTC_TBUY")) if venue == "spot" else (load("BTCPERP_QVOL"), load("BTCPERP_TBUY"))
    share = (b / v * 100).dropna()
    return float(share[share.index[-1] - pd.Timedelta(days=365):].median())


def liquidations(live: dict | None, hours: int = 1) -> dict[str, float] | None:
    """Ликвидации за последние hours часов по данным trade-news: лонги (вынужденные продажи) и шорты (покупки), $."""
    if not live or live["liq"].empty:
        return None
    liq = live["liq"]
    w = liq[liq.index > liq.index.max() - pd.Timedelta(hours=hours)]
    return {"long": float(w.loc[w["side"] == "long", "usd"].sum()),
            "short": float(w.loc[w["side"] == "short", "usd"].sum())}
