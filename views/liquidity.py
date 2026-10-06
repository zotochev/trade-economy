"""Этап 4. Ликвидность и долговой цикл: сколько денег в системе и сколько стоит долг."""
import pandas as pd
import streamlit as st

from core import ui
from core.charts import line_chart
from core.transforms import yoy_pct

PERIODS = {"3 года": 3, "5 лет": 5, "10 лет": 10, "20 лет": 20, "Вся история": None}


def cut(s: pd.Series, years: int | None) -> pd.Series:
    s = s.dropna()
    return s[s.index >= s.index[-1] - pd.DateOffset(years=years)] if years else s


def rebase(series: dict[str, pd.Series]) -> dict[str, pd.Series]:
    start = max(s.dropna().index[0] for s in series.values())
    return {n: s[s.index >= start] / s[s.index >= start].iloc[0] * 100 for n, s in series.items()}


@st.cache_data(ttl=3600)
def liquidity_parts() -> pd.DataFrame:
    walcl = ui.load("WALCL") / 1e6                                              # трлн $
    tga = ui.load("WTREGEN").reindex(walcl.index, method="ffill") / 1e6
    rrp = ui.load("RRPONTSYD").reindex(walcl.index, method="ffill").fillna(0) / 1e3
    df = pd.DataFrame({"Баланс ФРС": walcl, "Счёт Минфина (TGA)": tga, "Обратное РЕПО": rrp}).dropna()
    df["Чистая ликвидность"] = df["Баланс ФРС"] - df["Счёт Минфина (TGA)"] - df["Обратное РЕПО"]
    return df


@st.cache_data(ttl=3600)
def debt_frame() -> pd.DataFrame:
    gdp = ui.load("GDP")                                                        # млрд $/год
    debt = ui.load("GFDEGDQ188S") / 100 * gdp                                   # млрд $
    interest = ui.load("A091RC1Q027SBEA")                                       # млрд $/год
    df = pd.DataFrame({
        "Госдолг / ВВП, %": ui.load("GFDEGDQ188S"),
        "Проценты / ВВП, %": interest / gdp * 100,
        "Средняя ставка по госдолгу, %": interest / debt * 100,
        "Рост номинального ВВП, % г/г": yoy_pct(gdp),
    })
    return df.dropna(how="all")


def kpi(col, name: str, value: str, delta: str, help_: str) -> None:
    col.metric(name, value, delta, delta_color="off", border=True, help=help_)


st.title("Ликвидность и долговой цикл")
st.caption("Сколько денег в системе и сколько стоит долг. Дракенмиллер: рынок в целом двигают не прибыли, "
           "а ликвидность и центробанки. Далио: экономикой правит кредит, а у долга есть короткий и длинный циклы.")

liq = liquidity_parts()
debt = debt_frame()
m2 = yoy_pct(ui.load("M2SL")).dropna()
dollar = ui.load("DTWEXBGS")


def change(s: pd.Series, months: int) -> float:
    return float(s.iloc[-1] - s[:s.index[-1] - pd.DateOffset(months=months)].iloc[-1])


cols = st.columns(6)
kpi(cols[0], "Баланс ФРС, трлн $", f"{liq['Баланс ФРС'].iloc[-1]:.2f}",
    f"{change(liq['Баланс ФРС'], 12):+.2f} за год", "Активы ФРС (WALCL). Рост — QE, падение — QT.")
kpi(cols[1], "Ликвидность, трлн $", f"{liq['Чистая ликвидность'].iloc[-1]:.2f}",
    f"{change(liq['Чистая ликвидность'], 3):+.2f} за 3 мес.", "Баланс ФРС − TGA − обратное РЕПО.")
kpi(cols[2], "РЕПО, млрд $", f"{liq['Обратное РЕПО'].iloc[-1] * 1000:.0f}",
    f"{change(liq['Обратное РЕПО'], 12) * 1000:+.0f} за год", "Деньги фондов денежного рынка, припаркованные в ФРС.")
kpi(cols[3], "M2, % г/г", f"{m2.iloc[-1]:+.1f}", f"{change(m2, 12):+.1f} п.п. за год",
    f"Денежная масса, данные за {m2.index[-1]:%m.%Y}.")
kpi(cols[4], "Индекс доллара", f"{dollar.iloc[-1]:.1f}",
    f"{(dollar.iloc[-1] / dollar[:dollar.index[-1] - pd.DateOffset(years=1)].iloc[-1] - 1) * 100:+.1f}% за год",
    "Курс доллара к корзине валют торговых партнёров (DTWEXBGS).")
kpi(cols[5], "Проценты, % ВВП", f"{debt['Проценты / ВВП, %'].dropna().iloc[-1]:.2f}",
    f"{change(debt['Проценты / ВВП, %'].dropna(), 12):+.2f} п.п. за год",
    "Процентные расходы федерального правительства к ВВП.")

period = st.segmented_control("Период графиков", list(PERIODS), default="10 лет")
years = PERIODS[period or "10 лет"]
rec = ui.recessions()

