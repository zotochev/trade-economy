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

    @property
    def order(self) -> int:
        """Номер блока на экранах — в порядке контейнеров для трейдера (num — внутренний ключ)."""
        return ORDER[self.num]


BLOCKS = [
    Block(1, "Крипта и мировые деньги", "среда",
          "Ставки ФРС, доллар и ликвидность: насколько биткоин ходит вместе с акциями роста.",
          "views/crypto/world.py"),
    Block(2, "Институциональные двери", "среда",
          "Спотовые ETF, фьючерсы CME и базисная торговля, компании, которые копят биткоин на долг.",
          "views/crypto/doors.py"),
    Block(3, "Регулирование и шоки", "среда",
          "Решения регуляторов, суды, запреты и геополитика — события, которые меняют правила игры.",
          "views/crypto/rules.py"),
    Block(4, "Плечо и ликвидации", "устройство",
          "Фьючерсы, цена ликвидации, фандинг, открытый интерес — почему падения в крипте такие резкие.",
          "views/crypto/leverage.py"),
    Block(5, "Биржи, стейблкоины и точки отказа", "устройство",
          "Где лежат деньги крипты и что ломается: Tether и Circle, депеги, банкротства бирж.",
          "views/crypto/plumbing.py"),
    Block(6, "Предложение и держатели", "устройство",
          "Откуда берутся монеты, майнеры, долгосрочные держатели — кто и когда продаёт.",
          "views/crypto/supply.py"),
    Block(7, "Альткоины и токеномика", "устройство",
          "Разлоки, разводнение, сектора — почему альткоины ведут себя иначе, чем биткоин.",
          "views/crypto/alts.py"),
    Block(8, "Циклы", "устройство",
          "Четырёхлетний цикл, типичные просадки и откуда берутся пузыри.", "views/crypto/cycles.py"),
    Block(10, "Вайкофф: чтение фаз", "практика",
          "Накопление, рост, распределение, падение — язык фаз на графике и что из него подтверждается данными.",
          "views/crypto/wyckoff.py"),
    Block(9, "Риск-менеджмент и устройство торгов", "практика",
          "Размер позиции, плечо против волатильности, выходные и тонкие сессии, календарь событий.",
          "views/crypto/risk.py"),
]
BY_NUM = {b.num: b for b in BLOCKS}


# ---------- модель крипты по методу «Смыслы-Инварианты-Граф» ----------
@dataclass(frozen=True)
class Container:
    title: str
    why: str          # зачем существует
    defines: str      # что гарантирует / определяет
    blocks: tuple     # внутренние номера блоков


GOAL = "Понять, что двигает цену биткоина и альткоинов и что может уничтожить позицию с плечом."
CONTAINERS = [
    Container("Плечо", "Усилитель: позиции в долг через фьючерсы.",
              "Скорость и резкость движений и то, переживёт ли их ваша позиция.", (4,)),
    Container("Доллары и биржи", "Деньги внутри крипты: стейблкоины, биржи, залог.",
              "Топливо для покупок и залог под плечо — и главная точка отказа.", (5,)),
    Container("Альткоины", "Тот же рынок, только с усилением.",
              "Бета к биткоину больше 1 и риск разводнения токенов.", (7,)),
    Container("Среда: деньги и правила", "Погода для всех рисковых активов: ставки, доллар, регуляторы.",
              "Фон — дешёвые или дорогие деньги, правила игры. Большую часть движений не решает.", (1, 3)),
    Container("Двери для крупных денег", "Регулируемые обёртки для фондов: ETF, CME, компании.",
              "Отделяет настоящий спрос от арбитража, который цену не толкает.", (2,)),
    Container("Монеты, держатели и циклы", "Кто владеет монетами, по какой цене купил и когда продаёт.",
              "Тормоз роста (держатели в прибыли), продавцы на дне (майнеры), ритм цикла.", (6, 8)),
    Container("Ваш счёт", "Переводит модель в решения.",
              "Как читать фазы рынка, размер позиции и выживание счёта. На рынок не влияет.", (10, 9)),
]
ORDER = {n: i + 1 for i, n in enumerate(b for c in CONTAINERS for b in c.blocks)}


@dataclass(frozen=True)
class Law:
    text: str
    kind: str         # арифметика | механизм | факт | проверен на истории | спорный
    block: int        # внутренний номер блока, где закон показан на данных
    caveat: str = ""  # где закон не работает
    part: str = ""    # ключ внутренней части блока (BLOCK_SKELETON), где закон доказывается
    core: bool = True  # показывать на странице всей модели; False — только внутри блока


@dataclass(frozen=True)
class Part:
    """Внутренний контейнер блока: зачем существует и что гарантирует."""
    key: str
    title: str
    why: str
    guarantees: str


