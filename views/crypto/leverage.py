"""Крипта, блок «Плечо и ликвидации» — по методу «Смыслы-Инварианты-Граф»: блок собран из пяти частей (позиция в
долг → шум против запаса → плата за удержание → толпа и каскад → когда залога не хватило); у каждой — смысл, законы
и доказательства на данных."""
import pandas as pd
import streamlit as st

from core import crypto, learn, ui
from core.charts import dual_axis_chart, line_chart
from core.learn import Example
from core.transforms import cut

NUM = 4
PERIODS = {"1 год": 1, "3 года": 3, "Вся история": None}
LEVS = [2, 3, 5, 10, 20, 50]
HORIZONS = {"за день": 1, "за неделю": 7, "за месяц": 30}


def usd(x: float) -> str:
    return f"${x:,.0f}".replace(",", " ")


# ---------- данные ----------
df = crypto.candles(ui.load)
price = float(ui.load("BTC-USD").dropna().iloc[-1])
fund = crypto.funding_ann(ui.load)
fund_all = ui.load("FUND_BTC")
cost_avg = float(fund_all.mean() * 365)
cost_recent = float(fund_all["2024":].mean() * 365)
odds = crypto.liq_odds(df, LEVS, HORIZONS)
since = df.index[0].year
head, color, f_now, f_pct = crypto.lev_verdict(ui.load)

# ---------- верх: смысл, скелет, связи ----------
learn.crypto_header(crypto.BY_NUM[NUM], len(crypto.BLOCKS),
                    "Большая часть торговли криптой — не покупка монет, а фьючерсы с плечом: ставка на цену в долг. "
                    "Блок идёт от вашей позиции (части 1–3) к рынку целиком (части 4–5).")

learn.takeaway(f"Главный урок: с плечом 10x лонг, открытый в случайный день, биржа закрыла бы в течение месяца в "
               f"{odds.loc['10x', 'за месяц']:.0f}% случаев. Толпа сейчас: {head[0].lower() + head[1:]}.",
               {"orange": "warn"}.get(color, "neutral"))

c = st.columns(4)
c[0].metric("1 · Ликвидация при 10x", f"−{crypto.liq_distance(10):.1f}%", "от цены входа", delta_color="off",
            border=True)
c[1].metric("2 · Выбит за месяц при 10x", f"{odds.loc['10x', 'за месяц']:.0f}%", f"дней с {since} года",
            delta_color="off", border=True)
c[2].metric("3 · Цена удержания", f"{cost_recent:.0f}%", "годовых от позиции, с 2024", delta_color="off",
            border=True)
c[3].metric("4 · Фандинг сейчас", f"{f_now:.1f}%", f"годовых · выше {f_pct:.0f}% истории", delta_color="off",
            border=True)

# ---------- 1. позиция в долг ----------
with learn.part_section(NUM, "pos"):
    st.markdown("Вы вносите залог, биржа даёт позицию в несколько раз больше. Прибыль и убыток считаются от всей "
                "позиции: при 10x движение на 5% — это половина залога. Когда залог почти кончился, биржа закрывает "
                "позицию сама — это **ликвидация**.")
    left, right = st.columns([1, 2])
    with left:
        lev = st.select_slider("Плечо", options=LEVS, value=10, key="lev_x", format_func=lambda x: f"{x}x")
        side = st.segmented_control("Позиция", ["лонг", "шорт"], default="лонг", key="lev_side") or "лонг"
    dist = crypto.liq_distance(lev)
    liq_price = price * (1 - dist / 100) if side == "лонг" else price * (1 + dist / 100)
    with right:
        c = st.columns(2)
        c[0].metric("Цена ликвидации", usd(liq_price), f"{'−' if side == 'лонг' else '+'}{dist:.1f}% от {usd(price)}",
                    delta_color="off", border=True)
        c[1].metric("Залог на $10 000 позиции", usd(10_000 / lev), f"плечо {lev}x", delta_color="off", border=True)
    st.caption("Ползунок управляет и следующими двумя частями.")
    with st.expander("Подробнее: кросс-маржа, стоп, комиссии, марк-цена"):
        st.markdown(f"""
- **Кросс-маржа включена на Binance по умолчанию.** В изолированной марже вы рискуете только залогом позиции. В
  кросс-марже в залог идёт весь счёт: реальное плечо — позиция, делённая на весь счёт, а не цифра на ползунке.
- **Стоп-лосс — не ликвидация.** Стоп вы ставите сами, он срабатывает по цене последней сделки, в каскаде — с
  проскальзыванием. Стоп — заметно раньше ликвидации, а размер позиции считают от стопа (блок 10).
- **Комиссии.** Около {crypto.FEE}% от позиции за сделку по рынку: при 10x вход и выход съедают около 1% залога.
- **Марк-цена.** Ликвидация срабатывает не по последней сделке, а по индексу цены на нескольких биржах — это защищает
  от случайного выброса, но не от настоящего обвала. Поддерживающая маржа (~{crypto.MMR}% позиции) делает запас
  чуть меньше 100/плечо.
""")

