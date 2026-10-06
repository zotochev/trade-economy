"""Дашборд «Модель экономики». Запуск: uv run streamlit run app.py"""
import streamlit as st

st.set_page_config(page_title="Модель экономики", page_icon="📈", layout="wide")

pages = [
    st.Page("views/cockpit.py", title="Панель", icon="🛩️", default=True),
    st.Page("views/regime.py", title="Режим экономики", icon="🧭"),
    st.Page("views/rates.py", title="Ставки и облигации", icon="🏦"),
    st.Page("views/liquidity.py", title="Ликвидность и долг", icon="💧"),
    st.Page("views/valuation.py", title="Оценка рынка", icon="⚖️"),
    st.Page("views/explorer.py", title="Все ряды", icon="🔎"),
    st.Page("views/data_status.py", title="Данные", icon="🗄️"),
]
st.navigation(pages).run()
