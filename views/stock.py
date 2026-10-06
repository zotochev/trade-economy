"""Этап 8. Отдельная акция: проверки Грэма, Баффета и Линча и макро-контекст."""
from html import escape

import pandas as pd
import streamlit as st

from core import phase as phase_mod
from core import regime as R
from core import stock as S
from core import ui
from core.charts import grouped_bars, line_chart, theme
from core.cockpit_html import STATUS_COLOR, TOKENS, css, pill
from core.details import results
from core.regime_data import compute as regime_stats
from core.sectors import relative
from core.series import BY_KEY

POPULAR = ["KO", "AAPL", "MSFT", "NVDA", "JPM", "XOM", "JNJ", "BRK-B", "CAT", "WMT"]


@st.cache_data(ttl=6 * 3600, show_spinner="Загружаю данные компании…")
def load_stock(ticker: str) -> S.Stock:
    return S.fetch(ticker)


def num(v, digits: int = 2) -> str:
    """Число с пробелом между тысячами или «—», если значения нет."""
    return "—" if v is None else f"{v:,.{digits}f}".replace(",", " ")


def pick() -> None:
    st.session_state.ticker = st.session_state.popular or st.session_state.ticker


def checklist(title: str, who: str, v: S.Verdict) -> str:
    t = TOKENS[theme()]
    ok, n = v.score
    share = ok / n if n else 0
    status = "good" if share >= 0.7 else "warning" if share >= 0.4 else "serious"
    rows = []
    for c in v.checks:
        st_ = "neutral" if c.ok is None else "good" if c.ok else "critical"
        icon = "–" if c.ok is None else "✓" if c.ok else "✕"
        rows.append(
            f'<div style="display:grid;grid-template-columns:22px 1fr;gap:6px;padding:7px 0;'
            f'border-top:1px solid {t["border"]}"><span class="ic" style="background:{STATUS_COLOR[st_]}">{icon}</span>'
            f'<div><div style="font-weight:600;font-size:13.5px">{escape(c.name)}</div>'
            f'<div style="font-size:12.5px;color:{t["text2"]}">{escape(c.value)}</div>'
            f'<div style="font-size:11.5px;color:{t["muted"]}">{escape(c.rule)}</div></div></div>')
    return (f'<div style="padding:14px 16px;border:1px solid {t["border"]};border-radius:12px;background:{t["card"]};'
            f'color:{t["text"]}"><div style="display:flex;justify-content:space-between;align-items:center;gap:8px">'
            f'<div><div style="font-size:16px;font-weight:700">{escape(title)}</div>'
            f'<div style="font-size:12px;color:{t["muted"]}">{escape(who)}</div></div>'
            f'{pill(status, f"{ok} из {n}")}</div><div style="margin-top:8px">{"".join(rows)}</div></div>')


st.title("Отдельная акция")
st.caption("Проверки трёх инвесторов на данных Yahoo и макро-контекст: сектор, режим экономики, чувствительность к "
           "рынку и ставкам. Это чек-листы для размышления, а не рекомендация купить или продать.")

if "ticker" not in st.session_state:
    st.session_state.ticker = "KO"
c1, c2 = st.columns([1, 4])
c1.text_input("Тикер", key="ticker", help="Любой тикер Yahoo Finance: AAPL, KO, BRK-B …")
c2.pills("Популярные", POPULAR, key="popular", on_change=pick)
ticker = st.session_state.ticker.strip().upper()

try:
    s = load_stock(ticker)
except Exception as e:
    st.error(f"Не удалось загрузить «{ticker}»: {e}")
    st.stop()

i = s.info
ten = float(ui.load("DGS10").iloc[-1])
g_verdict = S.graham(s)
b_verdict = S.buffett(s, ten)
l_verdict, (category, category_hint), growth = S.lynch(s)
sector = i.get("sector")
etf = S.SECTOR_ETF.get(sector)
t = TOKENS[theme()]
st.html(f"<style>{css(theme())}</style>")

# --- шапка ---
c1, c2 = st.columns([3, 2], gap="large")
with c1:
    price = i.get("currentPrice") or i.get("regularMarketPrice")
    cap = i.get("marketCap")
    st.html(f'<div style="color:{t["text"]}"><div style="font-size:28px;font-weight:700;line-height:1.15">'
            f'{escape(i.get("longName") or i.get("shortName") or ticker)} <span style="color:{t["muted"]};font-size:18px">'
            f'{escape(ticker)}</span></div>'
            f'<div style="color:{t["text2"]};font-size:14px;margin-top:4px">{escape(S.SECTOR_RU.get(sector, sector or "сектор неизвестен"))}'
            f' · {escape(i.get("industry") or "")}</div>'
            f'<div style="font-size:15px;margin-top:10px">Цена <b>{num(price)} {escape(i.get("currency") or "")}</b>'
            f' · капитализация <b>{num(cap / 1e9 if cap else None, 0)} млрд</b> · P/E <b>{num(i.get("trailingPE"), 1)}</b>'
            f' · дивиденды <b>{num(i.get("dividendYield"))}%</b></div>'
            f'<div style="margin-top:12px;padding:10px 12px;border-radius:10px;background:{t["hero"]};border:1px solid {t["border"]}">'
            f'Категория по Линчу: <b>{escape(category)}</b><br><span style="color:{t["text2"]};font-size:13px">'
            f'{escape(category_hint)}</span></div></div>')
