"""Учебная подача слоёв модели: одинаковый каркас на каждом экране новой версии.

Уровни чтения экрана:
1. сразу видно — где слой в цепочке, главный вывод одной фразой, ключевые числа;
2. по раскрытию «Как это работает» — механизм, лаги, где сигнал ошибается;
3. по переключателю «Показать на реальных данных» — примеры: сначала как механизм работает
   в обычные годы, затем аномалии, где он ломается.
"""
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Callable

import pandas as pd
import streamlit as st


@dataclass(frozen=True)
class Layer:
    num: int
    title: str
    question: str          # на какой вопрос отвечает слой
    page: str | None       # путь к экрану новой версии; None — слой ещё не построен
    old_page: str | None = None  # экран старой версии, где пока смотреть данные слоя


LAYERS = [
    Layer(1, "Структура и долг", "С какой скоростью экономика может расти без перегрева и во что обходится долг?",
          "views/v2/structure.py"),
    Layer(2, "Политика ФРС", "ФРС сейчас тормозит экономику или разгоняет её?", "views/v2/policy.py"),
    Layer(3, "Рыночные ставки и ожидания", "Что рынок облигаций ждёт от ставок и инфляции?",
          "views/v2/market_rates.py"),
    Layer(4, "Финансовые условия и кредит", "Легко ли и дёшево ли сейчас получить деньги?", "views/v2/credit.py"),
    Layer(5, "Рост и риск рецессии", "Экономика ускоряется или замедляется?", "views/v2/growth.py"),
    Layer(6, "Инфляция", "Куда идут цены и устойчиво ли это?", "views/v2/inflation.py"),
    Layer(7, "Рынки", "Что всё это значит для акций, облигаций и золота?", "views/v2/markets.py"),
]
BY_NUM = {l.num: l for l in LAYERS}

# Метки сигнала: тип по времени и надёжность (насколько сигнал проверен вне выборки)
TIMING = {"опережающий": "blue", "совпадающий": "violet", "запаздывающий": "gray"}
RELIABILITY = {"проверен вне выборки": "green", "проверен на истории": "green", "спорный": "orange",
               "нарратив": "red"}
HELP_PAGE = "views/v2/help.py"


def chain_strip(current: int) -> str:
    """Цепочка слоёв одной строкой с выделенным текущим: 1 → 2 → **4** → …"""
    return " → ".join(f"**:blue[{l.num}. {l.title}]**" if l.num == current else f"{l.num}" for l in LAYERS)


def layer_header(num: int, lead: str) -> None:
    """Заголовок слоя: номер, место в цепочке и короткая вводная. Ответ слоя — в takeaway() под ним."""
    left, right = st.columns([5, 1], vertical_alignment="bottom")
    left.caption(f"Слой {num} из {len(LAYERS)} · " + chain_strip(num))
    with right:
        help_link("Как читать экран")
    st.title(BY_NUM[num].title)
    st.markdown(lead)


def help_link(label: str = "Справка") -> None:
    st.page_link(HELP_PAGE, label=label, icon="❓")


def takeaway(text: str, tone: str = "neutral") -> None:
    """Главный вывод слоя одной-двумя фразами — то, что стоит унести с экрана."""
    icon = {"good": "🟢", "bad": "🔴", "warn": "🟠"}.get(tone, "⚪")
    with st.container(border=True):
        st.markdown(f"#### {icon} {text}")


def tags(timing: str, reliability: str) -> None:
    """Метки сигнала: опережает ли он экономику и насколько ему можно верить."""
    st.markdown(f":{TIMING[timing]}-badge[{timing}] :{RELIABILITY[reliability]}-badge[{reliability}]",
                help="**Опережающий** меняется раньше экономики, **совпадающий** — вместе с ней, "
                     "**запаздывающий** — позже.  \n**Проверен вне выборки** — сигнал работал на данных, "
                     "которых не видели авторы модели; **проверен на истории** — связь видна в прошлых данных, "
                     "но строгого теста вне выборки нет; **спорный** — исследования расходятся; "
                     "**нарратив** — популярная история без строгой проверки.  \nПодробнее — в «Справке».")


@contextmanager
def how_it_works(title: str = "Как это работает"):
    with st.expander(f"💡 {title}"):
        yield


@dataclass(frozen=True)
class Example:
    title: str
    render: Callable[[], None]
    normal: bool = True  # True — обычная работа механизма; False — аномалия, где модель ломается


def examples(items: list[Example], key: str) -> None:
    """Примеры на реальных данных по переключателю: считаются и рисуются, только когда их открыли."""
    if not st.toggle("📊 Показать на реальных данных", key=f"ex_{key}"):
        return
    with st.container(border=True):
        normal = [e for e in items if e.normal]
        odd = [e for e in items if not e.normal]
        groups = {}
        if normal:
            groups["Как механизм работает обычно"] = normal
        if odd:
            groups["Когда он ломается"] = odd
        kind = st.segmented_control("Что смотрим", list(groups), default=list(groups)[0], key=f"exk_{key}",
                                    label_visibility="collapsed") or list(groups)[0]
        chosen = groups[kind]
        if len(chosen) > 1:
            title = st.radio("Пример", [e.title for e in chosen], key=f"exr_{key}_{kind}", horizontal=True,
                             label_visibility="collapsed")
            ex = next(e for e in chosen if e.title == title)
        else:
            ex = chosen[0]
        st.markdown(f"**{ex.title}**")
        ex.render()


def next_steps(nums: list[int], why: str) -> None:
    """Куда импульс идёт дальше по цепочке — ссылки на следующие слои."""
    st.divider()
    st.markdown(f"**Куда дальше по цепочке.** {why}")
    cols = st.columns(len(nums) + 1)
    for col, n in zip(cols, nums):
        layer = BY_NUM[n]
        with col:
            if layer.page:
                st.page_link(layer.page, label=f"{n}. {layer.title}", icon="➡️")
            else:
                st.markdown(f"➡️ {n}. {layer.title}  \n:gray[слой в разработке]")
    with cols[-1]:
        st.page_link("views/v2/map.py", label="Вся карта", icon="🗺️")


def percentile(s: pd.Series, value: float) -> float:
    """Доля истории (в %), когда ряд был ниже value."""
    s = s.dropna()
    return float((s < value).mean() * 100)
