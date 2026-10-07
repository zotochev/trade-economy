"""Слой 7. Рынки: цена акций = прибыль × мультипликатор, мультипликатор — от реальной ставки и премии за риск;
страхуют ли облигации акции и что двигает золото."""
import numpy as np
import pandas as pd
import streamlit as st

from core import learn, markets, ui
from core import valuation as V
from core.charts import bucket_chart, cape_scatter, dual_axis_chart, grouped_bars, line_chart
from core.learn import Example
from core.regime import monthly_returns, treasury10_returns
from core.regime_data import summary
from core.sectors import RATIOS, ratio
from core.transforms import cut

PERIODS = {"10 лет": 10, "20 лет": 20, "50 лет": 50, "Вся история": None}


@st.cache_data(ttl=3600, show_spinner="Считаю историю с 1881 года…")
def cape_history():
    idx = V.real_total_return_index(ui.load("P"), ui.load("D"), ui.load("CPI"))
    return ui.load("CAPE").dropna(), V.forward_return(idx, 10)


# ---------- данные ----------
rec = ui.recessions()
cape = ui.load("CAPE").dropna()
real10 = ui.load("DFII10").dropna()
erp = markets.erp_tips(ui.load)
erp_long = markets.erp_long(ui.load)
corr = markets.stock_bond_corr(ui.load)
spx = ui.load("^GSPC")
gold, gold_chg = ui.load("GC=F").dropna(), markets.gold_change(ui.load)

# ---------- шапка ----------
learn.layer_header(7, "Конец цепочки: всё, что выше, сходится в цене активов. Ставки (слои 2–3) задают, во что "
                      "обходится ожидание, кредитный рынок (слой 4) — сколько платят за риск, рост (слой 5) — "
                      "прибыль компаний, инфляция (слой 6) — сочетаются ли акции с облигациями.")

head, color, prem, pct = markets.verdict(ui.load)
learn.takeaway(f"{head}. Ожидаемая реальная доходность акций ≈ {100 / cape.iloc[-1]:.1f}% в год (1/CAPE), "
               f"10-летние TIPS дают {real10.iloc[-1]:.1f}% сверх инфляции без риска — премия за риск акций "
               f"{prem:+.1f} п.п., ниже, чем в {100 - pct:.0f}% истории с 1881 года. Это говорит о доходности на "
               f"10 лет вперёд, а не о том, когда рынок развернётся.",
               {"orange": "warn", "green": "good"}.get(color, "neutral"))

c = st.columns(5)
c[0].metric("Shiller CAPE", f"{cape.iloc[-1]:.1f}", f"медиана с 1881: {cape.median():.0f}", delta_color="off",
            border=True, help="Цена S&P 500 к средней реальной прибыли за 10 лет.")
c[1].metric("Доходность акций", f"{100 / cape.iloc[-1]:.1f}%", "1 / CAPE, реальная", delta_color="off",
            border=True, help="Сколько реальной прибыли приходится на вложенный доллар — «купон» акций.")
c[2].metric("Реальная ставка 10 лет", f"{real10.iloc[-1]:.2f}%", "TIPS", delta_color="off", border=True,
            help="Доходность облигаций, защищённых от инфляции: безрисковая альтернатива акциям.")
c[3].metric("Премия за риск акций", f"{prem:+.1f} п.п.", f"медиана с 2003: {erp.median():.1f}",
            delta_color="off", border=True, help="1/CAPE − реальная ставка 10 лет. Сколько акции обещают "
                                                 "сверх облигаций за то, что их цена может упасть вдвое.")
c[4].metric("Корреляция акций и облигаций", f"{corr.iloc[-1]:+.2f}", "за 3 года", delta_color="off", border=True,
            help="Ниже нуля — облигации растут, когда акции падают, и страхуют портфель. Выше нуля — "
                 "падают вместе.")

years = PERIODS[st.segmented_control("Период графиков", list(PERIODS), default="20 лет", key="period")
                or "20 лет"]