# ---------- 2. шум против запаса ----------
with learn.part_section(NUM, "noise"):
    side_odds = odds if side == "лонг" else crypto.liq_odds(df, LEVS, HORIZONS, "short")
    recent = crypto.liq_odds(df["2023":], LEVS, HORIZONS, "long" if side == "лонг" else "short")
    st.markdown(f"Запас до ликвидации при {lev}x — около {dist:.1f}%. Цена почти никогда не идёт по прямой: "
                f"**{side}** с таким плечом биржа закрыла бы за неделю в "
                f"**{side_odds.loc[f'{lev}x', 'за неделю']:.0f}%** дней с {since} года — даже если потом цена пошла в "
                f"нужную сторону.")
    st.markdown(f"**Доказательство:** доля дней, когда {side} с плечом, открытый на закрытии, был бы ликвидирован, %.")
    st.dataframe(pd.concat([side_odds, recent.add_suffix(", с 2023")], axis=1).style.format("{:.0f}%"), width="stretch")
    st.caption(f"По дневным {'минимумам' if side == 'лонг' else 'максимумам'} биткоина; комиссии и фандинг не учтены, "
               f"а минимум последней сделки глубже марк-цены — это грубая оценка. У альткоинов колебания в разы больше.")

# ---------- 3. плата за удержание ----------
with learn.part_section(NUM, "fund"):
    st.markdown("У бессрочного фьючерса нет даты погашения. Чтобы его цена не отрывалась от монеты, одна сторона "
                "платит другой каждые несколько часов (у биткоина — раз в 8 часов, у многих альткоинов чаще). Обычно "
                "платят лонги. Плата идёт от всей позиции, поэтому с плечом она съедает залог быстрее.")
    c = st.columns(2)
    c[0].metric(f"Фандинг за год при {lev}x", f"{'−' if side == 'лонг' else '+'}{cost_recent * lev:.0f}%",
                f"от залога: {'платите' if side == 'лонг' else 'получаете'}, по средней ставке с 2024",
                delta_color="off", border=True)
    c[1].metric("Средний фандинг", f"{cost_avg:.0f}%", f"годовых с 2019 · с 2024 — {cost_recent:.0f}%",
                delta_color="off", border=True)
    st.caption("Тот же фандинг — у всех держателей позиций сразу. Поэтому дальше, в части 4, он становится "
               "градусником толпы: один ряд, два смысла.")

