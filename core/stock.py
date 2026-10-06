"""Отдельная акция: данные Yahoo и проверки по Грэму, Баффету и Линчу.

Ограничение источника: годовая отчётность только за ~4 последних года (Грэм просил 10–20),
поэтому часть критериев проверяется в укороченном виде — это указано в тексте проверки.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import yfinance as yf

# Сектор Yahoo → секторный ETF из каталога
SECTOR_ETF = {"Technology": "XLK", "Financial Services": "XLF", "Energy": "XLE", "Healthcare": "XLV",
              "Consumer Cyclical": "XLY", "Consumer Defensive": "XLP", "Utilities": "XLU",
              "Industrials": "XLI", "Basic Materials": "XLB", "Real Estate": "XLRE",
              "Communication Services": "XLC"}
SECTOR_RU = {"Technology": "Технологии", "Financial Services": "Финансы", "Energy": "Энергетика",
             "Healthcare": "Здравоохранение", "Consumer Cyclical": "Циклическое потребление",
             "Consumer Defensive": "Товары первой необходимости", "Utilities": "Коммунальные услуги",
             "Industrials": "Промышленность", "Basic Materials": "Материалы", "Real Estate": "Недвижимость",
             "Communication Services": "Коммуникации"}
CYCLICAL_SECTORS = {"Energy", "Basic Materials", "Industrials", "Consumer Cyclical"}
FINANCIAL_SECTORS = {"Financial Services", "Real Estate"}


@dataclass
class Stock:
    ticker: str
    info: dict
    years: pd.DataFrame          # по годам: выручка, прибыль, EPS, капитал, долг, FCF, оборотные активы/обязательства
    dividends: pd.Series         # выплаты на акцию
    prices: pd.Series            # скорректированные цены закрытия


@dataclass
class Check:
    name: str
    ok: bool | None              # None — нет данных или критерий неприменим
    value: str
    rule: str


@dataclass
class Verdict:
    checks: list[Check] = field(default_factory=list)

    @property
    def score(self) -> tuple[int, int]:
        known = [c for c in self.checks if c.ok is not None]
        return int(sum(bool(c.ok) for c in known)), len(known)


def _row(df: pd.DataFrame, name: str) -> pd.Series:
    return df.loc[name] if name in df.index else pd.Series(dtype=float)


def fetch(ticker: str) -> Stock:
    t = yf.Ticker(ticker)
    info = t.info or {}
    if not info.get("shortName") and not info.get("longName"):
        raise ValueError(f"Yahoo не знает тикер «{ticker}»")
    inc, bs, cf = t.income_stmt, t.balance_sheet, t.cashflow
    years = pd.DataFrame({
        "Выручка": _row(inc, "Total Revenue"), "Чистая прибыль": _row(inc, "Net Income"),
        "EPS": _row(inc, "Diluted EPS"), "Капитал": _row(bs, "Stockholders Equity"),
        "Долг": _row(bs, "Total Debt"), "FCF": _row(cf, "Free Cash Flow"),
        "Оборотные активы": _row(bs, "Current Assets"), "Краткосрочные обязательства": _row(bs, "Current Liabilities"),
    })
    years.index = pd.to_datetime(years.index)
    years = years.sort_index().dropna(how="all")
    years = years[years[["Выручка", "Чистая прибыль"]].notna().any(axis=1)]
    prices = t.history(period="10y", auto_adjust=True)["Close"]
    prices.index = prices.index.tz_localize(None)
    dividends = t.dividends
    if len(dividends):
        dividends.index = dividends.index.tz_localize(None)
    return Stock(ticker.upper(), info, years, dividends, prices)


# ---------- вспомогательные расчёты ----------

def cagr(s: pd.Series) -> float | None:
    s = s.dropna()
    if len(s) < 2 or s.iloc[0] <= 0 or s.iloc[-1] <= 0:
        return None
    years = (s.index[-1] - s.index[0]).days / 365.25
    return ((s.iloc[-1] / s.iloc[0]) ** (1 / years) - 1) * 100 if years > 0 else None


def dividend_years(div: pd.Series) -> int:
    """Сколько последних календарных лет подряд были выплаты (текущий неполный год не считаем)."""
    if div.empty:
        return 0
    paid = set(div.index.year)
    year = pd.Timestamp.today().year - 1
    n = 0
    while year in paid:
        n += 1
        year -= 1
    return n


def graham_number(info: dict) -> float | None:
    eps, bv = info.get("trailingEps"), info.get("bookValue")
    if eps and bv and eps > 0 and bv > 0:
        return float(np.sqrt(22.5 * eps * bv))
    return None


def years_word(n: int) -> str:
    """1 год, 2 года, 5 лет."""
    if n % 10 == 1 and n % 100 != 11:
        return f"{n} год"
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return f"{n} года"
    return f"{n} лет"


def _fmt(v, suffix: str = "", digits: int = 1) -> str:
    return "нет данных" if v is None or (isinstance(v, float) and not np.isfinite(v)) else f"{v:,.{digits}f}{suffix}".replace(",", " ")


# ---------- Грэм: «защитный инвестор» (Разумный инвестор, гл. 14), адаптировано ----------

def graham(s: Stock) -> Verdict:
    i, y = s.info, s.years
    financial = i.get("sector") in FINANCIAL_SECTORS
    pe, pb = i.get("trailingPE"), i.get("priceToBook")
    cap = i.get("marketCap")
    cr = i.get("currentRatio")
    ni = y["Чистая прибыль"].dropna()
    eps = y["EPS"].dropna()
    div_n = dividend_years(s.dividends)
    gn = graham_number(i)
    price = i.get("currentPrice") or i.get("regularMarketPrice")
    v = Verdict([
        Check("Достаточный размер", None if cap is None else cap >= 2e9, _fmt(cap / 1e9 if cap else None, " млрд"),
              "капитализация от 2 млрд $ (у Грэма — крупная компания)"),
        Check("Прочное положение", None if financial or cr is None else cr >= 2, _fmt(cr, "", 2),
              "оборотные активы ≥ 2 × краткосрочных обязательств" + (" — для финансовых компаний неприменимо" if financial else "")),
        Check("Стабильная прибыль", None if ni.empty else bool((ni > 0).all()),
              f"в плюсе {(ni > 0).sum()} из {years_word(len(ni))}" if len(ni) else "нет данных",
              f"прибыль каждый год (Грэм — 10 лет, доступно {years_word(len(ni))})"),
        Check("Дивиденды без перерыва", div_n >= 20, f"{years_word(div_n)} подряд", "не меньше 20 лет подряд"),
        Check("Рост прибыли", None if len(eps) < 2 else bool(eps.iloc[-1] > eps.iloc[0]),
              f"EPS {_fmt(eps.iloc[0], '', 2)} → {_fmt(eps.iloc[-1], '', 2)}" if len(eps) >= 2 else "нет данных",
              f"EPS выше, чем в начале периода (Грэм — +33% за 10 лет, доступно {years_word(len(eps))})"),
        Check("Умеренный P/E", None if not pe else pe <= 15, _fmt(pe), "P/E не выше 15"),
        Check("Умеренная цена к капиталу", None if not (pe and pb) else (pb <= 1.5 or pe * pb <= 22.5),
              f"P/B {_fmt(pb, '', 2)}, P/E × P/B {_fmt(pe * pb if pe and pb else None)}",
              "P/B не выше 1.5 или P/E × P/B не выше 22.5"),
        Check("Цена ниже числа Грэма", None if not (gn and price) else price <= gn,
              f"цена {_fmt(price, '', 2)}, число Грэма {_fmt(gn, '', 2)}", "√(22.5 × EPS × балансовая стоимость на акцию)"),
    ])
    return v


# ---------- Баффет: качество бизнеса ----------

def buffett(s: Stock, ten_year: float | None) -> Verdict:
    i, y = s.info, s.years
    financial = i.get("sector") in FINANCIAL_SECTORS
    roe = (y["Чистая прибыль"] / y["Капитал"]).replace([np.inf, -np.inf], np.nan).dropna() * 100
    de = (y["Долг"] / y["Капитал"]).dropna()
    fcf = y["FCF"].dropna()
    margin = (y["Чистая прибыль"] / y["Выручка"]).dropna() * 100
    cap = i.get("marketCap")
    fcf_yield = fcf.iloc[-1] / cap * 100 if len(fcf) and cap else None
    return Verdict([
        Check("Высокая рентабельность капитала", None if roe.empty else bool(roe.mean() >= 15),
              f"ROE в среднем {_fmt(roe.mean() if len(roe) else None, '%')}", "ROE ≥ 15% в среднем за доступные годы"),
        Check("Умеренный долг", None if financial or de.empty else bool(de.iloc[-1] <= 0.5),
              _fmt(de.iloc[-1] if len(de) else None, "×", 2),
              "долг / капитал не выше 0.5" + (" — для банков неприменимо" if financial else "")),
        Check("Свободный денежный поток каждый год", None if financial or fcf.empty else bool((fcf > 0).all()),
              f"в плюсе {(fcf > 0).sum()} из {years_word(len(fcf))}" if len(fcf) else "нет данных",
              "бизнес сам генерирует деньги, а не потребляет их" + (" — у банков денежный поток включает движение "
                                                                    "депозитов, неприменимо" if financial else "")),
        Check("Высокая маржа (признак «рва»)", None if margin.empty else bool(margin.mean() >= 15),
              f"чистая маржа в среднем {_fmt(margin.mean() if len(margin) else None, '%')}",
              "≥ 15%: конкуренты не могут сбить цены"),
        Check("Доходность для владельца выше облигаций", None if financial or fcf_yield is None or ten_year is None
              else bool(fcf_yield >= ten_year), f"FCF / капитализация {_fmt(fcf_yield, '%', 2)} против 10 лет {_fmt(ten_year, '%', 2)}",
              "«доходы владельца» на вложенный доллар не ниже безрисковой ставки"),
    ])


# ---------- Линч: категория и PEG ----------

def lynch_category(s: Stock, growth: float | None) -> tuple[str, str]:
    i = s.info
    ni = s.years["Чистая прибыль"].dropna()
    pb = i.get("priceToBook")
    if i.get("sector") in CYCLICAL_SECTORS:
        return "Цикличная", "прибыль следует за экономикой; покупать при высоком P/E на дне цикла, продавать при низком на пике"
    if len(ni) and ni.iloc[-1] < 0:
        return "Восстанавливающаяся?", "убыток в последнем году: смотреть на долг и шансы пережить трудности"
    if pb is not None and 0 < pb < 1:
        return "Активная (asset play)?", "рынок оценивает компанию дешевле её балансовой стоимости"
    if growth is None:
        return "Не определить", "нет данных о росте прибыли"
    if growth >= 20:
        return "Быстрорастущая", "главное — продлится ли рост; риск — переплатить"
    if growth >= 10:
        return "Стабильная (stalwart)", "покупать на просадках, фиксировать +30–50%"
    return "Медленнорастущая", "покупают ради дивидендов"


def lynch(s: Stock) -> tuple[Verdict, tuple[str, str], float | None]:
    i = s.info
    growth = cagr(s.years["EPS"])
    pe = i.get("trailingPE")
    peg_own = pe / growth if pe and growth and growth > 0 else None
    peg_yahoo = i.get("trailingPegRatio")
    v = Verdict([
        Check("PEG по истории прибыли", None if peg_own is None else bool(peg_own <= 1),
              f"P/E {_fmt(pe)} / рост EPS {_fmt(growth, '% в год')} = {_fmt(peg_own, '', 2)}",
              "PEG ≤ 1 — дёшево для своего роста; 1–2 — нормально; > 2 — дорого"),
        Check("PEG по прогнозу (Yahoo)", None if not peg_yahoo else bool(peg_yahoo <= 1), _fmt(peg_yahoo, "", 2),
              "то же, но рост — по прогнозам аналитиков на 5 лет"),
        Check("Долг под контролем", None if i.get("debtToEquity") is None or i.get("sector") in FINANCIAL_SECTORS
              else i["debtToEquity"] <= 100, _fmt(i.get("debtToEquity"), "%"),
              "долг / капитал до 100%: Линч избегал компаний, которые могут не пережить спад"),
    ])
    return v, lynch_category(s, growth), growth


# ---------- макро-чувствительность ----------

def sensitivities(prices: pd.Series, market: pd.Series, ten_year: pd.Series, years: int = 5) -> dict:
    """Бета к рынку и реакция на ставки по месячным данным за N лет."""
    m = lambda s: s.resample("ME").last()  # noqa: E731
    df = pd.concat({"stock": m(prices).pct_change() * 100, "mkt": m(market).pct_change() * 100,
                    "dy": m(ten_year).diff()}, axis=1).dropna()
    df = df[df.index >= df.index[-1] - pd.DateOffset(years=years)]
    if len(df) < 24:
        return {}
    beta = np.polyfit(df["mkt"], df["stock"], 1)[0]
    rate = np.polyfit(df["dy"], df["stock"], 1)[0]
    rate_mkt = np.polyfit(df["dy"], df["mkt"], 1)[0]
    return {"beta": float(beta), "rate": float(rate), "rate_mkt": float(rate_mkt), "months": len(df)}
