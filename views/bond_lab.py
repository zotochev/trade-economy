"""Лаборатория облигаций: двигайте параметры и смотрите, как меняются цена, риск и доходность.
Два режима: учебная облигация (всё задаётся ползунками) и реальная (условия выпуска и цена из брокера)."""
from dataclasses import replace
from datetime import date

import numpy as np
import pandas as pd
import streamlit as st

from core import bond_lab as B
from core import curve, learn, ui
from core.bond_charts import cashflows, lines, price_yield, waterfall
from core.charts import hbar_chart

LEARN, REAL = "Учебная облигация", "Реальная облигация"
# Ориентиры по рейтингам: типичный спред и средняя доля дефолтов в год за долгую историю (Moody's, S&P), примерно
RATINGS = {"AAA": (0.6, 0.02), "AA": (0.8, 0.05), "A": (1.1, 0.1), "BBB": (1.6, 0.25), "BB": (3.0, 1.0),
           "B": (4.5, 3.5), "CCC": (10.0, 12.0)}


@st.cache_data(ttl=3600)
def market() -> dict:
    last = min(ui.load(k).index[-1] for k in curve.MATURITIES)
    c = curve.curve_at(ui.load, last)
    return {"curve": c, "date": last, "be": float(ui.load("T10YIE").dropna().iloc[-1]),
            "ig": float(ui.load("BAMLC0A0CM").dropna().iloc[-1]), "hy": float(ui.load("BAMLH0A0HYM2").dropna().iloc[-1])}


m = market()


def rf_at(years: float) -> float:
    c = m["curve"]
    return float(np.interp(years, c.index.to_numpy(dtype=float), c.to_numpy(dtype=float)))


PRESETS = {
    "10-летняя казначейская сейчас": dict(kind="fixed", years=10.0, coupon=round(rf_at(10) * 8) / 8, freq=2,
                                          spread=0.0),
    "Бескупонная на 30 лет": dict(kind="zero", years=30.0, coupon=0.0, freq=2, spread=0.0),
    "Купон 0,6% из 2020 года": dict(kind="fixed", years=4.0, coupon=0.625, freq=2, spread=0.0),
    "Мусорная облигация": dict(kind="fixed", years=7.0, coupon=8.0, freq=2, spread=round(m["hy"] + 1, 1),
                               pd=4.0, rec=40),
    "Плавающая ставка": dict(kind="floating", years=5.0, coupon=0.5, freq=4, spread=0.5),
    "TIPS на 10 лет": dict(kind="tips", years=10.0, coupon=1.5, freq=2, spread=0.0),
}
DEFAULTS = dict(kind="fixed", years=10.0, coupon=round(rf_at(10) * 8) / 8, freq=2, spread=0.0, pd=0.5, rec=40,
                curve=True, be=round(m["be"], 2), shock=1.0, hold=5.0, tshock=0.0, delta=1.0, infl=round(m["be"], 1))


def apply(values: dict) -> None:
    for k, v in values.items():
        st.session_state[f"bl_{k}"] = v
    st.session_state["bl_curve"] = True


def apply_rating() -> None:
    r = st.session_state["bl_rating"]
    if r in RATINGS:
        st.session_state["bl_spread"], st.session_state["bl_pd"] = RATINGS[r]


# Значения по умолчанию — только для отсутствующих ключей: Streamlit стирает состояние ползунков, которых не было
# на экране (например, учебных в режиме реальной облигации), а заданные пользователем трогать нельзя.
for k, v in DEFAULTS.items():
    st.session_state.setdefault(f"bl_{k}", v)

# ---------- шапка ----------
left, right = st.columns([5, 1], vertical_alignment="bottom")
left.caption("Подробнее к слою 3 «Рыночные ставки» · песочница")
with right:
    st.page_link("views/v2/market_rates.py", label="К слою 3", icon="⬅️")