# ---------- 1. тождество ----------
st.header("1. Цена = прибыль × мультипликатор")
st.markdown("Любое движение индекса раскладывается на две части: **выросла прибыль** компаний или инвесторы "
            "согласились **платить больше за каждый доллар прибыли** (мультипликатор, CAPE). Плюс дивиденды.")
learn.tags("совпадающий", "проверен на истории")
table = pd.DataFrame({h: markets.decompose(ui.load, y) for h, y in markets.HORIZONS.items()}).T
st.plotly_chart(grouped_bars(table, units="%", height=320), width="stretch")
st.caption("Средняя годовая доходность S&P 500 за последние N лет и из чего она сложилась. «Прибыль» — средняя "
           "за 10 лет (цена / CAPE), так провалы рецессий не искажают картину.")

with learn.how_it_works():
    st.markdown("""
- **Откуда берётся мультипликатор.** Акция — право на поток будущей прибыли. Чем дороже деньги сегодня, тем
  меньше стоит далёкая прибыль. Упрощённо (модель Гордона): **P/E ≈ 1 / (r − g)**, где r — реальная ставка
  плюс премия за риск, g — рост прибыли.
- **Как сюда приходит цепочка.** Реальная ставка — из слоёв 2–3, премия за риск — из слоя 4 (тот же страх,
  что расширяет кредитные спреды), рост прибыли — из слоя 5.
- **Обратная форма.** 1/CAPE — ожидаемая реальная доходность акций. Вычтите реальную ставку TIPS — получите
  премию, которую рынок сейчас закладывает за риск.
- **Чего тождество не говорит.** Мультипликатор может годами держаться выше или ниже «справедливого» —
  это про ожидаемую доходность, а не про точку разворота.
""")


def ex_horizon():
    rows = {h: markets.typical_swing(ui.load, y) for h, y in markets.HORIZONS.items()}
    df = pd.DataFrame(rows).T
    st.plotly_chart(grouped_bars(df, units=" п.п.", height=300), width="stretch")
    st.markdown(
        f"Насколько в типичном окне (с 1950 года) прибыль и мультипликатор сдвигают годовую доходность. За год "
        f"мультипликатор — главный: ±{df.iloc[0, 1]:.0f} п.п. против ±{df.iloc[0, 0]:.0f} у прибыли. За 20 лет "
        f"его вклад сжимается до ±{df.iloc[-1, 1]:.0f} п.п.: настроения рынка колеблются вокруг средней и гасят "
        f"друг друга, а прибыль накапливается. Поэтому на коротком горизонте рынок — про ставки и страх, "
        f"на длинном — про экономику.")


def ex_2022():
    cape_ = ui.load("CAPE")
    df = pd.DataFrame({
        "CAPE": cape_["2020":].resample("MS").mean(),
        "Реальная ставка 10 лет, %": real10["2020":].resample("MS").mean()}).dropna()
    st.plotly_chart(dual_axis_chart(("CAPE", df["CAPE"], ""), ("Реальная ставка 10 лет", df.iloc[:, 1], "%"),
                                    recessions=rec, invert_right=True), width="stretch")
    a, b = pd.Timestamp("2021-12-01"), pd.Timestamp("2022-10-01")
    st.markdown(
        f"Механизм в чистом виде. С декабря 2021 по октябрь 2022 реальная ставка выросла с {df.loc[a].iloc[1]:.1f}% "
        f"до {df.loc[b].iloc[1]:.1f}%, и CAPE упал с {df.loc[a, 'CAPE']:.0f} до {df.loc[b, 'CAPE']:.0f}. Прибыль "
        f"компаний при этом почти не изменилась — подешевело то, сколько за неё платят. (Правая ось перевёрнута: "
        f"линии идут вместе, когда связь обратная.)")


