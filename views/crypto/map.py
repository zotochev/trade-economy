"""Карта крипты: объект в центре, вокруг — среда (что давит снаружи) и устройство (из чего крипта состоит и как
части толкают друг друга). У построенных блоков — вывод по свежим данным."""
import pandas as pd
import streamlit as st

from core import crypto, learn, ui

ICON = {"green": "🟢", "red": "🔴", "orange": "🟠", "blue": "🔵", "gray": "⚪"}

# Как части крипты действуют друг на друга: (откуда, куда, что передаётся)
LINKS = [
    ("Мировые деньги", "ETF и большие деньги", "дешёвые деньги — фонды берут больше риска"),
    ("ETF и большие деньги", "Цена", "покупка в ETF — покупка настоящих монет"),
    ("Стейблкоины", "Цена", "новые стейблкоины — свежие доллары, готовые к покупке"),
    ("Предложение и майнеры", "Цена", "халвинг вдвое режет поток новых монет на продажу"),
    ("Цена", "Плечо", "рост цены — участники берут больше плеча"),
    ("Плечо", "Цена", "падение цены — ликвидации — вынужденные продажи — ещё падение"),
    ("Цена", "Альткоины", "альткоины повторяют движения биткоина, но сильнее"),
]


def answer(num: int) -> tuple[str, str, str]:
    if num == 1:
        w = crypto.weekly(ui.load)
        head, color, c = crypto.verdict(w)
        _, after = crypto.era_corr(w)
        return head, (f"Корреляция с Nasdaq за полгода {c:+.2f} (в среднем с 2020 года {after:+.2f}), со связью с "
                      f"ликвидностью ФРС {crypto.liquidity_corr(ui.load):+.2f}."), color
    raise KeyError(num)


left, right = st.columns([5, 1], vertical_alignment="bottom")
left.title("Карта крипты")
with right:
    learn.help_link("Справка")
st.markdown("Чтобы понимать крипту, мало смотреть на цену. Нужно видеть, **из чего она состоит** и **в какой среде "
            "живёт**. Карта собирает обе стороны: снаружи — мировые деньги и институционалы, внутри — монеты, "
            "доллары крипты, плечо и участники.")

with learn.how_it_works("Как читать карту"):
    st.markdown("""
- **Среда** — силы снаружи: ставки ФРС, доллар, фонды и регуляторы. Крипта на них не влияет, а они на неё — да.
- **Устройство** — части самой крипты: откуда берутся монеты, на какие деньги их покупают, сколько взято в
  долг, кто участники. Они толкают друг друга и создают внутренние циклы.
- **Связи** внизу — как одна часть передаёт импульс другой. Самая важная для трейдера — петля плеча: она делает
  падения в крипте резкими.
- Блоки строятся по одному. У построенного — вывод по свежим данным и ссылка на экран.
""")

# ---------- объект в центре ----------
btc = ui.load("BTC-USD").dropna()
dd = crypto.drawdown(btc)
year = float((btc.iloc[-1] / btc[:btc.index[-1] - pd.DateOffset(years=1)].iloc[-1] - 1) * 100)
with st.container(border=True):
    st.caption("В центре · объект")
    c = st.columns(3)
    c[0].metric("Биткоин", f"${btc.iloc[-1]:,.0f}".replace(",", " "), border=True)
    c[1].metric("За год", f"{year:+.0f}%", border=True)
    c[2].metric("От максимума", f"{dd.iloc[-1]:.0f}%", f"максимум ${btc.max():,.0f}".replace(",", " "),
                delta_color="off", border=True)

for side, title in (("среда", "Среда: что давит снаружи"), ("устройство", "Устройство: из чего крипта состоит")):
    st.subheader(title)
    for b in [b for b in crypto.BLOCKS if b.side == side]:
        with st.container(border=True):
            left, right = st.columns([5, 1], vertical_alignment="center")
            with left:
                st.caption(f"Блок {b.num} · {b.title}")
                if b.page:
                    try:
                        head, why, color = answer(b.num)
                        st.markdown(f"#### {ICON[color]} {head}")
                        st.markdown(why)
                    except Exception as e:  # один недоступный ряд не должен гасить всю карту
                        st.warning(f"Нет данных: {e}")
                else:
                    st.markdown(f"{b.about}  \n:gray[блок в разработке]")
            with right:
                if b.page:
                    st.page_link(b.page, label="Открыть блок", icon="➡️")

st.subheader("Связи: как части толкают друг друга")
st.markdown("\n".join(f"- **{a}** → **{b}**: {what}" for a, b, what in LINKS))
st.caption("Петля «цена → плечо → цена» работает в обе стороны: на росте плечо подливает топливо, на падении — "
           "ликвидации превращают спад в обвал.")