st.title("Лаборатория облигаций")
st.markdown("Облигация — простой инструмент: вам обещают купоны и возврат номинала. Всё остальное — цена, риск, "
            "доходность — следует из этого обещания и рыночной ставки. Двигайте настройки и смотрите, что меняется.")
mode = st.segmented_control("Режим", [LEARN, REAL], default=LEARN, key="bl_mode", label_visibility="collapsed") \
    or LEARN

# ---------- настройки ----------
with st.container(border=True):
    if mode == LEARN:
        st.caption("Готовые примеры")
        cols = st.columns(len(PRESETS))
        for col, (name, values) in zip(cols, PRESETS.items()):
            col.button(name, on_click=apply, args=(values,), key=f"bl_p_{name}", width="stretch")
        a, b, c, d = st.columns(4)
        kind = a.selectbox("Тип", list(B.KINDS), format_func=B.KINDS.get, key="bl_kind",
                           help="Бескупонная платит только номинал в конце. Плавающая — купон = ставка + надбавка, "
                                "пересматривается каждый период. TIPS — номинал растёт вместе с инфляцией.")
        years = b.slider("Срок до погашения, лет", 0.5, 30.0, step=0.5, key="bl_years")
        coupon_label = {"floating": "Надбавка к плавающей ставке, п.п.", "tips": "Реальный купон, % в год"}.get(
            kind, "Купон, % в год")
        coupon = c.slider(coupon_label, 0.0, 12.0, step=0.125, key="bl_coupon", disabled=kind == "zero",
                          help="Сколько процентов от номинала платят в год.")
        freq = d.segmented_control("Выплат в год", [1, 2, 4, 12], key="bl_freq") or 2
        e, f, g = st.columns([2, 1, 1])
        with e:
            use_curve = st.toggle("Ставка гособлигаций — с текущей кривой", key="bl_curve",
                                  help=f"Ставка казначейских облигаций того же срока на {m['date']:%d.%m.%Y}.")
            if use_curve:
                st.session_state["bl_rf"] = round(rf_at(years), 2)
            rf = st.slider("Ставка гособлигаций того же срока, %", 0.0, 12.0, step=0.05, key="bl_rf",
                           disabled=use_curve, help="Безрисковая доходность: от неё отсчитывается всё остальное.")
        spread = f.slider("Кредитный спред, п.п.", 0.0, 12.0, step=0.1, key="bl_spread",
                          help=f"Надбавка за риск неплатежа. Сейчас на рынке: надёжные компании ≈ {m['ig']:.1f}, "
                               f"мусорные ≈ {m['hy']:.1f} п.п.")
        be = g.slider("Ожидаемая инфляция, %", 0.0, 8.0, step=0.05, key="bl_be",
                      help="Breakeven: какую инфляцию закладывает рынок. Нужна для TIPS и вкладки «Инфляция». "
                           "По умолчанию — 10-летний breakeven.")
        bond = B.Bond(kind, years, 0.0 if kind == "zero" else coupon, int(freq), rf, spread, be)
        clean = None
    else:
        st.caption("Возьмите условия выпуска и цену из брокера или с сайта биржи. Цена — «чистая», в % от номинала "
                   "(так её показывают в котировках).")
        a, b, c, d = st.columns(4)
        kind = a.selectbox("Тип", ["fixed", "zero", "tips"], format_func=B.KINDS.get, key="bl_rkind")
        maturity = b.date_input("Дата погашения", value=date(date.today().year + 5, 6, 15), min_value=date.today(),
                                max_value=date(date.today().year + 40, 12, 31), key="bl_rmat")
        coupon = c.number_input("Купон, % в год" if kind != "tips" else "Реальный купон, % в год", 0.0, 20.0,
                                4.0, 0.125, key="bl_rcoupon", disabled=kind == "zero")
        freq = d.selectbox("Выплат в год", [2, 1, 4, 12], key="bl_rfreq",
                           help="Казначейские и большинство корпоративных облигаций США — 2 раза в год.")
        e, f, g, h = st.columns(4)
        clean = e.number_input("Цена, % от номинала", 1.0, 300.0, 97.5, 0.05, key="bl_rprice")
        years = max((maturity - date.today()).days / 365.25, 1 / 365)
        rf = rf_at(years)
        be = g.number_input("Ожидаемая инфляция, %", 0.0, 10.0, round(m["be"], 2), 0.05, key="bl_rbe",
                            help="Только для TIPS: реальная доходность = ставка гособлигаций − ожидаемая инфляция.")
        recovery_r = h.slider("Возврат при дефолте, %", 0, 100, 40, key="bl_rrec",
                              help="Доля номинала, которую держатели в среднем получают после дефолта: ~40% для "
                                   "старших необеспеченных облигаций.")
        base = B.Bond(kind, years, 0.0 if kind == "zero" else coupon, int(freq), rf, 0.0, be)
        spread = B.implied_spread(base, clean)
        bond = replace(base, spread=spread)
        f.metric("Ставка гособлигаций того же срока", f"{rf:.2f}%", f"срок {years:.1f} г.", delta_color="off")
        st.checkbox("Облигация отзывная (эмитент может погасить раньше)", key="bl_rcall",
                    help="Многие корпоративные облигации отзывные. Тогда доходность к погашению завышает реальную: "
                         "при падении ставок облигацию погасят и купоны кончатся раньше.")

