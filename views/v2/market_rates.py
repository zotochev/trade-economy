"""Слой 3. Рыночные ставки и ожидания: как короткая ставка ФРС превращается в длинные ставки,
верит ли рынок в цель по инфляции и что говорит кривая доходности."""
import numpy as np
import pandas as pd
import streamlit as st

from core import bonds, curve, learn, ui
from core.charts import (contrib_chart, curve_chart, dual_axis_chart, grouped_bars, hbar_chart, line_chart,
                         price_yield_chart)
from core.learn import Example
from core.transforms import cut

PERIODS = {"5 лет": 5, "10 лет": 10, "20 лет": 20, "Вся история": None}


@st.cache_data(ttl=3600)
def ten_year() -> pd.DataFrame:
    return curve.parts(ui.load)


@st.cache_data(ttl=3600)
def curves() -> dict[str, pd.Series]:
    last = min(ui.load(k).index[-1] for k in curve.MATURITIES)
    return {f"Сейчас ({last:%d.%m.%Y})": curve.curve_at(ui.load, last),
            "Год назад": curve.curve_at(ui.load, last - pd.DateOffset(years=1)),
            "Два года назад": curve.curve_at(ui.load, last - pd.DateOffset(years=2))}


def monthly(key: str) -> pd.Series:
    return ui.load(key).resample("MS").mean()


# ---------- данные ----------
tyr = ten_year()
rec = ui.recessions()
y10, tp, real, be = (float(ui.load(k).iloc[-1]) for k in ("DGS10", "THREEFYTP10", "DFII10", "T10YIE"))
ff = float(ui.load("T5YIFR").iloc[-1])
slope = float(ui.load("T10Y3M").iloc[-1])

# ---------- шапка ----------
learn.layer_header(3, "ФРС управляет только **самой короткой** ставкой. Длинные ставки — по которым считаются "
                      "ипотека, корпоративные облигации и оценка акций — рынок назначает сам: это его ставка на "
                      "будущее ФРС, инфляцию и риск. Здесь видно, **поверил ли рынок ФРС**.")

head, color = curve.verdict(tp, slope, ff)
learn.takeaway(f"{head}. 10-летние {y10:.2f}%: из них ≈ {y10 - tp:.1f}% — ожидаемые ставки, ≈ {tp:+.1f} п.п. — "
               f"премия за срок. Дальние инфляционные ожидания {ff:.2f}% — "
               + ("заякорены около цели 2%." if curve.anchored(ff) else "ушли от цели 2%."),
               {"red": "bad", "orange": "warn", "blue": "good"}.get(color, "neutral"))

c = st.columns(5)
c[0].metric("10-летние", f"{y10:.2f}%", f"{y10 - ui.load('DGS10')[:ui.load('DGS10').index[-1] - pd.DateOffset(years=1)].iloc[-1]:+.2f} за год",
            delta_color="off", border=True, help="Доходность 10-летних гособлигаций США (DGS10).")
c[1].metric("Премия за срок", f"{tp:+.2f} п.п.", "модель Кима–Райта", delta_color="off", border=True,
            help="Доплата за то, чтобы держать длинную облигацию, а не перекатывать короткие (THREEFYTP10).")
c[2].metric("Реальная 10 лет", f"{real:.2f}%", "облигации TIPS", delta_color="off", border=True,
            help="Доходность облигаций, защищённых от инфляции (DFII10): цена денег на 10 лет без инфляции.")
c[3].metric("Ожидания 5y5y", f"{ff:.2f}%", "заякорены" if curve.anchored(ff) else "расшатаны",
            delta_color="off", border=True,
            help="Средняя инфляция, которую рынок ждёт через 5–10 лет (T5YIFR). Около 2–2,5% — рынок верит в цель ФРС.")
c[4].metric("Наклон кривой", f"{slope:+.2f} п.п.", "перевёрнута" if slope < 0 else "нормальная",
            delta_color="off", border=True, help="10 лет минус 3 месяца (T10Y3M). Ниже нуля — инверсия.")

