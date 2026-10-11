"""Облигации Московской биржи через бесплатный API ISS: кривая ОФЗ (КБД) и данные выпуска по тикеру или ISIN —
цена, накопленный купон, график купонов, амортизаций и оферт.

Данные приходят с задержкой около 15 минут. Все суммы приводятся к 100 текущего (непогашенного) номинала —
в тех же единицах, в которых биржа котирует цену.
"""
from dataclasses import dataclass, field
from datetime import date

import numpy as np
import pandas as pd
import requests

ISS = "https://iss.moex.com/iss"
_session = requests.Session()


def _get(path: str, **params) -> dict:
    params.setdefault("iss.meta", "off")
    r = _session.get(f"{ISS}{path}.json", params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def _rows(j: dict, name: str) -> list[dict]:
    t = j.get(name) or {"columns": [], "data": []}
    return [dict(zip(t["columns"], row)) for row in t["data"]]


def _date(s) -> date | None:
    if not s or str(s).startswith("0000"):
        return None
    return date.fromisoformat(str(s)[:10])


def kbd() -> tuple[pd.Series, str]:
    """Кривая бескупонной доходности ОФЗ: срок в годах → эффективная годовая доходность, %; и дата."""
    rows = _rows(_get("/engines/stock/zcyc", **{"iss.only": "yearyields"}), "yearyields")
    s = pd.Series({float(r["period"]): float(r["value"]) for r in rows}).sort_index()
    return s, rows[-1]["tradedate"] if rows else ""


@dataclass
class RuBond:
    secid: str
    isin: str
    name: str
    kind: str                 # fixed | floating | tips | zero — как в core.bond_lab.KINDS
    currency: str
    face: float               # текущий номинал в валюте
    price: float              # чистая цена, % номинала
    price_note: str           # откуда цена и на какое время
    accrued: float            # накопленный купон, % номинала
    settle: date              # дата расчётов по сделке сегодня
    maturity: date
    coupon_rate: float
    freq: int
    moex_yield: float | None  # доходность к погашению, которую показывает биржа, — для сверки
    moex_yield_offer: float | None  # то же к ближайшей оферте
    t: np.ndarray             # годы от даты расчётов до каждой выплаты
    coupons: np.ndarray       # купоны на 100 текущего номинала
    principal: np.ndarray     # погашения номинала на 100 текущего номинала
    unknown: np.ndarray       # купон ещё не объявлен — подставлен последний известный, движется со ставкой
    outstanding: np.ndarray   # непогашенный номинал перед выплатой, на 100
    dates: list = field(default_factory=list)
    offers: list = field(default_factory=list)  # (дата, вид оферты)
    notes: list = field(default_factory=list)   # оговорки к расчёту

    def until(self, d: date) -> "RuBond":
        """Тот же выпуск, если его погасят в дату d (оферта): остаток номинала выплачивается в этот день."""
        keep = np.array([x <= d for x in self.dates])
        t, c, p = self.t[keep], self.coupons[keep], self.principal[keep].copy()
        rest = 100 - p.sum()
        dates = [x for x, k in zip(self.dates, keep) if k]
        if dates and dates[-1] == d:
            p[-1] += rest
        else:
            t = np.append(t, (d - self.settle).days / 365)
            c, p = np.append(c, 0.0), np.append(p, rest)
            dates.append(d)
        out = 100 - np.concatenate([[0.0], np.cumsum(p)[:-1]])
        return RuBond(**{**self.__dict__, "t": t, "coupons": c, "principal": p, "outstanding": out,
                         "unknown": self.unknown[:len(t)] if len(self.unknown) >= len(t)
                         else np.append(self.unknown[keep], False), "dates": dates, "maturity": d})


def _resolve(query: str) -> str:
    q = query.strip().upper()
    rows = _rows(_get("/securities", q=q, engine="stock", market="bonds",
                      **{"securities.columns": "secid,isin,shortname"}), "securities")
    if not rows:
        raise ValueError(f"На Мосбирже не найдена облигация «{query}»")
    exact = [r for r in rows if q in (str(r["secid"]).upper(), str(r["isin"]).upper())]
    return (exact or rows)[0]["secid"]


def _bondization(secid: str) -> dict[str, list[dict]]:
    out = {"coupons": [], "amortizations": [], "offers": []}
    start = 0
    while True:
        j = _get(f"/statistics/engines/stock/markets/bonds/bondization/{secid}", limit=100, start=start)
        total = 0
        for name in out:
            rows = _rows(j, name)
            out[name] += rows
            cur = _rows(j, f"{name}.cursor")
            total = max(total, cur[0]["TOTAL"] if cur else 0)
        start += 100
        if start >= total:
            return out


def fetch(query: str) -> RuBond:
    secid = _resolve(query)
    desc = {r["name"]: r["value"] for r in _rows(_get(f"/securities/{secid}"), "description")}
    j = _get(f"/engines/stock/markets/bonds/securities/{secid}", **{"iss.only": "securities,marketdata"})
    secs, mds = _rows(j, "securities"), {r["BOARDID"]: r for r in _rows(j, "marketdata")}
    if not secs:
        raise ValueError(f"{secid}: выпуск сейчас не торгуется на Мосбирже")
    sec = max(secs, key=lambda r: (mds.get(r["BOARDID"], {}).get("LAST") is not None,
                                   mds.get(r["BOARDID"], {}).get("VALTODAY") or 0))
    md = mds.get(sec["BOARDID"], {})
    price, note = None, ""
    for key, label in (("LAST", "последняя сделка"), ("WAPRICE", "средневзвешенная за день")):
        if md.get(key):
            price, note = float(md[key]), f"{label}, {md.get('SYSTIME') or md.get('UPDATETIME') or ''}"
            break
    if price is None:
        for key in ("PREVLEGALCLOSEPRICE", "PREVPRICE", "PREVWAPRICE"):
            if sec.get(key):
                price, note = float(sec[key]), f"закрытие {sec.get('PREVDATE') or 'прошлого дня'} — сегодня сделок нет"
                break
    if price is None:
        raise ValueError(f"{secid}: нет цены — по выпуску давно не было сделок")

    face = float(sec["FACEVALUE"])
    settle = _date(sec.get("SETTLEDATE")) or date.today()
    btype = f"{sec.get('BONDTYPE') or ''} {desc.get('BOND_TYPE') or ''}"
    if "плавающ" in btype.lower():
        kind = "floating"
    elif "линкер" in btype.lower() or sec.get("FACEVALUE_TYPE") == "Индексированный":
        kind = "tips"
    elif not float(sec.get("COUPONPERCENT") or 0):
        kind = "zero"
    else:
        kind = "fixed"

    bz = _bondization(secid)
    events: dict[date, dict] = {}
    for r in bz["coupons"]:
        d = _date(r["coupondate"])
        if d and d > settle:
            e = events.setdefault(d, {"c": 0.0, "p": 0.0, "unknown": False, "rate": None, "face": None})
            if r["value"]:
                e["c"] += float(r["value"])
                e["rate"] = r["valueprc"]
            else:
                e["unknown"] = True
            e["face"] = float(r["facevalue"]) if r.get("facevalue") else None
    for r in bz["amortizations"]:
        d = _date(r["amortdate"])
        if d and d > settle and r["value"]:
            events.setdefault(d, {"c": 0.0, "p": 0.0, "unknown": False, "rate": None, "face": None})["p"] += \
                float(r["value"])
    if not events:
        raise ValueError(f"{secid}: нет будущих выплат — выпуск погашен")
    dates = sorted(events)
    # Купоны, которые ещё не объявлены: подставляем последнюю известную ставку на непогашенный номинал
    principal = np.array([events[d]["p"] for d in dates]) / face * 100
    if abs(principal.sum() - 100) > 0.5:  # погашение не попало в график — добавим остаток в дату погашения
        principal[-1] += 100 - principal.sum()
    outstanding = 100 - np.concatenate([[0.0], np.cumsum(principal)[:-1]])
    known_rate = float(sec.get("COUPONPERCENT") or 0)
    coupons, unknown, prev = [], [], settle
    for d, out in zip(dates, outstanding):
        e = events[d]
        if e["rate"]:
            known_rate = float(e["rate"])
        if e["unknown"] and not e["c"]:
            coupons.append(known_rate * out / 100 * (d - prev).days / 365)
            unknown.append(True)
        else:
            coupons.append(e["c"] / face * 100)
            unknown.append(False)
        prev = d
    if kind == "floating":  # биржа заполняет будущие купоны текущей ставкой; на деле они пойдут за ставкой
        unknown = [False] + [True] * (len(unknown) - 1)
    t = np.array([(d - settle).days / 365 for d in dates])
    period = float(sec.get("COUPONPERIOD") or 0)
    freq = min([1, 2, 4, 12], key=lambda f: abs(365 / f - period)) if period else int(desc.get("COUPONFREQUENCY") or 2)

    offers = sorted({(_date(r["offerdate"]), r.get("offertype") or "оферта") for r in bz["offers"]
                     if _date(r["offerdate"]) and _date(r["offerdate"]) > settle})
    notes = []
    if any(unknown) and kind != "floating":
        notes.append(f"{sum(unknown)} будущих купонов ещё не объявлены — подставлена последняя известная ставка "
                     f"{known_rate:.2f}%; в сценариях они движутся вместе со ставкой.")
    if kind == "tips":
        notes.append("Номинал индексируется по инфляции: расчёт ведётся в реальных деньгах, доходность — реальная.")
    if principal[:-1].sum() > 0.5:
        notes.append("Амортизация: номинал гасится частями — см. график выплат.")
    return RuBond(secid=secid, isin=str(sec.get("ISIN") or desc.get("ISIN") or ""),
                  name=str(sec.get("SECNAME") or desc.get("NAME") or secid), kind=kind,
                  currency=str(sec.get("FACEUNIT") or "SUR").replace("SUR", "RUB"), face=face, price=price,
                  price_note=note, accrued=float(sec.get("ACCRUEDINT") or 0) / face * 100, settle=settle,
                  maturity=dates[-1], coupon_rate=float(sec.get("COUPONPERCENT") or 0), freq=freq,
                  moex_yield=float(md["YIELD"]) if md.get("YIELD") else None,
                  moex_yield_offer=float(md["YIELDTOOFFER"]) if md.get("YIELDTOOFFER") else None, t=t, coupons=np.array(coupons),
                  principal=principal, unknown=np.array(unknown), outstanding=outstanding, dates=dates,
                  offers=offers, notes=notes)
