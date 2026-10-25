"""Крипта: цепочка до цены — неглубокая рабочая модель для торговли: причины → участники → стакан → цена, по 2–3
показателя на звено. Подробно разобрано звено «стакан»; остальные — коротко."""
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from core import crypto, flows, orderbook, ui
from core.charts import line_chart

ICON = {"up": "🟢", "down": "🔴", "flat": "⚪"}
MACRO = {"cb_meeting", "opex_monthly", "quarter_end", "vix_expiry", "index_rebalance", "token_unlock", "month_end"}


@st.cache_data(ttl=60, show_spinner="Смотрю стакан…")
def book():
    return {v: orderbook.depth(v) for v in ("spot", "perp")}, {v: orderbook.taker_share(v) for v in ("spot", "perp")}


@st.cache_data(ttl=120, show_spinner=False)
def depth_history():
    return orderbook.history("BTC", 24)


@st.cache_data(ttl=300, show_spinner=False)
def live():
    return crypto.live(days=1)


@st.cache_data(ttl=3600, show_spinner=False)
def events():
    try:
        ev = flows.calendar(date.today(), date.today() + timedelta(days=7))
    except Exception:
        return None
    big = {"BTC", "ETH", "SOL", "XRP", "BNB", "DOGE", "ADA", "AVAX", "LINK", "SUI", "TON", "TRX"}
    out, small = [], 0
    for e in ev:
        if e["type"] == "cb_meeting" and "ФРС" not in e["title"]:
            continue  # для крипты из центробанков важна только ФРС
        if e["type"] == "token_unlock":
            if set(e.get("assets") or []) & big:
                out.append(e)
            elif e.get("major"):
                small += 1
        elif e["type"] in MACRO and e.get("major"):
            out.append(e)
    return out, small


def mln(x: float) -> str:
    return f"${x / 1e6:.1f} млн"


st.title("Крипта: цепочка до цены")
st.markdown("Цена двигается не сама: **причины** (новости, события) меняют решения **участников**, участники "
            "приходят в **стакан** заявками, и только сделки в стакане двигают **цену**. Здесь по 2–3 показателя на "
            "каждое звено — ровно столько, чтобы понять, кто сейчас толкает цену. Это описание текущего момента, а не "
            "прогноз.")

try:
    dep, tak = book()
except Exception as e:  # биржа недоступна — показываем остальное
    dep, tak = None, None
    st.warning(f"Binance не отвечает: {e}")
lv = live()
hist = depth_history()
src = "Binance вживую"
if hist is not None:
    last = hist[hist["ts"] == hist["ts"].max()]
    kinds = orderbook.by_kind(last)
    if (pd.Timestamp.now(tz="UTC") - hist["ts"].max()) < pd.Timedelta(minutes=15) and {"spot", "perp"} <= set(kinds):
        dep = {k: {**(dep or {}).get(k, {}), **v} for k, v in kinds.items()}
        src = f"снимок trade-news {hist['ts'].max():%H:%M} UTC"
norm = {v: orderbook.taker_norm(ui.load, v) for v in ("spot", "perp")}

# ---------- выводы по звеньям ----------
aggr = {v: tak[v][4] - norm[v] for v in tak} if tak else {}
imb = {v: (d["bids"] - d["asks"]) / (d["bids"] + d["asks"]) * 100 for v, d in dep.items()} if dep else {}
push = sum(aggr.values()) / len(aggr) if aggr else 0.0
push_dir = "up" if push > 1 else "down" if push < -1 else "flat"

