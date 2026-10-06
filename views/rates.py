"""Этап 2. Ставки и облигации: кривая доходности, наклон, реальные ставки, кредит,
поведение облигационных ETF и песочница «цена облигации ↔ доходность»."""
import numpy as np
import pandas as pd
import streamlit as st

from core import bonds, ui
from core.charts import curve_chart, hbar_chart, line_chart, price_yield_chart

MATURITIES = {"DGS1MO": 1 / 12, "DGS3MO": 0.25, "DGS6MO": 0.5, "DGS1": 1, "DGS2": 2, "DGS5": 5,
              "DGS7": 7, "DGS10": 10, "DGS20": 20, "DGS30": 30}
PERIODS = {"1 год": 1, "3 года": 3, "5 лет": 5, "10 лет": 10, "20 лет": 20, "Вся история": None}


def cut(s: pd.Series, years: int | None) -> pd.Series:
    s = s.dropna()
    return s[s.index >= s.index[-1] - pd.DateOffset(years=years)] if years else s


def curve_at(date: pd.Timestamp) -> pd.Series:
    """Кривая доходности на дату: последнее известное значение каждого срока."""
    return pd.Series({m: ui.load(k)[:date].iloc[-1] for k, m in MATURITIES.items()}).sort_index()


def rebased(keys: dict[str, str], years: int | None) -> dict[str, pd.Series]:
    out = {}
    for name, k in keys.items():
        s = cut(ui.load(k), years)
        out[name] = s / s.iloc[0] * 100
    start = max(s.index[0] for s in out.values())  # общий старт, чтобы база = 100 совпадала
    return {n: s[s.index >= start] / s[s.index >= start].iloc[0] * 100 for n, s in out.items()}


st.title("Ставки и облигации")
st.caption("Цена денег в экономике: от ставки ФРС на один день до 30-летних облигаций. "
           "Серые полосы на графиках — рецессии США.")

# --- ключевые ставки ---
kpi = [("Ставка ФРС", "DFF"), ("2 года", "DGS2"), ("10 лет", "DGS10"), ("30 лет", "DGS30"),
       ("Реальная 10 лет", "DFII10"), ("Ожид. инфляция 10 лет", "T10YIE")]
cols = st.columns(len(kpi))
for col, (name, key) in zip(cols, kpi):
    s = ui.load(key)
    month_ago = s[:s.index[-1] - pd.DateOffset(months=1)].iloc[-1]
    col.metric(name, f"{s.iloc[-1]:.2f}%", f"{s.iloc[-1] - month_ago:+.2f} п.п. за месяц",
               delta_color="off", border=True, help=f"`{key}` на {s.index[-1]:%d.%m.%Y}")

period = st.segmented_control("Период графиков", list(PERIODS), default="10 лет")
years = PERIODS[period or "10 лет"]
rec = ui.recessions()

# --- кривая и её наклон ---
c1, c2 = st.columns(2, gap="large")
with c1:
    st.subheader("Кривая доходности")
    last = min(ui.load(k).index[-1] for k in MATURITIES)
    curves = {f"Сейчас ({last:%d.%m.%Y})": curve_at(last),
              "Год назад": curve_at(last - pd.DateOffset(years=1)),
              "2 года назад": curve_at(last - pd.DateOffset(years=2))}
    st.plotly_chart(curve_chart(curves), width="stretch", theme="streamlit")
    st.caption("Доходность гособлигаций США по срокам. Нормальная кривая растёт слева направо: за долгий срок "
               "платят больше. Если короткие ставки выше длинных (инверсия) — рынок ждёт, что ФРС будет "
               "снижать ставку из-за слабой экономики.")
with c2:
    st.subheader("Наклон кривой")
    st.plotly_chart(line_chart({"10 лет − 3 мес.": cut(ui.load("T10Y3M"), years),
                                "10 лет − 2 года": cut(ui.load("T10Y2Y"), years)},
                               units="п.п.", recessions=rec, zero_line=True, height=340),
                    width="stretch", theme="streamlit")
    st.caption("Ниже нуля — инверсия. Перед каждой рецессией с 1970-х наклон уходил ниже нуля, а сама рецессия "
               "обычно начиналась уже после возврата выше нуля.")

# --- ставки и их состав ---
c1, c2 = st.columns(2, gap="large")
with c1:
    st.subheader("Короткие и длинные ставки")
    st.plotly_chart(line_chart({"Ставка ФРС": cut(ui.load("DFF"), years), "2 года": cut(ui.load("DGS2"), years),
                                "10 лет": cut(ui.load("DGS10"), years)},
                               units="%", recessions=rec, height=320), width="stretch", theme="streamlit")
    st.caption("ФРС управляет только самой короткой ставкой. Двухлетние идут чуть впереди неё — это ожидания "
               "рынка по ставке ФРС. Десятилетние зависят ещё от инфляции и спроса на долг.")