years = PERIODS[st.segmented_control("Период графиков", list(PERIODS), default="20 лет", key="period")
                or "20 лет"]

# ---------- 1. из чего складывается ставка ----------
st.header("1. Из чего складывается 10-летняя ставка")
st.markdown("Одну и ту же ставку можно разложить двумя способами — и каждый отвечает на свой вопрос.")
learn.tags("совпадающий", "спорный")
t = cut(tyr.dropna(subset=["tp"]), years)
left, right = st.columns(2)
with left:
    st.markdown("**Ожидания ставок + премия за срок**  \nЧего рынок ждёт от ФРС и сколько берёт сверху за риск.")
    st.plotly_chart(contrib_chart(t[["expected", "tp"]].rename(columns={"expected": "Ожидаемые ставки ФРС",
                                                                        "tp": "Премия за срок"}),
                                  t["y10"], units="%", recessions=rec, height=340), width="stretch")
with right:
    st.markdown("**Реальная ставка + инфляция**  \nСколько стоят деньги без инфляции и какую инфляцию ждут.")
    r = t.dropna(subset=["real", "be"])
    st.plotly_chart(contrib_chart(r[["real", "be"]].rename(columns={"real": "Реальная ставка (TIPS)",
                                                                    "be": "Инфляционная компенсация"}),
                                  r["y10"], units="%", recessions=rec, height=340), width="stretch")

with learn.how_it_works():
    st.markdown("""
- **Ожидания.** Купить 10-летнюю облигацию — почти то же, что 10 лет перекладывать деньги под ставку ФРС.
  Поэтому большая часть длинной ставки — это средняя ставка ФРС, которую рынок ждёт на 10 лет.
- **Премия за срок** — доплата за то, что за 10 лет может случиться что угодно: инфляция, дефициты бюджета,
  смена политики. Она растёт, когда будущее туманнее и когда облигаций на рынке больше (дефициты, QT).
  Это **оценка модели**: модели Кима–Райта и ACM (ФРБ Нью-Йорка) дают разные числа — отсюда метка «спорный».
- **Реальная ставка + инфляция.** Облигации TIPS защищены от инфляции; разница с обычными — «инфляционная
  компенсация», которую рынок закладывает. В неё входят ожидания и небольшая премия за риск инфляции.
- **Почему это важно дальше по цепочке.** От 10-летней ставки считаются ипотека и корпоративные кредиты
  (слой 4), а реальная ставка — главный «гравитационный» фактор для оценки акций (слой 7).
""")


def ex_passthrough():
    ffr, y, tpm = monthly("DFF"), monthly("DGS10"), monthly("THREEFYTP10")
    d = pd.concat({"ffr": ffr.diff(12), "y10": y.diff(12)}, axis=1, sort=True).dropna()
    beta = d["ffr"].cov(d["y10"]) / d["ffr"].var()  # наклон регрессии: на сколько 10-летние на 1 п.п. ставки
    rows = {}
    for name, a, z in [("2015–2018", "2015-12", "2018-12"), ("2022–2023", "2022-03", "2023-07")]:
        g = lambda s: float(s[z].iloc[0] - s[a].iloc[0])
        rows[name] = {"Ставка ФРС": g(ffr), "10-летние": g(y), "из них ожидания": g(y - tpm),
                      "из них премия": g(tpm)}
    st.plotly_chart(grouped_bars(pd.DataFrame(rows).T, units=" п.п.", height=300), width="stretch")
    st.markdown(
        f"Два цикла повышения ставки. ФРС подняла ставку на 2 и почти на 5 п.п. — 10-летние выросли намного "
        f"меньше, и почти весь рост пришёлся на **ожидания**. Так и устроено: рынок знает, что высокая ставка "
        f"временная, и усредняет её с будущими снижениями. По всей истории с 1962 года каждый процентный "
        f"пункт изменения ставки ФРС за год сдвигал 10-летние в среднем на **{beta:.1f} п.п.**")


