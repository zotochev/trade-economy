"""Слой 1: структура и долг — потолок роста, нейтральная ставка r* и арифметика госдолга (r − g).

Долг к ВВП d меняется за год на (r − g) / (1 + g) · d + первичный дефицит. Пока средняя ставка по долгу r
ниже номинального роста g, экономика «перерастает» долг; когда выше — долг растёт сам по себе даже при
сбалансированном бюджете без учёта процентов.
"""
from dataclasses import dataclass
from typing import Callable

import pandas as pd

from core.transforms import yoy_pct

Load = Callable[[str], pd.Series]
ERAS = {"1948–1973": ("1948", "1973"), "1974–1994": ("1974", "1994"), "1995–2004": ("1995", "2004"),
        "2005–2019": ("2005", "2019"), "2020–н.в.": ("2020", None)}


def potential_growth(load: Load) -> pd.Series:
    """Рост потенциального ВВП по CBO, % г/г; без прогнозной части ряда."""
    pot = load("GDPPOT")
    return yoy_pct(pot[:pd.Timestamp.today()]).dropna()


def cbo_outlook(load: Load) -> float:
    """Средний рост потенциального ВВП на следующие 10 лет по прогнозу CBO, % в год."""
    pot = load("GDPPOT")
    now = pot[:pd.Timestamp.today()]
    years = (pot.index[-1] - now.index[-1]).days / 365.25
    return float(((pot.iloc[-1] / now.iloc[-1]) ** (1 / years) - 1) * 100)


def cagr(s: pd.Series, a: str, b: str | None) -> float:
    s = s[a:b].dropna()
    years = (s.index[-1] - s.index[0]).days / 365.25
    return float(((s.iloc[-1] / s.iloc[0]) ** (1 / years) - 1) * 100)


def sources(load: Load) -> pd.DataFrame:
    """Рост производительности и рабочей силы по эпохам, % в год. Их сумма ≈ потолок роста."""
    op, lf = load("OPHNFB"), load("CLF16OV").resample("QS").mean()
    return pd.DataFrame({e: {"Производительность": cagr(op, a, b), "Рабочая сила": cagr(lf, a, b)}
                         for e, (a, b) in ERAS.items()}).T


def rstar(load: Load) -> dict[str, pd.Series]:
    """Три оценки нейтральной реальной ставки: модель, прогноз ФРС, рынок."""
    fwd = ((10 * load("DFII10") - 5 * load("DFII5")) / 5).dropna()
    return {"Модель HLW (ФРБ Нью-Йорка)": load("rstar_hlw").dropna(),
            "Прогноз ФРС: долгосрочная ставка − 2%": (load("FEDTARMDLR") - 2).dropna(),
            "Рынок: реальная ставка через 5 лет на 5 лет": fwd.resample("MS").mean().dropna()}


def public_debt(load: Load) -> pd.Series:
    """Госдолг в руках публики, % ВВП (без долга одних госфондов другим)."""
    return load("FYGFGDQ188S").dropna()


def debt_rate(load: Load) -> pd.Series:
    """Средняя ставка по госдолгу: процентные расходы / долг в руках публики, %."""
    return (load("A091RC1Q027SBEA") / (public_debt(load) / 100 * load("GDP")) * 100).dropna()


def nominal_growth(load: Load, years: int = 5) -> pd.Series:
    """Средний рост номинального ВВП за N лет, % в год."""
    gdp = load("GDP")
    return (((gdp / gdp.shift(4 * years)) ** (1 / years) - 1) * 100).dropna()


@dataclass(frozen=True)
class Debt:
    d: float          # долг к ВВП, %
    r_avg: float      # средняя ставка по долгу
    r_new: float      # ставка по новым займам (10-летние)
    g: float          # долгосрочный номинальный рост: потенциал CBO + инфляционные ожидания
    primary: float    # первичное сальдо бюджета (без процентов), % ВВП; минус — дефицит

    def stabilizing(self, r: float) -> float:
        """Первичное сальдо, при котором долг к ВВП не меняется, % ВВП."""
        return (r - self.g) / (100 + self.g) * self.d

    def drift(self, r: float) -> float:
        """На сколько п.п. ВВП в год меняется долг при ставке r и нынешнем первичном сальдо."""
        return self.stabilizing(r) - self.primary


def debt_now(load: Load) -> Debt:
    balance, interest = load("FYFSGDA188S").dropna(), load("FYOIGDA188S").dropna()
    return Debt(d=float(public_debt(load).iloc[-1]), r_avg=float(debt_rate(load).iloc[-1]),
                r_new=float(load("DGS10").dropna().iloc[-1]),
                g=cbo_outlook(load) + float(load("T10YIE").dropna().iloc[-1]),
                primary=float(balance.iloc[-1] + interest.iloc[-1]))


def path(d0: float, r: float, g: float, primary: float, years: int = 10) -> list[float]:
    """Траектория долга к ВВП при постоянных r, g и первичном сальдо."""
    out = [d0]
    for _ in range(years):
        out.append(out[-1] * (1 + r / 100) / (1 + g / 100) - primary)
    return out


def verdict(load: Load) -> tuple[str, str, Debt]:
    """(вывод, цвет, арифметика долга)."""
    x = debt_now(load)
    if x.r_new < x.g:
        head, color = "Долг дешевле роста: экономика «перерастает» долг", "green"
    elif x.r_avg < x.g:
        head, color = "Долг пока дешевле роста, но новые займы уже дороже — нагрузка начнёт расти", "orange"
    else:
        head, color = "Долг дороже роста: нагрузка растёт сама по себе", "red"
    return head, color, x