# --- ликвидность ---
st.subheader("Ликвидность")
c1, c2 = st.columns(2, gap="large")
with c1:
    st.markdown("**Из чего складывается чистая ликвидность**")
    st.plotly_chart(line_chart({k: cut(liq[k], years) for k in liq.columns}, units="трлн $", recessions=rec,
                               height=320), width="stretch", theme="streamlit")
    st.caption("ФРС печатает резервы (баланс), но часть денег «заперта»: на счёте Минфина (TGA) и в обратном РЕПО. "
               "Рынку доступно то, что осталось. В 2023–2024 QT шло за счёт опустошения обратного РЕПО (2.55 трлн $ "
               "в конце 2022 → почти ноль), а не за счёт резервов банков. Эта подушка израсходована.")
with c2:
    st.markdown("**Чистая ликвидность и S&P 500** (начало периода = 100)")
    spx = ui.load("^GSPC")
    nl = liq["Чистая ликвидность"]
    st.plotly_chart(line_chart(rebase({"Чистая ликвидность": cut(nl, years),
                                       "S&P 500": cut(spx.reindex(nl.index, method="ffill"), years)}),
                               recessions=rec, height=320), width="stretch", theme="streamlit")
    st.caption("В 2020–2022 рынок и ликвидность шли в одну сторону: вместе вверх на QE, вместе вниз на QT "
               "(корреляция уровней 0.81). С 2023 года связь разорвалась: ликвидность сокращалась, а S&P 500 рос "
               "(−0.56). Ликвидность — сильный ветер, но не единственный: прибыли и оценка тоже двигают рынок.")

c1, c2 = st.columns(2, gap="large")
with c1:
    st.markdown("**Денежная масса M2 и инфляция** (% г/г)")
    cpi = yoy_pct(ui.load("CPIAUCSL")).dropna()
    st.plotly_chart(line_chart({"M2": cut(m2, years), "Инфляция CPI": cut(cpi, years)}, units="%",
                               recessions=rec, zero_line=True, height=300), width="stretch", theme="streamlit")
    st.caption("В 2020–2021 M2 рос на 27% в год — через год CPI дошёл до 9%. В 2023 M2 впервые с начала ряда "
               "(1959) сократился год к году. Деньги действуют на цены с лагом около года, но связь неточная.")
with c2:
    st.markdown("**Доллар и финансовые условия**")
    nfci = ui.load("NFCI")
    st.caption("Индекс финансовых условий ФРБ Чикаго (NFCI)")
    st.plotly_chart(line_chart({"Индекс финансовых условий (NFCI)": cut(nfci, years)}, units="", recessions=rec,
                               zero_line=True, height=150), width="stretch", theme="streamlit")
    st.caption("Доллар, широкий индекс к валютам торговых партнёров")
    st.plotly_chart(line_chart({"Доллар, широкий индекс": cut(dollar, years)}, units="", recessions=rec,
                               height=150), width="stretch", theme="streamlit")
    st.caption("NFCI ниже нуля — условия мягче среднего. Сильный доллар ужесточает условия для всего мира "
               "(долги в долларах дорожают) и обычно давит на сырьё и развивающиеся рынки.")

# --- долговой цикл ---
st.subheader("Долговой цикл")
c1, c2 = st.columns(2, gap="large")
with c1:
    st.markdown("**Нагрузка госдолга**")
    st.caption("Госдолг, % ВВП")
    st.plotly_chart(line_chart({"Госдолг / ВВП, %": cut(debt["Госдолг / ВВП, %"], years)}, units="%",
                               recessions=rec, height=150), width="stretch", theme="streamlit")
    st.caption("Процентные расходы государства, % ВВП")
    st.plotly_chart(line_chart({"Процентные расходы / ВВП, %": cut(debt["Проценты / ВВП, %"], years)},
                               units="%", recessions=rec, height=150), width="stretch", theme="streamlit")
    st.caption("Далио: длинный долговой цикл кончается, когда обслуживание долга съедает слишком большую долю "
               "доходов. Сейчас проценты — около 3.9% ВВП, выше всего с конца 1990-х (пик — 5% в 1991 г.).")
with c2:
    st.markdown("**Средняя ставка по долгу, доходность 10 лет и рост экономики** (%)")
    st.plotly_chart(line_chart({"Средняя ставка по госдолгу": cut(debt["Средняя ставка по госдолгу, %"], years),
                                "Доходность 10 лет": cut(ui.load("DGS10"), years),
                                "Рост номинального ВВП (r против g)": cut(debt["Рост номинального ВВП, % г/г"], years)},
                               units="%", recessions=rec, height=320), width="stretch", theme="streamlit")
    st.caption("Пока средняя ставка по долгу ниже рыночной, проценты будут расти: старый дешёвый долг "
               "рефинансируется по новым ставкам. Устойчивость долга — «r против g»: если рост номинального ВВП (g) "
               "выше средней ставки (r), долг к ВВП может снижаться даже при дефиците.")

c1, c2 = st.columns(2, gap="large")
with c1:
    st.markdown("**Обслуживание долга домохозяйств** (% располагаемого дохода)")
    st.plotly_chart(line_chart({"Платежи по долгам / доход": cut(ui.load("TDSP"), years)}, units="%",
                               recessions=rec, height=240), width="stretch", theme="streamlit")
with c2:
    st.markdown("&nbsp;")
    st.caption("Частный долговой цикл: в 2007 году домохозяйства отдавали на долги почти 16% дохода — и это кончилось "
               "ипотечным кризисом. После 2008 они сократили долги, и сейчас нагрузка около 11%. Значит, частный "
               "сектор не главный источник риска в этом цикле; главный — государственный долг.")
