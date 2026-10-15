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
          "Спотовые ETF, фьючерсы CME и базисная торговля, компании, которые копят биткоин на долг.", None),
    Block(3, "Регулирование и шоки", "среда",
          "Решения регуляторов, суды, запреты и геополитика — события, которые меняют правила игры.", None),
    Block(4, "Плечо и ликвидации", "устройство",
          "Фьючерсы, цена ликвидации, фандинг, открытый интерес — почему падения в крипте такие резкие.",
          "views/crypto/leverage.py"),
    Block(5, "Биржи, стейблкоины и точки отказа", "устройство",
          "Где лежат деньги крипты и что ломается: Tether и Circle, депеги, банкротства бирж.", None),
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
