"""Загрузка рядов из FRED, yfinance, данных Шиллера и CSV-файлов ФРС с дисковым кэшем.

Каждый ряд хранится в data_cache/<source>/<key>.csv (колонки date,value).
Ряд перекачивается, если файла нет или он старше MAX_AGE. При ошибке
загрузки старый файл не трогается.
"""
from __future__ import annotations

import io
import re
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import yfinance as yf

from core.series import BY_KEY, CATALOG

CACHE_DIR = Path(__file__).resolve().parent.parent / "data_cache"
MAX_AGE = 12 * 3600  # секунд
FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"
SHILLER_PAGE = "https://shillerdata.com/"
HEADERS = {"User-Agent": "Mozilla/5.0"}  # только для Шиллера: FRED с этим заголовком не отвечает
FED_NOTES = "https://www.federalreserve.gov/econres/notes/feds-notes/"
# Файл ФРС → {колонка: ключ ряда}. Каждый файл скачивается одним запросом.
FED_FILES = {
    FED_NOTES + "ebp_csv.csv": {"gz_spread": "gz_spread", "ebp": "ebp", "est_prob": "ebp_prob"},
    FED_NOTES + "fci_g_public_monthly_3yr.csv": {
        "FCI-G Index (baseline)": "FCIG", "FFR": "FCIG_FFR", "10Yr Treasury": "FCIG_10Y",
        "Mortgage Rate": "FCIG_MORT", "BBB": "FCIG_BBB", "Stock Market": "FCIG_STOCK",
        "House Prices": "FCIG_HOUSE", "Dollar": "FCIG_USD"},
}
FED_SCALE = {"ebp_prob": 100}  # вероятность в файле — доля, храним в %
HLW_URL = ("https://www.newyorkfed.org/medialibrary/media/research/economists/williams/data/"
           "Holston_Laubach_Williams_current_estimates.xlsx")
HLW_COLS = {2: "trend_g_hlw", 10: "rstar_hlw", 14: "gap_hlw"}  # колонки США на листе «HLW Estimates»
CURVE_PROB_URL = "https://www.newyorkfed.org/medialibrary/media/research/capital_markets/allmonth.xls"
GSCPI_URL = "https://www.newyorkfed.org/medialibrary/research/interactives/gscpi/downloads/gscpi_data.xlsx"
NY = ZoneInfo("America/New_York")
MARKET_CLOSE_HOUR = 17  # после 17:00 по Нью-Йорку дневной бар считаем закрытым


@dataclass
class UpdateResult:
    key: str
    ok: bool
    rows: int = 0
    error: str = ""


def _path(key: str) -> Path:
    src = BY_KEY[key].source
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", key)
    return CACHE_DIR / src / f"{safe}.csv"


def is_fresh(key: str) -> bool:
    p = _path(key)
    return p.exists() and time.time() - p.stat().st_mtime < MAX_AGE


def _save(key: str, s: pd.Series) -> UpdateResult:
    """Сохранить ряд; пустой ряд — ошибка, старый файл остаётся."""
    s = s.dropna()
    if s.empty:
        return UpdateResult(key, False, error="пустой ответ источника")
    p = _path(key)
    p.parent.mkdir(parents=True, exist_ok=True)
    s.rename("value").rename_axis("date").to_csv(p)
    return UpdateResult(key, True, len(s))


# ---------- источники ----------

def _fetch_fred(key: str) -> pd.Series:
    r = requests.get(FRED_URL.format(key), timeout=60)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text), index_col=0, parse_dates=True)
    return pd.to_numeric(df.iloc[:, 0], errors="coerce")


def _drop_unfinished_day(s: pd.Series) -> pd.Series:
    """yfinance отдаёт текущий день до закрытия торгов — такой бар не сохраняем."""
    now = datetime.now(NY)
    if len(s) and s.index[-1].date() >= now.date() and now.hour < MARKET_CLOSE_HOUR:
        return s.iloc[:-1]
    return s