# ---------- 1. причины ----------
with st.container(border=True):
    st.markdown("#### 1. Причины")
    got = events()
    if got is None:
        st.caption("Календарь trade-news не отвечает.")
    else:
        ev, small = got
        tail = f" Крупных разлоков мелких токенов: {small} — на биткоин не влияют." if small else ""
        if not ev:
            st.markdown("На неделе крупных событий для биткоина нет — движение задают участники, а не новости." + tail)
        else:
            st.markdown(f"**Событий на неделе: {len(ev)}.** Ближайшие: "
                        + "; ".join(f"{e['title']} ({e['date'][8:]}.{e['date'][5:7]})" for e in ev[:3]) + "." + tail)
    st.caption("Решения ФРС, экспирации, крупные разлоки токенов. Главные новости дня — позже, когда появится их поток.")

# ---------- 2. участники ----------
etf = ui.load("ETF_FLOW_BTC")
head, color, f_now, f_pct = crypto.lev_verdict(ui.load)
stab = crypto.supply_growth(ui.load, 30)
with st.container(border=True):
    st.markdown("#### 2. Участники")
    c = st.columns(3)
    c[0].metric("Спотовые ETF за 5 дней", f"${etf.iloc[-5:].sum():+,.0f} млн".replace(",", " "),
                "долгие деньги", delta_color="off", border=True)
    c[1].metric("Спекулянты с плечом: фандинг", f"{f_now:.1f}%", f"годовых · выше {f_pct:.0f}% истории",
                delta_color="off", border=True, help="Сколько лонги платят шортам. Высокий — толпа покупает в долг.")
    c[2].metric("Стейблкоины за 30 дней", f"{stab.iloc[-1]:+.1f}%", "топливо внутри крипты", delta_color="off",
                border=True)

# ---------- 3. стакан ----------
with st.container(border=True):
    st.markdown("#### 3. Стакан — где цена решается")
    st.markdown("В стакане два вида заявок. **Лимитные** стоят и ждут: они **держат** цену. **Рыночные** исполняются "
                "сразу по лучшей встречной цене: они **двигают** цену. Цена сдвигается, только когда агрессор "
                "(рыночная заявка) съедает весь уровень лимитных заявок. Значит, важны три вещи: сколько стоит "
                "рядом с ценой, кто сейчас агрессор и сколько рыночных заявок идёт **вынужденно** — от ликвидаций.")
    if dep:
        c = st.columns(2)
        for col, (v, name) in zip(c, (("spot", "Спот"), ("perp", "Фьючерсы"))):
            d = dep[v]
            col.metric(f"{name}: стакан ±{orderbook.BAND}%", f"{mln(d['bids'])} / {mln(d['asks'])}",
                       f"покупка / продажа · перевес {imb[v]:+.0f}%" + (f" · {d['venues']}" if d.get("venues") else ""),
                       delta_color="off", border=True,
                       help="Сумма лимитных заявок на покупку и на продажу в пределах ±0,1% от цены. Перевес — какая "
                            "сторона толще: толстая сторона тормозит движение в свою сторону.")
        c = st.columns(2)
        for col, (v, name) in zip(c, (("spot", "Спот"), ("perp", "Фьючерс"))):
            col.metric(f"{name}: агрессивные покупки за 4 ч", f"{tak[v][4]:.1f}%",
                       f"норма {norm[v]:.1f}% · {aggr[v]:+.1f} п.п. · за 1 ч {tak[v][1]:.0f}% · за 24 ч {tak[v][24]:.0f}%",
                       delta_color="off", border=True,
                       help="Доля покупок по рынку в обороте. Выше нормы — агрессор покупатель, ниже — продавец. "
                            "Норма — медиана дневных значений за прошлый год.")
    if hist is not None and hist["ts"].nunique() > 1:
        with st.expander("Глубина за сутки"):
            rows = []
            for ts, g in hist.groupby("ts"):
                k = orderbook.by_kind(g)
                rows.append({"ts": ts, **{f"{kind} {side}": k[kind][side] / 1e6 for kind in k for side in ("bids", "asks")}})
            h = pd.DataFrame(rows).set_index("ts")
            names = {"spot bids": "Спот: покупка", "spot asks": "Спот: продажа", "perp bids": "Фьючерсы: покупка",
                     "perp asks": "Фьючерсы: продажа"}
            st.plotly_chart(line_chart({names[c]: h[c] for c in h.columns if c in names}, units="млн $", height=260),
                            width="stretch")
            st.caption("Сумма заявок ±0,1% от цены, млн $, снимки trade-news раз в 5 минут. История копится с "
                       "25.10.2026 — когда её станет достаточно, здесь появится проверка: что бывает с ценой после "
                       "истончения стакана.")
    lq = orderbook.liquidations(lv)
    if lq and dep:
        hit_bids = lq["long"] / dep["perp"]["bids"] * 100
        hit_asks = lq["short"] / dep["perp"]["asks"] * 100
        st.metric("Ликвидации за час против стакана фьючерсов ±0,1%",
                  f"продажи {hit_bids:.0f}% · покупки {hit_asks:.0f}%",
                  f"лонги {mln(lq['long'])}, шорты {mln(lq['short'])}", delta_color="off", border=True,
                  help="Вынужденные рыночные заявки за час в процентах от того, что стоит в стакане рядом с ценой. "
                       "Когда это десятки процентов и больше — тонкий стакан не держит, начинается каскад. Binance "
                       "присылает не больше одной ликвидации в секунду — в каскаде цифра занижена.")
    elif not lq:
        st.caption("Ликвидации: trade-news не отвечает.")
    if dep and tak:
        thin = "сверху" if dep["spot"]["asks"] + dep["perp"]["asks"] < dep["spot"]["bids"] + dep["perp"]["bids"] else "снизу"
        st.markdown(f"**Вывод по стакану:** "
                    + {"up": "агрессоры — покупатели (выше нормы)", "down": "агрессоры — продавцы (ниже нормы)",
                       "flat": "агрессоры уравновешены"}[push_dir]
                    + f"; стакан тоньше {thin} — в эту сторону цене легче пройти.")
    st.caption(f"Глубина: {src}. Описание текущего момента, не проверено на истории: история глубины копится в "
               f"trade-news с 25.10.2026 — когда её станет достаточно, здесь появится проверка.")

