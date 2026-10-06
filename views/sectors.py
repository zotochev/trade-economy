"""Этап 6. Акции и сектора: кто ведёт рынок, где дешевле и что подсказывает режим."""
import pandas as pd
import streamlit as st

from core import data, ui
from core import regime as R
from core import sectors as S
from core.charts import heatmap, hbar_chart, line_chart, rotation_chart
from core.regime_data import compute as regime_stats
from core.series import BY_KEY

PERIODS = {"1 год": 1, "3 года": 3, "5 лет": 5, "10 лет": 10, "Вся история": None}
HORIZONS = {"1 мес.": 1, "3 мес.": 3, "6 мес.": 6, "12 мес.": 12}


def label(k: str) -> str:
    return f"{S.SECTORS.get(k) or S.FACTORS.get(k)} ({k})"


@st.cache_data(ttl=3600)
def relative_table() -> pd.DataFrame:
    spy = ui.load("SPY")
    keys = list(S.SECTORS) + list(S.FACTORS)
    return pd.DataFrame({h: {label(k): S.relative(ui.load(k), spy, m) for k in keys} for h, m in HORIZONS.items()})


@st.cache_data(ttl=3600, show_spinner="Загружаю P/E по ETF…")
def snapshot() -> pd.DataFrame:
    return data.update_snapshot(S.SNAPSHOT_TICKERS)


st.title("Акции и сектора")
st.caption("Какие части рынка ведут, а какие отстают, где дешевле и что подсказывает текущий режим экономики. "
           "Всё — относительно S&P 500 (SPY): +5 значит «обогнал рынок на 5 процентных пунктов».")

rel = relative_table()

# --- соотношения-индикаторы ---
cols = st.columns(len(S.RATIOS))
for col, (num, den, name, meaning) in zip(cols, S.RATIOS):
    r = S.ratio(ui.load(num), ui.load(den))
    ch = S.change(r, 6)
    col.metric(f"{name}, за 6 мес.", f"{'▲' if ch > 0 else '▼'} {ch:+.1f}%", border=True,
               help=f"{num} / {den}. Рост соотношения — {meaning}.")

# --- ротация ---
st.subheader("Кто ведёт рынок")
c1, c2 = st.columns([5, 4], gap="large")
with c1:
    order = rel.sort_values("6 мес.", ascending=False)
    st.plotly_chart(heatmap(order, order.map(lambda v: f"{v:+.1f} п.п. к S&P 500"), scale_title="п.п."),
                    width="stretch",
                    theme="streamlit")
    st.caption("Опережение S&P 500 в процентных пунктах, по убыванию за 6 мес. Синий — сектор сильнее рынка, "
               "красный — слабее.")
with c2:
    pts = rel.loc[[label(k) for k in S.SECTORS], ["6 мес.", "1 мес."]]
    pts.index = list(S.SECTORS)
    st.plotly_chart(rotation_chart(pts, "6 мес.", "1 мес.", "Сила за 6 мес., п.п.", "Сила за 1 мес., п.п.",
                                   ("Лидеры", "Слабеют", "Отстающие", "Улучшаются")),
                    width="stretch", theme="streamlit")
    st.caption("Ротация секторов: справа — сильные за полгода, сверху — сильные за последний месяц. Сектора обычно "
               "движутся по кругу по часовой стрелке: улучшаются → лидеры → слабеют → отстают.")

leaders_6m = (rel.loc[[label(k) for k in S.SECTORS], "6 мес."] > 0).sum()
rsp6 = rel.loc[label("RSP"), "6 мес."]
if leaders_6m <= 3 and rsp6 < 0:
    st.warning(f"**Узкий рынок.** За 6 месяцев S&P 500 обогнали только {leaders_6m} из 11 секторов, а индекс равными "
               f"долями отстал на {abs(rsp6):.1f} п.п. Рост держится на небольшой группе крупнейших компаний. "
               f"Исторически узкий рынок уязвимее: если лидеры споткнутся, широкой поддержки нет.",
               icon=":material/warning:")

