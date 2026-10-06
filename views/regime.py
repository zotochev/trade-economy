"""Этап 3. Режим экономики: рост × инфляция и что исторически выигрывало в каждом режиме."""
from html import escape

import pandas as pd
import streamlit as st

from core import regime as R
from core import ui
from core.charts import heatmap, line_chart, quadrant_chart, regime_colors, regime_ribbon, theme
from core.cockpit_html import TOKENS
from core.regime_data import UNIVERSE, compute

@st.cache_data(ttl=3600)
def quality():
    return R.method_quality(ui.load, R.monthly_returns(ui.load("^GSPC")))


def chip(name: str, size: int = 15) -> str:
    c = regime_colors()[name]
    return (f'<span style="display:inline-flex;align-items:center;gap:6px;font-weight:700;font-size:{size}px">'
            f'<span style="width:12px;height:12px;border-radius:3px;background:{c}"></span>{escape(name)}</span>')


st.title("Режим экономики")
st.caption("Две оси: ускоряется ли рост и ускоряется ли инфляция. Их сочетание даёт четыре режима, и у каждого "
           "исторически свои победители. Каждая ось — голосование трёх рядов (идея Далио: один ряд шумный).")

f1, f2, _ = st.columns([3, 2, 3])
method_label = f1.segmented_control("Способ", list(R.METHODS.values()), default=R.METHODS[R.DEFAULT_METHOD],
                                    help=" · ".join(f"{R.METHODS[k]}: {v}" for k, v in R.METHOD_HELP.items()))
method = {v: k for k, v in R.METHODS.items()}[method_label or R.METHODS[R.DEFAULT_METHOD]]
lag_on = f2.toggle("С лагом публикации", value=True,
                   help="Данные за месяц выходят примерно через 2–6 недель. С лагом режим сопоставляется с "
                        "доходностью через 2 месяца — так, как его реально можно было торговать. Без лага — "
                        "«идеальное знание», заглядывание в будущее.")
lag = R.PUBLICATION_LAG if lag_on else 0
h, stats = compute(method, lag)
now = R.current(ui.load, method)
other = R.current(ui.load, "accel" if method == "trend" else "trend")
t = TOKENS[theme()]

# --- текущий режим и квадрант ---
c1, c2 = st.columns([2, 3], gap="large")
with c1:
    st.html(f'<div style="color:{t["muted"]};font-size:12px;letter-spacing:.08em;text-transform:uppercase;'
            f'font-weight:600">Текущий режим · данные за {now.as_of:%m.%Y}</div>'
            f'<div style="margin:6px 0 4px">{chip(now.name, 30)}</div>'
            f'<div style="color:{t["text2"]};font-size:14px">{escape(now.description)}; держится '
            f'{now.months} мес.</div>')
    if other.name != now.name:
        st.html(f'<div style="font-size:13px;color:{t["text2"]};margin-top:4px">Второй способ видит '
                f'{chip(other.name, 13)} — режим на границе, уверенность низкая.</div>')
    best, worst = R.leaders(stats, now.name)
    st.markdown(f"**Исторически в режиме «{now.name}»** (средняя доходность, % годовых"
                f"{', с лагом' if lag else ', без лага'}):")
    b1, b2 = st.columns(2)
    b1.markdown("Лучше всех\n" + "\n".join(f"- {n} — **{v:+.1f}%**" for n, v in best))
    b2.markdown("Хуже всех\n" + "\n".join(f"- {n} — **{v:+.1f}%**" for n, v in worst))
    st.caption("Это средние по истории, а не прогноз. Внутри любого режима бывают годы против среднего.")

    st.markdown("**Голоса рядов** (импульс в стандартных отклонениях; > 0 — ускоряется)")
    rows = []
    for axis_name, ax in (("Рост", h.growth), ("Инфляция", h.inflation)):
        for col in ax.components.columns:
            z = ax.components[col].dropna()
            y = ax.yoy[col].dropna()
            rows.append({"Ряд": f"{axis_name}: {col}", "Г/г, %": round(y.iloc[-1], 2),
                         "Импульс": round(z.iloc[-1], 2), "Голос": "↑" if z.iloc[-1] > 0 else "↓",
                         "За": f"{z.index[-1]:%m.%y}"})
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch",
                 column_config={"Ряд": st.column_config.TextColumn(width="medium")})
with c2:
    st.plotly_chart(quadrant_chart(h.growth.composite, h.inflation.composite), width="stretch", theme="streamlit")
    st.caption("Точка — среднее голосов по каждой оси. Серая линия — путь за последние 24 месяца: видно, "
               "в какой режим экономика движется.")

st.markdown("**История режимов** · сверху серым — рецессии")
st.plotly_chart(regime_ribbon(h.regime["1970":], ui.recessions()), width="stretch", theme="streamlit")

# --- что выигрывало ---
st.subheader("Что выигрывало в каждом режиме")
st.caption("Средняя месячная доходность × 12, % годовых. Синий — рост, красный — падение. Наведите на ячейку: "
           "доля растущих месяцев и сколько месяцев в выборке. ETF — с их запуска (2000-е), поэтому у них мало "
           "эпизодов каждого режима; длинная история — в первых двух строках.")
for group, assets in UNIVERSE.items():
    col = st
    s = stats[stats["Актив"].isin(assets)]
    table = s.pivot(index="Актив", columns="Режим", values="Годовых, %").reindex(index=list(assets), columns=R.REGIMES)
    hover = s.assign(h=lambda d: d.apply(lambda r: f"растущих месяцев: {r['Растущих месяцев, %']:.0f}%"
                                                   f" · месяцев: {r['Месяцев']} · с {r['С']}", axis=1)) \
        .pivot(index="Актив", columns="Режим", values="h").reindex(index=list(assets), columns=R.REGIMES)
    col.markdown(f"**{group}**")
    col.plotly_chart(heatmap(table, hover, highlight=now.name), width="stretch", theme="streamlit")

# --- способы и сюрпризы ---
c1, c2 = st.columns(2, gap="large")
with c1:
    st.subheader("Какой способ лучше")
    st.dataframe(quality().round(1), hide_index=True, width="stretch",
                 column_config={"Способ": st.column_config.TextColumn(width="small")})
    st.caption("Хороший способ даёт устойчивые режимы (не скачет каждый месяц) и сильно разделяет доходность. "
               "«Отклонение от средней» выигрывает по обоим пунктам, поэтому он по умолчанию.")
    st.info("**Сюрприз истории.** По учебнику лучший режим для акций — «Восстановление». На данных США с 1950 г. "
            "S&P 500 больше всего зарабатывал в «Замедлении»: рынок смотрит вперёд и отскакивает, пока данные ещё "
            "плохие и ФРС начинает смягчать. Макро-данные запаздывают, цены — нет.", icon=":material/lightbulb:")
with c2:
    st.subheader("Инфляция против ожиданий")
    cpi = R.yoy_pct(ui.load("CPIAUCSL")).dropna()
    st.plotly_chart(line_chart({"Инфляция CPI, г/г": cpi["2004":], "Ожидания рынка на 5 лет": ui.load("T5YIE")},
                               units="%", recessions=ui.recessions(), height=300), width="stretch", theme="streamlit")
    st.caption("Далио: рынки двигает отклонение от ожиданий. Когда факт уходит выше ожиданий и не возвращается, "
               "рынку приходится переоценивать ставки — так было в 2021–2022.")
