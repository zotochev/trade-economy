"""Сектора и факторы: относительная сила к рынку, соотношения-индикаторы."""
import pandas as pd

SECTORS = {"XLK": "Технологии", "XLF": "Финансы", "XLE": "Энергетика", "XLV": "Здравоохранение",
           "XLY": "Цикл. потребление", "XLP": "Товары первой необх.", "XLU": "Коммунальные",
           "XLI": "Промышленность", "XLB": "Материалы", "XLRE": "Недвижимость", "XLC": "Коммуникации"}
CYCLICAL = {"XLK", "XLF", "XLE", "XLY", "XLI", "XLB"}           # чувствительны к циклу
DEFENSIVE = {"XLV", "XLP", "XLU"}                                 # спрос почти не зависит от цикла
FACTORS = {"RSP": "S&P 500 равными долями", "IWM": "Малые компании", "IWD": "Стоимость", "IWF": "Рост"}
SNAPSHOT_TICKERS = list(SECTORS) + ["SPY"] + list(FACTORS)

# Соотношения-индикаторы: (числитель, знаменатель, название, что значит рост)
RATIOS = [
    ("XLY", "XLP", "Цикличные / защитные", "рынок ставит на рост экономики"),
    ("IWM", "SPY", "Малые / большие", "широкий рост, дешёвый кредит"),
    ("IWD", "IWF", "Стоимость / рост", "выигрывают дешёвые компании с прибылью сейчас"),
    ("RSP", "SPY", "Равные доли / обычный S&P", "рост широкий, а не за счёт нескольких гигантов"),
]


def change(s: pd.Series, months: int) -> float:
    past = s[:s.index[-1] - pd.DateOffset(months=months)]
    return float((s.iloc[-1] / past.iloc[-1] - 1) * 100) if len(past) else float("nan")


def relative(s: pd.Series, bench: pd.Series, months: int) -> float:
    """На сколько п.п. актив обогнал рынок за N месяцев."""
    a, b = change(s, months), change(bench, months)
    return ((1 + a / 100) / (1 + b / 100) - 1) * 100


def ratio(num: pd.Series, den: pd.Series) -> pd.Series:
    df = pd.concat({"n": num, "d": den}, axis=1).dropna()
    return df["n"] / df["d"]