def ex_conundrum():
    ffr, y, tpm = monthly("DFF")["2004":"2006"], monthly("DGS10")["2004":"2006"], monthly("THREEFYTP10")["2004":"2006"]
    st.plotly_chart(line_chart({"Ставка ФРС": ffr, "10-летние": y, "Премия за срок": tpm}, units="%",
                               recessions=rec, zero_line=True, height=320), width="stretch")
    st.markdown(
        f"2004–2006: ФРС подняла ставку на **{ffr.max() - ffr.min():.1f} п.п.**, а 10-летние почти не "
        f"сдвинулись. Гринспен назвал это «загадкой». Разгадка видна на графике: **премия за срок упала** — "
        f"азиатские центробанки и экспортёры нефти массово скупали американский госдолг. Длинные ставки "
        f"остались низкими, ипотека — дешёвой, и ужесточение ФРС почти не дошло до рынка жилья.")


def ex_2023():
    g = tyr["2023":"2024"]
    st.plotly_chart(contrib_chart(g[["expected", "tp"]].rename(columns={"expected": "Ожидаемые ставки ФРС",
                                                                        "tp": "Премия за срок"}),
                                  g["y10"], units="%", recessions=rec, height=320), width="stretch")
    rise = float(g.loc["2023-10", "y10"].iloc[0] - g.loc["2023-04", "y10"].iloc[0])
    tp_rise = float(g.loc["2023-10", "tp"].iloc[0] - g.loc["2023-04", "tp"].iloc[0])
    st.markdown(
        f"С апреля по октябрь 2023 года 10-летние выросли на **{rise:.1f} п.п.**, хотя ФРС за это время подняла "
        f"ставку всего дважды по 0,25 п.п. Около {tp_rise / rise * 100:.0f}% роста — **премия за срок**: Минфин "
        f"объявил большие займы под дефицит, ФРС сокращала баланс (QT), и инвесторы потребовали доплату. Длинные "
        f"ставки ужесточили условия сами — без решения ФРС.")


learn.examples([Example("Ставка ФРС доходит до 10-летних примерно на треть", ex_passthrough),
                Example("2004–2006: «загадка Гринспена»", ex_conundrum, normal=False),
                Example("2023: длинные ставки выросли без ФРС", ex_2023, normal=False)], key="decomp")

# ---------- 2. инфляционные ожидания ----------
st.header("2. Верит ли рынок в цель по инфляции")
st.markdown("Ожидания инфляции — то, что делает инфляцию устойчивой: если все ждут роста цен, компании "
            "заранее повышают цены, а работники — требования к зарплате. Ключевой вопрос — **«заякорены»** "
            "ли дальние ожидания около 2%.")
learn.tags("опережающий", "проверен на истории")
st.plotly_chart(line_chart({"Рынок: следующие 5 лет": cut(ui.load("T5YIE"), years),
                            "Рынок: через 5–10 лет (5y5y)": cut(ui.load("T5YIFR"), years),
                            "Домохозяйства: через год": cut(ui.load("MICH"), years)}, units="%",
                           recessions=rec, height=360), width="stretch")

with learn.how_it_works():
    st.markdown("""
- **Якорь.** Если дальние ожидания (5y5y) стоят около 2–2,5%, временный скачок цен не превращается в
  спираль «цены → зарплаты → цены». Это главное отличие 2022 года от 1970-х (модель Бернанке–Бланшара).
- **Ближние ожидания** следуют за текущими ценами — особенно за бензином. Это нормально и не опасно, пока
  дальние стоят на месте.
- **Домохозяйства** почти всегда ждут инфляцию выше рынка: они смотрят на цены в магазине и на заправке.
  Важно не само значение, а куда оно движется.
- **Тонкость.** Рыночные ожидания содержат премии за риск и ликвидность облигаций TIPS. Модель ФРБ Кливленда
  (`EXPINF10YR` в «Всех рядах») пытается их убрать.
""")


