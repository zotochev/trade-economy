"""Стандартные преобразования рядов: уровень, годовой темп, годовое изменение, индекс."""
import pandas as pd

from core.series import LEVEL, YOY


def _year_ago(s: pd.Series) -> pd.Series:
    """Значение ряда год назад для каждой даты (ближайшее известное на ту дату)."""
    s = s.dropna()
    target = pd.DataFrame({"t": s.index - pd.DateOffset(years=1)})
    hist = pd.DataFrame({"t": s.index, "v": s.values})
    # Для каждой даты — последнее значение не позже, чем ровно год назад.
    # Через merge_asof, а не сдвиг индекса: 29.02 + 1 год даёт дубликат 28.02.
    v = pd.merge_asof(target, hist, on="t")["v"].to_numpy()
    first = s.index[0] + pd.DateOffset(years=1)
    return pd.Series(v, index=s.index).where(s.index >= first)


def yoy_pct(s: pd.Series) -> pd.Series:
    return (s / _year_ago(s) - 1) * 100


def yoy_diff(s: pd.Series) -> pd.Series:
    return s - _year_ago(s)


def rebase(s: pd.Series) -> pd.Series:
    s = s.dropna()
    return s / s.iloc[0] * 100


TRANSFORMS = {
    LEVEL: lambda s: s,
    YOY: yoy_pct,
    "Изменение г/г, разница": yoy_diff,
    "Индекс (начало периода = 100)": rebase,
}

