"""Состояние кэша и кнопки обновления."""
import streamlit as st

from core import data, ui

st.title("Данные")
st.caption(f"Кэш хранится в `{data.CACHE_DIR}`. Ряд считается свежим {data.MAX_AGE // 3600} ч, "
           "после этого докачивается. Из терминала: `uv run python update_data.py [--force]`.")

c1, c2, _ = st.columns([2, 2, 6])
force = None
if c1.button("Обновить устаревшие", type="primary"):
    force = False
if c2.button("Перекачать всё"):
    force = True

if force is not None:
    with st.spinner("Скачиваю…"):
        results = data.update(force=force)
    ui.clear()
    bad = [r for r in results if not r.ok]
    if not results:
        st.info("Все ряды свежие — обновлять нечего.")
    elif bad:
        st.error(f"Обновлено {len(results) - len(bad)}, ошибок {len(bad)}:\n\n"
                 + "\n".join(f"- `{r.key}`: {r.error}" for r in bad))
    else:
        st.success(f"Обновлено рядов: {len(results)}")

st.dataframe(data.status(), width="stretch", hide_index=True,
             column_config={"Последнее": st.column_config.NumberColumn(format="%.2f")})