with c2:
    res, _ = results()
    ph = phase_mod.classify(res)
    now = R.current(ui.load)
    lines = [f"Фаза цикла: <b>{escape(ph.name)}</b>", f"Режим: <b>{escape(now.name)}</b>"]
    if etf:
        _, stats = regime_stats(R.DEFAULT_METHOD, R.PUBLICATION_LAG)
        row = stats[(stats["Актив"] == f"{BY_KEY[etf].name} ({etf})") & (stats["Режим"] == now.name)]
        sect_mean = stats[(stats["Режим"] == now.name) & stats["Актив"].str.contains(r"\(XL")]["Годовых, %"].mean()
        if len(row):
            h = float(row["Годовых, %"].iloc[0])
            lines.append(f"Сектор ({etf}) в этом режиме исторически: <b>{h:+.1f}%</b> год. "
                         f"(средний сектор {sect_mean:+.1f}%)")
        lines.append(f"Сектор к S&P 500 за 6 мес.: <b>{relative(ui.load(etf), ui.load('SPY'), 6):+.1f} п.п.</b>")
    lines.append(f"Акция к S&P 500 за 6 мес.: <b>{relative(s.prices, ui.load('SPY'), 6):+.1f} п.п.</b>")
    st.html(f'<div style="padding:14px 16px;border-radius:12px;background:{t["hero"]};border:1px solid {t["border"]};'
            f'color:{t["text"]};font-size:14px;line-height:1.7"><div class="eyebrow" style="font-size:11px;'
            f'letter-spacing:.08em;text-transform:uppercase;color:{t["muted"]};font-weight:600">Макро-контекст</div>'
            f'{"<br>".join(lines)}</div>')

# --- чек-листы ---
c1, c2, c3 = st.columns(3, gap="medium")
c1.html(checklist("Грэм", "«Разумный инвестор», защитный инвестор: дёшево и надёжно", g_verdict))
c2.html(checklist("Баффет", "качество бизнеса: рентабельность, «ров», деньги владельцу", b_verdict))
c3.html(checklist("Линч", "цена против роста: PEG и категория", l_verdict))
st.caption(f"Отчётность Yahoo доступна за {S.years_word(len(s.years))} — меньше, чем просили Грэм (10–20) и Баффет. "
           "«–» — нет данных или критерий неприменим (например, к банкам). Разные инвесторы почти никогда не "
           "соглашаются по одной акции: Грэм ищет дешёвое, Баффет — качественное, Линч — рост по разумной цене.")

# --- графики ---
c1, c2 = st.columns(2, gap="large")
with c1:
    st.markdown("**Цена против рынка и сектора** (5 лет, начало = 100)")
    series = {ticker: s.prices, "S&P 500 (SPY)": ui.load("SPY")}
    if etf:
        series[f"Сектор ({etf})"] = ui.load(etf)
    start = max(s.prices.index[0], s.prices.index[-1] - pd.DateOffset(years=5))
    series = {n: x[x.index >= start] / x[x.index >= start].iloc[0] * 100 for n, x in series.items()}
    st.plotly_chart(line_chart(series, recessions=ui.recessions(), height=320), width="stretch", theme="streamlit")
with c2:
    st.markdown("**Выручка, прибыль и свободный денежный поток**, млрд")
    y = s.years[["Выручка", "Чистая прибыль", "FCF"]] / 1e9
    y.index = [d.strftime("%Y") for d in y.index]
    st.plotly_chart(grouped_bars(y.rename(columns={"FCF": "Свободный денежный поток"})), width="stretch",
                    theme="streamlit")

# --- чувствительность ---
sens = S.sensitivities(s.prices, ui.load("SPY"), ui.load("DGS10"))
if sens:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Бета к рынку", f"{sens['beta']:.2f}", border=True,
              help="На сколько % в среднем менялась акция при движении S&P 500 на 1% (месячные данные, 5 лет). "
                   "> 1 — сильнее рынка, < 1 — спокойнее.")
    c2.metric(f"Реакция на ставки (рынок {sens['rate_mkt']:+.1f}%)", f"{sens['rate']:+.1f}%", border=True, help="Средняя доходность акции за месяц, когда 10-летняя доходность выросла на 1 п.п. — "
                                "«дюрация» акции. Сильнее рынка — акция похожа на длинную облигацию (компании роста).")
    payout = i.get("payoutRatio")
    c3.metric("Доля прибыли на дивиденды", f"{payout * 100:.0f}%" if payout is not None else "—", border=True,
              help="Сколько прибыли компания отдаёт дивидендами. Выше 100% — платит больше, чем зарабатывает.")
    c4.metric("Рост EPS в год", f"{growth:+.1f}%" if growth is not None else "—", border=True,
              help=f"Среднегодовой рост прибыли на акцию за доступные {S.years_word(len(s.years))}.")

st.caption("Источник — Yahoo Finance; данные компаний бывают с ошибками и задержкой. Перед любым решением "
           "сверяйтесь с отчётностью компании (10-K). Это учебный инструмент, а не инвестиционная рекомендация.")