def _fetch_yf(keys: list[str]) -> dict[str, pd.Series]:
    df = yf.download(keys, period="max", auto_adjust=True, progress=False,
                     group_by="column", threads=True)
    close = df["Close"]
    if isinstance(close, pd.Series):
        close = close.to_frame(keys[0])
    return {k: _drop_unfinished_day(close[k].dropna()) for k in keys if k in close}


def _fetch_shiller() -> pd.DataFrame:
    """Таблица Шиллера (ie_data.xls). Ссылка на файл содержит меняющийся id,
    поэтому каждый раз ищем её на странице shillerdata.com."""
    page = requests.get(SHILLER_PAGE, headers=HEADERS, timeout=30).text
    m = re.search(r'href="((?:https:)?//[^"]+/ie_data\.xls[^"]*)"', page)
    if not m:
        raise RuntimeError("ссылка на ie_data.xls не найдена на shillerdata.com")
    url = m.group(1) if m.group(1).startswith("http") else "https:" + m.group(1)
    raw = requests.get(url, headers=HEADERS, timeout=120).content
    df = pd.read_excel(io.BytesIO(raw), sheet_name="Data", header=7)
    df = df[pd.to_numeric(df["Date"], errors="coerce").notna()]
    # Дата записана числом: 2026.01 = январь, 2026.1 = октябрь
    d = df["Date"].astype(float)
    year = d.astype(int)
    month = ((d - year) * 100).round().astype(int)
    df.index = pd.to_datetime(dict(year=year, month=month, day=1))
    return df.apply(pd.to_numeric, errors="coerce")


def _fetch_fed(keys: list[str]) -> dict[str, pd.Series]:
    """CSV-файлы из заметок ФРС (FEDS Notes): качаем только файлы, где есть нужные ключи."""
    out = {}
    for url, cols in FED_FILES.items():
        if not set(cols.values()) & set(keys):
            continue
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        df = pd.read_csv(io.StringIO(r.text), index_col=0, parse_dates=True)
        for col, key in cols.items():
            out[key] = pd.to_numeric(df[col], errors="coerce") * FED_SCALE.get(key, 1)
    return out


def _fetch_nyfed(keys: list[str]) -> dict[str, pd.Series]:
    """Файлы ФРБ Нью-Йорка: оценки HLW (r*, трендовый рост, разрыв выпуска), вероятность рецессии по кривой
    и индекс давления в цепочках поставок (GSCPI)."""
    out = {}
    if set(HLW_COLS.values()) & set(keys):
        raw = requests.get(HLW_URL, timeout=60).content
        df = pd.read_excel(io.BytesIO(raw), sheet_name="HLW Estimates", header=None, skiprows=6)
        df.index = pd.to_datetime(df[0], errors="coerce")
        df = df[df.index.notna()]
        out |= {key: pd.to_numeric(df[col], errors="coerce") for col, key in HLW_COLS.items()}
    if "curve_prob" in keys:
        raw = requests.get(CURVE_PROB_URL, timeout=60).content
        df = pd.read_excel(io.BytesIO(raw), sheet_name="rec_prob")
        # В файле вероятность стоит на месяце, НА КОТОРЫЙ прогноз (+12 мес.). Переносим на месяц сигнала
        # и на первое число — как у остальных месячных рядов.
        date = pd.to_datetime(df["Date"]).dt.to_period("M").dt.to_timestamp() - pd.DateOffset(months=12)
        out["curve_prob"] = pd.Series(pd.to_numeric(df["Rec_prob"], errors="coerce").values * 100, index=date)
    if "GSCPI" in keys:
        raw = requests.get(GSCPI_URL, timeout=60).content
        df = pd.read_excel(io.BytesIO(raw), sheet_name="GSCPI Monthly Data", header=None, usecols=[0, 1])
        date = pd.to_datetime(df[0], format="%d-%b-%Y", errors="coerce")
        df = df[date.notna()]
        out["GSCPI"] = pd.Series(pd.to_numeric(df[1], errors="coerce").values,
                                 index=date[date.notna()].dt.to_period("M").dt.to_timestamp())
    return out


