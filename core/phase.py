"""Итог панели: фаза цикла и главные сигналы (ревью панели, Маркс: «где мы в цикле»).

Правила простые и прозрачные — это первая версия, уточняется на этапе 3.
"""
from dataclasses import dataclass

from core.indicators import CRITICAL, GOOD, LEADING, SCORE, SERIOUS, WARNING, Result, group_status

ECONOMY = ["Рост", "Инфляция", "ФРС и ставки"]
MARKET = ["Кредит и ликвидность", "Оценка", "Рынок и сентимент"]

PHASES = {
    "recession": ("Рецессия", "Экономика сокращается. Исторически лучшее время покупать — в её второй половине, когда рынок уже упал."),
    "pre_recession": ("Предрецессия", "Опережающие сигналы ухудшаются при ещё нормальных текущих данных. Время сокращать риск."),
    "late": ("Поздний цикл", "Экономика держится, но рынок дорогой, а кредит беспечный. Тренд ещё вверх — время осторожности, а не паники."),
    "early": ("Ранний цикл", "Рынок недорог, условия смягчаются. Исторически самая доходная фаза для акций."),
    "mid": ("Середина цикла", "Без явных перекосов. Рынок следует за прибылью компаний."),
}


@dataclass
class Signal:
    key: str
    text: str
    status: str


@dataclass
class Phase:
    key: str
    name: str
    description: str
    economy: tuple[str, str]
    market: tuple[str, str]
    signals: list[Signal]


def _group_score(results: dict[str, Result], groups: list[str]) -> list[str]:
    return [r.status for r in results.values() if r.ind.group in groups]


def signals(results: dict[str, Result], limit: int = 8) -> list[Signal]:
    """Самое важное на панели: тревожные статусы, исторические экстремумы,
    предупреждения опережающих индикаторов."""
    out: list[tuple[int, Signal]] = []
    for k, r in results.items():
        name = r.ind.name
        if r.status in (CRITICAL, SERIOUS):
            out.append((SCORE[r.status], Signal(k, f"{name}: {r.label.lower()}", r.status)))
        elif r.status == WARNING and r.ind.kind == LEADING:
            out.append((0, Signal(k, f"{name}: {r.label.lower()}", r.status)))
        if r.extreme:
            note = r.ind.extreme_low if r.extreme == "low" else r.ind.extreme_high
            if note:
                out.append((-1, Signal(k, f"{name}: {note[0].lower() + note[1:]}", "extreme")))
    out.sort(key=lambda t: t[0])
    seen, result = set(), []
    for _, sig in out:  # один сигнал на прибор — самый сильный
        if sig.key not in seen:
            seen.add(sig.key)
            result.append(sig)
    return result[:limit]


def classify(results: dict[str, Result]) -> Phase:
    r = results
    valuation = [x.status for x in r.values() if x.ind.group == "Оценка"]
    val_score = sum(SCORE[s] for s in valuation) / max(len(valuation), 1)

    def st(key):
        return r[key].status if key in r else None

    def lb(key):
        return r[key].label if key in r else ""

    if st("sahm") == CRITICAL:
        key = "recession"
    elif lb("curve") in ("Инверсия", "Выход из инверсии") and (st("claims") != GOOD or st("permit") == SERIOUS):
        key = "pre_recession"
    elif val_score <= -1 and st("credit") == GOOD and st("trend") == GOOD:
        key = "late"
    elif val_score >= 0.5 and st("trend") == GOOD:
        key = "early"
    else:
        key = "mid"
    name, desc = PHASES[key]
    return Phase(key, name, desc,
                 group_status(_group_score(r, ECONOMY)), group_status(_group_score(r, MARKET)),
                 signals(r))
