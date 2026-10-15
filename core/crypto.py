"""Крипта: среда, устройство и практика. Блоки страницы крипты и расчёты блока «Крипта и мировые деньги».

Блок 1 проверяет на истории, насколько биткоин — отдельный мир, а насколько — рисковый актив, который двигают
те же силы, что и акции роста: ставки, доллар, ликвидность ФРС.
"""
from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd

Load = Callable[[str], pd.Series]


@dataclass(frozen=True)
class Block:
    num: int
    title: str
    side: str            # "среда" — что давит на крипту снаружи; "устройство" — из чего она состоит внутри
    about: str           # что блок объясняет
    page: str | None     # экран; None — блок ещё не построен


BLOCKS = [
    Block(1, "Крипта и мировые деньги", "среда",
          "Ставки ФРС, доллар и ликвидность: насколько биткоин ходит вместе с акциями роста.",
          "views/crypto/world.py"),
    Block(2, "Институциональные двери", "среда",
          "Спотовые ETF, фьючерсы CME и базисная торговля, компании, которые копят биткоин на долг.",
          "views/crypto/doors.py"),
    Block(3, "Регулирование и шоки", "среда",
          "Решения регуляторов, суды, запреты и геополитика — события, которые меняют правила игры.", None),
    Block(4, "Плечо и ликвидации", "устройство",
          "Фьючерсы, цена ликвидации, фандинг, открытый интерес — почему падения в крипте такие резкие.",
          "views/crypto/leverage.py"),
    Block(5, "Биржи, стейблкоины и точки отказа", "устройство",
          "Где лежат деньги крипты и что ломается: Tether и Circle, депеги, банкротства бирж.",
          "views/crypto/plumbing.py"),
    Block(6, "Предложение и держатели", "устройство",
          "Откуда берутся монеты, майнеры, долгосрочные держатели — кто и когда продаёт.", None),
    Block(7, "Альткоины и токеномика", "устройство",
          "Разлоки, разводнение, сектора — почему альткоины ведут себя иначе, чем биткоин.", None),
    Block(8, "Циклы", "устройство",
          "Четырёхлетний цикл, типичные просадки и откуда берутся пузыри.", None),
    Block(9, "Риск-менеджмент и устройство торгов", "практика",
          "Размер позиции, плечо против волатильности, выходные и тонкие сессии, календарь событий.", None),
]
BY_NUM = {b.num: b for b in BLOCKS}


def net_liquidity(load: Load) -> pd.Series:
    """Чистая ликвидность ФРС, трлн $: баланс − счёт Минфина (TGA) − обратное РЕПО."""
    walcl = load("WALCL")
    tga = load("WTREGEN").reindex(walcl.index, method="ffill")
    rrp = load("RRPONTSYD").reindex(walcl.index, method="ffill").fillna(0) * 1000
    return ((walcl - tga - rrp) / 1e6).dropna()


def weekly(load: Load) -> pd.DataFrame:
    """Недельные изменения: биткоин, Nasdaq, доллар (лог-доходности, %) и реальная ставка (п.п.)."""
    def ret(key):
        return np.log(load(key).dropna().resample("W-FRI").last()).diff() * 100
    return pd.concat({"btc": ret("BTC-USD"), "ndx": ret("^IXIC"), "usd": ret("DTWEXBGS"),
                      "real": load("DFII10").dropna().resample("W-FRI").last().diff()},
                     axis=1, sort=True).dropna()


WEEKS = 52  # окно корреляции: за 26 недель стандартная ошибка ≈ 0,2 — вывод прыгал бы от шума


def noise(weeks: int = WEEKS) -> float:
    """Полуширина 95%-полосы, внутри которой корреляция неотличима от нуля: 2/√n."""
    return 2 / np.sqrt(weeks)


def rolling_corr(w: pd.DataFrame, other: str = "ndx", weeks: int = WEEKS) -> pd.Series:
    return w["btc"].rolling(weeks).corr(w[other]).dropna()