LAWS = [
    Law("Ликвидация наступает при движении против вас примерно на 100/плечо %.", "арифметика", 4,
        "При кросс-марже плечо считается от всего счёта; у альткоинов поддерживающая маржа выше; комиссии сокращают "
        "запас.", part="pos"),
    Law("Стоп ставите вы, ликвидацию — биржа. Стоп должен стоять раньше ликвидации.", "механизм", 4,
        "В каскаде стоп исполняется с проскальзыванием.", part="pos", core=False),
    Law("Колебания важнее направления: с высоким плечом позицию выбивает по дороге, даже если направление угадано.",
        "проверен на истории", 4, "С 2023 года рынок спокойнее; у альткоинов риск в разы выше.", part="noise"),
    Law("Удержание стоит фандинг × плечо в год от залога; обычно платят лонги.", "арифметика", 4,
        "Знак может смениться, ставка плавает.", part="fund", core=False),
    Law("Принудительные продажи толкают цену дальше — поэтому обвалы каскадные, а самые резкие падения случаются "
        "внутри дня.", "проверен на истории", 4, "Глубину каскада заранее не знать.", part="crowd"),
    Law("Фандинг показывает, сколько плеча смотрит в одну сторону, но не говорит, когда начнётся обвал.", "спорный",
        4, "После 2023 года крайних значений почти нет; 10.10.2025 каскад начался без перегрева.", part="crowd"),
    Law("CVD показывает, кто давит прямо сейчас — покупатели монет на споте или игроки с плечом во фьючерсах, — но "
        "на дневках не предсказывает, чем кончится рост.", "спорный", 4,
        "Одна биржа (Binance); внутри дня CVD информативнее, чем на дневках.", part="crowd", core=False),
    Law("Убыток сверх залога ложится на страховой фонд биржи, а затем на прибыльные позиции другой стороны.",
        "механизм", 4, "Бывает редко, правила у бирж разные.", part="adl", core=False),
    Law("Стейблкоинов становится больше вместе с ростом цены, а не заранее: это след притока, а не его прогноз.",
        "проверен на истории", 5, "Сокращение итога не всегда вывод денег (UST 2022, BUSD 2023).", part="money",
        core=False),
    Law("Стейблкоин стоит $1, пока открыто погашение и есть долларовые резервы.", "механизм", 5,
        "На отдельной бирже цена может упасть, даже когда в среднем по рынку $1 (USDe на Binance, 10.10.2025).",
        part="peg"),
    Law("Проценты по резервам забирает эмитент: его доход ≈ резервы в векселях × ставка ФРС.", "арифметика", 5,
        "Часть резервов не в векселях; переоценка золота и биткоина меняет настоящую прибыль.", part="rates",
        core=False),
    Law("Монеты на бирже — долг биржи перед вами, а не ваше имущество.", "факт", 5, part="exchanges"),
    Law("Эмитент может заморозить стейблкоины на любом адресе по запросу властей.", "факт", 5,
        "Для пользователей под санкционным риском это главный риск стейблкоина.", part="control", core=False),
    Law("Альткоины идут за биткоином примерно один к одному, но с большим собственным риском: колеблются сильнее и "
        "падают глубже.", "проверен на истории", 7, "Список — сегодняшние выжившие; у отдельных токенов свои риски: "
        "разлоки, делистинг, обнуление."),
    Law("С 2020 года биткоин — рисковый актив: в плохие недели падает вместе с акциями роста. Связь одновременная, "
        "а не прогноз.", "проверен на истории", 1, "До 2020 года связи не было."),
    Law("Аварии внутри крипты бьют сильнее регуляторов.", "спорный", 3,
        "Событий мало, и аварии выбраны задним числом — потому что был обвал."),
    Law("Деньги в ETF и стейблкоины приходят вместе с ценой и вслед за ней, а не перед ней.",
        "проверен на истории", 2, "История ETF — с 2024 года."),
    Law("Не каждый приток толкает цену: базисная сделка выглядит как покупка, но ставки на рост в ней нет.",
        "механизм", 2),
    Law("Цену решает спрос, а не выпуск монет: новых монет — меньше 1% в год.", "механизм", 6),
    Law("Держатели в большой прибыли тормозят рост, держатели в убытке дают дно.", "спорный", 6,
        "Циклов всего четыре."),
    Law("Размер позиции считают от стопа: сколько готовы потерять, делённое на расстояние до стопа. Плечо — "
        "следствие, а не выбор.", "арифметика", 9),
    Law("Потеря и возврат несимметричны: после −50% нужно +100%, чтобы вернуться.", "арифметика", 9),
    Law("Результат решает не доля удачных сделок, а ожидание: доля удачных × (прибыль / риск) − доля неудачных. "
        "Половина удачных сделок при прибыли вдвое больше риска — уже плюс.", "арифметика", 9),
    Law("Серии убытков неизбежны: даже при половине удачных сделок 5–7 убытков подряд за сотню сделок — "
        "обычное дело.", "арифметика", 9),
    Law("Ложные пробои границ диапазона (spring и upthrust по Вайкоффу) на дневках биткоина и эфира сами по себе "
        "не дают преимущества.", "проверен на истории", 10, "Проверены механические правила; опытный глаз видит "
        "больше, но это уже не проверить на данных."),
    Law("Фазы Вайкоффа описывают те же силы, что модель: накопление — держатели в убытке и вынужденные продавцы "
        "кончились, распределение — держатели в прибыли продают в спрос.", "механизм", 10),
]
# Скелет блоков: внутренние части в порядке, в котором их загружать в голову
BLOCK_SKELETON = {
    4: [
        Part("pos", "Позиция в долг", "Объяснить, что покупается: залог плюс заём биржи.",
             "Результат = движение × плечо; есть цена, при которой биржа закроет позицию сама."),
        Part("noise", "Шум против запаса", "Сравнить запас до ликвидации с обычными колебаниями цены.",
             "Чем выше плечо и дольше удержание, тем чаще позицию выбивает — даже при верном направлении."),
        Part("fund", "Плата за удержание", "Показать, что держать позицию стоит денег.",
             "Фандинг списывается, пока позиция открыта, и умножается на плечо."),
        Part("crowd", "Толпа с плечом и каскад", "Перейти от вашей позиции к сумме чужих.",
             "Чужие ликвидации двигают цену к вашей; фандинг и открытый интерес показывают, сколько этого топлива."),
        Part("adl", "Когда залога не хватило", "Показать, кто платит за обвал сверх залога.",
             "Биржа свой минус не берёт: сначала страховой фонд, потом принудительное закрытие прибыльных позиций."),
    ],
}
BLOCK_SKELETON[5] = [
    Part("money", "Доллары внутри крипты", "Показать, на чём идёт торговля и что лежит в залоге.",
         "Стейблкоины — топливо для покупок и залог под плечо; выпускают их только крупные клиенты эмитента."),
    Part("peg", "Что держит $1", "Объяснить, почему токен стоит доллар и когда перестаёт.",
         "Пока открыто погашение и есть резервы — цена ≈ $1; сомнение в резервах запускает бегство."),
    Part("rates", "Эмитенты и ставки", "Показать, кто зарабатывает на стейблкоинах.",
         "Эмитент держит резервы в векселях и забирает проценты — ставки ФРС доходят до крипты."),
    Part("exchanges", "Биржи", "Показать, где лежат монеты и что с ними бывает.",
         "Монеты на бирже — долг биржи; её банкротство превращает клиентов в кредиторов."),
    Part("control", "Кто может заморозить", "Показать внешние рычаги над этими деньгами.",
         "Эмитенты замораживают адреса по запросу властей; регуляторы задают правила резервов."),
]
# Граф блока: (откуда, куда, что передаётся). Внешние узлы — в квадратных скобках.
BLOCK_EDGES = {
    4: [
        ("[Доллары и биржи]", "Позиция в долг", "залог"),
        ("[Доллары и биржи]", "Позиция в долг", "депег залога"),
        ("Позиция в долг", "Шум против запаса", "запас ≈ 100/плечо %"),
        ("[Цена биткоина]", "Шум против запаса", "колебания"),
        ("Позиция в долг", "Плата за удержание", "размер позиции"),
        ("Плата за удержание", "Толпа с плечом и каскад", "тот же фандинг — у всех"),
        ("Шум против запаса", "Толпа с плечом и каскад", "ликвидации"),
        ("Толпа с плечом и каскад", "[Цена биткоина]", "принудительные продажи"),
        ("Толпа с плечом и каскад", "Когда залога не хватило", "убыток сверх залога"),
        ("[Альткоины]", "Толпа с плечом и каскад", "тонкий рынок"),
        ("Шум против запаса", "[Ваш счёт]", "выбит?"),
        ("Плата за удержание", "[Ваш счёт]", "расход"),
        ("Когда залога не хватило", "[Ваш счёт]", "закрыли без спроса"),
    ],
    5: [
        ("[Цена биткоина]", "Доллары внутри крипты", "приток вслед за ценой"),
        ("Доллары внутри крипты", "[Плечо]", "залог"),
        ("Доллары внутри крипты", "[Цена биткоина]", "покупки"),
        ("Что держит $1", "Доллары внутри крипты", "доверие к $1"),
        ("[Среда: ставки ФРС]", "Эмитенты и ставки", "ставка по векселям"),
        ("Эмитенты и ставки", "Что держит $1", "резервы"),
        ("[Банки]", "Что держит $1", "крах банка эмитента"),
        ("Биржи", "Доллары внутри крипты", "где лежат"),
        ("Биржи", "[Цена биткоина]", "банкротство биржи"),
        ("Кто может заморозить", "Доллары внутри крипты", "заморозка адресов"),
        ("Что держит $1", "[Плечо]", "депег залога → ликвидации"),
        ("Биржи", "[Ваш счёт]", "долг биржи"),
    ],
}


