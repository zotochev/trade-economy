"""Дашборд «Модель экономики». Запуск: uv run streamlit run app.py"""
import streamlit as st

st.set_page_config(page_title="Модель экономики", page_icon="📈", layout="wide")

NEW, OLD = "Новая", "Старая"


def old_pages(with_cockpit: bool = True) -> list:
    pages = [
        st.Page("views/cockpit.py", title="Панель", icon="🛩️", default=with_cockpit),
        st.Page("views/regime.py", title="Режим экономики", icon="🧭"),
        st.Page("views/rates.py", title="Ставки и облигации", icon="🏦"),
        st.Page("views/liquidity.py", title="Ликвидность и долг", icon="💧"),
        st.Page("views/valuation.py", title="Оценка рынка", icon="⚖️"),
        st.Page("views/sectors.py", title="Акции и сектора", icon="🏭"),
        st.Page("views/stock.py", title="Отдельная акция", icon="🔬"),
    ]
    return pages if with_cockpit else pages[1:]


reference = [
    st.Page("views/explorer.py", title="Все ряды", icon="🔎"),
    st.Page("views/data_status.py", title="Данные", icon="🗄️"),
]

version = st.sidebar.radio("Версия дашборда", [NEW, OLD], key="version",
                           help="Новая версия строит модель экономики как цепочку из семи слоёв. "
                                "Старая — прежняя панель приборов и тематические экраны.")
if version == NEW:
    nav = {
        "Модель экономики": [
            st.Page("views/v2/map.py", title="Карта: цепочка слоёв", icon="🗺️", default=True),
            st.Page("views/v2/structure.py", title="1. Структура и долг", icon="🏗️"),
            st.Page("views/v2/policy.py", title="2. Политика ФРС", icon="🏛️"),
            st.Page("views/v2/market_rates.py", title="3. Рыночные ставки", icon="📉"),
            st.Page("views/v2/credit.py", title="4. Финансовые условия", icon="💳"),
            st.Page("views/v2/growth.py", title="5. Рост и риск рецессии", icon="⚙️"),
            st.Page("views/v2/inflation.py", title="6. Инфляция", icon="🔥"),
            st.Page("views/v2/markets.py", title="7. Рынки", icon="💹"),
            st.Page("views/v2/help.py", title="Справка", icon="❓"),
        ],
        "Подробнее о рынках": [
            st.Page("views/sectors.py", title="Сектора и факторы", icon="🏭"),
            st.Page("views/stock.py", title="Отдельная акция", icon="🔬"),
            st.Page("views/regime.py", title="Режимы экономики", icon="🧭"),
        ],
        "Справочник": reference,
    }
else:
    nav = old_pages() + reference
st.navigation(nav, expanded=True).run()