def ex_since2023():
    a = pd.Timestamp("2022-10-01")
    st.plotly_chart(line_chart({"Премия за риск акций, п.п.": erp["2015":],
                                "Реальная ставка 10 лет, %": real10["2015":].resample("MS").mean()},
                               recessions=rec, zero_line=True, height=320), width="stretch")
    st.markdown(
        f"После октября 2022 года реальная ставка осталась высокой (сейчас {real10.iloc[-1]:.1f}%), а CAPE вырос с "
        f"{cape[a]:.0f} до {cape.iloc[-1]:.0f}. По формуле мультипликатор должен был остаться низким — сжалась "
        f"премия за риск: с {erp[a]:.1f} до {erp.iloc[-1]:+.1f} п.п. Рынок поверил в рост прибыли (ИИ, высокая "
        f"маржа крупнейших компаний). Связь ставок и мультипликатора видна в крупные сдвиги, но на годах её "
        f"перекрывает премия — величина, которую нельзя наблюдать напрямую.")


learn.examples([Example("На коротком сроке — мультипликатор, на длинном — прибыль", ex_horizon),
                Example("2022: ставка выросла — мультипликатор упал", ex_2022),
                Example("2023–2026: ставки высокие, а акции дорожают", ex_since2023, normal=False)], key="identity")

# ---------- 2. дороги ли акции ----------
st.header("2. Дороги ли акции относительно облигаций")
st.markdown("Премия за риск — сколько акции обещают сверх безрисковых облигаций. Когда она низкая, будущая "
            "доходность акций исторически была скромной: рынок уже «съел» часть будущего роста.")
learn.tags("опережающий", "проверен на истории")
st.plotly_chart(line_chart({"Премия: 1/CAPE − реальная ставка TIPS": cut(erp, years),
                            "Премия с 1881 г. (10 лет − прошлая инфляция)": cut(erp_long, years)},
                           units=" п.п.", recessions=rec, zero_line=True, height=360), width="stretch")
with learn.how_it_works():
    st.markdown("""
- **Опережающий — но на 10 лет, а не на месяцы.** Премия и CAPE объясняют около четверти разброса доходности
  на следующие 10 лет и почти ничего (≈ 4%) — на следующий год.
- **Две версии.** TIPS торгуются с 2003 года; для длинной истории реальную ставку приходится оценивать как
  10-летнюю ставку минус инфляцию за прошлые 10 лет.
- **Где ошибается.** Если прибыль растёт быстрее обычного (выше маржа, ниже налоги), высокий CAPE оправдан —
  так было в 2010-х. Подробные таблицы — на экране «Оценка рынка».
""")


def ex_cape():
    c_, fwd = cape_history()
    model = V.fit(c_, fwd)
    tbl = V.cape_table(c_, fwd)
    now = float(c_.iloc[-1])
    bucket = next(l for lo, hi, l in zip(V.BUCKETS[:-1], V.BUCKETS[1:], V.BUCKET_LABELS) if lo <= now < hi)
    st.plotly_chart(cape_scatter(c_, fwd, now, model.predict, height=380), width="stretch")
    st.plotly_chart(bucket_chart(tbl, bucket, height=300), width="stretch")
    st.markdown(
        f"Каждая точка — месяц покупки с 1881 года. Чем выше CAPE в момент покупки, тем ниже реальная доходность "
        f"следующих 10 лет. Сейчас CAPE {now:.0f} — корзина «{bucket}»: медиана в ней "
        f"{tbl.loc[bucket, 'Медиана, % год.']:.1f}% в год, но разброс широкий. Регрессия даёт ≈ "
        f"{model.predict(now):.1f}% ± {model.resid_std:.0f} п.п.")


def ex_2010s():
    c_, fwd = cape_history()
    model = V.fit(c_, fwd)
    x = pd.concat({"cape": c_, "fwd": fwd}, axis=1).dropna()["2009":]
    x["Прогноз по CAPE"] = model.predict(x["cape"])
    st.plotly_chart(line_chart({"Факт: доходность следующих 10 лет": x["fwd"],
                                "Прогноз по CAPE": x["Прогноз по CAPE"]}, units="%", height=320),
                    width="stretch")
    st.markdown(
        f"Покупка в 2010–2015 годах при CAPE ≈ 20–27 обещала по регрессии около "
        f"{x['Прогноз по CAPE']['2010':'2015'].mean():.0f}% в год, а дала {x['fwd']['2010':'2015'].mean():.0f}%. "
        f"Ошибку объясняют сдвиги, которых модель не видит: ставки ушли к нулю, налог на прибыль снизили с 35% "
        f"до 21%, маржа крупнейших компаний выросла. CAPE — про средний исход, а не гарантия.")