s = B.stats(bond)
y = bond.y

# ---------- итог ----------
c = st.columns(5)
if mode == REAL:
    c[0].metric("Доходность к погашению", f"{y:.2f}%",
                "реальная" if kind == "tips" else "в год, если держать до конца", delta_color="off", border=True)
    c[1].metric("Спред к гособлигациям", f"{spread:+.2f} п.п.",
                f"рынок закладывает ≈ {B.implied_default(spread, recovery_r):.1f}% дефолтов в год", delta_color="off",
                border=True, help="Доходность минус ставка гособлигаций того же срока (G-спред). Вероятность — если "
                                  "весь спред считать платой за ожидаемые потери при заданном возврате.")
    c[2].metric("Цена с накопленным купоном", f"{s.price:.2f}", f"накопленный купон {B.accrued(bond):.2f}",
                delta_color="off", border=True, help="Сколько вы реально заплатите: чистая цена + доля текущего "
                                                    "купона, которую продавец уже «заработал».")
else:
    c[0].metric("Цена", f"{s.price:.2f}", f"{s.price - 100:+.2f} к номиналу", delta_color="off", border=True,
                help="За 100 номинала, с накопленным купоном.")
    c[1].metric("Доходность к погашению", f"{y:.2f}%", "реальная" if kind == "tips" else "ставка + спред",
                delta_color="off", border=True)
    c[2].metric("Текущая доходность", f"{s.current_yield:.2f}%", "купон / цена", delta_color="off", border=True,
                help="Сколько приносят купоны в год относительно цены — без учёта того, что цена к погашению "
                     "придёт к 100.")
c[3].metric("Дюрация", f"{s.duration:.1f}", f"−{s.duration * 0.01:.1%} цены на +1 п.п.", delta_color="off",
            border=True, help="На сколько процентов меняется цена, если ставка сдвинулась на 1 п.п.")
c[4].metric("Центр тяжести выплат", f"{s.center:.1f} г.", f"последняя выплата — {s.last_share:.0f}% цены",
            delta_color="off", border=True, help="Средний срок выплат, взвешенный по их стоимости сегодня "
                                                 "(дюрация Маколея).")

if mode == REAL:
    if st.session_state.get("bl_rcall"):
        st.warning("Для отзывной облигации доходность к погашению — верхняя граница. Посмотрите в брокере "
                   "«доходность к худшему исходу» (yield to worst).")
    if spread < -0.15 and kind != "tips":
        st.info("Доходность ниже гособлигаций того же срока: проверьте цену и купон. Так бывает у муниципальных "
                "облигаций — их доход не облагается федеральным налогом.")