# ---------- 4. толпа и каскад ----------
with learn.part_section(NUM, "crowd"):
    st.markdown("Когда биржа закрывает чужие лонги, она продаёт их по рынку, и цена падает к следующим. Падение "
                "разгоняется, пока не кончатся позиции с плечом или не придут покупатели. Поэтому самые резкие "
                "движения крипты случаются внутри дня, а потом цена частично возвращается.")
    st.markdown("**Доказательство каскадов:** самые резкие падения внутри дня с запуска фьючерсов Binance в 2019 году.")
    st.dataframe(crypto.crash_days(ui.load).style.format("{:.1f}"), width="stretch")
    st.markdown("**Доказательство про фандинг:** высокий фандинг — много плеча в одну сторону. Но предупреждает ли "
                "он об обвале?")
    years = PERIODS[st.segmented_control("Период графика", list(PERIODS), default="3 года", key="period") or "3 года"]
    st.plotly_chart(dual_axis_chart(("Биткоин", cut(df["c"], years), "$"),
                                    ("Фандинг за неделю", cut(fund, years), "% годовых"), height=300), width="stretch")
    t_old = crypto.funding_test(ui.load, "2019", "2022")
    t_new = crypto.funding_test(ui.load, "2023", "2026")
    crash_col, n_col = t_old.columns[2], t_old.columns[3]
    top, mid = "самый высокий", "средний"
    n_new = float(t_new[n_col].get(top, 0))
    st.markdown(f"Недели разбиты на пять групп по фандингу. В 2019–2022 годах после самого высокого фандинга биткоин "
                f"падал на 15%+ за месяц в {t_old[crash_col][top]:.0f}% случаев, после среднего — в "
                f"{t_old[crash_col][mid]:.0f}%. "
                + (f"С 2023 года самый высокий фандинг набирается лишь на ≈{n_new:.0f} независимых месяцев — "
                   f"{t_new[crash_col][top]:.0f}% против {t_new[crash_col][mid]:.0f}%: проверить почти не на чем."
                   if top in t_new.index else "С 2023 года такого фандинга не было ни разу."))
    with st.expander("Таблицы проверки и почему сигнал ослаб"):
        c = st.columns(2)
        c[0].markdown("**2019–2022**")
        c[0].dataframe(t_old.style.format("{:.1f}", subset=t_old.columns[:3]), width="stretch")
        c[1].markdown("**2023–2026**")
        c[1].dataframe(t_new.style.format("{:.1f}", subset=t_new.columns[:3]), width="stretch")
        st.markdown("Когда фандинг высокий, фонды покупают монету и продают фьючерс — забирают фандинг почти без "
                    "риска. Их шорты гасят перекос. Часть плеча ушла в альткоины и опционы — фандинг биткоина видит "
                    "не всё.")

    st.markdown("**Топливо сейчас** — факт на сегодня, а не доказательство закона: история копится в trade-news с "
                "13.10.2026.")
    lv = crypto.live()
    if lv is None or lv["totals"].empty:
        st.warning("Сервис trade-news не отвечает — свежих данных о плече нет.")
    else:
        tot, liq = lv["totals"], lv["liq"]
        oi_now, oi_prev = tot["oi_usd"].iloc[-1], tot["oi_usd"][:tot.index[-1] - pd.Timedelta(hours=24)]
        oi_chg = (oi_now / oi_prev.iloc[-1] - 1) * 100 if len(oi_prev) else float("nan")
        day = liq[liq.index > liq.index.max() - pd.Timedelta(hours=24)] if len(liq) else liq
        long_l = float(day.loc[day["side"] == "long", "usd"].sum()) if len(day) else 0.0
        short_l = float(day.loc[day["side"] == "short", "usd"].sum()) if len(day) else 0.0
        c = st.columns(3)
        c[0].metric("Открытый интерес", f"${oi_now / 1e9:.1f} млрд", f"{oi_chg:+.1f}% за сутки", delta_color="off",
                    border=True, help="Сумма всех открытых фьючерсных позиций по BTC на Binance, Bybit и OKX.")
        c[1].metric("Ликвидировано лонгов", f"${long_l / 1e6:.1f} млн", "за сутки", delta_color="off", border=True,
                    help="Принудительные продажи. В каскаде цифра занижена: Binance присылает не больше одной "
                         "ликвидации в секунду.")
        c[2].metric("Ликвидировано шортов", f"${short_l / 1e6:.1f} млн", "за сутки", delta_color="off", border=True)
        with st.expander("График за трое суток"):
            st.plotly_chart(dual_axis_chart(("Открытый интерес", tot["oi_usd"] / 1e9, "млрд $"),
                                            ("Цена", lv["snapshots"].groupby("ts")["mark_price"].mean()
                                             .pipe(lambda s: s.set_axis(pd.to_datetime(s.index))), "$"), height=280),
                            width="stretch")
            st.caption("Рост открытого интереса вместе с ценой — новые деньги с плечом; падение интереса при падении "
                       "цены — закрытия и ликвидации.")

# ---------- 5. когда залога не хватило ----------
with st.expander("5. Когда залога не хватило — страховой фонд и ADL"):
    with learn.part_section(NUM, "adl"):
        st.markdown("В резком обвале позицию иногда закрывают хуже нуля. Этот минус биржа покрывает из страхового "
                    "фонда, а если фонда мало — включает **ADL**: принудительно закрывает прибыльные позиции другой "
                    "стороны. Даже выигрышный хедж могут закрыть без спроса — так было 10.10.2025 (пример ниже).")