learn.examples([Example("Дорогой рынок → скромная доходность на 10 лет", ex_cape),
                Example("2010-е: дорогой рынок всё равно дал много", ex_2010s, normal=False)], key="value")

# ---------- 3. акции и облигации ----------
st.header("3. Страхуют ли облигации акции")
st.markdown("Классический портфель «60/40» держится на том, что облигации растут, когда акции падают. Но это "
            "верно не всегда: знак связи задаёт **главный риск экономики** — рост или инфляция.")
learn.tags("совпадающий", "проверен на истории")
st.plotly_chart(line_chart({"Корреляция S&P 500 и 10-летних гособлигаций, 3 года": cut(corr, years)},
                           recessions=rec, zero_line=True, height=320), width="stretch")
with learn.how_it_works():
    st.markdown("""
- **Главный риск — рост (слой 5).** В спад прибыль падает, ФРС снижает ставки — акции дешевеют, облигации
  дорожают. Корреляция отрицательная, облигации — страховка.
- **Главный риск — инфляция (слой 6).** Инфляция заставляет ФРС поднимать ставки — дешевеют и облигации, и
  акции (через мультипликатор). Корреляция положительная, страховки нет.
- Так было в 1970–90-х и снова с 2022 года. Смена знака — один из самых важных для портфеля сигналов.
""")


def period_returns(start: str, end: str) -> dict[str, float]:
    out = {}
    for name, r in {"Акции (S&P 500)": monthly_returns(spx), "Гособлигации 10 лет": treasury10_returns(ui.load),
                    "Золото": monthly_returns(gold)}.items():
        x = r[start:end]
        out[name] = float(((1 + x / 100).prod() - 1) * 100) if len(x) else np.nan
    return out


def ex_hedge():
    rows = {"Кризис 2008 (сен. 08 – фев. 09)": period_returns("2008-09", "2009-02"),
            "Ковид (фев. – мар. 2020)": period_returns("2020-02", "2020-03")}
    st.plotly_chart(grouped_bars(pd.DataFrame(rows).T, units="%", height=300), width="stretch")
    st.markdown(f"В кризисах роста облигации компенсировали падение акций. С 2000 по 2020 год корреляция в "
                f"среднем была {corr['2000':'2020'].mean():+.2f}.")


def ex_2022b():
    rows = {"2022 год": period_returns("2022-01", "2022-12")}
    st.plotly_chart(grouped_bars(pd.DataFrame(rows).T, units="%", height=300), width="stretch")
    st.markdown(f"В 2022 году главным риском стала инфляция — и облигации упали вместе с акциями: худший год "
                f"«60/40» за десятилетия. Корреляция стала положительной (сейчас {corr.iloc[-1]:+.2f}), как в "
                f"1970–1999 годах (в среднем {corr['1970':'1999'].mean():+.2f}).")


learn.examples([Example("Кризисы роста: облигации спасают", ex_hedge),
                Example("2022: инфляция — падают оба", ex_2022b, normal=False)], key="mix")

# ---------- 4. золото ----------
st.header("4. Золото и реальные ставки")
st.markdown("Золото не платит ни купона, ни дивидендов. Поэтому держать его тем дороже, чем выше **реальная "
            "ставка**: за отказ от облигаций вы теряете реальный доход.")
learn.tags("совпадающий", "спорный")
st.plotly_chart(dual_axis_chart(("Золото", cut(gold, years), "$"), ("Реальная ставка 10 лет", cut(real10, years), "%"),
                                recessions=rec, invert_right=True), width="stretch")
st.caption("Правая ось перевёрнута: если линии идут вместе — работает обратная связь «ставка вверх, золото вниз».")


