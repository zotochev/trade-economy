"""Окно «Подробнее» для прибора панели и общий расчёт приборов с кэшем."""
import pandas as pd
import streamlit as st

from core import ui
from core.charts import line_chart, theme
from core.cockpit_html import css, pill
from core.indicators import INDICATORS, evaluate

PERIODS = {"5 лет": 5, "10 лет": 10, "20 лет": 20, "Вся история": None}


@st.cache_data(ttl=3600, show_spinner="Считаю приборы…")
def results():
    out, errors = {}, {}
    for ind in INDICATORS:
        try:
            out[ind.key] = evaluate(ind, ui.load)
        except Exception as e:  # один сломанный ряд не должен гасить всю панель
            errors[f"{ind.group}:{ind.name}"] = str(e)
    return out, errors


def current_regime():
    """(режим, лучшие, худшие) или None, если не посчитался."""
    try:
        from core.regime_data import summary
        return summary()
    except Exception:
        return None


def render_details(key: str) -> None:
    """Содержимое окна «Подробнее» (отдельно от st.dialog — чтобы проверять тестом)."""
    res = results()[0][key]
    ind = res.ind
    st.markdown(f"### {ind.name}")
    st.caption(f"{ind.kind.capitalize()} индикатор · {ind.metric}")
    st.html(f"<style>{css(theme())}</style>{pill(res.status, res.label)}")
    if res.r.extra:
        st.write(res.r.extra)
    if res.extreme:
        note = ind.extreme_low if res.extreme == "low" else ind.extreme_high
        st.info(f"Исторический {'минимум' if res.extreme == 'low' else 'максимум'}: "
                f"{res.percentile:.0f}-й перцентиль. {note}", icon=":material/diamond:")
    period = st.segmented_control("Период", list(PERIODS), default="10 лет", label_visibility="collapsed")
    years = PERIODS[period or "10 лет"]
    s = res.r.series.dropna()
    view = s[s.index >= s.index[-1] - pd.DateOffset(years=years)] if years else s
    st.plotly_chart(line_chart({f"{ind.name}, {ind.metric}": view}, units=ind.units, recessions=ui.recessions(),
                               zero_line=view.min() < 0 < view.max(), height=320),
                    width="stretch", theme="streamlit")
    c1, c2 = st.columns(2)
    c1.markdown("**Как читать**")
    c1.write(ind.how_to_read)
    c2.markdown("**Зоны прибора**")
    rows, prev = [], None
    for lim, _, label in res.bands:
        rows.append(f"- {'< ' if prev is None else f'{prev:.3g} … '}{lim:.3g} — {label}")
        prev = lim
    rows.append(f"- ≥ {prev:.3g} — {ind.top[1]}" if prev is not None else f"- {ind.top[1]}")
    c2.markdown("\n".join(rows))
    st.caption("Ряды: " + ", ".join(f"`{k}`" for k in ind.sources) + " · серые полосы — рецессии США")


details = st.dialog("Подробнее", width="large")(render_details)
