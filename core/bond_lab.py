"""Лаборатория облигаций: денежные потоки, цена, дюрация, доходность на горизонте, кредитный риск и инфляция.

Упрощения, чтобы видеть механизм, а не технические детали: кривая доходности плоская (все сроки дисконтируются
по одной ставке), купоны реинвестируются под доходность облигации, цена — «грязная» (с накопленным купоном),
номинал 100. Ставки и сдвиги — в процентах и процентных пунктах.
"""
from dataclasses import dataclass, replace

import numpy as np

KINDS = {"fixed": "Обычная (фиксированный купон)", "zero": "Бескупонная",
         "floating": "С плавающим купоном", "tips": "Защищённая от инфляции (TIPS)"}
H = 0.01  # шаг для численной дюрации, п.п.


@dataclass(frozen=True)
class Bond:
    kind: str = "fixed"
    years: float = 10.0
    coupon: float = 4.0     # фиксированный купон; для плавающей — надбавка к ставке; для TIPS — реальный купон
    freq: int = 2           # выплат в год
    rf: float = 4.0         # ставка гособлигаций того же срока
    spread: float = 0.0     # кредитный спред, п.п.
    breakeven: float = 2.3  # ожидаемая рынком инфляция (для TIPS)

    @property
    def y(self) -> float:
        """Доходность, по которой дисконтируются выплаты. Для TIPS — реальная."""
        base = self.rf - self.breakeven if self.kind == "tips" else self.rf
        return base + self.spread

    def times(self) -> np.ndarray:
        n = max(int(np.ceil(self.years * self.freq - 1e-9)), 1)
        return self.years - (n - np.arange(1, n + 1)) / self.freq

    def coupons(self, shift: float = 0.0) -> np.ndarray:
        t = self.times()
        if self.kind == "zero":
            return np.zeros(len(t))
        if self.kind == "floating":
            c = np.full(len(t), (self.rf + shift + self.coupon) / self.freq)
            c[0] = (self.rf + self.coupon) / self.freq  # ближайший купон уже зафиксирован
            return c
        return np.full(len(t), self.coupon / self.freq)

    def flows(self, shift: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
        cf = self.coupons(shift).copy()
        cf[-1] += 100
        return self.times(), cf


def discount(y: float, t, freq: int):
    return (1 + y / 100 / freq) ** (-np.asarray(t) * freq)


def grow(t_from: float, t_to: float, y: float, freq: int) -> float:
    return float((1 + y / 100 / freq) ** (max(t_to - t_from, 0) * freq))


def price(b: Bond, shift: float = 0.0) -> float:
    t, cf = b.flows(shift)
    return float((cf * discount(b.y + shift, t, b.freq)).sum())


@dataclass(frozen=True)
class Stats:
    price: float
    duration: float     # эффективная дюрация: −% изменения цены на 1 п.п. ставки
    convexity: float
    center: float       # «центр тяжести» выплат (дюрация Маколея), лет
    current_yield: float
    last_share: float   # доля цены, которая приходится на последнюю выплату, %


def stats(b: Bond) -> Stats:
    t, cf = b.flows()
    pv = cf * discount(b.y, t, b.freq)
    p, up, dn = float(pv.sum()), price(b, H), price(b, -H)
    annual = float(b.coupons().mean() * b.freq)
    return Stats(p, (dn - up) / (2 * p * H / 100), (dn + up - 2 * p) / (p * (H / 100) ** 2),
                 float((t * pv).sum() / p), annual / p * 100, float(pv[-1] / p * 100))


def taylor(s: Stats, shift: float) -> float:
    """Изменение цены по дюрации и выпуклости, %: −D·Δy + ½·C·Δy²."""
    d = shift / 100
    return (-s.duration * d + 0.5 * s.convexity * d * d) * 100


# ---------- держать или продать ----------

@dataclass(frozen=True)
class Horizon:
    coupons: float      # сумма купонов, полученных до горизонта
    reinvest: float     # «процент на процент»: доход от реинвестирования выплат
    price_gain: float   # цена продажи (или погашение) минус цена покупки
    wealth: float       # итог на горизонте
    annual: float       # средняя годовая доходность, %


def horizon(b: Bond, hold: float, t_shock: float, delta: float) -> Horizon:
    """Купили сейчас; через t_shock лет ставки сдвинулись на delta п.п. и так остались; держим hold лет."""
    p0 = price(b)
    t = b.times()
    before, after = b.coupons(), b.coupons(delta)
    cpn = np.where((b.kind == "floating") & (t - 1 / b.freq >= t_shock), after, before)
    y0, y1 = b.y, b.y + delta

    def factor(s: float) -> float:  # рост денег от s до горизонта
        mid = min(max(t_shock, s), hold)
        return grow(s, mid, y0, b.freq) * grow(max(mid, s), hold, y1, b.freq)

    got = t <= hold + 1e-9
    flows = cpn + np.where(np.arange(len(t)) == len(t) - 1, 100, 0)
    coupons = float(cpn[got].sum())
    reinvest = float(sum(f * (factor(s) - 1) for s, f in zip(t[got], flows[got])))
    y_sale = y1 if hold >= t_shock else y0
    sale = float((flows[~got] * discount(y_sale, t[~got] - hold, b.freq)).sum())
    principal = 100.0 if got[-1] else 0.0
    wealth = p0 + coupons + reinvest + (sale + principal - p0)
    return Horizon(coupons, reinvest, sale + principal - p0, wealth,
                   ((wealth / p0) ** (1 / hold) - 1) * 100 if hold > 0 else 0.0)


# ---------- кредитный риск ----------

def irr(p0: float, t: np.ndarray, cf: np.ndarray, freq: int) -> float:
    lo, hi = -50.0, 200.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if (cf * discount(mid, t, freq)).sum() > p0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


@dataclass(frozen=True)
class Credit:
    promised: float        # обещанная доходность, если всё заплатят
    expected: float        # ожидаемая с учётом дефолтов
    default_prob: float    # вероятность дефолта до погашения, %
    expected_loss: float   # обещанная − ожидаемая, п.п.


def credit(b: Bond, pd_annual: float, recovery: float) -> Credit:
    """pd_annual — вероятность дефолта за год, %; recovery — доля номинала, возвращаемая при дефолте, %."""
    t, cf = b.flows()
    surv = (1 - pd_annual / 100) ** t
    prev = np.concatenate([[1.0], surv[:-1]])
    expected_cf = cf * surv + recovery * (prev - surv)
    p0 = price(b)
    exp = irr(p0, t, expected_cf, b.freq)
    return Credit(b.y, exp, (1 - surv[-1]) * 100, b.y - exp)


# ---------- инфляция ----------

def real_return(nominal: float, inflation: float) -> float:
    return ((1 + nominal / 100) / (1 + inflation / 100) - 1) * 100


def nominal_from_real(real: float, inflation: float) -> float:
    return ((1 + real / 100) * (1 + inflation / 100) - 1) * 100


def as_kind(b: Bond, kind: str) -> Bond:
    return replace(b, kind=kind)


# ---------- реальная облигация ----------

def accrued(b: Bond) -> float:
    """Накопленный купон: доля текущего купона, которую продавец уже «заработал». Платит покупатель сверх цены."""
    if b.kind == "zero":
        return 0.0
    t_next = float(b.times()[0])
    return float(b.coupons()[0]) * max(1 - t_next * b.freq, 0.0)


def implied_spread(b: Bond, clean: float) -> float:
    """Спред к ставке гособлигаций, при котором модель даёт рыночную чистую цену."""
    dirty = clean + accrued(b)
    lo, hi = -20.0, 60.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if price(replace(b, spread=mid)) > dirty:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def implied_default(spread: float, recovery: float) -> float:
    """Какую вероятность дефолта за год закладывает спред, если весь он — плата за ожидаемые потери, %."""
    return max(spread, 0.0) / max(1 - recovery / 100, 0.01)
