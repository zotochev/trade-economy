"""Оценка рынка: CAPE → последующая доходность, премия акций над облигациями, модель Гордона.

Данные Шиллера: месячная цена S&P Composite (P), дивиденды за 12 мес. (D), CPI.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

BUCKETS = [0, 10, 15, 20, 25, 30, 1000]
BUCKET_LABELS = ["< 10", "10–15", "15–20", "20–25", "25–30", "> 30"]


def real_total_return_index(p: pd.Series, d: pd.Series, cpi: pd.Series) -> pd.Series:
    """Индекс реальной полной доходности: цена + реинвестированные дивиденды, в ценах последнего месяца."""
    df = pd.concat({"p": p, "d": d, "cpi": cpi}, axis=1).sort_index()
    df["d"] = df["d"].ffill()            # последние месяцы дивиденды ещё не опубликованы
    df = df.dropna()
    nominal = (df["p"] + df["d"] / 12) / df["p"].shift(1)
    real = nominal * df["cpi"].shift(1) / df["cpi"]
    return real.fillna(1).cumprod()


def forward_return(index: pd.Series, years: int = 10) -> pd.Series:
    """Средняя годовая доходность за следующие N лет (%), для каждой даты, где она уже известна."""
    fwd = index.shift(-12 * years) / index
    return ((fwd ** (1 / years) - 1) * 100).dropna()


def cape_table(cape: pd.Series, fwd: pd.Series) -> pd.DataFrame:
    """Последующая 10-летняя реальная доходность по корзинам CAPE."""
    df = pd.concat({"cape": cape, "fwd": fwd}, axis=1).dropna()
    df["Корзина"] = pd.cut(df["cape"], BUCKETS, labels=BUCKET_LABELS, right=False)
    g = df.groupby("Корзина", observed=True)["fwd"]
    out = pd.DataFrame({"Медиана, % год.": g.median(), "Худший, % год.": g.min(), "Лучший, % год.": g.max(),
                        "Доля < 0, %": g.apply(lambda x: (x < 0).mean() * 100), "Месяцев": g.size()})
    return out.reindex(BUCKET_LABELS)


@dataclass
class Fit:
    a: float
    b: float
    resid_std: float

    def predict(self, cape: float) -> float:
        return self.a + self.b * np.log(1 / cape)


def fit(cape: pd.Series, fwd: pd.Series) -> Fit:
    """Линейная регрессия: доходность ~ a + b · ln(1/CAPE)."""
    df = pd.concat({"cape": cape, "fwd": fwd}, axis=1).dropna()
    x = np.log(1 / df["cape"].to_numpy())
    y = df["fwd"].to_numpy()
    b, a = np.polyfit(x, y, 1)
    resid = y - (a + b * x)
    return Fit(float(a), float(b), float(resid.std()))


def fair_pe(real_yield: float, premium: float, growth: float) -> float:
    """Модель Гордона в терминах прибыли: P/E = 1 / (r − g), r = реальная ставка + премия за риск.
    Предполагает, что вся прибыль в итоге достаётся акционерам (выплаты или выкуп по справедливой цене)."""
    r = real_yield + premium
    return 100 / (r - growth) if r > growth else float("inf")


def implied_premium(cape: float, real_yield: float, growth: float) -> float:
    """Какую премию за риск закладывает рынок при данном CAPE: 1/CAPE + g − реальная ставка."""
    return 100 / cape + growth - real_yield
