"""Приборы панели: что показываем, как считаем, как оцениваем.

Каждый прибор считает «метрику прибора» (по ней стрелка, зоны, статус и перцентиль)
и, если нужно, отдельный ряд для мини-графика (например, заявки: статус — по
изменению г/г, а на графике — сам уровень).

Статус читается «с точки зрения риска для экономики и рынка»: good — попутный
ветер, critical — сильный встречный. Отдельно от статуса — флаг исторического
экстремума (перцентиль ≤ 5 или ≥ 95) с контр-прочтением по Марксу/Баффету.
Пороги — первая версия, уточняются на этапах плана.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import pandas as pd

from core.transforms import yoy_pct

Load = Callable[[str], pd.Series]

GOOD, WARNING, SERIOUS, CRITICAL, NEUTRAL = "good", "warning", "serious", "critical", "neutral"
SCORE = {GOOD: 1, NEUTRAL: 0, WARNING: 0, SERIOUS: -1, CRITICAL: -2}
LEADING, COINCIDENT, LAGGING = "опережающий", "совпадающий", "запаздывающий"

GROUPS = ["Рост", "Инфляция", "ФРС и ставки", "Кредит и ликвидность", "Оценка", "Рынок и сентимент"]

# Зоны: список (верхняя граница, статус, слово) по возрастанию + последняя зона без границы
Bands = list[tuple[float, str, str]]


@dataclass
class Reading:
    series: pd.Series                  # метрика прибора (стрелка, статус, перцентиль)
    spark: pd.Series | None = None     # что рисовать на мини-графике (по умолчанию series)
    status: str | None = None          # переопределение статуса (иначе — по зонам)
    label: str | None = None
    extra: str = ""
    bands: Bands | None = None         # переопределение зон (например, по перцентилям истории)


@dataclass
class Indicator:
    key: str
    name: str
    group: str
    kind: str                          # опережающий / совпадающий / запаздывающий
    metric: str                        # подпись метрики прибора
    units: str
    compute: Callable[[Load], Reading]
    bands: Bands
    top: tuple[str, str]               # зона выше последней границы
    domain: tuple[float, float]        # шкала стрелочного прибора
    how_to_read: str
    sources: list[str]
    freq: str = "D"                    # для пометки свежести: D, W, M, Q
    delta_months: int = 3
    digits: int = 2
    extreme_low: str = ""              # контр-прочтение исторического минимума
    extreme_high: str = ""


def classify(value: float, bands: Bands, top: tuple[str, str]) -> tuple[str, str]:
    for limit, status, label in bands:
        if value < limit:
            return status, label
    return top


def _change(s: pd.Series, months: int) -> pd.Series:
    """Изменение в % за N месяцев для каждой даты."""
    past = s.copy()
    past.index = past.index + pd.DateOffset(months=months)
    past = past[~past.index.duplicated()]
    base = past.reindex(s.index.union(past.index)).sort_index().ffill().reindex(s.index)
    return ((s / base - 1) * 100).dropna()


def _monthly(s: pd.Series) -> pd.Series:
    return s.resample("MS").mean().dropna()


# ---------------- Рост ----------------

def _permit(load: Load) -> Reading:
    lvl = load("PERMIT").rolling(3).mean().dropna()
    return Reading(yoy_pct(lvl).dropna(), spark=lvl)


def _claims(load: Load) -> Reading:
    lvl = load("ICSA").rolling(4).mean().dropna() / 1000
    return Reading(yoy_pct(lvl).dropna(), spark=lvl,
                   extra=f"Сейчас {lvl.iloc[-1]:.0f} тыс. заявок в неделю (средняя за 4 недели).")


def _sahm(load: Load) -> Reading:
    return Reading(load("SAHMREALTIME"))


# ---------------- Инфляция ----------------

def _cpi(load: Load) -> Reading:
    return Reading(yoy_pct(load("CPIAUCSL")).dropna())


def _wages(load: Load) -> Reading:
    return Reading(yoy_pct(load("CES0500000003")).dropna())


def _breakeven(load: Load) -> Reading:
    return Reading(load("T5YIE"))


# ---------------- ФРС и ставки ----------------

def _fed(load: Load) -> Reading:
    dff = load("DFF")
    core = yoy_pct(load("PCEPILFE")).dropna()
    real = (_monthly(dff) - core).dropna()
    return Reading(real, spark=dff,
                   extra=f"Ставка ФРС {dff.iloc[-1]:.2f}% минус базовая инфляция PCE {core.iloc[-1]:.2f}% "
                         f"(за {core.index[-1]:%m.%Y}).")


def _fed_path(load: Load) -> Reading:
    dgs2 = load("DGS2")
    dff = load("DFF").reindex(dgs2.index, method="ffill")
    s = (dgs2 - dff).dropna()
    return Reading(s, extra=f"Доходность 2-летних {dgs2.iloc[-1]:.2f}% против ставки ФРС {dff.iloc[-1]:.2f}%. "
                            "Двухлетние облигации отражают среднюю ставку, которую рынок ждёт на 2 года вперёд.")


def _curve(load: Load) -> Reading:
    s = load("T10Y3M")
    recent = s[s.index >= s.index[-1] - pd.DateOffset(months=18)]
    if s.iloc[-1] >= 0 and recent.min() < 0:
        return Reading(s, status=WARNING, label="Выход из инверсии",
                       extra="Кривая была инвертирована в последние 18 мес. Исторически рецессия "
                             "начиналась как раз после выхода из инверсии, а не во время неё.")
    return Reading(s)


# ---------------- Кредит и ликвидность ----------------

def _credit(load: Load) -> Reading:
    s = load("BAA10Y")
    extra = ""
    try:
        hy = load("BAMLH0A0HYM2")
        extra = f"Спред high yield (ICE): {hy.iloc[-1]:.2f} п.п. на {hy.index[-1]:%d.%m.%Y}."
    except Exception:
        pass
    return Reading(s, extra=extra)


def _net_liquidity(load: Load) -> Reading:
    walcl = load("WALCL")                                                      # млн $
    tga = load("WTREGEN").reindex(walcl.index, method="ffill")                 # млн $
    rrp = load("RRPONTSYD").reindex(walcl.index, method="ffill").fillna(0) * 1000  # млрд → млн
    lvl = ((walcl - tga - rrp) / 1e6).dropna()                                 # трлн $
    return Reading(_change(lvl, 3), spark=lvl,
                   extra=f"Сейчас {lvl.iloc[-1]:.2f} трлн $ = баланс ФРС − TGA − обратное РЕПО.")


def _interest_burden(load: Load) -> Reading:
    s = (load("A091RC1Q027SBEA") / load("GDP") * 100).dropna()
    return Reading(s)


# ---------------- Оценка ----------------

def _cape(load: Load) -> Reading:
    return Reading(load("CAPE"))


def _buffett(load: Load) -> Reading:
    s = (load("BOGZ1LM893064105Q") / 1000 / load("GDP") * 100).dropna()
    # У этого ряда своя шкала (все корпорации к ВВП, а не Wilshire 5000 к ВНП),
    # поэтому зоны — по перцентилям его собственной истории.
    q = s.quantile([0.5, 0.8, 0.95])
    bands = [(q[0.5], GOOD, "Ниже медианы"), (q[0.8], WARNING, "Выше нормы"), (q[0.95], SERIOUS, "Дорого")]
    return Reading(s, bands=bands,
                   extra=f"Медиана с {s.index[0]:%Y} г. — {q[0.5]:.0f}%, 80-й перцентиль — {q[0.8]:.0f}%, "
                         f"95-й — {q[0.95]:.0f}%.")


def _erp(load: Load) -> Reading:
    ey = 100 / load("CAPE")
    s = (ey - _monthly(load("DFII10"))).dropna()
    return Reading(s, extra=f"Доходность акций (1/CAPE) {ey.iloc[-1]:.2f}% минус реальная доходность "
                            f"10-летних облигаций {load('DFII10').iloc[-1]:.2f}%.")


# ---------------- Рынок и сентимент ----------------

def _trend(load: Load) -> Reading:
    states = []
    for key in ("^GSPC", "^IXIC"):
        p = load(key)
        ma = p.rolling(200).mean()
        states.append((p.iloc[-1] > ma.iloc[-1], ma.iloc[-1] > ma.iloc[-21]))
    spx = load("^GSPC")
    s = ((spx / spx.rolling(200).mean() - 1) * 100).dropna()
    if all(a and r for a, r in states):
        st, lb = GOOD, "Бычий"
    elif all(not a and not r for a, r in states):
        st, lb = CRITICAL, "Медвежий"
    else:
        st, lb = WARNING, "Смешанный"
    detail = "; ".join(f"{n}: {'выше' if a else 'ниже'} 200-дн. средней, средняя {'растёт' if r else 'падает'}"
                       for n, (a, r) in zip(("S&P 500", "NASDAQ"), states))
    return Reading(s, spark=spx, status=st, label=lb, extra=detail + ".")


def _vix(load: Load) -> Reading:
    return Reading(load("VIXCLS"))


def _copper_gold(load: Load) -> Reading:
    cu, au = load("HG=F"), load("GC=F")
    lvl = (cu / au.reindex(cu.index, method="ffill") * 1000).dropna()
    return Reading(_change(lvl, 6), spark=lvl)


INDICATORS: list[Indicator] = [
    # --- Рост ---
    Indicator("permit", "Разрешения на стройку", "Рост", LEADING, "г/г, 3-мес. средняя", "%", _permit,
              [(-15, SERIOUS, "Спад"), (-5, WARNING, "Слабеют")], (GOOD, "Растут"), (-40, 40),
              "Сколько новых домов разрешили строить, изменение за год. Жильё первым реагирует на ставки "
              "и первым разворачивается перед рецессией и после неё.", ["PERMIT"], freq="M", delta_months=3, digits=1),
    Indicator("claims", "Заявки на пособие", "Рост", LEADING, "г/г, 4-нед. средняя", "%", _claims,
              [(10, GOOD, "Спокойно"), (25, WARNING, "Растут")], (CRITICAL, "Резкий рост"), (-40, 80),
              "Сколько людей впервые подали на пособие по безработице, изменение средней за 4 недели к году назад. "
              "Самый быстрый сигнал: увольнения видны здесь раньше, чем в безработице.",
              ["ICSA"], freq="W", digits=0),
    Indicator("sahm", "Правило Сама", "Рост", COINCIDENT, "п.п. над минимумом", "п.п.", _sahm,
              [(0.3, GOOD, "Норма"), (0.5, WARNING, "Растёт")], (CRITICAL, "Сигнал рецессии"), (0, 2),
              "Насколько 3-месячная средняя безработицы поднялась над минимумом последних 12 месяцев. "
              "С 1970 года каждый раз, когда значение доходило до 0.5, экономика уже была в рецессии.",
              ["SAHMREALTIME"], freq="M"),
    # --- Инфляция ---
    Indicator("cpi", "Инфляция CPI", "Инфляция", LAGGING, "г/г", "%", _cpi,
              [(1, WARNING, "Слишком низкая"), (2.5, GOOD, "У цели"), (3.5, WARNING, "Выше цели"), (5, SERIOUS, "Высокая")],
              (CRITICAL, "Очень высокая"), (-2, 10),
              "Рост цен потребительской корзины за год — цифра из новостей. Цель ФРС — около 2%.",
              ["CPIAUCSL"], freq="M", delta_months=12),
    Indicator("wages", "Рост зарплат", "Инфляция", COINCIDENT, "г/г", "%", _wages,
              [(2, WARNING, "Слабый"), (3.5, GOOD, "Умеренный"), (4.5, WARNING, "Давит на цены")],
              (SERIOUS, "Спираль цен"), (0, 9),
              "Средняя почасовая зарплата, изменение за год. Источник устойчивой инфляции услуг: "
              "при росте производительности ~1.5% зарплаты до ~3.5% совместимы с инфляцией 2%.",
              ["CES0500000003"], freq="M", delta_months=12, digits=1),
    Indicator("breakeven", "Ожидания инфляции 5 лет", "Инфляция", LEADING, "рыночные, 5 лет", "%", _breakeven,
              [(1.5, WARNING, "Риск дефляции"), (2.6, GOOD, "Заякорены"), (3, WARNING, "Растут")],
              (SERIOUS, "Отвязались"), (0, 4),
              "Какую среднюю инфляцию на 5 лет закладывает рынок облигаций. Если ожидания «отвязываются» "
              "от 2%, ФРС вынуждена действовать жёстче.", ["T5YIE"]),
    # --- ФРС и ставки ---
    Indicator("fed", "Ставка ФРС", "ФРС и ставки", LAGGING, "реальная: ставка − базовый PCE", "п.п.", _fed,
              [(0, WARNING, "Мягкая"), (1, GOOD, "Нейтральная"), (2, WARNING, "Жёсткая")], (SERIOUS, "Очень жёсткая"),
              (-6, 6),
              "Цена коротких денег. Прибор показывает реальную ставку — ставка минус базовая инфляция: "
              "чем она выше, тем сильнее ФРС тормозит экономику. На мини-графике — сама ставка.",
              ["DFF", "PCEPILFE"], freq="M", delta_months=6),
    Indicator("fed_path", "Куда рынок ведёт ФРС", "ФРС и ставки", LEADING, "2 года − ставка ФРС", "п.п.", _fed_path,
              [(-0.25, NEUTRAL, "Ждёт снижения"), (0.25, GOOD, "Пауза")], (WARNING, "Ждёт повышения"), (-3, 2),
              "Разница доходности 2-летних облигаций и текущей ставки ФРС. Выше нуля — рынок ждёт повышения "
              "ставки (ужесточение впереди), ниже — снижения. ФРС редко идёт против этого ожидания (Дракенмиллер).",
              ["DGS2", "DFF"], delta_months=1),
    Indicator("curve", "Кривая 10 лет − 3 мес.", "ФРС и ставки", LEADING, "наклон кривой", "п.п.", _curve,
              [(0, SERIOUS, "Инверсия"), (0.5, WARNING, "Плоская")], (GOOD, "Нормальная"), (-2, 4),
              "Наклон кривой доходности. Отрицательный (инверсия) — рынок ждёт снижения ставок из-за слабой "
              "экономики. Перед каждой рецессией с 1970-х кривая инвертировалась.", ["T10Y3M"]),
    # --- Кредит и ликвидность ---
    Indicator("credit", "Кредитный спред Baa", "Кредит и ликвидность", COINCIDENT, "Baa − 10 лет", "п.п.", _credit,
              [(2, GOOD, "Кредит открыт"), (3, WARNING, "Напряжение"), (4, SERIOUS, "Стресс")],
              (CRITICAL, "Кредитный кризис"), (0.5, 6),
              "Сколько компании среднего качества переплачивают по долгу сверх государства. Расширение — "
              "кредиторы боятся дефолтов, кредит дорожает для всей экономики.",
              ["BAA10Y", "BAMLH0A0HYM2"],
              extreme_low="Риск никто не оценивает — по Марксу, признак самоуспокоенности",
              extreme_high="Кредит в панике — по Марксу, лучшее время для смелых"),
    Indicator("liquidity", "Чистая ликвидность ФРС", "Кредит и ликвидность", LEADING, "изменение за 3 мес.", "%",
              _net_liquidity, [(-1, WARNING, "Убывает"), (1, NEUTRAL, "Без изменений")], (GOOD, "Прибывает"), (-12, 12),
              "Баланс ФРС минус счёт Минфина (TGA) минус обратное РЕПО — деньги, реально доступные рынку. "
              "Дракенмиллер: рынок в целом двигает ликвидность, а не прибыль.",
              ["WALCL", "WTREGEN", "RRPONTSYD"], freq="W", digits=1),
    Indicator("debt", "Проценты по госдолгу", "Кредит и ликвидность", LAGGING, "% ВВП", "% ВВП", _interest_burden,
              [(2.5, GOOD, "Посильно"), (3.5, WARNING, "Тяжелеет")], (SERIOUS, "Тяжёлая нагрузка"), (0, 5),
              "Процентные расходы государства к ВВП. Далио: когда обслуживание долга съедает растущую долю "
              "экономики, долгосрочный долговой цикл подходит к концу — остаются инфляция, налоги или реструктуризация.",
              ["A091RC1Q027SBEA", "GDP"], freq="Q", delta_months=12),
    # --- Оценка ---
    Indicator("cape", "Shiller CAPE", "Оценка", LAGGING, "P/E за 10 лет", "раз", _cape,
              [(20, GOOD, "Дёшево"), (28, WARNING, "Выше нормы"), (35, SERIOUS, "Дорого")], (CRITICAL, "Очень дорого"),
              (5, 45),
              "Цена S&P 500 к средней реальной прибыли за 10 лет. Плохо предсказывает следующий год, "
              "но хорошо — среднюю доходность на 10 лет: чем выше CAPE, тем она ниже.",
              ["CAPE"], freq="M", digits=1,
              extreme_high="Дороже почти всей истории с 1881 г.", extreme_low="Дешевле почти всей истории — по Грэму, запас прочности"),
    Indicator("buffett", "Индикатор Баффета", "Оценка", LAGGING, "капитализация / ВВП", "%", _buffett,
              [], (CRITICAL, "Очень дорого"), (0, 420),
              "Капитализация всех компаний США к ВВП. Баффет называл его, пожалуй, лучшей единой мерой оценки "
              "рынка. Зоны — по перцентилям собственной истории ряда. Квартальные данные, выходят с задержкой.",
              ["BOGZ1LM893064105Q", "GDP"], freq="Q", delta_months=12, digits=0,
              extreme_high="Исторический максимум оценки"),
    Indicator("erp", "Премия акций над облигациями", "Оценка", LAGGING, "1/CAPE − реальная 10 лет", "п.п.", _erp,
              [(1, SERIOUS, "Почти нет"), (3, WARNING, "Низкая")], (GOOD, "Высокая"), (-2, 10),
              "Доходность акций (1/CAPE) минус реальная доходность 10-летних облигаций — сколько акции платят "
              "сверх безрискового вложения. По Грэму — запас прочности рынка в целом.",
              ["CAPE", "DFII10"], freq="M", delta_months=12,
              extreme_low="Облигации конкурируют с акциями сильнее, чем почти когда-либо"),
    # --- Рынок и сентимент ---
    Indicator("trend", "Первичный тренд", "Рынок и сентимент", COINCIDENT, "S&P 500 к 200-дн. средней", "%", _trend,
              [(-10, CRITICAL, "Глубоко ниже"), (0, WARNING, "Ниже средней")], (GOOD, "Выше средней"), (-30, 30),
              "Primary Trend Projector Прудена: S&P 500 и NASDAQ выше растущей 200-дневной средней — бычий рынок, "
              "оба ниже падающей — медвежий. Стрелка — насколько S&P 500 выше своей 200-дневной средней.",
              ["^GSPC", "^IXIC"], delta_months=1, digits=1),
    Indicator("vix", "VIX — индекс страха", "Рынок и сентимент", COINCIDENT, "ожидаемая волатильность", "пт", _vix,
              [(20, GOOD, "Спокойно"), (30, WARNING, "Нервно")], (SERIOUS, "Страх"), (9, 60),
              "Ожидаемая волатильность S&P 500 на месяц. Экстремумы — контр-индикатор.",
              ["VIXCLS"], delta_months=1, digits=1,
              extreme_high="Паника — по Баффету, время покупать, а не продавать",
              extreme_low="Полное спокойствие — рынок не ждёт неприятностей"),
    Indicator("copper_gold", "Медь / золото", "Рынок и сентимент", LEADING, "изменение за 6 мес.", "%", _copper_gold,
              [(-5, WARNING, "Бегство в защиту"), (5, NEUTRAL, "Без изменений")], (GOOD, "Аппетит растёт"), (-40, 40),
              "Медь нужна растущей промышленности, золото покупают в страхе. Растущее отношение — рынок ставит "
              "на рост экономики.", ["HG=F", "GC=F"], delta_months=1, digits=1),
]


@dataclass
class Result:
    """Готовое к отрисовке состояние прибора."""
    ind: Indicator
    r: Reading
    value: float
    status: str
    label: str
    bands: Bands
    percentile: float
    extreme: str = ""                  # "", "low", "high"
    stale: bool = False
    notes: list[str] = field(default_factory=list)


STALE_DAYS = {"D": 10, "W": 21, "M": 75, "Q": 200}


def evaluate(ind: Indicator, load: Load, today: pd.Timestamp | None = None) -> Result:
    r = ind.compute(load)
    s = r.series.dropna()
    value = float(s.iloc[-1])
    bands = r.bands if r.bands is not None else ind.bands
    status, label = (r.status, r.label) if r.status else classify(value, bands, ind.top)
    pct = float((s < value).mean() * 100)
    extreme = "low" if pct <= 5 else "high" if pct >= 95 else ""
    today = today or pd.Timestamp.today().normalize()
    stale = (today - s.index[-1]).days > STALE_DAYS[ind.freq]
    return Result(ind, r, value, status, label, bands, pct, extreme, stale)


def group_status(statuses: list[str]) -> tuple[str, str]:
    score = sum(SCORE[s] for s in statuses) / len(statuses)
    return classify(score, [(-1, CRITICAL, "Тревога"), (-0.34, SERIOUS, "Напряжение"), (0.34, WARNING, "Смешанно")],
                    (GOOD, "Норма"))