# Петли: где цепочка возвращается в цену и сама себя усиливает (внутренний номер блока — где показана)
LOOPS = [
    ("Петля плеча", "цена ↓ → ликвидации → вынужденные продажи → цена ↓. На росте наоборот: шорты закрываются "
                    "покупками.", 4),
    ("Залог и депег", "стейблкоин или токен-залог теряет $1 → позиции под ним ликвидируются → цена ↓.", 5),
    ("Петля ETF", "цена ↑ → в ETF приходят новые деньги → покупка монет → цена ↑.", 2),
    ("Петля компаний-казначейств", "цена ↑ → премия к стоимости монет → компания выпускает акции и покупает "
                                   "ещё → цена ↑. На спаде может развернуться.", 2),
    ("Тормоз держателей", "цена ↑ → у держателей большая прибыль → они продают → рост замедляется.", 6),
    ("Петля майнеров", "цена ↓ → выручка майнеров ниже затрат → продают запасы → цена ↓.", 6),
]


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


# ---------- блок 1: плечо и ликвидации ----------
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


# ---------- блок 6: институциональные двери ----------
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


# ---------- блок 2: биржи, стейблкоины и точки отказа ----------
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


def depegs(load: Load, coin: str, below: float = 0.99) -> pd.DataFrame:
    """Дни, когда дневная цена стейблкоина (DefiLlama, с 2021 года) была ниже below, сгруппированные в эпизоды."""
    p = load(f"PEG_{coin}")
    bad = p[p < below]
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