def by_year(w: pd.DataFrame) -> pd.DataFrame:
    """По годам: корреляции недельных движений биткоина с Nasdaq, долларом и реальной ставкой; во сколько раз
    биткоин волатильнее Nasdaq."""
    rows = {}
    for y, g in w.groupby(w.index.year):
        if len(g) < 20:
            continue
        rows[str(y)] = {"С Nasdaq": g["btc"].corr(g["ndx"]), "С долларом": g["btc"].corr(g["usd"]),
                        "С реальной ставкой": g["btc"].corr(g["real"]),
                        "Во сколько раз волатильнее Nasdaq": g["btc"].std() / g["ndx"].std()}
    return pd.DataFrame(rows).T


def era_corr(w: pd.DataFrame, split: str = "2020") -> tuple[float, float]:
    """Корреляция с Nasdaq до и после split."""
    before, after = w[:str(int(split) - 1)], w[split:]
    return float(before["btc"].corr(before["ndx"])), float(after["btc"].corr(after["ndx"]))


def vol_ratio(w: pd.DataFrame, weeks: int = 156) -> float:
    """Во сколько раз недельные колебания биткоина больше, чем у Nasdaq, за последние weeks недель."""
    g = w.iloc[-weeks:]
    return float(g["btc"].std() / g["ndx"].std())


def beta(w: pd.DataFrame, since: str = "2020") -> float:
    """На сколько % в среднем двигается биткоин на 1% движения Nasdaq за неделю."""
    g = w[since:]
    return float(g["btc"].cov(g["ndx"]) / g["ndx"].var())


def selloff_weeks(w: pd.DataFrame, threshold: float = -3, since: str = "2020") -> dict[str, float]:
    """Недели, когда Nasdaq упал сильнее threshold %: как часто биткоин падал вместе с ним и насколько."""
    g = w[since:]
    bad = g[g["ndx"] < threshold]
    return {"n": len(bad), "down_share": float((bad["btc"] < 0).mean() * 100),
            "worse_share": float((bad["btc"] < bad["ndx"]).mean() * 100),
            "btc_median": float(bad["btc"].median()), "ndx_median": float(bad["ndx"].median())}


def liquidity_corr(load: Load, months: int = 3, since: str = "2020") -> tuple[float, int]:
    """Корреляция изменений за непересекающиеся окна по months месяцев: биткоин и чистая ликвидность ФРС."""
    m = pd.concat({"btc": np.log(load("BTC-USD").dropna()).resample("MS").last(),
                   "liq": np.log(net_liquidity(load)).resample("MS").last()}, axis=1, sort=True).dropna()
    c = m.iloc[::months].diff().dropna()[since:]  # непересекающиеся окна: перекрытие завышает и шумит
    return float(c["btc"].corr(c["liq"])), len(c)


def drawdown(s: pd.Series) -> pd.Series:
    """Просадка от предыдущего максимума, %."""
    s = s.dropna()
    return (s / s.cummax() - 1) * 100


def window(load: Load, start: str, end: str) -> dict[str, float]:
    """Изменение биткоина и Nasdaq за период, %: с последнего закрытия до start по последнее до end."""
    out = {}
    for name, key in (("Биткоин", "BTC-USD"), ("Nasdaq", "^IXIC")):
        s = load(key).dropna()
        out[name] = float((s[:end].iloc[-1] / s[:start].iloc[-1] - 1) * 100)
    return out


def strength(c: float) -> str:
    """Словами: насколько сильна связь при корреляции c (R² = c² — доля движений, которую она объясняет)."""
    r2 = c * c
    if abs(c) < noise():
        return "неотличима от нуля"
    if r2 < 0.1:
        return "слабая"
    if r2 < 0.3:
        return "умеренная"
    return "сильная"