# --- где дешевле и режим ---
c1, c2 = st.columns(2, gap="large")
with c1:
    st.subheader("Где дешевле")
    snap = snapshot()
    pe = snap["P/E"].dropna()
    pe = pe[[k for k in list(S.SECTORS) + list(S.FACTORS) + ["SPY"] if k in pe.index]].sort_values()
    st.plotly_chart(hbar_chart([label(k) if k != "SPY" else "S&P 500 (SPY)" for k in pe.index], list(pe.values),
                               units="", height=36 * len(pe) + 40, signed=False), width="stretch", theme="streamlit")
    st.caption(f"P/E за последние 12 месяцев по данным Yahoo на {data.snapshot_date() or 'сегодня'} — только "
               "текущее значение, без истории. У секторов разные «нормальные» P/E (технологии почти всегда "
               "дороже коммунальных), поэтому честнее сравнивать сектор с его собственной историей — её здесь нет.")
with c2:
    st.subheader("Что подсказывает режим")
    now = R.current(ui.load)
    _, stats = regime_stats(R.DEFAULT_METHOD, R.PUBLICATION_LAG)
    hist = stats[stats["Режим"] == now.name].set_index("Актив")["Годовых, %"]
    names = {k: f"{BY_KEY[k].name} ({k})" for k in S.SECTORS}  # так активы названы в таблице режимов
    df = pd.DataFrame({
        "hist": [hist.get(names[k]) for k in S.SECTORS],
        "now": [rel.loc[label(k), "6 мес."] for k in S.SECTORS],
    }, index=list(S.SECTORS)).dropna()
    df["hist"] = df["hist"] - df["hist"].mean()   # относительно среднего сектора в этом режиме
    st.plotly_chart(rotation_chart(df, "hist", "now", f"История: «{now.name}», п.п. к среднему сектору",
                                   "Сейчас: сила за 6 мес., п.п.",
                                   ("Режим за, рынок за", "Режим за, рынок против", "Режим против, рынок против",
                                    "Режим против, рынок за")),
                    width="stretch", theme="streamlit")
    st.caption(f"По горизонтали — как сектор исторически вёл себя в режиме «{now.name}» (с лагом публикации), по "
               "вертикали — как ведёт сейчас. Сектор справа сверху поддержан и историей, и рынком. ETF секторов "
               "живут с 1998 года, поэтому история короткая — это подсказка, а не правило.")

# --- факторы ---
st.subheader("Факторы и широта рынка")
period = st.segmented_control("Период", list(PERIODS), default="5 лет")
years = PERIODS[period or "5 лет"]
series = {}
for num, den, name, _ in S.RATIOS:
    r = S.ratio(ui.load(num), ui.load(den)).dropna()
    r = r[r.index >= r.index[-1] - pd.DateOffset(years=years)] if years else r
    series[name] = r / r.iloc[0] * 100
start = max(s.index[0] for s in series.values())
series = {n: s[s.index >= start] / s[s.index >= start].iloc[0] * 100 for n, s in series.items()}
st.plotly_chart(line_chart(series, recessions=ui.recessions(), height=340), width="stretch", theme="streamlit")
st.caption("Соотношения, начало периода = 100. Растёт линия — выигрывает первая часть пары. Цикличные против "
           "защитных — голос рынка о росте экономики; малые против больших и равные доли против обычного индекса — "
           "широта ралли.")

# --- Линч ---
with st.expander("Шесть категорий акций Питера Линча и при чём тут макро", expanded=False):
    st.markdown("""
| Категория | Пример | Что важно | Роль макро |
|---|---|---|---|
| Медленнорастущие | коммунальные (XLU) | дивиденды | ставки: дивидендные акции конкурируют с облигациями |
| Стабильные (stalwarts) | товары первой необходимости (XLP), здравоохранение (XLV) | P/E против роста 10–12% | слабая: защита в спаде |
| Быстрорастущие | технологии (XLK), рост (IWF) | рост прибыли, PEG | реальные ставки — «дюрация» акций |
| **Цикличные** | энергетика, материалы, промышленность, авто (XLE, XLB, XLI, XLY) | **фаза цикла** | **главная**: прибыль следует за экономикой |
| Восстанавливающиеся | компании после кризиса | выживание, долг | кредитные спреды, ставки |
| Активные (asset plays) | недооценённые активы на балансе | стоимость активов | почти никакой |

**Правило Линча для цикличных:** покупать, когда P/E *высокий* (прибыль на дне цикла, дальше будет расти), а продавать,
когда P/E *низкий* (прибыль на пике, дальше будет падать). Обратно обычной логике — и именно здесь нужна
макро-панель: она говорит, где мы в цикле.
""")
