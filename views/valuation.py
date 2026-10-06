"""Этап 5. Оценка рынка: сколько стоит рынок и что это значило для будущей доходности."""
import numpy as np
import pandas as pd
import streamlit as st

from core import ui
from core import valuation as V
from core.charts import bucket_chart, cape_scatter, line_chart, xy_lines

PERIODS = {"20 лет": 20, "50 лет": 50, "С 1881 года": None}


def cut(s: pd.Series, years: int | None) -> pd.Series:
    s = s.dropna()
    return s[s.index >= s.index[-1] - pd.DateOffset(years=years)] if years else s


@st.cache_data(ttl=3600, show_spinner="Считаю историю с 1871 года…")
def history():
    cape = ui.load("CAPE")
    idx = V.real_total_return_index(ui.load("P"), ui.load("D"), ui.load("CPI"))
    fwd = V.forward_return(idx, 10)
    cpi = ui.load("CPI")
    infl10 = ((cpi / cpi.shift(120)) ** (1 / 10) - 1) * 100       # средняя инфляция за 10 лет — прокси ожиданий
    erp_long = (100 / cape - (ui.load("Rate GS10") - infl10)).dropna()
    erp_tips = (100 / cape - ui.load("DFII10").resample("MS").mean()).dropna()
    e_real = (ui.load("E") / cpi * cpi.iloc[-1]).dropna().rolling(120).mean().dropna()
    years = (e_real.index[-1] - e_real.index[0]).days / 365.25
    g_hist = ((e_real.iloc[-1] / e_real.iloc[0]) ** (1 / years) - 1) * 100
    buffett = (ui.load("BOGZ1LM893064105Q") / 1000 / ui.load("GDP") * 100).dropna()
    profits = (ui.load("CP") / ui.load("GDP") * 100).dropna()
    return cape, fwd, erp_long, erp_tips, g_hist, buffett, profits


cape, fwd, erp_long, erp_tips, g_hist, buffett, profits = history()
table = V.cape_table(cape, fwd)
model = V.fit(cape, fwd)
now = float(cape.iloc[-1])
real10 = float(ui.load("DFII10").iloc[-1])
pe12 = (ui.load("P") / ui.load("E")).dropna()
bucket = next(lbl for lo, hi, lbl in zip(V.BUCKETS[:-1], V.BUCKETS[1:], V.BUCKET_LABELS) if lo <= now < hi)
row = table.loc[bucket]

st.title("Оценка рынка")
st.caption("Сколько стоит рынок акций США и что такая цена исторически означала для доходности на 10 лет вперёд. "
           "Грэм: цена — то, что платишь, стоимость — то, что получаешь.")


def pct_rank(s: pd.Series) -> str:
    return f"{(s.dropna() < s.dropna().iloc[-1]).mean() * 100:.0f}-й перцентиль"


cols = st.columns(6)
cols[0].metric("Shiller CAPE", f"{now:.1f}", pct_rank(cape), delta_color="off", border=True,
               help=f"Цена к средней реальной прибыли за 10 лет. Медиана с 1881 г. — {cape.median():.1f}.")
cols[1].metric("P/E за 12 мес.", f"{pe12.iloc[-1]:.1f}", pct_rank(pe12), delta_color="off", border=True,
               help=f"Цена к прибыли за последние 12 мес. (данные Шиллера за {pe12.index[-1]:%m.%Y}).")
cols[2].metric("Доходность акций", f"{100 / now:.2f}%", "1 / CAPE", delta_color="off", border=True,
               help="Сколько реальной прибыли приходится на каждый вложенный доллар — «купон» акций.")
cols[3].metric("Премия, п.п.", f"{erp_tips.iloc[-1]:+.2f}", pct_rank(erp_tips), delta_color="off",
               border=True, help="1/CAPE − реальная доходность 10-летних TIPS (с 2003 г.).")
cols[4].metric("Баффет, % ВВП", f"{buffett.iloc[-1]:.0f}", pct_rank(buffett), delta_color="off",
               border=True, help="Капитализация всех компаний США к ВВП (с 1945 г.).")
