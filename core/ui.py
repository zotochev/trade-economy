"""Общие для страниц обёртки над загрузкой с кэшем Streamlit."""
import pandas as pd
import streamlit as st

from core import data
from core.charts import recession_spans


@st.cache_data(ttl=3600, show_spinner="Загружаю данные…")
def load(key: str) -> pd.Series:
    return data.load(key)


@st.cache_data(ttl=3600)
def recessions() -> list[tuple]:
    return recession_spans(load("USREC"))


def clear() -> None:
    st.cache_data.clear()
