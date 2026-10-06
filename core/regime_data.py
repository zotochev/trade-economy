"""Вселенная активов для таблицы «что выигрывало в режиме» и расчёт с кэшем Streamlit."""
import streamlit as st

from core import regime as R
from core import ui
from core.series import BY_KEY

UNIVERSE = {
    "Классы активов": {
        "S&P 500 (с 1950, без дивидендов)": "^GSPC", "Гособлигации 10 лет (с 1962, оценка)": "T10_EST",
        "SPY — акции США": "SPY", "TLT — гособлигации 20+ лет": "TLT", "IEF — гособлигации 7–10 лет": "IEF",
        "SHY — гособлигации 1–3 года": "SHY", "TIP — защищённые от инфляции": "TIP",
        "LQD — корп. облигации IG": "LQD", "HYG — high yield": "HYG", "GLD — золото": "GLD",
        "DBC — сырьё": "DBC",
    },
    "Сектора и факторы": {
        **{f"{BY_KEY[k].name} ({k})": k for k in
           ["XLK", "XLF", "XLE", "XLV", "XLY", "XLP", "XLU", "XLI", "XLB", "XLRE", "XLC"]},
        "Малые компании (IWM)": "IWM", "Стоимость (IWD)": "IWD", "Рост (IWF)": "IWF",
    },
}


@st.cache_data(ttl=3600, show_spinner="Считаю режимы…")
def compute(method: str, lag: int):
    h = R.history(ui.load, method)
    reg = R.tradeable_regime(h, lag)
    returns = {}
    for group in UNIVERSE.values():
        for name, key in group.items():
            returns[name] = R.treasury10_returns(ui.load) if key == "T10_EST" else R.monthly_returns(ui.load(key))
    return h, R.stats_by_regime(returns, reg)


@st.cache_data(ttl=3600)
def summary(method: str = R.DEFAULT_METHOD, lag: int = R.PUBLICATION_LAG):
    """Текущий режим и лидеры/аутсайдеры в нём — для шапки панели."""
    _, stats = compute(method, lag)
    now = R.current(ui.load, method)
    best, worst = R.leaders(stats, now.name)
    return now, best, worst
