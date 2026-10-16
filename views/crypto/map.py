"""Крипта: что сейчас — рабочая панель модели. По каждому контейнеру модели («Модель за 5 минут») — вывод по
свежим данным, по одной главной цифре на блок."""
import pandas as pd
import streamlit as st

from core import crypto, learn, ui

ICON = {"green": "🟢", "red": "🔴", "orange": "🟠", "blue": "🔵", "gray": "⚪"}


def answer(num: int) -> tuple[str, str, str]:
    if num == 1:
        w = crypto.weekly(ui.load)
        head, color, c = crypto.verdict(w)
        return head, f"Nasdaq объясняет около {c * c * 100:.0f}% движений биткоина за последний год.", color
    if num == 2:
        bas, bill = crypto.basis(ui.load), ui.load("DGS3MO").dropna()
        edge = float(bas.iloc[-1] - bill.iloc[-1] - 0.75)
        head = ("Базисная сделка выгодна: часть притока в ETF — арбитраж" if edge > 0.5 else
                "Базисная сделка убыточна — арбитражный приток в ETF иссякает" if edge < -0.5 else
                "Базисная сделка на грани безубыточности")
        return head, (f"Фьючерс CME дороже спота на ≈{bas.iloc[-1]:.1f}% годовых, безрисковые векселя дают "
                      f"{bill.iloc[-1]:.1f}%."), "orange" if edge < -0.5 else "gray"
    if num == 3:
        ev = crypto.event_study(ui.load)
        by = ev.groupby("Вид")["За 2 дня, %"].median()
        return ("Аварии внутри крипты бьют сильнее регуляторов",
                f"За 2 дня после аварий внутри крипты — {by['шок']:+.0f}% (медиана), после смягчения правил — "
                f"{by['рег+']:+.1f}%.", "gray")
    if num == 4:
        head, color, f, pct = crypto.lev_verdict(ui.load)
        odds = crypto.liq_odds(crypto.candles(ui.load), [10], {"м": 30})
        return head, (f"Фандинг за неделю {f:.1f}% годовых — выше, чем в {pct:.0f}% дней с 2019 года. С плечом 10x "
                      f"лонг закрывался бы биржей в течение месяца в {odds.iloc[0, 0]:.0f}% случаев."), color
    if num == 5:
        g = crypto.supply_growth(ui.load)
        pct = float((g["2019":] < g.iloc[-1]).mean() * 100)
        tot = ui.load("STABLE_TOTAL")
        head = ("Топливо прибывает: стейблкоинов становится заметно больше" if pct >= 70 else
                "Топливо почти не прибывает" if pct <= 30 else "Топливо прибывает в обычном темпе")
        return head, (f"Стейблкоинов в обращении ${tot.iloc[-1]:.0f} млрд, {g.iloc[-1]:+.1f}% за 90 дней. Рост "
                      f"идёт вместе с ценой, а не заранее."), "orange" if pct <= 30 else "gray"
    if num == 6:
        o = crypto.onchain(ui.load)
        mv = float(o["mvrv"].iloc[-1])
        head = ("Держатели в большой прибыли — рынок перегрет" if mv >= 3 else
                "Держатели в убытке — исторически зона дна" if mv < 1 else "Держатели в умеренной прибыли")
        return head, (f"MVRV {mv:.2f}: цена ${o['price'].iloc[-1]:,.0f} против средней цены покупки "
                      f"${o['realized'].iloc[-1]:,.0f}."
                      ).replace(",", " "), "orange" if mv >= 3 else "green" if mv < 1 else "gray"
    if num == 7:
        btc, eth = ui.load("BTC-USD").dropna(), ui.load("ETH-USD").dropna()
        eb = (eth / btc).dropna()
        chg = float((eb.iloc[-1] / eb[:eb.index[-1] - pd.Timedelta(days=90)].iloc[-1] - 1) * 100)
        head = ("Сезон альткоинов: эфир обгоняет биткоин" if chg > 15 else
                "Альткоины отстают от биткоина" if chg < -5 else "Альткоины идут вровень с биткоином")
        return head, (f"Эфир к биткоину {eb.iloc[-1]:.4f}, {chg:+.0f}% за 90 дней; на пике 2021 года — "
                      f"{eb['2021'].max():.4f}."), "green" if chg > 15 else "orange" if chg < -5 else "gray"
    if num == 8:
        p = crypto.onchain(ui.load)["price"]
        dd = float((p.iloc[-1] / p.max() - 1) * 100)
        days = (p.index[-1] - p.idxmax()).days
        return (f"Медвежья фаза цикла: {days} дней после вершины" if dd < -20 else "Бычья фаза цикла",
                f"Вершина {p.idxmax():%d.%m.%Y}, цена сейчас {dd:.0f}% от неё. В прошлых циклах дно приходило "
                f"примерно через год после вершины.", "orange" if dd < -20 else "green")
    if num == 9:
        return ("Размер позиции считают от стопа", "Риск на сделку 0,5–2% счёта; плечо — следствие, а не выбор.", "gray")
    if num == 10:
        df = crypto.ohlcv(ui.load, "BTC")
        m = crypto.wyckoff_marks(df)
        pos = (df["c"].iloc[-1] - m["lo"].iloc[-1]) / (m["hi"].iloc[-1] - m["lo"].iloc[-1]) * 100
        head = ("Биткоин у низа диапазона 60 дней" if pos < 25 else "Биткоин у верха диапазона 60 дней" if pos > 75
                else "Биткоин в середине диапазона 60 дней")
        return head, f"Цена на {pos:.0f}% высоты диапазона. Фазу определяйте по силам модели, а не по пробоям.", "gray"
    raise KeyError(num)


left, right = st.columns([5, 1], vertical_alignment="bottom")
left.title("Крипта: что сейчас")
with right:
    st.page_link(learn.CRYPTO_MODEL, label="Модель за 5 минут", icon="🧠")
st.markdown("Рабочая панель: по одному выводу на каждую часть модели — что показывают данные сегодня. Из каких "
            "частей состоит рынок, какие законы его держат и как части связаны — на странице «Модель за 5 минут».")

# ---------- объект в центре ----------
btc = ui.load("BTC-USD").dropna()
dd = crypto.drawdown(btc)
year = float((btc.iloc[-1] / btc[:btc.index[-1] - pd.DateOffset(years=1)].iloc[-1] - 1) * 100)
c = st.columns(3)
c[0].metric("Биткоин", f"${btc.iloc[-1]:,.0f}".replace(",", " "), border=True)
c[1].metric("За год", f"{year:+.0f}%", border=True)
c[2].metric("От максимума", f"{dd.iloc[-1]:.0f}%", delta_color="off", border=True)

for i, cont in enumerate(crypto.CONTAINERS, 1):
    st.subheader(f"{i}. {cont.title}")
    for n in cont.blocks:
        b = crypto.BY_NUM[n]
        with st.container(border=True):
            left, right = st.columns([5, 1], vertical_alignment="center")
            with left:
                st.caption(f"Блок {b.order} · {b.title}")
                if b.page:
                    try:
                        head, why, color = answer(n)
                        st.markdown(f"#### {ICON[color]} {head}")
                        st.markdown(why)
                    except Exception as e:  # один недоступный ряд не должен гасить всю карту
                        st.warning(f"Нет данных: {e}")
                else:
                    st.markdown(f"{b.about}  \n:gray[блок в разработке]")
            with right:
                if b.page:
                    st.page_link(b.page, label="Открыть", icon="➡️")
