"""Дашборд «Модель экономики». Запуск: uv run streamlit run app.py"""
import streamlit as st

st.set_page_config(page_title="Модель экономики", page_icon="📈", layout="wide")

OLD, NEW = "Старая", "Новая (в разработке)"


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

version = st.sidebar.radio("Версия дашборда", [OLD, NEW], key="version",
                           help="Новая версия строит модель экономики как цепочку слоёв. "
                                "Пока она собирается, старые экраны остаются доступны.")
if version == NEW:
    nav = {
        "Модель экономики": [
            st.Page("views/v2/map.py", title="Карта: цепочка слоёв", icon="🗺️", default=True),
            st.Page("views/v2/policy.py", title="2. Политика ФРС", icon="🏛️"),
            st.Page("views/v2/market_rates.py", title="3. Рыночные ставки", icon="📉"),
            st.Page("views/v2/credit.py", title="4. Финансовые условия", icon="💳"),
            st.Page("views/v2/growth.py", title="5. Рост и риск рецессии", icon="⚙️"),
            st.Page("views/v2/inflation.py", title="6. Инфляция", icon="🔥"),
            st.Page("views/v2/markets.py", title="7. Рынки", icon="💹"),
            st.Page("views/sectors.py", title="7а. Сектора и факторы", icon="🏭"),
            st.Page("views/stock.py", title="7б. Отдельная акция", icon="🔬"),
            st.Page("views/v2/help.py", title="Справка", icon="❓"),
        ],
        "Пока из старой версии": [p for p in old_pages(with_cockpit=False)
                                  if p.title not in ("Акции и сектора", "Отдельная акция")],
        "Справочник": reference,
    }
else:
    nav = old_pages() + reference
st.navigation(nav).run()