# ---------- блок 5: регулирование и шоки ----------
# (дата, событие, вид, что произошло). Вид: «рег+» — правила смягчают, «рег−» — ужесточают, «шок» — авария внутри
# крипты, «внешний» — шок снаружи (пандемия, банки, пошлины). Список составлен вручную, задним числом.
EVENTS = [
    ("2017-09-04", "Китай запрещает ICO", "рег−", "Народный банк Китая запретил размещения токенов; вскоре закрылись и местные биржи."),
    ("2021-05-21", "Китай: удар по майнингу", "рег−", "Госсовет Китая объявил о борьбе с майнингом биткоина."),
    ("2021-09-24", "Китай запрещает операции с криптой", "рег−", "Все операции с криптой объявлены незаконными."),
    ("2021-10-19", "Первый фьючерсный ETF в США", "рег+", "Начал торговаться ETF на биткоин-фьючерсы (BITO)."),
    ("2023-06-05", "SEC подаёт в суд на Binance", "рег−", "Регулятор США обвинил крупнейшую биржу в нарушениях."),
    ("2023-06-06", "SEC подаёт в суд на Coinbase", "рег−", "На следующий день — иск к крупнейшей бирже США."),
    ("2023-06-15", "BlackRock подаёт заявку на ETF", "рег+", "Крупнейший управляющий мира попросил разрешить спотовый ETF."),
    ("2023-07-13", "Суд по Ripple", "рег+", "Суд США решил, что продажи XRP на биржах не были продажей ценных бумаг."),
    ("2023-08-29", "Grayscale выигрывает суд у SEC", "рег+", "Суд признал отказ SEC в ETF необоснованным."),
    ("2023-11-21", "Binance платит Минюсту США", "рег−", "Биржа признала нарушения, заплатила $4,3 млрд, глава ушёл."),
    ("2024-01-10", "SEC одобряет спотовые ETF", "рег+", "Одобрены спотовые биткоин-ETF, торги — с 11 января."),
    ("2024-05-23", "SEC одобряет эфир-ETF", "рег+", "Одобрены заявки на спотовые эфир-ETF."),
    ("2024-11-05", "Выборы в США", "рег+", "Победили кандидаты, обещавшие мягкое регулирование крипты."),
    ("2025-01-23", "Указ о цифровых активах", "рег+", "Президент США подписал указ о поддержке крипто-индустрии."),
    ("2025-03-06", "Указ о резерве биткоина", "рег+", "Создан государственный резерв из уже конфискованных биткоинов — без покупок."),
    ("2025-07-18", "Закон GENIUS о стейблкоинах", "рег+", "Первый федеральный закон США о стейблкоинах."),
    ("2020-03-12", "Пандемия: чёрный четверг", "внешний", "Паника на всех рынках, каскад ликвидаций."),
    ("2022-05-09", "Крах UST", "шок", "Алгоритмический стейблкоин потерял привязку и обнулился."),
    ("2022-11-08", "Крах FTX", "шок", "Биржа остановила вывод средств, деньги клиентов растрачены."),
    ("2023-03-10", "Крах банка SVB", "внешний", "Рухнул банк, где лежала часть резервов USDC."),
    ("2025-02-21", "Взлом биржи Bybit", "шок", "Хакеры увели около $1,5 млрд в эфире — крупнейшая кража в истории крипты."),
    ("2025-10-10", "Пошлины против Китая", "внешний", "Объявление о пошлинах вечером пятницы, рекордные ликвидации."),
]


def month_up_share(load: Load, since: str = "2017") -> float:
    """Базовая линия: доля всех дней, когда через 30 дней биткоин был выше, %."""
    btc = load("BTC-USD").dropna()[since:]
    return float(((btc.shift(-30) / btc - 1).dropna() > 0).mean() * 100)


def event_study(load: Load) -> pd.DataFrame:
    """Реакция биткоина на события: изменение от закрытия накануне до следующего дня, через неделю и месяц, %, и
    размер дневной реакции в обычных колебаниях (σ за 2 дня по прошлым 60 дням)."""
    btc = load("BTC-USD").dropna()
    btc.index = btc.index.normalize()
    r = np.log(btc).diff()
    rows = []
    for d, title, kind, _ in EVENTS:
        i = btc.index.get_indexer([pd.Timestamp(d)], method="bfill")[0]
        p0 = float(btc.iloc[i - 1])
        sigma = float(r.iloc[i - 60:i - 1].std() * 100 * np.sqrt(2))

        def ch(n: int) -> float:
            return float((btc.iloc[i + n] / p0 - 1) * 100) if i + n < len(btc) else float("nan")
        rows.append({"Дата": pd.Timestamp(d), "Событие": title, "Вид": kind,
                     "За месяц до, %": float((p0 / btc.iloc[max(i - 31, 0)] - 1) * 100), "За 2 дня, %": ch(1),
                     "В обычных колебаниях": ch(1) / sigma, "За неделю, %": ch(7), "За месяц, %": ch(30)})
    return pd.DataFrame(rows).sort_values("Дата")


