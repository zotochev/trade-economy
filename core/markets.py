"""Слой 7: рынки — цена акций как тождество «прибыль × мультипликатор», мультипликатор — от реальной ставки
и премии за риск; связь акций с облигациями и золотом.

Тождество: цена = прибыль на акцию × P/E. По модели Гордона P/E ≈ 1 / (r − g), где r = реальная ставка
(слои 2–3) + премия за риск акций (слой 4), g — рост прибыли (слой 5). Обратная форма: ожидаемая реальная
доходность акций ≈ 1/CAPE, а премия над облигациями ≈ 1/CAPE − реальная доходность 10-летних TIPS.
"""
from typing import Callable

import numpy as np
import pandas as pd

from core.regime import monthly_returns, treasury10_returns

Load = Callable[[str], pd.Series]
HORIZONS = {"1 год": 1, "3 года": 3, "5 лет": 5, "10 лет": 10, "20 лет": 20}


def e10(load: Load) -> pd.Series:
    """Средняя прибыль за 10 лет в текущих долларах: цена / CAPE. Сглаживает провалы прибыли в рецессии."""
    return (load("P") / load("CAPE")).dropna()


def decompose(load: Load, years: int, end: pd.Timestamp | None = None) -> dict[str, float]:
    """Средняя годовая доходность S&P за N лет до end: рост средней прибыли за 10 лет + изменение CAPE + дивиденды.
    Цена = E10 × CAPE, поэтому первые два слагаемых в сумме точно дают рост цены."""
    df = pd.concat({"p": load("P"), "cape": load("CAPE"), "d": load("D")}, axis=1).sort_index()
    df["d"] = df["d"].ffill()
    df = df.dropna()
    end = df.index[-1] if end is None else df[:end].index[-1]
    start = df[:end - pd.DateOffset(years=years)].index[-1]
    a, b = df.loc[start], df.loc[end]
    span = (end - start).days / 365.25

    def ann(x: float) -> float:
        return (x ** (1 / span) - 1) * 100

    return {"Рост прибыли": ann((b["p"] / b["cape"]) / (a["p"] / a["cape"])),
            "Изменение мультипликатора": ann(b["cape"] / a["cape"]),
            "Дивиденды": float(df.loc[start:end, "d"].div(df.loc[start:end, "p"]).mean() * 100)}


def typical_swing(load: Load, years: int, since: str = "1950") -> dict[str, float]:
    """Насколько в типичном окне N лет (медиана модуля) двигают годовую доходность прибыль и мультипликатор, п.п."""
    df = pd.concat({"p": load("P"), "cape": load("CAPE")}, axis=1).dropna()[since:]
    n = 12 * years
    mult = (df["cape"] / df["cape"].shift(n)) ** (1 / years) - 1
    earn = ((df["p"] / df["cape"]) / (df["p"] / df["cape"]).shift(n)) ** (1 / years) - 1
    return {"Рост прибыли": float(earn.dropna().abs().median() * 100),
            "Изменение мультипликатора": float(mult.dropna().abs().median() * 100)}


def erp_tips(load: Load) -> pd.Series:
    """Премия акций над облигациями: 1/CAPE − реальная доходность 10-летних TIPS (с 2003 г.)."""
    return (100 / load("CAPE") - load("DFII10").resample("MS").mean()).dropna()


def erp_long(load: Load) -> pd.Series:
    """Та же премия с 1881 г.: вместо TIPS — 10-летняя ставка минус инфляция за прошлые 10 лет."""
    cpi = load("CPI")
    infl10 = ((cpi / cpi.shift(120)) ** (1 / 10) - 1) * 100
    return (100 / load("CAPE") - (load("Rate GS10") - infl10)).dropna()


def real_earnings_growth(load: Load) -> float:
    """Исторический рост 10-летней средней реальной прибыли S&P, % в год — g по умолчанию для модели Гордона."""
    cpi = load("CPI")
    e = (load("E") / cpi * cpi.iloc[-1]).dropna().rolling(120).mean().dropna()
    years = (e.index[-1] - e.index[0]).days / 365.25
    return float(((e.iloc[-1] / e.iloc[0]) ** (1 / years) - 1) * 100)


def buffett(load: Load) -> pd.Series:
    """Капитализация всех компаний США к ВВП, %."""
    return (load("BOGZ1LM893064105Q") / 1000 / load("GDP") * 100).dropna()


def profit_share(load: Load) -> pd.Series:
    """Прибыль корпораций до налогов к ВВП, %."""
    return (load("CP") / load("GDP") * 100).dropna()


def stock_bond_corr(load: Load, months: int = 36) -> pd.Series:
    """Скользящая корреляция месячных доходностей S&P 500 и 10-летних гособлигаций."""
    df = pd.concat({"s": monthly_returns(load("^GSPC")), "b": treasury10_returns(load)}, axis=1).dropna()
    return df["s"].rolling(months).corr(df["b"]).dropna()


def change_corr(a: pd.Series, b: pd.Series, start: str | None = None, end: str | None = None) -> float:
    """Корреляция изменений за 12 месяцев двух рядов (месячные средние)."""
    df = pd.concat({"a": a.resample("MS").mean(), "b": b.resample("MS").mean()}, axis=1).dropna()
    df = df.diff(12).dropna()[start:end]
    return float(df["a"].corr(df["b"])) if len(df) > 12 else float("nan")


def gold_change(load: Load) -> pd.Series:
    g = load("GC=F").resample("MS").mean()
    return (np.log(g / g.shift(12)) * 100).dropna()


def verdict(load: Load) -> tuple[str, str, float, float]:
    """(вывод, цвет, премия акций над TIPS в п.п., её перцентиль в истории с 1881 г.)."""
    erp = float(erp_tips(load).iloc[-1])
    hist = erp_long(load)
    pct = float((hist < erp).mean() * 100)
    spx = load("^GSPC")
    up = float(spx.iloc[-1]) > float(spx.rolling(200).mean().iloc[-1])
    if pct < 20:
        head, color = "Акции дороги: ожидаемая доходность почти не выше облигаций", "orange"
    elif pct > 60:
        head, color = "Акции недороги относительно облигаций", "green"
    else:
        head, color = "Акции оценены около нормы относительно облигаций", "gray"
    return head + (", тренд восходящий" if up else ", тренд нисходящий"), color, erp, pct
