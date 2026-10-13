"""Слой 8: вынужденные потоки — кто обязан купить или продать по правилу, марже, календарю или мандату.

Три части:
- справочник механизмов (сжатая версия отчёта reports/Что двигает цену и вынужденные участники.md);
- даты событий в прошлом, рассчитанные по тем же правилам, что календарь trade-news (он смотрит только вперёд);
- проверка события на истории (event study): средняя «избыточная» доходность вокруг события — сверх обычного
  дневного дрейфа актива — с доверительным интервалом.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd
import requests

CALENDAR_URL = os.environ.get("TRADE_NEWS_URL", "http://127.0.0.1:10000") + "/api/calendar"

# ---------- справочник механизмов ----------
# (группа, кто вынужден, триггер и направление, когда, рынки, надёжность — ключ learn.RELIABILITY, где смотреть)
MECHANISMS = [
    ("Индексы", "Индексные фонды при включении/исключении бумаги", "покупают добавленные, продают исключённые",
     "дата вступления, по закрытию", "акции", "проверен на истории", "S&P DJI, MSCI, FTSE Russell, Мосбиржа"),
    ("Индексы", "Плечевые и инверсные ETF", "в конце дня докупают после роста, продают после падения",
     "каждый день, последние 30 минут", "акции, крипта", "проверен вне выборки", "активы ETF × движение дня"),
    ("Индексы", "ETF при притоке и оттоке", "создание и погашение паёв → покупка и продажа корзины", "ежедневно",
     "акции, облигации, крипта", "проверен на истории", "Farside, SoSoValue, сайты эмитентов"),
    ("Мандаты", "Пенсионные фонды и портфели 60/40", "после роста акций продают акции и покупают облигации",
     "конец месяца, сильнее — конец квартала", "акции, облигации", "проверен вне выборки",
     "считаем сами: акции против облигаций с начала квартала"),
    ("Мандаты", "Фонды риск-паритета", "волатильность выросла → сокращают все классы", "дни после всплеска",
     "акции, облигации, сырьё", "проверен на истории", "моделируем по волатильности"),
    ("Правила риска", "Фонды с таргетом волатильности", "волатильность выросла → продают, упала → докупают",
     "дни после скачка", "акции", "проверен на истории", "моделируем: волатильность за 10–20 дней"),
    ("Правила риска", "Трендовые фонды (CTA)", "цена пробила уровень тренда → разворот позиции",
     "известные уровни", "все", "проверен на истории", "моделируем + CFTC COT"),
    ("Опционы", "Маркетмейкеры с короткой гаммой", "хеджируются по ходу движения и усиливают его",
     "весь день, сильнее к закрытию", "акции, облигации, валюты", "проверен вне выборки",
     "SqueezeMetrics, SpotGamma; Deribit"),
    ("Опционы", "Маркетмейкеры с длинной гаммой", "хеджируются против движения → цена «прилипает» к страйкам",
     "перед экспирацией", "акции", "проверен на истории", "открытый интерес Cboe, OCC, Deribit"),
    ("Опционы", "Экспирации (OPEX, «тройная ведьма», VIX)", "снятие хеджей освобождает рынок",
     "третья пятница; квартальные — сильнее", "акции, крипта", "проверен на истории", "календарь trade-news"),
    ("Плечо", "Трейдеры с плечом на криптобиржах", "ликвидации лонгов при падении, шортов при росте",
     "у скоплений ликвидационных уровней", "крипта", "проверен на истории",
     "открытый интерес, фандинг: API бирж, Coinglass"),
    ("Плечо", "Клиенты брокеров с маржой", "маржин-колл → продажа", "после резких падений", "акции",
     "проверен на истории", "маржинальный долг FINRA"),
    ("Плечо", "Керри-трейдеры", "валюта фондирования крепнет → закрывают всё сразу",
     "после сюрпризов ЦБ и всплесков волатильности", "валюты, акции, крипта", "проверен на истории",
     "CFTC COT по иене, разница ставок"),
    ("Плечо", "Базисные арбитражёры", "рост маржи → закрывают позиции на весь объём", "стрессы фондирования",
     "облигации, крипта", "проверен на истории", "CFTC COT (leveraged funds)"),
    ("Шорты", "Шортисты при сквизе", "рост цены и отзыв бумаг → вынуждены откупать",
     "высокий шорт и дорогой займ", "акции, крипта", "проверен на истории", "FINRA, iBorrowDesk, ORTEX"),
    ("Компании", "Выкуп акций", "компания покупает по программе", "вне тихого периода перед отчётом",
     "акции", "спорный", "10-Q, 8-K; даты отчётов — календарь trade-news"),
    ("Компании", "Допэмиссии и продажи крупных акционеров", "новое предложение бумаг", "после объявления",
     "акции", "проверен на истории", "SEC EDGAR: S-3, 424B, 8-K"),
    ("Компании", "Окончание локапа после IPO", "инсайдеры получают право продать", "90–180 дней после IPO",
     "акции", "проверен на истории", "проспект IPO; календарь trade-news"),
    ("Компании", "Экспортёры", "продают валютную выручку под налоги", "налоговые даты", "валюты",
     "проверен на истории", "налоговый календарь; календарь trade-news"),
    ("Фонды", "Фонды с оттоком клиентов", "продают то, что держат", "после плохих результатов",
     "акции, облигации", "проверен вне выборки", "ICI, 13F"),
    ("Фонды", "Продажа ради налогового убытка", "продают убыточное в декабре", "декабрь–январь",
     "акции, крипта", "спорный", "календарь"),
    ("Государство", "ЦБ: QE и QT", "покупает или отпускает облигации по графику", "по объявленному графику",
     "облигации", "проверен на истории", "FRED: WALCL (слой 2)"),
    ("Государство", "Минфин РФ по бюджетному правилу", "нефть выше базы → покупает валюту, ниже → продаёт",
     "анонс на 3-й рабочий день, операции весь месяц", "рубль", "проверен на истории",
     "minfin.gov.ru; календарь trade-news"),
    ("Государство", "Продажа конфискованной крипты", "государство продаёт изъятые монеты", "после решения суда",
     "крипта", "проверен на истории", "Arkham"),
    ("Календарь", "Банки перед отчётной датой", "сокращают баланс → дефицит репо", "конец квартала и года",
     "облигации, валюты", "проверен на истории", "ставки репо (FRED)"),
    ("Крипта", "Получатели разлоков токенов", "новое предложение → продажи", "график публичен; давление за ~30 дней",
     "крипта", "проверен на истории", "DefiLlama; календарь trade-news"),
    ("Крипта", "Майнеры", "продают добытое; после халвинга — больше", "непрерывно; халвинг по графику",
     "крипта", "проверен на истории", "mempool.space"),
    ("Крипта", "Эмитенты стейблкоинов", "выпуск = новые деньги для покупок", "непрерывно", "крипта", "спорный",
     "DefiLlama"),
]


# ---------- даты событий в прошлом ----------

def third_friday(y: int, m: int) -> date:
    d = date(y, m, 15)
    return d + timedelta(days=(4 - d.weekday()) % 7)


def last_friday(y: int, m: int) -> date:
    d = (date(y, m + 1, 1) if m < 12 else date(y + 1, 1, 1)) - timedelta(days=1)
    return d - timedelta(days=(d.weekday() - 4) % 7)


def _months(start: int, end: int):
    for y in range(start, end + 1):
        for m in range(1, 13):
            yield y, m


@dataclass(frozen=True)
class EventType:
    title: str
    who: str                      # кто вынужден и в какую сторону
    rule: str                     # как считается дата


EVENTS = {
    "quarter_end": EventType("Конец квартала", "пенсионные фонды возвращают доли акций и облигаций; банки сжимают "
                             "балансы", "последний торговый день квартала"),
    "month_end": EventType("Конец месяца", "ребалансировка фондов, хедж валюты иностранными держателями",
                           "последний торговый день месяца"),
    "opex_quarterly": EventType("Квартальная экспирация («тройная ведьма»)", "маркетмейкеры снимают хеджи; в тот "
                                "же день ребалансировка S&P", "третья пятница марта, июня, сентября, декабря"),
    "opex_monthly": EventType("Месячная экспирация опционов", "маркетмейкеры снимают хеджи",
                              "третья пятница месяца, кроме квартальных"),
    "vix_expiry": EventType("Экспирация VIX", "снятие хеджей по волатильности",
                            "за 30 дней до третьей пятницы следующего месяца (среда)"),
    "russell_recon": EventType("Реконституция Russell", "индексные фонды малых компаний меняют состав",
                               "последняя пятница июня"),
    "year_end": EventType("Конец года", "продажа ради налогового убытка, «причёсывание» отчётности",
                          "последний торговый день года"),
    "ru_tax_period": EventType("Налоговый период в России", "экспортёры продают валюту под налоги → рубль крепнет",
                               "28-е число месяца"),
}


def event_dates(kind: str, trading_days: pd.DatetimeIndex) -> list[pd.Timestamp]:
    """Даты события в прошлом, привязанные к торговым дням актива (последний торговый день не позже правила)."""
    days = trading_days.sort_values()
    y0, y1 = days[0].year, days[-1].year
    if kind in ("month_end", "quarter_end", "year_end"):
        s = pd.Series(days, index=days)
        last = s.groupby([days.year, days.month]).max()
        months = {"month_end": range(1, 13), "quarter_end": (3, 6, 9, 12), "year_end": (12,)}[kind]
        return [d for (y, m), d in last.items() if m in months and d < days[-1]]
    if kind == "opex_quarterly":
        raw = [third_friday(y, m) for y, m in _months(y0, y1) if m in (3, 6, 9, 12)]
    elif kind == "opex_monthly":
        raw = [third_friday(y, m) for y, m in _months(y0, y1) if m not in (3, 6, 9, 12)]
    elif kind == "vix_expiry":
        raw = [third_friday(y + (m == 12), m % 12 + 1) - timedelta(days=30) for y, m in _months(y0, y1)]
    elif kind == "russell_recon":
        raw = [last_friday(y, 6) for y in range(max(y0, 1989), y1 + 1)]
    elif kind == "ru_tax_period":
        raw = [date(y, m, 28) for y, m in _months(y0, y1)]
    else:
        raise ValueError(kind)
    out = []
    for d in raw:
        i = days.searchsorted(pd.Timestamp(d), side="right") - 1
        if 0 <= i < len(days) - 1:
            out.append(days[i])
    return sorted(set(out))


# ---------- проверка события на истории ----------

@dataclass
class Study:
    days: np.ndarray            # дни относительно события: −W … +W
    path: np.ndarray            # средняя накопленная избыточная доходность, %
    lo: np.ndarray              # 95% интервал
    hi: np.ndarray
    daily: pd.DataFrame         # по дням: средняя, t-статистика, доля дней с избыточной доходностью > 0
    n: int                      # число событий
    drift: float                # обычный дневной дрейф актива, %


def study(prices: pd.Series, dates: list[pd.Timestamp], window: int = 10) -> Study:
    """Event study: избыточная доходность = дневная лог-доходность минус её среднее за весь период."""
    p = prices.dropna()
    r = np.log(p).diff().dropna()
    drift = float(r.mean())
    ab = (r - drift).to_numpy()
    idx = r.index
    rows = []
    for d in dates:
        i = idx.searchsorted(d, side="right") - 1
        if i - window >= 0 and i + window < len(ab) and idx[i] == d:
            rows.append(ab[i - window:i + window + 1])
    if len(rows) < 3:
        raise ValueError("слишком мало событий в выбранном периоде")
    m = np.array(rows) * 100
    n = len(m)
    cum = m.cumsum(axis=1)
    path = cum.mean(axis=0)
    se = cum.std(axis=0, ddof=1) / np.sqrt(n)
    k = np.arange(-window, window + 1)
    d_se = m.std(axis=0, ddof=1) / np.sqrt(n)
    daily = pd.DataFrame({"Средняя, %": m.mean(axis=0), "t": m.mean(axis=0) / d_se,
                          "Доля > 0, %": (m > 0).mean(axis=0) * 100}, index=k)
    return Study(k, path, path - 1.96 * se, path + 1.96 * se, daily, n, drift * 100)


def window_effect(s: Study, a: int, b: int) -> tuple[float, float]:
    """Накопленная избыточная доходность с дня a по день b включительно и её t-статистика (по дням независимо)."""
    sel = s.daily.loc[a:b]
    mean = float(sel["Средняя, %"].sum())
    se = float(np.sqrt(((sel["Средняя, %"] / sel["t"]) ** 2).sum()))
    return mean, mean / se if se else float("nan")


# ---------- календарь trade-news ----------

def calendar(start: date, end: date, timeout: float = 5.0) -> list[dict]:
    """События из trade-news (на этом же сервере). Бросает исключение, если сервис недоступен."""
    r = requests.get(CALENDAR_URL, params={"from": start.isoformat(), "to": end.isoformat()}, timeout=timeout)
    r.raise_for_status()
    return r.json()


# ---------- модельные потоки: что фонды обязаны делать по своим правилам ----------

def vol_control(prices: pd.Series, target: float = 10.0, cap: float = 1.5, window: int = 20) -> pd.DataFrame:
    """Фонд с таргетом волатильности: доля акций = таргет / реализованная волатильность за window дней, не выше cap."""
    r = np.log(prices.dropna()).diff()
    vol = r.rolling(window).std() * np.sqrt(252) * 100
    return pd.DataFrame({"vol": vol, "exposure": (target / vol).clip(upper=cap)}).dropna()


def vol_control_shock(prices: pd.Series, move_pct: float, target: float = 10.0, cap: float = 1.5,
                      window: int = 20) -> tuple[float, float]:
    """Если завтра рынок сдвинется на move_pct %: (доля акций сейчас, доля после пересчёта)."""
    p = prices.dropna()
    now = vol_control(p, target, cap, window)["exposure"].iloc[-1]
    nxt = pd.concat([p, pd.Series([p.iloc[-1] * (1 + move_pct / 100)], index=[p.index[-1] + pd.Timedelta(days=1)])])
    return float(now), float(vol_control(nxt, target, cap, window)["exposure"].iloc[-1])


TREND_HORIZONS = (20, 60, 120, 250)  # торговых дней: ~месяц, квартал, полгода, год


def trend(prices: pd.Series, target: float = 10.0) -> pd.DataFrame:
    """Трендовый фонд (упрощённо): сигнал = среднее знаков доходности за 4 горизонта (−1…+1),
    позиция = сигнал × таргет волатильности / волатильность за 60 дней (не больше 2)."""
    lp = np.log(prices.dropna())
    sig = sum(np.sign(lp - lp.shift(h)) for h in TREND_HORIZONS) / len(TREND_HORIZONS)
    vol = lp.diff().rolling(60).std() * np.sqrt(252) * 100
    return pd.DataFrame({"signal": sig, "position": sig * (target / vol).clip(upper=2)}).dropna()


def trend_flips(prices: pd.Series) -> dict[int, float]:
    """Уровни, при пересечении которых меняется знак сигнала по каждому горизонту: цена h дней назад."""
    p = prices.dropna()
    return {h: float(p.iloc[-h - 1]) for h in TREND_HORIZONS if len(p) > h}


def trend_returns(prices: pd.Series) -> pd.DataFrame:
    """Дневная лог-доходность трендовой стратегии (позиция вчера × доходность сегодня) и просто актива."""
    p = prices.dropna()
    r = np.log(p).diff()
    pos = trend(p)["position"]
    return pd.DataFrame({"trend": pos.shift(1) * r, "hold": r}).dropna()


def period_to_date(prices: pd.Series, freq: str = "M", skip_last: int = 0) -> float:
    """Доходность с начала текущего месяца (M) или квартала (Q), %; skip_last — не считать последние дни."""
    p = prices.dropna()
    start = p.index[-1].to_period(freq).start_time
    base = p[:start - pd.Timedelta(days=1)]
    seg = p[start:]
    end = seg.iloc[-1 - skip_last] if len(seg) > skip_last else seg.iloc[-1]
    return float((end / base.iloc[-1] - 1) * 100) if len(base) else float("nan")


def month_end_split(stocks: pd.Series, target: pd.Series) -> dict[str, list[pd.Timestamp]]:
    """Концы месяцев, разделённые по доходности акций с начала месяца (до дня −2): верхняя и нижняя трети."""
    rows = []
    for d in event_dates("month_end", target.dropna().index):
        m0 = d.to_period("M").start_time
        seg, base = stocks[m0:d].dropna(), stocks[:m0 - pd.Timedelta(days=1)].dropna()
        if len(seg) >= 5 and len(base):
            rows.append((d, (seg.iloc[-3] / base.iloc[-1] - 1) * 100))
    g = pd.DataFrame(rows, columns=["d", "mtd"])
    return {"up": g[g["mtd"] >= g["mtd"].quantile(2 / 3)]["d"].tolist(),
            "down": g[g["mtd"] <= g["mtd"].quantile(1 / 3)]["d"].tolist(),
            "thresholds": [float(g["mtd"].quantile(1 / 3)), float(g["mtd"].quantile(2 / 3))]}
