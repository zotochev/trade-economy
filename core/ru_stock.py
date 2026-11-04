"""Российские акции для страницы «Отдельная акция»: цена и история — Мосбиржа (ISS), отчётность и дивиденды —
smart-lab.ru (разбор HTML-страниц). Мосбиржа — основной источник: без неё акции нет. Smart-lab — дополнительный:
если он не ответил или поменял вёрстку, страница работает без отчётности (`Stock.notes` объясняет, чего нет)."""
import re

import lxml.html
import numpy as np
import pandas as pd
import requests

from core import moex
from core.stock import Stock

SL = "https://smart-lab.ru/q"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) economy-model-lab"}

# колонка Stock.years → (поля smart-lab по порядку предпочтения, множитель); вторые поля — у банков
YEAR_FIELDS = {"Выручка": (["revenue", "net_operating_income"], 1e9), "Чистая прибыль": (["net_income"], 1e9),
               "EPS": (["eps"], 1), "Капитал": (["book_value", "capital"], 1e9), "Долг": (["debt"], 1e9),
               "FCF": (["fcf"], 1e9)}
YEAR_COLUMNS = ["Выручка", "Чистая прибыль", "EPS", "Капитал", "Долг", "FCF", "Оборотные активы",
                "Краткосрочные обязательства"]


def _num(text: str) -> float:
    t = text.replace("\xa0", "").replace(" ", "").replace("%", "").replace("₽", "").replace(",", ".").strip()
    try:
        return float(t)
    except ValueError:
        return np.nan


def _iss(path: str, **params) -> dict:
    """Запрос к Мосбирже с одним повтором: ISS иногда не отвечает за 20 секунд."""
    try:
        return moex._get(path, **params)
    except requests.RequestException:
        return moex._get(path, **params)


def _page(path: str) -> lxml.html.HtmlElement:
    r = requests.get(f"{SL}/{path}", headers=UA, timeout=20, allow_redirects=False)
    r.raise_for_status()
    if r.status_code != 200:
        raise ValueError(f"smart-lab перенаправил запрос ({r.status_code})")
    return lxml.html.fromstring(r.text)


def fundamentals(ticker: str) -> pd.DataFrame:
    """Годовая отчётность МСФО: строки — поля smart-lab (revenue, eps…), колонки — годы и LTM."""
    doc = _page(f"{ticker}/f/y/MSFO/")
    head = doc.xpath('//tr[contains(@class,"header_row")]')
    if not head:
        raise ValueError("на странице smart-lab нет таблицы отчётности")
    cells = lambda tr: [c for c in tr.xpath("./td") if "chartrow" not in (c.get("class") or "")]  # noqa: E731
    labels = [c.text_content().strip().split()[0] if c.text_content().strip() else "" for c in cells(head[0])]
    rows = {}
    for tr in doc.xpath("//tr[@field]"):
        vals = [_num(c.text_content()) for c in cells(tr)]
        rows[tr.get("field")] = dict(zip(labels, vals))
    df = pd.DataFrame(rows).T
    keep = [c for c in df.columns if re.fullmatch(r"\d{4}", c) or c == "LTM"]
    if not keep or "net_income" not in df.index:
        raise ValueError("таблица smart-lab не похожа на отчётность")
    return df[keep]


def dividends(ticker: str) -> pd.Series:
    """Выплаты на акцию по датам отсечки (только этот тикер, без привилегированных)."""
    doc = _page(f"{ticker}/dividend/")
    out = {}
    for tr in doc.xpath("//table[1]//tr"):
        td = [c.text_content().strip() for c in tr.xpath("./td")]
        if len(td) >= 5 and td[0].upper() == ticker:
            d = pd.to_datetime(td[2], format="%d.%m.%Y", errors="coerce")
            v = _num(td[4])
            if pd.notna(d) and np.isfinite(v):
                out[d] = out.get(d, 0) + v
    return pd.Series(out, dtype=float).sort_index()


def _prices(ticker: str, board: str) -> pd.Series:
    rows, start = [], 0
    while True:
        j = _iss(f"/engines/stock/markets/shares/boards/{board}/securities/{ticker}/candles", interval=24,
                      start=start, **{"from": "2010-01-01", "candles.columns": "begin,close"})
        data = j["candles"]["data"]
        if not data:
            break
        rows += data
        start += len(data)
    s = pd.Series({pd.Timestamp(b): c for b, c in rows}, dtype=float)
    return s.sort_index()