cols[5].metric("Прибыль, % ВВП", f"{profits.iloc[-1]:.1f}", pct_rank(profits), delta_color="off",
               border=True, help=f"Прибыль корпораций до налогов к ВВП. Средняя с 1947 г. — {profits.mean():.1f}%.")

# --- главный вопрос ---
st.subheader(f"Что CAPE {now:.1f} значил для следующих 10 лет")
c1, c2 = st.columns([1, 1], gap="large")
with c1:
    st.markdown(
        f"Когда CAPE был **{bucket}**, реальная доходность следующих 10 лет составляла в медиане "
        f"**{row['Медиана, % год.']:+.1f}% в год**: от {row['Худший, % год.']:+.1f}% до {row['Лучший, % год.']:+.1f}%, "
        f"и в **{row['Доля < 0, %']:.0f}%** случаев — меньше нуля.\n\n"
        f"Регрессия по всей истории даёт при текущем CAPE **≈ {model.predict(now):+.1f}% в год** "
        f"(типичная ошибка ±{model.resid_std:.1f} п.п.). Для сравнения, средняя реальная доходность рынка "
        f"с 1881 года — около 6.7% в год, а реальная доходность 10-летних TIPS сейчас — **{real10:.2f}%** "
        f"без риска.")
    st.warning(f"Честная оговорка: CAPE выше 30 с уже известным результатом на 10 лет вперёд был только в двух "
               f"эпизодах — 1929 и 1997–2002 ({int(row['Месяцев'])} месяцев, но это два случая, а не "
               f"{int(row['Месяцев'])}). CAPE почти ничего не говорит о следующем годе: дорогой рынок может "
               f"дорожать дальше годами.", icon=":material/info:")
    st.plotly_chart(bucket_chart(table, bucket), width="stretch", theme="streamlit")
    st.caption("Столбец — медиана, усы — худшее и лучшее 10-летие. Наведите на столбец: доля отрицательных "
               "10-летий и размер выборки. Выделен столбец текущего CAPE.")
with c2:
    st.plotly_chart(cape_scatter(cape, fwd, now, model.predict, height=560), width="stretch", theme="streamlit")
    st.caption("Каждая точка — месяц покупки с 1881 по 2016 год (для более поздних 10 лет ещё не прошло). "
               "Чем правее точка (дороже покупка), тем ниже она в среднем лежит. Текущий CAPE правее почти "
               "всей истории.")

# --- история оценок ---
period = st.segmented_control("Период графиков", list(PERIODS), default="50 лет")
years = PERIODS[period or "50 лет"]
rec = ui.recessions()
c1, c2 = st.columns(2, gap="large")
with c1:
    st.markdown("**Shiller CAPE**")
    st.plotly_chart(line_chart({"CAPE": cut(cape, years)}, units="", recessions=rec, height=300),
                    width="stretch", theme="streamlit")
    st.caption(f"Медиана с 1881 года — {cape.median():.1f}. Выше 30 рынок бывал в 1929, 1997–2002, в 69% "
               f"месяцев с 2017 года и без перерыва — с ноября 2023. Структурные причины выше старой нормы есть (меньше инфляция, больше "
               f"выкупов, другой состав индекса), но насколько выше — предмет спора.")
with c2:
    st.markdown("**Премия акций над облигациями**, п.п.")
    st.plotly_chart(line_chart({"1/CAPE − (10 лет − инфляция за 10 лет), с 1881": cut(erp_long, years),
                                "1/CAPE − TIPS, с 2003": cut(erp_tips, years)},
                               units="п.п.", recessions=rec, zero_line=True, height=300),
                    width="stretch", theme="streamlit")
    st.caption("Сколько акции «платят» сверх облигаций. Длинная версия использует среднюю инфляцию за прошлые "
               "10 лет как прокси ожиданий — она шумнее. Ниже нуля — облигации без риска платят больше, чем "
               "прибыль акций на вложенный доллар.")