def verdict(w: pd.DataFrame) -> tuple[str, str, float]:
    """(вывод, цвет, корреляция с Nasdaq за последние 52 недели). Пороги — по доле объяснённых движений (R²)."""
    c = float(rolling_corr(w).iloc[-1])
    if c * c >= 0.3:
        return "Биткоин сейчас ходит вместе с акциями роста — решают ставки и аппетит к риску", "orange", c
    if c >= noise():
        return "Биткоин связан с акциями, но большую часть движений задаёт сама крипта", "gray", c
    return "Биткоин сейчас живёт своей жизнью — мировые деньги почти не объясняют его движений", "blue", c


# ---------- блок 4: плечо и ликвидации ----------
MMR = 0.5  # поддерживающая маржа, % позиции: у Binance для небольших позиций BTC ~0,4–0,5%


def liq_distance(lev: float, mmr: float = MMR) -> float:
    """На сколько % цена должна пройти против позиции до ликвидации (изолированная маржа, без комиссий)."""
    return 100 / lev - mmr


def candles(load: Load) -> pd.DataFrame:
    """Закрытие дня (Yahoo) и максимум/минимум дня (Binance), сутки UTC."""
    c = load("BTC-USD").dropna()
    c.index = c.index.normalize()
    return pd.concat({"c": c, "lo": load("BTC_LOW"), "hi": load("BTC_HIGH")}, axis=1, sort=True).dropna()


def adverse_move(df: pd.DataFrame, days: int, side: str = "long") -> pd.Series:
    """Худшее движение против позиции за следующие days дней от закрытия, % (для лонга — по минимумам)."""
    if side == "long":
        ext = df["lo"][::-1].rolling(days, min_periods=days).min()[::-1].shift(-1)
        return ((df["c"] - ext) / df["c"] * 100).dropna()
    ext = df["hi"][::-1].rolling(days, min_periods=days).max()[::-1].shift(-1)
    return ((ext - df["c"]) / df["c"] * 100).dropna()


def liq_odds(df: pd.DataFrame, levs: list[float], horizons: dict[str, int], side: str = "long") -> pd.DataFrame:
    """Доля дней в истории, когда позиция с плечом, открытая на закрытии, была бы ликвидирована за горизонт, %."""
    out = {}
    for name, h in horizons.items():
        m = adverse_move(df, h, side)
        out[name] = {f"{lev:g}x": float((m >= liq_distance(lev)).mean() * 100) for lev in levs}
    return pd.DataFrame(out)


def funding_ann(load: Load, days: int = 7) -> pd.Series:
    """Фандинг биткоина за days дней в пересчёте на год, % от размера позиции."""
    return (load("FUND_BTC").rolling(days).mean() * 365).dropna()


def funding_test(load: Load, start: str, end: str, days: int = 30, crash: float = 15) -> pd.DataFrame:
    """Пятые доли истории по фандингу за неделю: что было с ценой за следующие days дней. Пороги долей — общие
    для всей истории с 2019 года, чтобы «высокий» значил одно и то же в любом периоде. Окна по days дней
    перекрываются, поэтому независимых наблюдений примерно в days раз меньше, чем дней."""
    df = candles(load)
    f7 = funding_ann(load)
    fwd = (df["c"].shift(-days) / df["c"] - 1) * 100
    x = pd.concat({"f": f7, "fwd": fwd, "dd": adverse_move(df, days)}, axis=1, sort=True).dropna()
    x["q"] = pd.qcut(x["f"], 5, labels=["самый низкий", "низкий", "средний", "высокий", "самый высокий"])
    x = x[start:end]
    t = x.groupby("q", observed=True).agg(f=("f", "mean"), fwd=("fwd", "median"),
                                          crash=("dd", lambda s: (s >= crash).mean() * 100),
                                          n=("f", lambda s: len(s) / days))
    t.columns = ["Фандинг, % годовых", f"Цена через {days} дн., медиана %", f"Падение на {crash:g}%+ за {days} дн., %",
                 "Независимых месяцев ≈"]
    return t


