"""Математика облигации с фиксированным купоном (полугодовые выплаты, номинал 100)."""
from dataclasses import dataclass

import numpy as np

FREQ = 2  # выплат купона в год (казначейские США — раз в полгода)


@dataclass
class BondStats:
    price: float
    modified_duration: float   # % изменения цены на 1 п.п. доходности (со знаком минус)
    convexity: float


def cash_flows(coupon_pct: float, years: float) -> tuple[np.ndarray, np.ndarray]:
    n = max(int(round(years * FREQ)), 1)
    t = np.arange(1, n + 1) / FREQ
    cf = np.full(n, coupon_pct / FREQ)
    cf[-1] += 100
    return t, cf


def price(coupon_pct: float, years: float, yield_pct: float) -> float:
    t, cf = cash_flows(coupon_pct, years)
    y = yield_pct / 100 / FREQ
    return float(np.sum(cf / (1 + y) ** (t * FREQ)))


def stats(coupon_pct: float, years: float, yield_pct: float) -> BondStats:
    t, cf = cash_flows(coupon_pct, years)
    y = yield_pct / 100 / FREQ
    disc = (1 + y) ** (t * FREQ)
    pv = cf / disc
    p = float(pv.sum())
    macaulay = float((t * pv).sum() / p)
    modified = macaulay / (1 + y)
    k = t * FREQ
    convexity = float((pv * k * (k + 1)).sum() / (p * (1 + y) ** 2) / FREQ ** 2)
    return BondStats(p, modified, convexity)


def price_change_pct(coupon_pct: float, years: float, yield_pct: float, shock_pp: float) -> float:
    """Точное изменение цены (%) при сдвиге доходности на shock_pp процентных пунктов."""
    p0 = price(coupon_pct, years, yield_pct)
    p1 = price(coupon_pct, years, max(yield_pct + shock_pp, -0.99))
    return (p1 / p0 - 1) * 100