c1, c2 = st.columns(2, gap="large")
with c1:
    st.markdown("**Индикатор Баффета**, % ВВП")
    st.plotly_chart(line_chart({"Капитализация / ВВП": cut(buffett, years)}, units="%", recessions=rec,
                               height=280), width="stretch", theme="streamlit")
    st.caption(f"Медиана с 1945 года — {buffett.median():.0f}%, сейчас — {buffett.iloc[-1]:.0f}%: исторический "
               f"максимум. Часть роста объясняется тем, что крупные компании США зарабатывают по всему миру, "
               f"а ВВП считает только внутреннюю экономику.")
with c2:
    st.markdown("**Прибыль компаний**, % ВВП")
    st.plotly_chart(line_chart({"Прибыль до налогов / ВВП": cut(profits, years)}, units="%", recessions=rec,
                               height=280), width="stretch", theme="streamlit")
    st.caption(f"Сейчас {profits.iloc[-1]:.1f}% — максимум с 1947 года при средней {profits.mean():.1f}%. "
               "Грэнтэм: маржа — самый склонный к возврату к среднему показатель в финансах. Если она вернётся "
               "к норме, «E» в P/E упадёт, и рынок окажется ещё дороже, чем показывает P/E.")

# --- песочница ---
st.divider()
st.subheader("Песочница: справедливый P/E и ставки")
st.caption("Модель Гордона: акция стоит столько, сколько будущая прибыль, дисконтированная по требуемой "
           "доходности. P/E = 1 / (r − g), где r = реальная ставка + премия за риск, g — реальный рост прибыли.")
s1, s2, s3 = st.columns(3)
ry = s1.slider("Реальная ставка (TIPS 10 лет), %", -1.0, 5.0, round(real10, 2), 0.05,
               help="По умолчанию — текущая.")
prem = s2.slider("Премия за риск акций, п.п.", 0.0, 8.0, round(float(erp_long.median()), 1), 0.1,
                 help=f"По умолчанию — медиана с 1881 г. ({erp_long.median():.1f}).")
g = s3.slider("Реальный рост прибыли, % в год", 0.0, 4.0, round(float(g_hist), 1), 0.1,
              help=f"По умолчанию — исторический рост 10-летней средней реальной прибыли ({g_hist:.1f}% в год).")
fair = V.fair_pe(ry, prem, g)
implied = V.implied_premium(now, ry, g)
m1, m2, m3 = st.columns(3)
m1.metric("Справедливый P/E (к 10-летней прибыли)", "∞" if not np.isfinite(fair) else f"{fair:.1f}",
          help="Сравнивается с CAPE, потому что модель про устойчивую, а не пиковую прибыль.")
m2.metric("Текущий CAPE против справедливого", f"{(now / fair - 1) * 100:+.0f}%" if np.isfinite(fair) else "—")
m3.metric("Премия, которую закладывает рынок", f"{implied:+.2f} п.п.",
          help="Какая премия за риск получается при текущем CAPE, выбранной ставке и росте: 1/CAPE + g − ставка.")
grid = np.linspace(-1, 5, 121)


def curve(growth: float) -> list:
    """Справедливый P/E по сетке ставок; выше 80 не рисуем (там модель уходит в бесконечность)."""
    return [pe if (pe := V.fair_pe(x, prem, growth)) <= 80 else None for x in grid]


st.plotly_chart(xy_lines({
    f"Стоимостные компании (рост {max(g - 1, 0):.1f}%)": (grid, curve(max(g - 1, 0))),
    f"Рынок (рост {g:.1f}%)": (grid, curve(g)),
    f"Компании роста (рост {g + 1:.1f}%)": (grid, curve(g + 1)),
}, "Реальная ставка, %", "Справедливый P/E", marker=(ry, fair, "выбрано") if fair <= 80 else None),
    width="stretch", theme="streamlit")
st.caption("Чем выше ожидаемый рост, тем круче линия: компании роста теряют в цене от роста ставок сильнее — "
           "у них «длинная дюрация», как у 30-летних облигаций. Поэтому 2022 год так ударил по технологиям.")