# ---------- блок 7: предложение и держатели ----------
HALVINGS = ["2012-11-28", "2016-07-09", "2020-05-11", "2024-04-20"]


def onchain(load: Load) -> pd.DataFrame:
    """Цена, реализованная цена (средняя цена последнего перемещения монет), MVRV, монеты на биржах (% всех)."""
    mc, mv, sup = load("CM_MCAP"), load("CM_MVRV"), load("CM_SUPPLY")
    return pd.DataFrame({"price": mc / sup, "realized": mc / mv / sup, "mvrv": mv,
                         "exch": load("CM_EXSUP") / sup * 100}).dropna(subset=["price", "mvrv"])


def mvrv_table(load: Load, since: str = "2013") -> pd.DataFrame:
    """Что было с ценой через год в зависимости от MVRV (дни с since)."""
    o = onchain(load)
    x = pd.DataFrame({"m": o["mvrv"], "f": (o["price"].shift(-365) / o["price"] - 1) * 100}).dropna()[since:]
    x["b"] = pd.cut(x["m"], [0, 1, 1.5, 2, 3, 100], labels=["ниже 1", "1–1,5", "1,5–2", "2–3", "выше 3"])
    t = x.groupby("b", observed=True)["f"].agg(["median", lambda s: (s > 0).mean() * 100, "size"])
    t.columns = ["Цена через год, медиана %", "Через год выше, % дней", "Дней"]
    t.loc["все дни"] = [x["f"].median(), (x["f"] > 0).mean() * 100, len(x)]
    return t


def hash_ribbon(load: Load, days: int = 90) -> dict[str, float]:
    """Проверка «капитуляции майнеров»: средний хешрейт за 30 дней ниже среднего за 60 — капитуляция; её конец —
    популярный сигнал покупки. Сравниваем цену через days дней после сигнала со всеми днями."""
    h = load("CM_HASH")
    p = onchain(load)["price"]
    cap = h.rolling(30).mean() < h.rolling(60).mean()
    ends = cap.index[(~cap) & cap.shift(1, fill_value=False)]
    kept = []
    for d in ends[ends > "2012"]:
        if not kept or (d - kept[-1]).days > 60:
            kept.append(d)
    f = ((p.shift(-days) / p - 1) * 100)
    ev, base = f.reindex(kept).dropna(), f["2012":].dropna()
    return {"n": len(ev), "ev_med": float(ev.median()), "ev_up": float((ev > 0).mean() * 100),
            "base_med": float(base.median()), "base_up": float((base > 0).mean() * 100)}


def halving_table(load: Load) -> pd.DataFrame:
    p = onchain(load)["price"]
    rows = {}
    for d in HALVINGS:
        t = pd.Timestamp(d)
        rows[t.year] = {"Год до, %": (p[:t].iloc[-1] / p[:t - pd.Timedelta(days=365)].iloc[-1] - 1) * 100,
                        "Год после, %": (p[:t + pd.Timedelta(days=365)].iloc[-1] / p[:t].iloc[-1] - 1) * 100
                        if t + pd.Timedelta(days=365) <= p.index[-1] else np.nan}
    return pd.DataFrame(rows).T


def hashprice(load: Load) -> pd.Series:
    """Выручка майнеров на единицу мощности, $ в день на петахеш в секунду."""
    return (load("BC_MINER_REV") / (load("CM_HASH") / 1e3)).dropna()


# ---------- блок 3: альткоины и токеномика ----------
ALTS = {"ETH-USD": "Эфир", "SOL-USD": "Solana", "XRP-USD": "XRP", "BNB-USD": "BNB", "DOGE-USD": "Dogecoin",
        "ADA-USD": "Cardano", "AVAX-USD": "Avalanche", "LINK-USD": "Chainlink"}


def alt_table(load: Load, since: str = "2021") -> pd.DataFrame:
    """Альткоины против биткоина по неделям с since: бета, корреляция, во сколько раз волатильнее, просадки."""
    b = np.log(load("BTC-USD").dropna()).resample("W-FRI").last().diff()[since:]
    rows = {}
    for key, name in ALTS.items():
        p = load(key).dropna()
        x = np.log(p).resample("W-FRI").last().diff()[since:].dropna()
        bb = b.reindex(x.index)
        rows[name] = {"Бета к биткоину": x.cov(bb) / bb.var(), "Корреляция": x.corr(bb),
                      "Волатильнее биткоина, раз": x.std() / bb.std(),
                      "От максимума сейчас, %": float((p.iloc[-1] / p.max() - 1) * 100),
                      f"Худшая просадка с {since}, %": float((p[since:] / p[since:].cummax() - 1).min() * 100)}
    return pd.DataFrame(rows).T