def share(ticker: str) -> dict | None:
    """Акция Мосбиржи по тикеру: название, режим торгов, цена, капитализация. None — такой акции нет."""
    q = ticker.strip().upper()
    rows = moex._rows(_iss("/securities", q=q, engine="stock", market="shares",
                                **{"securities.columns": "secid,shortname,name,primary_boardid"}), "securities")
    hit = [r for r in rows if str(r["secid"]).upper() == q]
    if not hit:
        return None
    r = hit[0]
    board = r["primary_boardid"] or "TQBR"
    md = moex._rows(_iss(f"/engines/stock/markets/shares/boards/{board}/securities/{q}",
                              **{"iss.only": "marketdata", "marketdata.columns": "LAST,LCURRENTPRICE,"
                                                                                 "ISSUECAPITALIZATION"}), "marketdata")
    m = md[0] if md else {}
    return {"secid": q, "board": board, "shortName": r["shortname"], "longName": r["name"],
            "price": m.get("LAST") or m.get("LCURRENTPRICE"), "cap": m.get("ISSUECAPITALIZATION")}


def fetch(ticker: str) -> Stock | None:
    """Stock в формате Yahoo-версии страницы. None — на Мосбирже нет такой акции."""
    sh = share(ticker)
    if sh is None:
        return None
    prices = _prices(sh["secid"], sh["board"])
    if prices.empty:
        raise ValueError(f"Мосбиржа не отдала историю цен «{ticker}»")
    price = sh["price"] or float(prices.iloc[-1])
    info = {"shortName": sh["shortName"], "longName": sh["longName"], "currency": "RUB", "currentPrice": price,
            "marketCap": sh["cap"], "exchange": "MOEX"}
    years = pd.DataFrame(columns=YEAR_COLUMNS, dtype=float)
    notes = []
    try:
        f = fundamentals(sh["secid"])
        yr = [c for c in f.columns if c != "LTM"]
        pick = lambda keys: next((k for k in keys if k in f.index and f.loc[k].notna().any()), None)  # noqa: E731
        years = pd.DataFrame({col: f.loc[k, yr] * mult if (k := pick(keys)) else np.nan
                              for col, (keys, mult) in YEAR_FIELDS.items()}).reindex(columns=YEAR_COLUMNS)
        years.index = pd.to_datetime([f"{y}-12-31" for y in yr])
        years = years[years[["Выручка", "Чистая прибыль"]].notna().any(axis=1)]
        last = "LTM" if "LTM" in f.columns and f["LTM"].notna().sum() > 5 else yr[-1]
        g = lambda k: float(f.loc[k, last]) if k in f.index and np.isfinite(f.loc[k, last]) else None  # noqa: E731
        bank = "revenue" not in f.index and "net_interest_income" in f.index
        eps, debt, book = g("eps"), g("debt"), g("book_value")
        bv = g("bv_share") or (price / g("p_b") if g("p_b") and g("p_b") > 0 else None)
        info |= {"trailingEps": eps, "bookValue": bv, "sector": "Financial Services" if bank else None,
                 "trailingPE": price / eps if eps and eps > 0 else None,
                 "priceToBook": price / bv if bv and bv > 0 else None,
                 "debtToEquity": debt / book * 100 if debt is not None and book and book > 0 else None,
                 "payoutRatio": (g("div_payout_ratio") or 0) / 100 if g("div_payout_ratio") is not None else None}
        if bank:
            notes.append("это банк: вместо выручки — операционный доход, проверки долга и денежного потока неприменимы")
    except Exception:
        notes.append("отчётность со smart-lab сейчас недоступна — проверки по отчётности пропущены. Цена и график "
                     "работают; попробуйте обновить страницу позже")
    try:
        div = dividends(sh["secid"])
        year_ago = div[div.index >= prices.index[-1] - pd.DateOffset(years=1)].sum()
        info["dividendYield"] = year_ago / price * 100 if price else None
    except Exception:
        div = pd.Series(dtype=float)
        notes.append("дивиденды со smart-lab сейчас недоступны — проверка «дивиденды без перерыва» не точна")
    return Stock(sh["secid"], info, years, div, prices, notes)