def ex_gold_rates():
    k = markets.change_corr(gold_chg, real10, "2006", "2021")
    st.markdown(f"С 2006 по 2021 год корреляция годовых изменений цены золота и реальной ставки — **{k:.2f}**. "
                f"В 2011 году реальная ставка ушла ниже нуля — золото на пике; в 2013-м она выросла на 1,5 п.п. — "
                f"золото потеряло четверть цены.")


def ex_gold_break():
    x = pd.concat({"g": np.log(gold.resample("MS").mean()), "r": real10.resample("MS").mean()}, axis=1).dropna()
    fit = x["2006":"2021"]
    b, a = np.polyfit(fit["r"], fit["g"], 1)
    pred = np.exp(a + b * x["r"])
    st.plotly_chart(line_chart({"Золото, факт": np.exp(x["g"]), "Модель по реальной ставке (2006–2021)": pred},
                               units="", height=320), width="stretch")
    st.markdown(
        f"Модель, построенная на 2006–2021 годах, объясняла {np.corrcoef(fit['r'], fit['g'])[0, 1] ** 2 * 100:.0f}% "
        f"колебаний цены. При нынешней реальной ставке она даёт ≈ ${pred.iloc[-1]:,.0f} за унцию, а факт — "
        f"${np.exp(x['g'].iloc[-1]):,.0f}. После 2022 года центробанки (особенно после заморозки резервов "
        f"России) покупают золото как актив без риска санкций — и этот спрос не зависит от ставок. Связь "
        f"не исчезла (изменения по-прежнему идут в разные стороны), но уровень сместился.")


learn.examples([Example("Реальная ставка растёт — золото дешевеет", ex_gold_rates),
                Example("С 2022: золото дорожает вопреки ставкам", ex_gold_break, normal=False)], key="gold")

# ---------- 5. режим, сектора и отдельные акции ----------
st.header("5. Что выигрывает сейчас: режим и сектора")
now, best, worst = summary()
st.markdown(f"Режим экономики по росту и инфляции: **{now.name}** ({now.description}), держится "
            f"{now.months} мес. В этом режиме исторически лучше всего были: "
            + ", ".join(f"{n} ({v:+.0f}% год.)" for n, v in best) + "; хуже всего: "
            + ", ".join(f"{n} ({v:+.0f}% год.)" for n, v in worst) + ".")
learn.tags("совпадающий", "спорный")
lines = {}
for num, den, name, _ in RATIOS[:2]:
    r = ratio(ui.load(num), ui.load(den))
    lines[name] = cut(r / r.rolling(250).mean() * 100 - 100, years).dropna()
st.plotly_chart(line_chart(lines, units="%", recessions=rec, zero_line=True, height=300), width="stretch")
st.caption("Отклонение соотношения от его средней за год: выше нуля — " + RATIOS[0][3] + "; для малых компаний — "
           + RATIOS[1][3] + ".")
with learn.how_it_works():
    st.markdown("""
- **Сектора — это ставка на слой 5.** Цикличные (потребление, промышленность) выигрывают, когда рост
  ускоряется; защитные (товары первой необходимости, коммунальные) — когда замедляется.
- **Малые компании живут в долг под плавающую ставку** — они первыми чувствуют дорогой кредит (слой 4).
- **Почему «спорный».** Таблицы «что выигрывало в режиме» построены на истории; режим определяется с задержкой
  публикации, и в отдельных циклах результат отличался от среднего.
""")
cols = st.columns(3)
with cols[0]:
    st.page_link("views/sectors.py", label="Сектора и факторы", icon="🏭")
with cols[1]:
    st.page_link("views/stock.py", label="Отдельная акция", icon="🔬")
with cols[2]:
    st.page_link("views/regime.py", label="Режим экономики подробно", icon="🧭")

learn.next_steps([4, 2], "Цены акций и жилья возвращаются в финансовые условия (слой 4): богатеющие семьи "
                         "тратят больше, дешёвый капитал помогает компаниям. ФРС тоже это видит (слой 2).")