# ---------- публичный API ----------

def update(keys: list[str] | None = None, force: bool = False) -> list[UpdateResult]:
    """Докачать устаревшие ряды (или все переданные, если force)."""
    if keys is None:
        keys = [s.key for s in CATALOG]
    stale = [k for k in keys if force or not is_fresh(k)]
    by_src: dict[str, list[str]] = {}
    for k in stale:
        by_src.setdefault(BY_KEY[k].source, []).append(k)
    results: list[UpdateResult] = []

    def one_fred(k: str) -> UpdateResult:
        try:
            return _save(k, _fetch_fred(k))
        except Exception as e:  # сеть/формат — не роняем всё обновление
            return UpdateResult(k, False, error=str(e))

    with ThreadPoolExecutor(max_workers=6) as ex:
        results += list(ex.map(one_fred, by_src.get("fred", [])))

    # yfinance, Шиллер и файлы ФРС отдают несколько рядов одним запросом
    for src, fetch in (("yf", _fetch_yf), ("shiller", lambda ks: _fetch_shiller()), ("fed", _fetch_fed),
                       ("nyfed", _fetch_nyfed)):
        ks = by_src.get(src, [])
        if not ks:
            continue
        try:
            got = fetch(ks)
        except Exception as e:
            results += [UpdateResult(k, False, error=str(e)) for k in ks]
            continue
        for k in ks:
            results.append(_save(k, got[k]) if k in got else
                           UpdateResult(k, False, error="нет ряда в ответе источника"))
    return results


def load(key: str) -> pd.Series:
    """Ряд из кэша; если его нет — скачать."""
    p = _path(key)
    if not p.exists():
        res = update([key], force=True)[0]
        if not res.ok:
            raise RuntimeError(f"{key}: {res.error}")
    s = pd.read_csv(p, index_col=0, parse_dates=True)["value"]
    s.name = key
    return s


def status() -> pd.DataFrame:
    """Сводка по кэшу: что скачано, с какой и по какую дату."""
    rows = []
    for s in CATALOG:
        p = _path(s.key)
        row = {"key": s.key, "Название": s.name, "Группа": s.group, "Источник": s.source,
               "С": None, "По": None, "Последнее": None, "Обновлено": None}
        if p.exists():
            d = pd.read_csv(p, index_col=0, parse_dates=True)["value"]
            row |= {"С": d.index[0].date(), "По": d.index[-1].date(), "Последнее": d.iloc[-1],
                    "Обновлено": datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")}
        rows.append(row)
    return pd.DataFrame(rows)


# ---------- снимок мультипликаторов ETF (без истории) ----------

SNAPSHOT_FIELDS = {"trailingPE": "P/E", "dividendYield": "Дивиденды, %"}


def _snapshot_path() -> Path:
    return CACHE_DIR / "snapshot" / "etf_info.csv"


def update_snapshot(tickers: list[str], force: bool = False) -> pd.DataFrame:
    """P/E и дивидендная доходность ETF на сегодня (yfinance Ticker.info). Только текущее значение."""
    p = _snapshot_path()
    if p.exists() and not force and time.time() - p.stat().st_mtime < MAX_AGE:
        return pd.read_csv(p, index_col=0)
    rows = {}
    for t in tickers:
        try:
            info = yf.Ticker(t).info
            rows[t] = {name: info.get(field) for field, name in SNAPSHOT_FIELDS.items()}
        except Exception:  # один тикер не должен ломать снимок
            rows[t] = {name: None for name in SNAPSHOT_FIELDS.values()}
    df = pd.DataFrame(rows).T
    if df.notna().any().any():
        p.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(p)
    elif p.exists():  # источник ничего не вернул — оставляем старый снимок
        return pd.read_csv(p, index_col=0)
    return df


def snapshot_date() -> str | None:
    p = _snapshot_path()
    return datetime.fromtimestamp(p.stat().st_mtime).strftime("%d.%m.%Y") if p.exists() else None