# ---------- примеры ----------
def show_crash(day: str, before: int, after: int, text: str) -> None:
    d = pd.Timestamp(day)
    w = df[d - pd.Timedelta(days=before):d + pd.Timedelta(days=after)]
    f = fund[d - pd.Timedelta(days=before):d + pd.Timedelta(days=after)]
    drop = (df.loc[d:d + pd.Timedelta(days=1), "lo"].min() / df["c"][:d].iloc[-2] - 1) * 100  # каскад бывает через полночь
    fb = float(fund[:d].iloc[-2])
    c = st.columns(3)
    c[0].metric("Падение за 2 дня", f"{drop:.0f}%", "минимум к закрытию накануне", delta_color="off", border=True)
    c[1].metric("Фандинг за неделю до", f"{fb:.0f}%", f"годовых, в среднем {cost_avg:.0f}%", delta_color="off",
                border=True)
    c[2].metric("Ликвидирован бы лонг", f"от {100 / (-drop + crypto.MMR):.0f}x", "за эти дни", delta_color="off",
                border=True)
    st.plotly_chart(line_chart({"Закрытие": w["c"], "Минимум дня": w["lo"]}, units="$", height=280), width="stretch")
    st.plotly_chart(line_chart({"Фандинг за неделю, % годовых": f}, height=200), width="stretch")
    heat = "выше" if fb > 1.5 * cost_avg else "ниже" if fb < 0.5 * cost_avg else "около"
    st.markdown(f"Фандинг за неделю до обвала — {fb:.0f}% годовых, {heat} среднего ({cost_avg:.0f}%). " + text)


st.subheader("Примеры: части 4–5 на реальных обвалах")
learn.examples([
    Example("12 марта 2020: «чёрный четверг»", lambda: show_crash(
        "2020-03-12", 20, 20,
        "Пандемия, паника на всех рынках. Падение акций запустило ликвидации на бирже BitMEX, их продажи уронили "
        "цену, что закрыло следующих. Каскад перешёл через полночь и остановился, когда около 02:15 UTC 13 марта "
        "BitMEX на время перестал работать (биржа объяснила это DDoS-атакой): продавать стало некому.")),
    Example("19 мая 2021: распродажа после пика", lambda: show_crash(
        "2021-05-19", 25, 15,
        "После рекордов весны 2021 года рынок был забит лонгами. 12 мая Tesla перестала принимать биткоин, 18 мая "
        "отраслевые ассоциации Китая напомнили банкам о запрете работать с криптой — падение началось, плечо "
        "превратило его в обвал, Binance в тот день тормозил под нагрузкой. Классика: перегретый фандинг → каскад.")),
    Example("10 октября 2025: каскад без перегрева и ADL", lambda: show_crash(
        "2025-10-10", 20, 10,
        "Градусник толпы не предупреждал. Вечер пятницы, около 21:00 UTC — объявление о 100% пошлинах США против "
        "Китая; биржи акций и CME закрыты, стакан тонкий. На Binance токен USDe, который многие держали как залог, "
        "упал примерно до 65 центов по внутреннему стакану биржи — позиции под этот залог ликвидировались, хотя "
        "сами не были перегреты. Альткоины проваливались на десятки процентов за минуты, страховых фондов не "
        "хватило — биржи включили ADL и закрывали прибыльные шорты и хеджи. Около $19 млрд ликвидаций — рекорд. "
        "Урок: каскад может запустить не толпа, а слабое звено в залогах (блок 2)."), normal=False),
], key="leverage")

# ---------- граф блока ----------
st.divider()
st.subheader("Как части блока связаны")
st.graphviz_chart(learn.block_graph(NUM), width="stretch")
st.caption("Синие — части этого блока, серые — соседние блоки и цена. Стрелки не показывают силу связи: депег залога "
           "бывает редко, но бьёт сильнее обычного движения.")
c = st.columns(3)
c[0].page_link(learn.CRYPTO_MODEL, label="Модель крипты", icon="🧠")
c[1].page_link("views/crypto/plumbing.py", label="2. Биржи и стейблкоины", icon="🪙")
c[2].page_link("views/crypto/risk.py", label="10. Риск-менеджмент", icon="🛡️")