elif kind != "zero":
    gap = coupon - y
    if kind == "floating":
        st.markdown("Купон плавающий: он сам подстраивается под ставку, поэтому цена держится около 100 и почти "
                    "не боится роста ставок.")
    elif abs(gap) < 0.1:
        st.markdown("Купон равен рыночной доходности — облигация стоит около номинала.")
    elif gap < 0:
        st.markdown(f"Купон **{coupon:.2f}%** ниже рыночной доходности **{y:.2f}%** — облигация продаётся со "
                    f"скидкой: недостающий доход покупатель получит, когда к погашению цена дорастёт до 100.")
    else:
        st.markdown(f"Купон **{coupon:.2f}%** выше рыночной доходности **{y:.2f}%** — облигация стоит дороже "
                    f"номинала: за щедрые купоны платят сверху, и к погашению цена сползает к 100.")

tabs = st.tabs(["Из чего цена", "Если ставки изменятся", "Держать или продать", "Кредитный риск", "Инфляция"])

# ---------- 1. из чего цена ----------
with tabs[0]:
    t, cf = bond.flows()
    pv = cf * B.discount(y, t, bond.freq)
    st.plotly_chart(cashflows(t, cf, pv, s.center), width="stretch")
    st.markdown(f"Контур — сколько заплатят, заливка — сколько эта выплата стоит **сегодня** при доходности "
                f"{y:.2f}%. Цена облигации — сумма заливки: **{s.price:.2f}**. Далёкие деньги стоят меньше: последняя "
                f"выплата через {t[-1]:.1f} г. обесценена до {pv[-1] / cf[-1] * 100:.0f}% своей суммы.")
    with learn.how_it_works():
        st.markdown("""
- **Дисконтирование.** Сто долларов через 10 лет стоят сегодня меньше ста: их можно заменить меньшей суммой,
  положенной под рыночный процент. Чем выше ставка и дальше выплата, тем сильнее скидка.
- **Центр тяжести.** Если положить выплаты на весы по их сегодняшней стоимости, точка равновесия — дюрация
  Маколея. У бескупонной облигации она совпадает со сроком, у купонной — раньше.
- **Попробуйте.** Поднимите купон — центр тяжести сдвинется ближе. Поднимите ставку — заливка у далёких выплат
  сожмётся сильнее, чем у ближних.
""")

# ---------- 2. сдвиг ставки ----------
with tabs[1]:
    shock = st.slider("Сдвиг рыночной ставки, п.п.", -3.0, 3.0, step=0.25, key="bl_shock")
    p1 = B.price(bond, shock)
    exact = (p1 / s.price - 1) * 100
    k = st.columns(3)
    k[0].metric("Цена после сдвига", f"{p1:.2f}", f"{exact:+.2f}%", border=True)
    k[1].metric("Оценка по дюрации", f"{-s.duration * shock:+.2f}%", "прямая линия", delta_color="off", border=True)
    k[2].metric("С поправкой на выпуклость", f"{B.taylor(s, shift=shock):+.2f}%", "дуга", delta_color="off",
                border=True)
    left, right = st.columns([3, 2], gap="large")
    with left:
        grid = np.linspace(max(y - 4, -1), y + 4, 120)
        prices = [B.price(bond, g - y) for g in grid]
        tangent = [s.price * (1 - s.duration * (g - y) / 100) for g in grid]
        st.plotly_chart(price_yield(grid, prices, tangent, y, s.price, y + shock, p1), width="stretch")
    with right:
        st.markdown(f"**Тот же сдвиг {shock:+.2f} п.п. для облигаций разных сроков**")
        terms = [2, 5, 10, 30]
        changes = [(B.price(b_, shock) / B.price(b_) - 1) * 100 for b_ in
                   [replace(bond, years=float(T), rf=rf_at(T), coupon=rf_at(T) if bond.kind != "floating"
                            else bond.coupon) for T in terms]]
        st.plotly_chart(hbar_chart([f"{T} {'года' if T == 2 else 'лет'}" for T in terms], changes, height=240),
                        width="stretch")
        st.caption("Того же типа, по номиналу, со ставкой своего срока на текущей кривой.")
    st.markdown(f"Дюрация {s.duration:.1f} — значит, сдвиг на 1 п.п. меняет цену примерно на {s.duration:.1f}% в "
                f"обратную сторону. Разница между точной ценой и оценкой по дюрации — **выпуклость**: при росте "
                f"ставок цена падает чуть меньше прямой, при снижении растёт чуть больше. Это бесплатный бонус "
                f"держателя, и он тем больше, чем длиннее облигация.")