def ex_oil():
    oil = monthly("DCOILWTICO").pct_change(12) * 100
    be5, ffm = monthly("T5YIE"), monthly("T5YIFR")
    x = pd.concat({"oil": oil, "be5": be5, "ff": ffm}, axis=1, sort=True).dropna()
    st.plotly_chart(dual_axis_chart(("Ожидания на 5 лет", cut(be5.dropna(), years), "%"),
                                    ("Нефть, изменение за год", cut(oil.dropna(), years), "%"), recessions=rec),
                    width="stretch")
    st.markdown(
        f"Ближние ожидания двигаются вслед за нефтью: корреляция с годовым изменением цены нефти "
        f"**{x['oil'].corr(x['be5']):.2f}**. Дальние (5y5y) реагируют слабее ({x['oil'].corr(x['ff']):.2f}) и "
        f"колеблются меньше: стандартное отклонение {x['ff'].std():.2f} против {x['be5'].std():.2f} п.п. "
        f"Так выглядит якорь в спокойные годы: бензин дорожает — люди ждут роста цен в ближайшие годы, но не "
        f"навсегда.")


def ex_2022_anchor():
    g = pd.concat({"Рынок: следующие 5 лет": monthly("T5YIE")["2020":"2024"],
                   "Рынок: через 5–10 лет (5y5y)": monthly("T5YIFR")["2020":"2024"]}, axis=1)
    st.plotly_chart(line_chart({k: g[k] for k in g}, units="%", recessions=rec, height=320), width="stretch")
    st.markdown(
        f"Инфляция в 2022 году дошла до 9%. Ближние ожидания подскочили до **{g.iloc[:, 0].max():.1f}%**, а "
        f"дальние не поднялись выше **{g.iloc[:, 1].max():.1f}%**. Рынок поверил, что ФРС вернёт инфляцию к 2%. "
        f"Именно поэтому скачок цен не превратился в многолетнюю спираль, как в 1970-е.")


def ex_households():
    g = pd.concat({"Домохозяйства: через год": ui.load("MICH")["2015":],
                   "Рынок: через 5–10 лет (5y5y)": monthly("T5YIFR")["2015":]}, axis=1, sort=True).dropna()
    st.plotly_chart(line_chart({k: g[k] for k in g}, units="%", recessions=rec, height=320), width="stretch")
    gap = g.iloc[:, 0] - g.iloc[:, 1]
    st.markdown(
        f"До 2020 года домохозяйства ждали инфляцию примерно на {gap[:'2019'].mean():.1f} п.п. выше рынка. "
        f"После всплеска цен разрыв вырос и держится: сейчас **{gap.iloc[-1]:+.1f} п.п.** Люди запомнили "
        f"подорожание и не верят в 2% так, как облигационный рынок. Если это закрепится в требованиях к "
        f"зарплате, якорь может начать сдвигаться — за этим ФРС следит отдельно.")


learn.examples([Example("Ближние ожидания следуют за нефтью, дальние стоят", ex_oil),
                Example("2022: проверка якоря", ex_2022_anchor),
                Example("Домохозяйства не верят рынку", ex_households, normal=False)], key="expect")

# ---------- 3. кривая доходности ----------
st.header("3. Кривая доходности")
st.markdown("Доходности на все сроки сразу. Обычно длинные ставки выше коротких — за срок доплачивают. "
            "Когда короткие выше длинных (**инверсия**), рынок ждёт, что ФРС скоро будет снижать ставку — "
            "чаще всего потому, что ждёт спада.")
learn.tags("опережающий", "проверен на истории")
left, right = st.columns(2)
with left:
    st.markdown("**Форма кривой сейчас и раньше**")
    st.plotly_chart(curve_chart(curves(), height=340), width="stretch")
with right:
    st.markdown("**Наклон: 10 лет − 3 месяца**")
    st.plotly_chart(line_chart({"Наклон 10 лет − 3 мес.": cut(ui.load("T10Y3M"), years)}, units="п.п.",
                               recessions=rec, zero_line=True, height=340), width="stretch")