def upcoming_unlocks(days: int = 30) -> list[dict] | None:
    """Крупные разлоки токенов на ближайшие days дней из календаря trade-news. None — сервис молчит."""
    from datetime import date, timedelta

    from core import flows
    try:
        ev = flows.calendar(date.today(), date.today() + timedelta(days=days))
    except Exception:
        return None
    return [e for e in ev if e["type"] == "token_unlock"]


# ---------- блок 8: циклы ----------
def bear_markets(load: Load, depth: float = -50, since: str = "2011") -> pd.DataFrame:
    """Медвежьи рынки биткоина (падение от вершины глубже depth %): вершина, дно, глубина, сколько дней падали и
    сколько возвращались к прежней вершине."""
    p = onchain(load)["price"][since:]
    dd = (p / p.cummax() - 1) * 100
    rows, start, inb = [], None, False
    for d, v in dd.items():
        if not inb and v < depth:
            inb, start = True, p[:d].idxmax()
        if inb and v == 0:
            seg = dd[start:d]
            rows.append((start, seg.idxmin(), seg.min(), d))
            inb = False
    if inb:
        seg = dd[start:]
        rows.append((start, seg.idxmin(), seg.min(), None))
    return pd.DataFrame([{"Вершина": a.date(), "Цена на вершине, $": float(p[a]), "Дно": b.date(), "Глубина, %": m,
                          "Дней до дна": (b - a).days, "Дней от дна до новой вершины": (c - b).days if c is not None
                          else np.nan} for a, b, m, c in rows])


def halving_peaks(load: Load) -> pd.DataFrame:
    """Через сколько дней после каждого халвинга была вершина цикла (максимум за следующие 900 дней)."""
    p = onchain(load)["price"]
    rows = []
    for h in HALVINGS:
        t = pd.Timestamp(h)
        w = p[t:t + pd.Timedelta(days=900)]
        rows.append({"Халвинг": t.date(), "Вершина": w.idxmax().date(), "Дней после халвинга": (w.idxmax() - t).days,
                     "Рост от халвинга до вершины, %": float((w.max() / p[:t].iloc[-1] - 1) * 100)})
    return pd.DataFrame(rows)


def yearly_vol(load: Load) -> pd.Series:
    p = onchain(load)["price"]["2011":]
    r = np.log(p).diff()
    return r.groupby(r.index.year).std() * np.sqrt(365) * 100


def container_of(num: int) -> Container:
    return next(c for c in CONTAINERS if num in c.blocks)


# Верх каждого блока: смысл одной фразой и связи «откуда → сюда → куда» (законы блока берутся из LAWS)
MEANING = {
    4: "Плечо ничего не двигает само: оно усиливает любое движение и решает, переживёт ли его ваша позиция.",
    5: "На этих долларах идёт торговля и держится залог: если они подводят, ломается всё, что на них стоит.",
    7: "Альткоины — тот же рынок, но рискованнее: куда биткоин, туда и они, только с большими колебаниями, а у многих "
       "сверху постоянное давление продаж.",
    1: "Ставки и доллар задают погоду для всех рисковых активов, но большую часть движений биткоина решает сама "
       "крипта.",
    3: "Правила открывают и закрывают двери для денег, а аварии внутри крипты бьют по доверию сильнее любых "
       "регуляторов.",
    2: "Через ETF, CME и компании приходят большие деньги — но не каждый приток означает ставку на рост.",
    6: "Цену решает не выпуск новых монет, а то, по какой цене купили нынешние держатели и когда им выгодно продать.",
    8: "Цикл — не отдельная часть рынка, а поведение всех частей во времени: петли разгоняют рост и падение, пока "
       "не кончатся новые покупатели или вынужденные продавцы.",
    10: "Вайкофф читает график как следы крупных игроков: где они набирают позицию, где раздают её толпе и как "
        "проверяют, остались ли продавцы.",
    9: "Рынок вы не контролируете — контролируете только размер позиции и то, сколько потеряете, если ошиблись.",
}
FLOW = {
    4: "залог из «Долларов и бирж» → **плечо** → цена биткоина и альткоинов → ваш счёт",
    5: "ставки ФРС → доход эмитентов → **стейблкоины и биржи** → залог для плеча, внутренние шоки цены",
    7: "цена биткоина → **альткоины** (плюс собственный риск) → тонкий рынок → каскады плеча",
    1: "ФРС и доллар (модель экономики, слои 2–3) → **аппетит к риску** → двери для денег, доход эмитентов",
    3: "регуляторы → **правила** → двери для денег; аварии бирж и стейблкоинов → цена и плечо",
    2: "мировые деньги → **ETF, CME, компании** → покупка монет (минус арбитраж) → цена → снова приток",
    6: "выпуск → майнеры → их продажи; спрос (ETF, компании) → **держатели** → их продажи в прибыли (тормоз роста)",
    8: "все петли модели → **рост → вершина → падение → дно**",
    10: "держатели, плечо, потоки ETF → **фазы на графике** → контекст для решения → размер позиции (блок 10)",
    9: "вся модель → **ваш счёт**: размер позиции, стоп, плечо → выживание счёта",
}
KIND_COLOR = {"арифметика": "blue", "механизм": "blue", "факт": "blue", "проверен на истории": "green",
              "спорный": "orange"}