def crash_days(load: Load, n: int = 8, since: str = "2019-09-15") -> pd.DataFrame:
    """Самые резкие падения внутри дня (минимум к закрытию прошлого дня) и фандинг за неделю до них."""
    df = candles(load)[since:]
    drop = (df["lo"] / df["c"].shift(1) - 1) * 100
    f7 = funding_ann(load).shift(1)
    top = drop.dropna().sort_values().head(n)
    return pd.DataFrame({"Падение внутри дня, %": top, "Фандинг за неделю до, % годовых": f7.reindex(top.index)})


def live(asset: str = "BTC", days: int = 3) -> dict | None:
    """Свежие снимки плеча из trade-news: открытый интерес, фандинг, лонги/шорты, ликвидации. None — сервис молчит."""
    import requests
    from datetime import datetime, timedelta, timezone

    from core.data import TRADE_NEWS_URL
    try:
        r = requests.get(f"{TRADE_NEWS_URL}/api/crypto/leverage", timeout=20,
                         params={"asset": asset, "from": (datetime.now(timezone.utc) - timedelta(days=days))
                                 .strftime("%Y-%m-%dT%H:%M:%SZ")})
        r.raise_for_status()
        d = r.json()
    except Exception:
        return None
    tot = pd.DataFrame(d["totals"])
    tot.index = pd.to_datetime(tot.pop("ts"))
    tot = tot[tot["exchanges"] == tot["exchanges"].max()]  # пока не все биржи отвечают, сумма занижена
    snap = pd.DataFrame(d["snapshots"])
    liq = pd.DataFrame(d["liquidations"])
    if len(liq):
        liq.index = pd.to_datetime(liq.pop("minute"))
    return {"totals": tot, "snapshots": snap, "liq": liq}


def lev_verdict(load: Load) -> tuple[str, str, float, float]:
    """(вывод, цвет, фандинг за неделю в % годовых, его перцентиль с 2019 года). Перекос опасен в обе стороны."""
    f = funding_ann(load)
    now = float(f.iloc[-1])
    pct = float((f < now).mean() * 100)
    if pct >= 80:
        return "Плечо перегрето: лонги платят много — толпа покупает в долг", "orange", now, pct
    if now < 0:
        return "Толпа в шортах: шорты платят лонгам — риск резкого выноса вверх", "orange", now, pct
    if pct <= 20:
        return "Плечо не перегрето: желающих купить в долг мало", "blue", now, pct
    return "Плечо в норме: фандинг около обычного уровня", "gray", now, pct


# ---------- блок 2: институциональные двери ----------
def _last_friday(ts: pd.Timestamp) -> pd.Timestamp:
    end = ts + pd.offsets.MonthEnd(0)
    return end - pd.Timedelta(days=(end.weekday() - 4) % 7)