with learn.how_it_works():
    st.markdown("""
- **Почему инверсия предсказывала рецессии.** Если ФРС держит короткую ставку очень высокой, рынок понимает,
  что экономика это не выдержит и ставку придётся снижать — и заранее опускает длинные ставки.
- **Почему 10 лет − 3 месяца.** ФРБ Нью-Йорка считает этот наклон лучшим среди вариантов и строит на нём
  модель вероятности рецессии.
- **Слабое место.** Длинная ставка может упасть не из-за ожидания спада, а из-за ожидания снижения инфляции
  или низкой премии за срок. Поэтому инверсию стоит проверять кредитным рынком (слой 4).
""")


def ex_before_rec():
    s = monthly("T10Y3M")
    rows = []
    for a, _ in rec:
        if a.year < 1985:
            continue
        w = s[(s.index < a) & (s.index >= a - pd.DateOffset(months=30))]
        first = w[w < 0].index.min()
        rows.append({"Рецессия началась": f"{a:%m.%Y}",
                     "Кривая перевернулась": f"{first:%m.%Y}" if pd.notna(first) else "—",
                     "За сколько месяцев": (a.year - first.year) * 12 + a.month - first.month
                     if pd.notna(first) else None})
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.markdown("Перед каждой рецессией с 1990 года кривая переворачивалась заранее — за 9–17 месяцев. "
                "Лаг длинный и разный: инверсия говорит «что-то сломается», но не «когда».")


def ex_2022_curve():
    g = pd.concat({"Наклон 10 лет − 3 мес.": monthly("T10Y3M")["2021":"2025"],
                   "Ставка ФРС": monthly("DFF")["2021":"2025"]}, axis=1)
    st.plotly_chart(dual_axis_chart(("Наклон 10 лет − 3 мес.", g.iloc[:, 0], "п.п."),
                                    ("Ставка ФРС", g.iloc[:, 1], "%"), recessions=rec), width="stretch")
    inv = monthly("T10Y3M") < 0
    runs = (inv != inv.shift()).cumsum()[inv]  # номера непрерывных серий инверсии
    longest = runs.value_counts()
    start = runs[runs == longest.idxmax()].index[0]
    st.markdown(
        f"С {start:%m.%Y} кривая была перевёрнута **{longest.max()} месяцев подряд** — дольше, чем когда-либо "
        f"с начала данных ({inv.index[0].year}), — и рецессии не случилось. Рынок ждал снижения ставки, потому "
        f"что ждал **снижения инфляции**, а не спада. Кредитный рынок с самого начала не подтверждал тревогу (слой 4). Урок: "
        f"инверсия — повод проверить другие слои, а не готовый ответ.")


learn.examples([Example("Инверсия перед рецессиями 1990–2020", ex_before_rec),
                Example("2022–2024: самая долгая инверсия без рецессии", ex_2022_curve, normal=False)],
               key="curve")

# ---------- 4. цена облигаций ----------
st.header("4. Что ставки делают с ценой облигаций")
st.markdown("Облигация — обещание платить купоны и вернуть номинал. Выросли рыночные ставки — старые облигации с "
            "низким купоном дешевеют. Насколько — зависит от **срока**: чем он длиннее, тем сильнее удар.")
learn.tags("совпадающий", "проверен на истории")
etf = {"TLT (20+ лет)": "TLT", "IEF (7–10 лет)": "IEF", "SHY (1–3 года)": "SHY"}
start = max(cut(ui.load(k), years).index[0] for k in etf.values())
st.plotly_chart(line_chart({n: ui.load(k)[start:] / ui.load(k)[start:].iloc[0] * 100 for n, k in etf.items()},
                           recessions=rec, height=320), width="stretch")
st.caption("Цена облигационных ETF с реинвестированием купонов, начало периода = 100.")
with learn.how_it_works():
    st.markdown("""
- **Дюрация** — на сколько процентов меняется цена облигации, если ставка сдвинулась на 1 п.п. У 2-летней
  облигации она около 2, у 30-летней — около 17.
- **Выпуклость.** Зависимость цены от ставки — не прямая, а дуга: при больших сдвигах цена падает меньше и
  растёт больше, чем обещает дюрация.
- **Связь с цепочкой.** Длинные облигации — ставка на снижение ставок (слой 2) и инфляции (слой 6). Короткие
  почти не рискуют ценой, но доход по ним меняется вместе со ставкой ФРС.
""")