# ---------- 3. держать или продать ----------
with tabs[2]:
    k = st.columns(3)
    max_h = float(np.ceil(bond.years + 5))
    for key in ("bl_hold", "bl_tshock"):  # срок могли сократить — значения не должны вылезать за шкалу
        st.session_state[key] = min(st.session_state.get(key, 0.0), max_h)
    hold = k[0].slider("Сколько лет держите", 0.5, max_h, step=0.5, key="bl_hold")
    tshock = k[1].slider("Через сколько лет меняются ставки", 0.0, max_h, step=0.5, key="bl_tshock")
    delta = k[2].slider("На сколько меняются ставки, п.п.", -3.0, 3.0, step=0.25, key="bl_delta")
    hz = B.horizon(bond, hold, tshock, delta)
    p0 = s.price
    left, right = st.columns(2, gap="large")
    with left:
        st.plotly_chart(waterfall([("Цена покупки", p0), ("Купоны", hz.coupons), ("Процент на процент", hz.reinvest),
                                   ("Цена продажи − покупки" if hold < bond.years else "Погашение − цена покупки",
                                    hz.price_gain)], "Итог"), width="stretch")
        st.metric("Средняя доходность за срок владения", f"{hz.annual:.2f}% в год", f"{hz.annual - y:+.2f} к "
                  f"обещанной {y:.2f}%", delta_color="normal")
    with right:
        hs = np.arange(0.5, max_h + 0.01, 0.5)
        series = {f"Ставки {d_:+.2f} п.п.": (hs, [B.horizon(bond, h_, tshock, d_).annual for h_ in hs])
                  for d_ in sorted({delta, 0.0, -delta})}
        st.plotly_chart(lines(series, "Сколько лет держите", "Доходность, % в год",
                              vline=(s.center, f"дюрация {s.center:.1f} г.")), width="stretch")
    st.markdown(
        "Рост ставок бьёт по цене сразу, но купоны дальше реинвестируются под новую, более высокую ставку. На "
        "коротком горизонте побеждает потеря в цене, на длинном — процент на процент. Если держать примерно "
        f"**столько, сколько дюрация ({s.center:.1f} г.)**, эффекты почти гасят друг друга — линии на графике "
        "сходятся. Так страховщики и пенсионные фонды «иммунизируют» обязательства.")
    if abs(hold - s.center) < 0.75 and tshock == 0:
        st.success("Сейчас горизонт ≈ дюрации: изменение ставок почти не влияет на итог.")