def basis(load: Load, smooth: int = 20) -> pd.Series:
    """Базис CME в % годовых: насколько ближний фьючерс дороже спота, в пересчёте на срок до экспирации
    (последняя пятница месяца). Оценка: закрытия CME и спота разнесены по времени — сглаживаем медианой."""
    c = pd.concat({"f": load("BTC=F"), "s": load("BTC-USD")}, axis=1, sort=True).dropna()
    dte = []
    for t in c.index:
        exp = _last_friday(t)
        if (exp - t).days < 5:  # ближний ряд Yahoo переходит на следующий контракт до экспирации
            exp = _last_friday(t + pd.offsets.MonthBegin(1))
        dte.append((exp - t).days)
    dte = pd.Series(dte, c.index)
    raw = (c["f"] / c["s"] - 1) * 365 / dte * 100
    # закрытия CME и спота разнесены на часы; при коротком сроке ошибка умножается на 365/срок — такие дни выкидываем
    return raw[dte >= 10].rolling(smooth, min_periods=smooth // 2).median().dropna()


def treasuries() -> dict | None:
    """Запасы биткоина у публичных компаний сейчас (CoinGecko). None — источник не ответил."""
    import requests
    try:
        r = requests.get("https://api.coingecko.com/api/v3/companies/public_treasury/bitcoin", timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def strategy_kpi() -> dict | None:
    """Капитализация, долг и привилегированные акции Strategy, $ (сайт компании) и деньги на счетах (Yahoo).
    None — источник не ответил."""
    import requests
    import yfinance as yf

    def num(x) -> float:
        return float(str(x).replace(",", "")) * 1e6
    try:
        r = requests.get("https://api.strategy.com/btc/mstrKpiData", timeout=20,
                         headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120"})
        r.raise_for_status()
        d = r.json()[0]
        out = {"cap": num(d["marketCap"]), "debt": num(d["debt"]), "pref": num(d["pref"])}
    except Exception:
        return None
    try:
        out["cash"] = float(yf.Ticker("MSTR").info.get("totalCash") or 0)
    except Exception:
        out["cash"] = 0.0
    return out


def mnav(kpi: dict, btc_value: float) -> tuple[float, float]:
    """(mNAV по капитализации, mNAV по стоимости компании = капитализация + долг + префы − деньги)."""
    ev = kpi["cap"] + kpi["debt"] + kpi["pref"] - kpi["cash"]
    return kpi["cap"] / btc_value, ev / btc_value


def pair_beta(load: Load, a: str, b: str = "BTC-USD", since: str = "2021") -> tuple[float, float]:
    """(бета, корреляция) недельных движений a к b."""
    r = np.log(pd.concat({"a": load(a), "b": load(b)}, axis=1, sort=True).dropna()).resample("W-FRI").last()
    r = r.diff().dropna()[since:]
    return float(r["a"].cov(r["b"]) / r["b"].var()), float(r["a"].corr(r["b"]))


# ---------- блок 5: биржи, стейблкоины и точки отказа ----------
def supply_growth(load: Load, days: int = 90) -> pd.Series:
    """Рост стейблкоинов в обращении за days дней, %."""
    s = load("STABLE_TOTAL")
    return ((s / s.shift(days) - 1) * 100).dropna()


def supply_vs_btc(load: Load, months: int = 3, since: str = "2019") -> dict[str, float]:
    """Связь изменений стейблкоинов и биткоина по непересекающимся окнам: в том же окне и с опережением на окно."""
    m = pd.concat({"s": np.log(load("STABLE_TOTAL")).resample("MS").last(),
                   "b": np.log(load("BTC-USD").dropna()).resample("MS").last()}, axis=1, sort=True).dropna()[since:]
    d = m.iloc[::months].diff().dropna()
    return {"same": float(d["s"].corr(d["b"])), "lead": float(d["s"].corr(d["b"].shift(-1))), "n": len(d)}


def depegs(load: Load, coin: str, below: float = 0.98) -> pd.DataFrame:
    """Эпизоды, когда минимум дня стейблкоина опускался ниже below: начало, дней, самая низкая цена."""
    lo = load(f"PEGLOW_{coin}")
    bad = lo[lo < below]
    if bad.empty:
        return pd.DataFrame(columns=["Дней", "Минимум, $"])
    ep = (bad.index.to_series().diff() > pd.Timedelta(days=7)).cumsum()
    g = bad.groupby(ep.values)
    return pd.DataFrame({"Начало": g.apply(lambda s: s.index[0].date()), "Дней": g.size(), "Минимум, $": g.min()})\
        .set_index("Начало").sort_values("Минимум, $")


def etf_vs_btc(load: Load) -> dict[str, float]:
    """Потоки в биткоин-ETF и цена по неделям: в ту же неделю, вслед за прошлой неделей цены, перед следующей."""
    f = load("ETF_FLOW_BTC").resample("W-FRI").sum()
    b = np.log(load("BTC-USD").dropna()).resample("W-FRI").last().diff() * 100
    w = pd.concat({"f": f, "b": b}, axis=1, sort=True).dropna()
    return {"same": float(w["f"].corr(w["b"])), "after": float(w["f"].corr(w["b"].shift(1))),
            "before": float(w["f"].corr(w["b"].shift(-1))), "n": len(w)}