def ex_2022_bonds():
    rows = {n: (ui.load(k)["2022-12"].iloc[-1] / ui.load(k)["2021-12"].iloc[-1] - 1) * 100 for n, k in etf.items()}
    st.plotly_chart(hbar_chart(list(rows), list(rows.values()), height=200), width="stretch")
    st.markdown(
        f"За 2022 год 10-летняя ставка выросла с {ui.load('DGS10')['2021-12'].mean():.1f}% до "
        f"{ui.load('DGS10')['2022-12'].mean():.1f}%. Длинные облигации потеряли {-rows['TLT (20+ лет)']:.0f}% — "
        f"как акции в медвежий рынок, короткие — лишь {-rows['SHY (1–3 года)']:.0f}%. «Надёжная» облигация "
        f"надёжна только в том, что вернёт номинал в срок; до срока её цена ходит вместе со ставками.")


def ex_sandbox():
    s1, s2, s3, s4 = st.columns(4)
    term = s1.slider("Срок, лет", 1, 30, 10, key="bs_term")
    coupon = s2.slider("Купон, % в год", 0.0, 10.0, round(y10 * 4) / 4, 0.25, key="bs_coupon")
    ytm = s3.slider("Рыночная доходность, %", 0.0, 12.0, round(y10, 2), 0.05, key="bs_ytm",
                    help="По умолчанию — текущая доходность 10-летних казначейских облигаций США.")
    shock = s4.slider("Сдвиг ставки, п.п.", -3.0, 3.0, 1.0, 0.25, key="bs_shock")
    b = bonds.stats(coupon, term, ytm)
    p1 = bonds.price(coupon, term, ytm + shock)
    m = st.columns(4)
    m[0].metric("Цена сейчас", f"{b.price:.2f}", help="За 100 номинала. Купон выше доходности → цена выше 100.")
    m[1].metric("Дюрация", f"{b.modified_duration:.1f}", help="На сколько % меняется цена при сдвиге ставки на 1 п.п.")
    m[2].metric(f"Цена после сдвига {shock:+.2f} п.п.", f"{p1:.2f}", f"{(p1 / b.price - 1) * 100:+.1f}%")
    m[3].metric("Оценка по дюрации", f"{-b.modified_duration * shock:+.1f}%",
                help="−дюрация × сдвиг. Расхождение с точным числом — выпуклость.")
    left, right = st.columns([3, 2], gap="large")
    with left:
        grid = np.linspace(max(0.0, min(ytm, ytm + shock) - 3), max(ytm, ytm + shock) + 3, 120)
        st.plotly_chart(price_yield_chart(grid, [bonds.price(coupon, term, y) for y in grid], ytm, b.price,
                                          ytm + shock, p1), width="stretch")
    with right:
        st.markdown(f"**Тот же сдвиг {shock:+.2f} п.п. для разных сроков**")
        now = curve.curve_at(ui.load, min(ui.load(k).index[-1] for k in curve.MATURITIES))
        terms = [2, 5, 10, 30]
        st.plotly_chart(hbar_chart([f"{t} {'года' if t == 2 else 'лет'}" for t in terms],
                                   [bonds.price_change_pct(now[t], t, now[t], shock) for t in terms], height=230),
                        width="stretch")
        st.caption("Облигации по номиналу с купоном, равным текущей доходности своего срока.")


learn.examples([Example("2022: длинные облигации потеряли треть", ex_2022_bonds),
                Example("Песочница: цена облигации и ставка", ex_sandbox)], key="bonds")

learn.next_steps([4], "Длинные ставки становятся ценой ипотеки, корпоративного кредита и капитала для "
                      "компаний — это слой финансовых условий.")
