"""Слой 5: рост и риск рецессии — скорость, загрузка, рынок труда и ансамбль сигналов рецессии.

Ни один сигнал рецессии не надёжен сам по себе, поэтому смотрим несколько моделей разного типа:
совпадающие (рецессия уже идёт?) и опережающие (будет ли через год?), у каждой — свой порог и свои ошибки.
"""
from dataclasses import dataclass
from typing import Callable

import pandas as pd

from core.transforms import yoy_pct


@dataclass(frozen=True)
class Signal:
    name: str
    timing: str        # «совпадающий» | «опережающий»
    units: str
    threshold: float
    above: bool        # тревога, когда значение выше порога (иначе — ниже)
    failure: str       # когда сигнал ошибался


SIGNALS = {
    "RECPROUSM156N": Signal("Модель Шове–Пигера", "совпадающий", "%", 50, True,
                            "ложных тревог не было, но в 1973 и 2001 гг. не поднялась выше 50%"),
    "SAHMREALTIME": Signal("Правило Сама", "совпадающий", "п.п.", 0.5, True,
                           "ложно сработало в 1976 и 2024 гг. (в 2024 — приток рабочей силы)"),
    "CFNAI3": Signal("Индекс активности CFNAI, 3 мес.", "совпадающий", "ст. откл.", -0.7, False,
                     "шумный: краткие провалы бывали и без рецессии"),
    "curve_prob": Signal("Кривая доходности (ФРБ Нью-Йорка)", "опережающий", "%", 30, True,
                         "ложная тревога 2022–2024: до 71% без рецессии"),
    "ebp_prob": Signal("Кредитный рынок (ФРС, EBP)", "опережающий", "%", 30, True,
                       "ложные тревоги 2011 и 2015–2016 гг."),
    "PERMIT_YOY": Signal("Разрешения на строительство, г/г", "опережающий", "%", -20, False,
                         "в 2022–2023 гг. упали на 26% без рецессии"),
}


def signal_series(load: Callable[[str], pd.Series]) -> dict[str, pd.Series]:
    """Ряды сигналов рецессии в тех единицах, в которых заданы пороги."""
    out = {k: load(k) for k in ("RECPROUSM156N", "SAHMREALTIME", "curve_prob", "ebp_prob")}
    out["CFNAI3"] = load("CFNAI").rolling(3).mean()
    out["PERMIT_YOY"] = yoy_pct(load("PERMIT"))
    return {k: s.dropna() for k, s in out.items()}


def triggered(key: str, value: float) -> bool:
    s = SIGNALS[key]
    return value >= s.threshold if s.above else value <= s.threshold


def risk_table(load: Callable[[str], pd.Series]) -> pd.DataFrame:
    rows = []
    for key, s in signal_series(load).items():
        sig, v = SIGNALS[key], float(s.iloc[-1])
        rows.append({"Сигнал": sig.name, "Тип": sig.timing, "Сейчас": f"{v:+.2f} {sig.units}",
                     "Порог": f"{'≥' if sig.above else '≤'} {sig.threshold:g} {sig.units}",
                     "Тревога": "🔴 да" if triggered(key, v) else "🟢 нет", "Данные за": f"{s.index[-1]:%m.%Y}",
                     "Когда ошибался": sig.failure})
    return pd.DataFrame(rows)


def gdp_growth(load: Callable[[str], pd.Series]) -> pd.Series:
    """Рост реального ВВП за год, %."""
    g = load("GDPC1")
    return (g / g.shift(4) - 1) * 100


def cbo_gap(load: Callable[[str], pd.Series]) -> pd.Series:
    """Разрыв выпуска по CBO: ВВП к потенциальному, % (прогнозные кварталы CBO отрезаются)."""
    g = load("GDPC1")
    return ((g / load("GDPPOT").reindex(g.index) - 1) * 100).dropna()


def verdict(load: Callable[[str], pd.Series]) -> tuple[str, str]:
    """(вывод, цвет): есть ли спад и с какой скоростью растёт экономика относительно потенциала."""
    sig = {k: float(s.iloc[-1]) for k, s in signal_series(load).items()}
    coincident = [k for k, v in sig.items() if SIGNALS[k].timing == "совпадающий" and triggered(k, v)]
    leading = [k for k, v in sig.items() if SIGNALS[k].timing == "опережающий" and triggered(k, v)]
    if coincident:
        return "Похоже, экономика уже входит в спад", "red"
    if len(leading) >= 2:
        return "Экономика растёт, но опережающие сигналы предупреждают о спаде", "orange"
    now = float(load("GDPNOW").iloc[-1])
    trend = float(load("trend_g_hlw").iloc[-1])
    tail = "; одиночный опережающий сигнал тревоги" if leading else "; признаков спада нет"
    if now > trend + 0.5:
        return "Экономика растёт быстрее своего потенциала" + tail, "green"
    if now < trend - 1:
        return "Рост замедлился ниже потенциала" + tail, "orange"
    return "Экономика растёт около своего потенциала" + tail, "green"
