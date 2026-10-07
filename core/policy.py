"""Слой 2: стойкость политики ФРС — реальная ставка против нейтральной и правила Тейлора.

Формулы правил — как в Monetary Policy Report ФРС (2025):
  Тейлор (1993):      R = r* + π + 0.5·(π − 2) + 1·(u* − u)
  Сбалансированное:   R = r* + π + 0.5·(π − 2) + 2·(u* − u)
π — базовая инфляция PCE г/г, u — безработица, u* — естественная безработица (CBO), r* — нейтральная реальная ставка.
"""
from typing import Callable

import pandas as pd

from core.transforms import yoy_pct

RSTAR_BAND = 1.0  # ± п.п.: типичная неопределённость оценок r* (оценки разных моделей расходятся на 1–2 п.п.)


def frame(load: Callable[[str], pd.Series]) -> pd.DataFrame:
    """Месячная таблица: ставка, инфляция, безработица, r*, правила, реальная ставка и её отклонение от r*."""
    u = load("UNRATE")
    end = u.index[-1]  # NROU содержит прогноз CBO на годы вперёд — отрезаем будущее
    monthly = lambda s: s[:end].resample("MS").ffill().reindex(u.index, method="ffill")
    df = pd.concat({
        "ffr": load("DFF").resample("MS").mean(),
        "pi": yoy_pct(load("PCEPILFE")),
        "u": u,
        "u_star": monthly(load("NROU")),
        "r_star": monthly(load("rstar_hlw")),
    }, axis=1, sort=True).dropna()
    core = df["r_star"] + df["pi"] + 0.5 * (df["pi"] - 2)
    df["taylor"] = core + 1 * (df["u_star"] - df["u"])
    df["balanced"] = core + 2 * (df["u_star"] - df["u"])
    df["real"] = df["ffr"] - df["pi"]
    df["stance"] = df["real"] - df["r_star"]  # > 0 — ставка выше нейтральной, ФРС тормозит
    return df


def fomc_rstar(load: Callable[[str], pd.Series]) -> pd.Series:
    """Нейтральная реальная ставка по прогнозам самих членов FOMC: долгосрочная ставка − цель 2%."""
    return load("FEDTARMDLR") - 2


def verdict(stance: float) -> tuple[str, str]:
    """(вывод, цвет) по отклонению реальной ставки от нейтральной."""
    if stance > 1:
        return "ФРС тормозит экономику", "red"
    if stance > 0.25:
        return "ФРС слегка тормозит экономику", "orange"
    if stance < -1:
        return "ФРС разгоняет экономику", "green"
    if stance < -0.25:
        return "ФРС слегка разгоняет экономику", "blue"
    return "ФРС держит ставку около нейтральной", "gray"
