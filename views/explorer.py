"""Обзор любого ряда из каталога: описание, текущее значение, место в истории, график."""
import pandas as pd
import streamlit as st

from core import ui
from core.charts import line_chart
from core.series import BY_KEY, CATALOG, GROUPS, LEVEL, YOY
from core.transforms import TRANSFORMS, rebase

PERIODS = {"1 год": 1, "5 лет": 5, "10 лет": 10, "20 лет": 20, "Вся история": None}

st.title("Обзор рядов")
st.caption("Любой показатель из каталога: что он значит, где он сейчас и как вёл себя в прошлом. "
           "Серые полосы — рецессии США (NBER).")

# --- фильтры одной строкой ---
c1, c2, c3, c4 = st.columns([2, 4, 3, 2])
group = c1.selectbox("Группа", GROUPS)
keys = [s.key for s in CATALOG if s.group == group]
key = c2.selectbox("Показатель", keys, format_func=lambda k: f"{BY_KEY[k].name} ({k})")
meta = BY_KEY[key]
names = list(TRANSFORMS)
transform = c3.selectbox("Преобразование", names, index=names.index(meta.view),
                         key=f"transform_{key}")
period = c4.selectbox("Период", list(PERIODS), index=3)

raw = ui.load(key)
s = TRANSFORMS[transform](raw).dropna()
units = {LEVEL: meta.units, YOY: "%", "Изменение г/г, разница": meta.units}.get(transform, "")
years = PERIODS[period]
start = s.index[-1] - pd.DateOffset(years=years) if years else s.index[0]
view = s[s.index >= start]
if transform.startswith("Индекс"):  # база = 100 в начале выбранного периода
    view = rebase(raw[raw.index >= start])

# --- описание ---
if meta.about:
    st.write(meta.about)
if meta.note:
    st.warning(meta.note, icon="⚠️")

# --- карточки: последнее значение, изменение, перцентиль ---
last, last_date = view.iloc[-1], view.index[-1]
year_ago = view[view.index <= last_date - pd.DateOffset(years=1)]
pct = (s < last).mean() * 100  # место текущего значения во всей истории ряда

m1, m2, m3, m4 = st.columns(4)
m1.metric(f"Последнее, {units}".rstrip(", "), f"{last:,.2f}")
m2.metric("Дата", last_date.strftime("%d.%m.%Y"))
m3.metric("Изменение за год", f"{last - year_ago.iloc[-1]:+,.2f}" if len(year_ago) else "—")
m4.metric("Перцентиль в истории", f"{pct:.0f}%",
          help=f"Доля наблюдений с {s.index[0]:%Y} г., которые были ниже текущего значения. "
               "Около 0% или 100% — исторический экстремум (идея Говарда Маркса: «насколько горячо сейчас»).")

fig = line_chart({meta.name: view}, units=units, recessions=ui.recessions(),
                 zero_line=view.min() < 0 < view.max())
st.plotly_chart(fig, width="stretch", theme="streamlit")

with st.expander("Таблица значений"):
    st.dataframe(view.rename(meta.name).to_frame().sort_index(ascending=False),
                 width="stretch")
st.caption(f"Источник: {'FRED' if meta.source == 'fred' else 'Yahoo Finance' if meta.source == 'yf' else 'Robert Shiller'}"
           f" · ключ `{key}` · частота {meta.freq} · история с {raw.index[0]:%Y}")