# ---------- блок 10: риск-менеджмент ----------
FEE = 0.05   # комиссия тейкера за сделку, % позиции (вход и выход — дважды)
SLIP = 0.1   # запас на проскальзывание стопа, % позиции


def position(account: float, risk_pct: float, stop_pct: float, fee: float = FEE, slip: float = SLIP) -> dict[str, float]:
    """Размер позиции от стопа: риск на сделку / (расстояние до стопа + комиссии входа и выхода + проскальзывание);
    плечо — позиция / счёт (сколько плеча нужно минимум)."""
    risk = account * risk_pct / 100
    size = risk / ((stop_pct + 2 * fee + slip) / 100)
    return {"risk": risk, "size": size, "lev": size / account}


def expectancy(p_win: float, rr: float) -> float:
    """Ожидаемый результат сделки в долях риска (R): доля удачных × прибыль/риск − доля неудачных."""
    return p_win * rr - (1 - p_win)


def max_streak_odds(p_win: float, trades: int, k: int, sims: int = 4000, seed: int = 0) -> float:
    """Вероятность хотя бы одной серии из k убытков подряд за trades сделок при доле удачных p_win (моделирование)."""
    rng = np.random.default_rng(seed)
    loss = rng.random((sims, trades)) >= p_win
    run = np.zeros(sims, dtype=int)
    best = np.zeros(sims, dtype=int)
    for j in range(trades):
        run = np.where(loss[:, j], run + 1, 0)
        best = np.maximum(best, run)
    return float((best >= k).mean() * 100)


def weekday_stats(load: Load, since: str = "2019-09", top: int = 60) -> pd.DataFrame:
    """По дням недели (UTC): среднее движение за день (модуль изменения закрытия) и сколько из top самых резких
    падений внутри дня пришлось на день."""
    df = candles(load)[since:]
    drop = (df["lo"] / df["c"].shift(1) - 1) * 100
    r = (np.log(df["c"]).diff() * 100).abs()
    worst = drop.nsmallest(top)
    names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    t = pd.DataFrame({"Среднее движение за день, %": r.groupby(r.index.dayofweek).mean(),
                      f"Из {top} худших падений": pd.Series(worst.index.dayofweek).value_counts()})
    t.index = [names[i] for i in t.index]
    return t.fillna(0)



def mvrv_cycle_peaks(load: Load) -> pd.DataFrame:
    """Пик MVRV в каждом цикле — между соседними халвингами (и после последнего)."""
    mv = onchain(load)["mvrv"]
    bounds = [pd.Timestamp(h) for h in HALVINGS] + [mv.index[-1] + pd.Timedelta(days=1)]
    rows = []
    for a, b in zip(bounds[:-1], bounds[1:]):
        w = mv[a:b]
        rows.append({"Цикл": f"{a.year}–{min(b.year, mv.index[-1].year)}", "Пик MVRV": float(w.max()),
                     "Дата пика": w.idxmax().date()})
    return pd.DataFrame(rows)



# ---------- блок 10 (на экране — 9): Вайкофф ----------
def ohlcv(load: Load, coin: str = "BTC") -> pd.DataFrame:
    """Дневные свечи спота Binance: максимум, минимум, закрытие, оборот в $."""
    return pd.concat({"h": load(f"{coin}_HIGH"), "l": load(f"{coin}_LOW"), "c": load(f"{coin}_CLOSE"),
                      "v": load(f"{coin}_QVOL")}, axis=1, sort=True).dropna()


def _thin(idx: pd.Index, gap: int = 20) -> list:
    """Оставить события, разделённые не меньше чем gap дней: соседние дни — один и тот же случай."""
    out = []
    for d in idx:
        if not out or (d - out[-1]).days > gap:
            out.append(d)
    return out


def wyckoff_marks(df: pd.DataFrame, n: int = 60) -> pd.DataFrame:
    """Границы диапазона за n дней и события: spring — минимум ниже границы, закрытие снова выше; upthrust — максимум
    выше верхней границы, закрытие снова ниже; «усилие без результата» — оборот вдвое выше обычного при движении
    меньше 1%."""
    lo = df["l"].rolling(n).min().shift(1)
    hi = df["h"].rolling(n).max().shift(1)
    volr = df["v"] / df["v"].rolling(50).median().shift(1)
    ret = (df["c"] / df["c"].shift(1) - 1) * 100
    return pd.DataFrame({"lo": lo, "hi": hi, "volr": volr,
                         "spring": (df["l"] < lo) & (df["c"] > lo), "upthrust": (df["h"] > hi) & (df["c"] < hi),
                         "effort": (volr > 2) & (ret.abs() < 1)})


