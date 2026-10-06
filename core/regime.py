"""Режим экономики: рост × инфляция, каждая ось — ускоряется или замедляется.

Каждая ось — голосование нескольких рядов (Далио: один ряд шумный). Для каждого
ряда считаем «импульс» годового темпа, нормируем (z-оценка), усредняем по
доступным рядам; знак среднего = направление оси.

Два способа считать импульс (открытый вопрос плана, сравниваются на экране):
  accel — ускорение: годовой темп сейчас минус 6 мес. назад;
  trend — отклонение годового темпа от его средней за 3 года.

Лаг публикации: данные за месяц m выходят в середине месяца m+1. Значит режим,
посчитанный по месяцу m, можно использовать для сделки в конце m+1, и он
«отвечает» за доходность месяца m+2 — сдвиг на 2 месяца, без заглядывания вперёд.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from core.transforms import yoy_pct  # noqa: F401 (используется и страницей режима)

GROWTH = {"INDPRO": "Промпроизводство", "PAYEMS": "Занятость", "RETAIL_REAL": "Реальные розничные продажи"}
INFLATION = {"CPIAUCSL": "CPI", "CPILFESL": "Базовый CPI", "PCEPILFE": "Базовый PCE"}

REGIMES = ["Восстановление", "Перегрев", "Стагфляция", "Замедление"]
QUADRANTS = {
    (True, False): "Восстановление",
    (True, True): "Перегрев",
    (False, True): "Стагфляция",
    (False, False): "Замедление",
}
# Только определения. Что в каком режиме выигрывало — считается по данным (stats_by_regime),
# а не берётся из учебника: на истории США учебная схема подтверждается не везде.
DESCRIPTIONS = {
    "Восстановление": "рост ускоряется, инфляция замедляется",
    "Перегрев": "рост и инфляция ускоряются",
    "Стагфляция": "рост замедляется, инфляция ускоряется",
    "Замедление": "рост и инфляция замедляются",
}
METHODS = {"trend": "Отклонение от средней", "accel": "Ускорение"}
METHOD_HELP = {"trend": "годовой темп минус его средняя за 3 года", "accel": "годовой темп сейчас минус 6 мес. назад"}
PUBLICATION_LAG = 2  # месяца, см. docstring
DEFAULT_METHOD = "trend"  # устойчивее и сильнее разделяет доходность — см. method_quality


def _monthly(s: pd.Series) -> pd.Series:
    return s.resample("MS").mean().dropna()


def _impulse(yoy: pd.Series, method: str) -> pd.Series:
    if method == "accel":
        return (yoy - yoy.shift(6)).dropna()
    return (yoy - yoy.rolling(36).mean()).dropna()


def _series(load, key: str) -> pd.Series:
    if key == "RETAIL_REAL":  # розничные продажи номинальные — убираем инфляцию
        return (_monthly(load("RSAFS")) / _monthly(load("CPIAUCSL"))).dropna()
    return _monthly(load(key))


@dataclass
class Axis:
    composite: pd.Series          # среднее z-импульсов (знак = направление)
    components: pd.DataFrame      # z-импульс каждого ряда
    yoy: pd.DataFrame             # годовые темпы рядов, %


def axis(load, keys: dict[str, str], method: str) -> Axis:
    yoys, zs = {}, {}
    for key, name in keys.items():
        y = yoy_pct(_series(load, key)).dropna()
        imp = _impulse(y, method)
        yoys[name] = y
        zs[name] = imp / imp.std()
    z = pd.DataFrame(zs)
    return Axis(z.mean(axis=1, skipna=True).dropna(), z, pd.DataFrame(yoys))


@dataclass
class History:
    method: str
    growth: Axis
    inflation: Axis
    regime: pd.Series             # название режима по месяцам (дата = месяц данных)


def history(load, method: str = DEFAULT_METHOD) -> History:
    g = axis(load, GROWTH, method)
    i = axis(load, INFLATION, method)
    df = pd.concat({"g": g.composite, "i": i.composite}, axis=1).dropna()
    reg = pd.Series([QUADRANTS[(bool(a > 0), bool(b > 0))] for a, b in zip(df["g"], df["i"])], index=df.index)
    return History(method, g, i, reg)


# ---------- текущий режим (для шапки панели) ----------

@dataclass
class Regime:
    name: str
    description: str
    growth_up: bool
    inflation_up: bool
    as_of: pd.Timestamp
    months: int                   # сколько месяцев подряд держится режим


def current(load, method: str = DEFAULT_METHOD) -> Regime:
    h = history(load, method)
    name = h.regime.iloc[-1]
    runs = (h.regime != h.regime.shift()).cumsum()
    months = int((runs == runs.iloc[-1]).sum())
    g_up = h.growth.composite[: h.regime.index[-1]].iloc[-1] > 0
    i_up = h.inflation.composite[: h.regime.index[-1]].iloc[-1] > 0
    return Regime(name, DESCRIPTIONS[name], bool(g_up), bool(i_up), h.regime.index[-1], months)


# ---------- доходности активов по режимам ----------

def monthly_returns(prices: pd.Series) -> pd.Series:
    """Доходность за месяц по ценам на конец месяца; индекс — первое число месяца."""
    m = prices.resample("ME").last().pct_change().dropna() * 100
    m.index = m.index.to_period("M").to_timestamp()
    return m


def treasury10_returns(load) -> pd.Series:
    """Оценка месячной доходности 10-летних гособлигаций по доходности (история с 1962 г.):
    купонный доход за месяц − дюрация × изменение доходности."""
    y = load("DGS10").resample("ME").last().dropna()
    duration = 7.5
    r = (y.shift(1) / 12 - duration * y.diff()).dropna()
    r.index = r.index.to_period("M").to_timestamp()
    return r


def tradeable_regime(h: History, lag: int = PUBLICATION_LAG) -> pd.Series:
    """Режим, который был известен к началу каждого месяца доходности."""
    r = h.regime.copy()
    r.index = r.index + pd.DateOffset(months=lag)
    return r


def stats_by_regime(returns: dict[str, pd.Series], regime: pd.Series) -> pd.DataFrame:
    """Средняя доходность (% годовых), доля растущих месяцев и число месяцев по режимам."""
    rows = []
    for name, r in returns.items():
        df = pd.concat({"r": r, "reg": regime}, axis=1).dropna()
        for reg in REGIMES:
            x = df.loc[df["reg"] == reg, "r"].astype(float)
            rows.append({"Актив": name, "Режим": reg, "Годовых, %": x.mean() * 12 if len(x) else np.nan,
                         "Растущих месяцев, %": (x > 0).mean() * 100 if len(x) else np.nan,
                         "Месяцев": len(x), "С": df.index[0].year if len(df) else None})
    return pd.DataFrame(rows)


def method_quality(load, returns: pd.Series) -> pd.DataFrame:
    """Сравнение способов: насколько устойчивы режимы и насколько они разделяют доходность."""
    rows = []
    for m, label in METHODS.items():
        h = history(load, m)
        reg = h.regime["1970":]
        switches = int((reg != reg.shift()).sum()) - 1
        years = len(reg) / 12
        st = stats_by_regime({"x": returns}, tradeable_regime(h))
        spread = st["Годовых, %"].max() - st["Годовых, %"].min()
        rows.append({"Способ": label, "Смен в год": switches / years,
                     "Длина режима, мес.": len(reg) / max(switches + 1, 1),
                     "Разброс S&P, п.п.": spread})
    return pd.DataFrame(rows)


def leaders(stats: pd.DataFrame, regime_name: str, min_months: int = 24, n: int = 3) -> tuple[list, list]:
    """Лучшие и худшие активы в режиме по средней доходности (при достаточной истории)."""
    x = stats[(stats["Режим"] == regime_name) & (stats["Месяцев"] >= min_months)].sort_values("Годовых, %")
    best = list(zip(x["Актив"][::-1][:n], x["Годовых, %"][::-1][:n]))
    worst = list(zip(x["Актив"][:n], x["Годовых, %"][:n]))
    return best, worst