with c2:
    st.subheader("Из чего состоит доходность 10 лет")
    st.plotly_chart(line_chart({"Номинальная": cut(ui.load("DGS10"), years),
                                "Реальная (TIPS)": cut(ui.load("DFII10"), years),
                                "Ожидания инфляции": cut(ui.load("T10YIE"), years)},
                               units="%", recessions=rec, height=320), width="stretch", theme="streamlit")
    st.caption("Номинальная доходность ≈ реальная + ожидаемая инфляция. Если растёт реальная — деньги дорожают "
               "по-настоящему (плохо для акций роста и золота); если ожидания — рынок боится инфляции.")

# --- кредит и облигации на практике ---
c1, c2 = st.columns(2, gap="large")
with c1:
    st.subheader("Кредитные спреды")
    st.plotly_chart(line_chart({"Baa − 10 лет": cut(ui.load("BAA10Y"), years),
                                "High yield (ICE, 3 года)": cut(ui.load("BAMLH0A0HYM2"), years)},
                               units="п.п.", recessions=rec, height=320), width="stretch", theme="streamlit")
    st.caption("Надбавка за риск дефолта сверх госдолга. Расширяется в кризисы, сужается в спокойные времена. "
               "Ряд high yield в FRED доступен только за 3 года.")
with c2:
    st.subheader("Облигации на практике: дюрация")
    st.plotly_chart(line_chart(rebased({"TLT (20+ лет)": "TLT", "IEF (7–10 лет)": "IEF",
                                        "SHY (1–3 года)": "SHY"}, years),
                               units="", recessions=rec, height=320), width="stretch", theme="streamlit")
    st.caption("Цена облигационных ETF с реинвестированием купонов, начало периода = 100. Чем длиннее срок, тем "
               "сильнее цена реагирует на ставки: в 2022 году TLT упал почти на треть, SHY — на несколько процентов.")

# --- песочница ---
st.divider()
st.subheader("Песочница: цена облигации и ставка")
st.caption("Облигация — это обещание заплатить купоны и вернуть номинал. Если рыночная ставка растёт, старые "
           "облигации с низким купоном становятся менее привлекательными и дешевеют. Подвигайте ползунки.")
ten = float(ui.load("DGS10").iloc[-1])
s1, s2, s3, s4 = st.columns(4)
years_to_maturity = s1.slider("Срок, лет", 1, 30, 10)
coupon = s2.slider("Купон, % в год", 0.0, 10.0, round(ten * 4) / 4, 0.25)
ytm = s3.slider("Рыночная доходность, %", 0.0, 12.0, round(ten, 2), 0.05,
                help="По умолчанию — текущая доходность 10-летних казначейских облигаций США.")
shock = s4.slider("Сдвиг ставки, п.п.", -3.0, 3.0, 1.0, 0.25)

b = bonds.stats(coupon, years_to_maturity, ytm)
p1 = bonds.price(coupon, years_to_maturity, ytm + shock)
exact = (p1 / b.price - 1) * 100
approx = -b.modified_duration * shock
m1, m2, m3, m4 = st.columns(4)
m1.metric("Цена сейчас", f"{b.price:.2f}", help="За 100 номинала. Купон выше доходности → цена выше 100.")
m2.metric("Дюрация", f"{b.modified_duration:.1f}",
          help="Модифицированная дюрация: на сколько % примерно меняется цена при сдвиге ставки на 1 п.п.")
m3.metric(f"Цена после сдвига {shock:+.2f} п.п.", f"{p1:.2f}", f"{exact:+.1f}%", border=False)
m4.metric("Оценка по дюрации", f"{approx:+.1f}%",
          help="−дюрация × сдвиг. Расхождение с точным числом — выпуклость: при больших сдвигах цена падает "
               "меньше и растёт больше, чем предсказывает дюрация.")

c1, c2 = st.columns([3, 2], gap="large")
with c1:
    grid = np.linspace(max(0.0, min(ytm, ytm + shock) - 3), max(ytm, ytm + shock) + 3, 120)
    st.plotly_chart(price_yield_chart(grid, [bonds.price(coupon, years_to_maturity, y) for y in grid],
                                      ytm, b.price, ytm + shock, p1), width="stretch", theme="streamlit")
    st.caption("Цена от доходности: кривая выгнута (выпуклость) — это и есть «бесплатная» защита держателя "
               "длинной облигации при больших движениях ставок.")
with c2:
    st.markdown(f"**Тот же сдвиг {shock:+.2f} п.п. для облигаций разных сроков**")
    curve_now = curve_at(min(ui.load(k).index[-1] for k in MATURITIES))
    terms = [2, 5, 10, 30]
    changes = [bonds.price_change_pct(curve_now[t], t, curve_now[t], shock) for t in terms]
    st.plotly_chart(hbar_chart([f"{t} {'года' if t == 2 else 'лет'}" for t in terms], changes, height=230),
                    width="stretch", theme="streamlit")
    st.caption("Облигации по номиналу с купоном = текущей доходности своего срока. Длинные облигации — "
               "ставка на снижение ставок, короткие — почти кэш.")