def wyckoff_test(load: Load, coin: str = "BTC", days: int = 30) -> pd.DataFrame:
    """Что было с ценой через days дней после событий Вайкоффа, и для сравнения — в обычный день."""
    df = ohlcv(load, coin)
    m = wyckoff_marks(df)
    fwd = (df["c"].shift(-days) / df["c"] - 1) * 100
    dd = (df["c"] / df["c"].cummax() - 1) * 100
    nolow = df["l"][::-1].rolling(5).min()[::-1].shift(-1) > df["l"]
    fwd5 = (df["c"].shift(-days - 5) / df["c"].shift(-5) - 1) * 100
    cases = {"Spring (ложный пробой вниз)": (m["spring"], fwd),
             "Spring после падения на 40%+": (m["spring"] & (dd < -40), fwd),
             "Spring с подтверждением (вход через 5 дней без нового минимума)": (m["spring"] & nolow, fwd5),
             "Upthrust (ложный пробой вверх)": (m["upthrust"], fwd),
             "Усилие без результата (большой объём, цена стоит)": (m["effort"], fwd)}
    rows = {}
    for name, (mask, f) in cases.items():
        x = f.reindex(_thin(mask[mask.fillna(False)].index)).dropna()
        rows[name] = {"Случаев": len(x), f"Через {days} дн., медиана %": x.median(), "Цена выше, %": (x > 0).mean() * 100}
    base = fwd.dropna()
    rows["Обычный день"] = {"Случаев": len(base), f"Через {days} дн., медиана %": base.median(),
                            "Цена выше, %": (base > 0).mean() * 100}
    return pd.DataFrame(rows).T


def ranges(load: Load, coin: str = "BTC", width: float = 30, min_days: int = 30, after: int = 90) -> pd.DataFrame:
    """Боковые диапазоны (размах не больше width %) длиной от min_days дней и самое большое движение за after дней
    после выхода — проверка закона «причина и следствие»."""
    df = ohlcv(load, coin)
    h, l, c = df["h"].values, df["l"].values, df["c"].values
    rows, i, n = [], 0, len(df)
    while i < n - min_days:
        j, hi, lo = i + 1, h[i], l[i]
        while j < n:
            hi, lo = max(hi, h[j]), min(lo, l[j])
            if (hi - lo) / lo * 100 > width:
                break
            j += 1
        if j - i >= min_days and j < n - after:
            c0 = c[j - 1]
            move = max(h[j:j + after].max() / c0 - 1, 1 - l[j:j + after].min() / c0) * 100
            rows.append({"Начало": df.index[i].date(), "Дней в диапазоне": j - i, "Ход за 90 дней после, %": move})
            i = j
        else:
            i += 1
    return pd.DataFrame(rows)



# ---------- CVD: кто давит — спот или плечо ----------
def cvd(load: Load, window: int = 30) -> pd.DataFrame:
    """Дельта объёма: агрессивные покупки минус агрессивные продажи (по рынку), $. Для спота и фьючерса биткоина —
    накопленная (CVD) и доля чистого давления за window дней в % оборота, в том числе относительно обычного уровня за
    прошлый год (у Binance дельта спота почти всегда ниже нуля — сравнивать с нулём нельзя)."""
    d = pd.concat({"c": load("BTC_CLOSE"), "sv": load("BTC_QVOL"), "sb": load("BTC_TBUY"),
                   "fv": load("BTCPERP_QVOL"), "fb": load("BTCPERP_TBUY")}, axis=1, sort=True).dropna()
    d["sd"], d["fd"] = 2 * d["sb"] - d["sv"], 2 * d["fb"] - d["fv"]
    out = pd.DataFrame({"c": d["c"], "cvd_spot": d["sd"].cumsum(), "cvd_perp": d["fd"].cumsum()})
    for k, dv, v in (("spot", "sd", "sv"), ("perp", "fd", "fv")):
        r = d[dv].rolling(window).sum() / d[v].rolling(window).sum() * 100
        out[f"{k}_press"] = r - r.rolling(365, min_periods=180).median()
    return out


def cvd_test(load: Load, days: int = 30, window: int = 30) -> pd.DataFrame:
    """Рост больше 15% за window дней: кто вёл — спот или фьючерс (по давлению относительно нормы), и что было с
    ценой через days дней; для сравнения — все такие росты и обычный день."""
    x = cvd(load, window)
    ret = (x["c"] / x["c"].shift(window) - 1) * 100
    fwd = (x["c"].shift(-days) / x["c"] - 1) * 100
    up = ret > 15
    cases = {"Рост: вёл спот": up & (x["spot_press"] > x["perp_press"]),
             "Рост: вело плечо (фьючерс)": up & (x["perp_press"] > x["spot_press"]),
             "Все росты больше 15%": up,
             "Цена стоит, сильные покупки спота (поглощение)":
                 (ret.abs() < 5) & (x["spot_press"] > x["spot_press"].rolling(365).quantile(0.8))}
    rows = {}
    for name, mask in cases.items():
        f = fwd.reindex(_thin(mask[mask.fillna(False)].index, 30)).dropna()
        rows[name] = {"Случаев": len(f), f"Через {days} дн., медиана %": f.median(), "Цена выше, %": (f > 0).mean() * 100}
    base = fwd.dropna()
    rows["Обычный день"] = {"Случаев": len(base), f"Через {days} дн., медиана %": base.median(),
                            "Цена выше, %": (base > 0).mean() * 100}
    return pd.DataFrame(rows).T