# ---------- 4. кредитный риск ----------
with tabs[3]:
    if mode == LEARN:
        k = st.columns(3)
        k[0].selectbox("Подставить ориентир по рейтингу", ["—"] + list(RATINGS), key="bl_rating",
                       on_change=apply_rating,
                       help="Типичный спред и средняя доля дефолтов в год за долгую историю — примерно.")
        pd_ = k[1].slider("Вероятность дефолта за год, %", 0.0, 30.0, step=0.05, key="bl_pd")
        rec = k[2].slider("Возврат при дефолте, % номинала", 0, 100, step=5, key="bl_rec")
    else:
        rec = recovery_r
        pd_ = st.slider("Вероятность дефолта за год, %", 0.0, 30.0,
                        round(min(B.implied_default(spread, rec), 30.0), 2), 0.05,
                        help="По умолчанию — сколько закладывает рынок. Сравните со своей оценкой.")
    cr = B.credit(bond, pd_, rec)
    k = st.columns(4)
    k[0].metric("Обещанная доходность", f"{cr.promised:.2f}%", "если всё заплатят", delta_color="off", border=True)
    k[1].metric("Ожидаемая доходность", f"{cr.expected:.2f}%", f"{-cr.expected_loss:+.2f} п.п.", border=True)
    k[2].metric("Дефолт до погашения", f"{cr.default_prob:.0f}%", f"из 100 таких выпусков — {cr.default_prob:.0f}",
                delta_color="off", border=True)
    premium = bond.spread - cr.expected_loss
    k[3].metric("Премия сверх потерь", f"{premium:+.2f} п.п.", "плата за неопределённость", delta_color="off",
                border=True)
    base_rf = bond.rf - (bond.breakeven if bond.kind == "tips" else 0)
    st.plotly_chart(waterfall([("Ставка гособлигаций", base_rf), ("Покрытие ожидаемых потерь", cr.expected_loss),
                               ("Премия за риск", premium)], "Обещанная доходность", units="%", height=300),
                    width="stretch")
    msg = (f"Спред {bond.spread:.2f} п.п. складывается из двух частей: {cr.expected_loss:.2f} п.п. уходят на "
           f"покрытие ожидаемых дефолтов, остальное — премия за то, что дефолты приходят волнами в кризис, когда "
           f"деньги нужнее всего.")
    if premium < 0:
        msg += " **Сейчас спред не покрывает даже ожидаемых потерь** — при таких допущениях облигация невыгодна."
    st.markdown(msg + f" Для ориентира: средний спред надёжных компаний США сейчас ≈ {m['ig']:.1f} п.п., "
                      f"мусорных ≈ {m['hy']:.1f} п.п. (слой 4).")

# ---------- 5. инфляция ----------
with tabs[4]:
    infl = st.slider("Какой окажется инфляция, % в год", 0.0, 12.0, step=0.1, key="bl_infl")
    rf_nom = bond.rf + bond.spread
    real_tips = bond.rf - bond.breakeven + bond.spread
    xs = np.linspace(0, 12, 121)
    st.plotly_chart(lines({"Обычная облигация": (xs, [B.real_return(rf_nom, x) for x in xs]),
                           "TIPS": (xs, [real_tips] * len(xs))}, "Фактическая инфляция, %",
                          "Реальная доходность, % в год", vline=(bond.breakeven, f"ожидания {bond.breakeven:.1f}%"),
                          point=(infl, B.real_return(rf_nom, infl), "вы здесь")), width="stretch")
    T = bond.years
    k = st.columns(3)
    k[0].metric("Обычная: реальная доходность", f"{B.real_return(rf_nom, infl):.2f}%",
                f"номинальная {rf_nom:.2f}%", delta_color="off", border=True)
    k[1].metric("TIPS: реальная доходность", f"{real_tips:.2f}%",
                f"номинальная {B.nominal_from_real(real_tips, infl):.2f}%", delta_color="off", border=True)
    k[2].metric(f"100 $ через {T:.0f} лет, в сегодняшних деньгах",
                f"{100 * (1 + B.real_return(rf_nom, infl) / 100) ** T:.0f} $ / {100 * (1 + real_tips / 100) ** T:.0f} $",
                "обычная / TIPS", delta_color="off", border=True)
    winner = "TIPS" if infl > bond.breakeven else "обычная облигация"
    st.markdown(f"Обычная облигация обещает фиксированные {rf_nom:.2f}% в долларах — что они купят, зависит от "
                f"инфляции. TIPS обещает {real_tips:.2f}% **сверх** инфляции, какой бы она ни была. Точка "
                f"безразличия — ожидаемая рынком инфляция {bond.breakeven:.1f}%. При инфляции {infl:.1f}% выигрывает "
                f"**{winner}**. В 2021–2022 годах инфляция оказалась намного выше ожиданий — держатели обычных "
                f"облигаций потеряли покупательную способность.")
