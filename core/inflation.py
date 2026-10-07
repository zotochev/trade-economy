"""Слой 6: инфляция — уровень и направление, устойчивая часть, товары и услуги, давление рынка труда.

Вывод слоя опирается не на одну меру, а на медиану нескольких мер устойчивой инфляции: каждая по-своему
отсекает разовые скачки цен отдельных товаров.
"""
from typing import Callable

import pandas as pd

from core.transforms import yoy_pct

TARGET = 2.0
NEAR = 0.5  # ± от цели — «около цели»
UNDERLYING = {  # мера → ключ ряда (уже в % г/г) или None, если считаем г/г из индекса
    "Базовая PCE": "PCEPILFE",
    "Усечённая средняя PCE": "PCETRIM12M159SFRBDAL",
    "Медианный CPI": "MEDCPIM158SFRBCLE",
    "«Липкие» базовые цены": "CORESTICKM159SFRBATL",
}


def core_pce(load: Callable[[str], pd.Series]) -> pd.Series:
    return yoy_pct(load("PCEPILFE")).dropna()


def three_month(load: Callable[[str], pd.Series], key: str = "PCEPILFE") -> pd.Series:
    """Темп за последние 3 месяца в годовом выражении — самое свежее направление."""
    p = load(key)
    return (((p / p.shift(3)) ** 4 - 1) * 100).dropna()


def underlying(load: Callable[[str], pd.Series]) -> dict[str, float]:
    """Последние значения мер устойчивой инфляции, % г/г."""
    out = {}
    for name, key in UNDERLYING.items():
        s = core_pce(load) if key == "PCEPILFE" else load(key).dropna()
        out[name] = float(s.iloc[-1])
    return out


def vu(load: Callable[[str], pd.Series]) -> pd.Series:
    """Напряжённость рынка труда: вакансий на одного безработного."""
    return (load("JTSJOL") / load("UNEMPLOY")).dropna()


def verdict(load: Callable[[str], pd.Series]) -> tuple[str, str, float]:
    """(вывод, цвет, медиана мер устойчивой инфляции)."""
    level = float(pd.Series(underlying(load)).median())
    yoy, recent = float(core_pce(load).iloc[-1]), float(three_month(load).iloc[-1])
    if level > TARGET + NEAR:
        head, color = "Инфляция выше цели ФРС", "orange"
    elif level < TARGET - NEAR:
        head, color = "Инфляция ниже цели ФРС", "blue"
    else:
        head, color = "Инфляция близка к цели ФРС", "green"
    if recent < yoy - 0.3:
        head += " и замедляется"
    elif recent > yoy + 0.3:
        head += " и ускоряется"
        color = "orange" if color == "green" else "red" if color == "orange" else color
    else:
        head += " и держится на месте"
    return head, color, level
