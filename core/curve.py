"""Слой 3: рыночные ставки и ожидания — разложение длинной ставки, якорь инфляционных ожиданий, кривая."""
from typing import Callable

import pandas as pd

MATURITIES = {"DGS1MO": 1 / 12, "DGS3MO": 0.25, "DGS6MO": 0.5, "DGS1": 1, "DGS2": 2, "DGS5": 5,
              "DGS7": 7, "DGS10": 10, "DGS20": 20, "DGS30": 30}
ANCHOR = (1.8, 2.7)  # 5y5y в этом коридоре — ожидания «заякорены» около цели ФРС 2%
TP_HIGH = 0.5        # премия за срок выше — длинные ставки заметно завышены доплатой за риск


def curve_at(load: Callable[[str], pd.Series], date: pd.Timestamp) -> pd.Series:
    """Кривая доходности на дату: индекс — срок в годах, значения — доходность, %."""
    return pd.Series({m: load(k)[:date].iloc[-1] for k, m in MATURITIES.items()}).sort_index()


def parts(load: Callable[[str], pd.Series]) -> pd.DataFrame:
    """Месячные средние: 10-летняя ставка в двух разложениях.
    Ожидания + премия за срок (Ким–Райт) и реальная ставка + инфляционная компенсация (TIPS)."""
    m = lambda k: load(k).resample("MS").mean()
    df = pd.concat({"y10": m("DGS10"), "tp": m("THREEFYTP10"), "real": m("DFII10"), "be": m("T10YIE")},
                   axis=1, sort=True)
    df["expected"] = df["y10"] - df["tp"]
    return df


def anchored(ff: float) -> bool:
    return ANCHOR[0] <= ff <= ANCHOR[1]


def verdict(tp: float, slope: float, ff: float) -> tuple[str, str]:
    """(вывод, цвет) слоя: что рынок облигаций говорит о ставках и инфляции."""
    if slope < 0:
        head, color = "Рынок ждёт снижения ставок: длинные ставки ниже коротких", "orange"
    elif tp > TP_HIGH:
        head, color = "Длинные ставки высоки из-за доплаты за риск, а не из-за ожиданий ставок", "orange"
    elif tp < 0:
        head, color = "Длинный долг дешёвый: инвесторы держат его почти без доплаты за риск", "blue"
    else:
        head, color = "Рынок ждёт ставки примерно на нынешнем уровне", "gray"
    if not anchored(ff):
        head += "; инфляционные ожидания расшатаны"
        color = "red"
    return head, color