# ---------- 4. цена ----------
px = ui.load("BTC-USD").dropna()
d24 = float((dep["spot"]["mid"] / px.iloc[-2] - 1) * 100) if dep else float((px.iloc[-1] / px.iloc[-2] - 1) * 100)
move = "up" if d24 > 1 else "down" if d24 < -1 else "flat"
with st.container(border=True):
    st.markdown("#### 4. Цена")
    c = st.columns(2)
    c[0].metric("Биткоин", f"${(dep['spot']['mid'] if dep else px.iloc[-1]):,.0f}".replace(",", " "),
                f"{d24:+.1f}% к вчерашнему закрытию", delta_color="off", border=True)
    if tak:
        a24 = sum(tak[v][24] - norm[v] for v in tak) / len(tak)
        agree = (move == "up" and a24 > 0) or (move == "down" and a24 < 0) or move == "flat"
        c[1].metric("Сходится ли с агрессорами", "да" if agree else "нет",
                    f"давление за 24 ч {a24:+.1f} п.п. к норме", delta_color="off", border=True)
        st.markdown("Цена почти стоит: силы уравновешены." if move == "flat" else
                    "Цена идёт туда, куда давят агрессоры, — движение подтверждено сделками." if agree else
                    "Цена идёт **против** давления агрессоров: их заявки кто-то поглощает лимитными. На дневной "
                    "истории такое поглощение вело себя непоследовательно (раздел «Крипта», блок 1, CVD) — это "
                    "повод присмотреться, а не сигнал.")

st.caption("Данные: глубина — снимки trade-news (Binance, Bybit, OKX) или Binance вживую; часовые свечи — Binance; ликвидации, открытый интерес и "
           "календарь — trade-news; потоки ETF — Farside через trade-news; стейблкоины — DefiLlama. Подробно о каждом "
           "звене — в разделе «Крипта».")
