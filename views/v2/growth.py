"""Слой 5. Рост и риск рецессии: скорость экономики, загрузка относительно потенциала, рынок труда
и несколько моделей рецессии рядом — с их ошибками."""
import numpy as np
import pandas as pd
import streamlit as st

from core import growth, learn, ui
from core.charts import dual_axis_chart, line_chart
from core.learn import Example
from core.transforms import cut, yoy_pct

PERIODS = {"5 лет": 5, "10 лет": 10, "20 лет": 20, "Вся история": None}


@st.cache_data(ttl=3600)
def signals() -> dict[str, pd.Series]:
    return growth.signal_series(ui.load)


@st.cache_data(ttl=3600)
def risk() -> pd.DataFrame:
    return growth.risk_table(ui.load)


def starts(after: int = 1968) -> list[pd.Timestamp]:
    return [a for a, _ in rec if a.year > after]


def months_between(a: pd.Timestamp, b: pd.Timestamp) -> int:
    return (b.year - a.year) * 12 + b.month - a.month


# ---------- данные ----------
rec = ui.recessions()
gq = growth.gdp_growth(ui.load).dropna()
gdpnow = ui.load("GDPNOW")
trend = ui.load("trend_g_hlw")
wei = ui.load("WEI")
cbo = growth.cbo_gap(ui.load)
hlw_gap = ui.load("gap_hlw")
u = ui.load("UNRATE")
u_star = ui.load("NROU")[:u.index[-1]]
lmci_level, lmci_mom = ui.load("FRBKCLMCILA"), ui.load("FRBKCLMCIM")
sig = signals()

# ---------- шапка ----------
learn.layer_header(5, "Сюда с задержкой в полгода–полтора приходит всё, что случилось выше по цепочке: "
                      "дешёвые или дорогие деньги меняют расходы компаний и семей, а значит — производство и "
                      "найм. Это слой **реальной экономики**: сколько производим и сколько людей работает.")

head, color = growth.verdict(ui.load)
learn.takeaway(
    f"{head}. Наукаст ВВП текущего квартала {gdpnow.iloc[-1]:+.1f}% в годовом темпе при трендовом росте "
    f"≈ {trend.iloc[-1]:.1f}%; безработица {u.iloc[-1]:.1f}% при естественной ≈ {u_star.iloc[-1]:.1f}%.",
    {"red": "bad", "orange": "warn", "green": "good"}.get(color, "neutral"))

c = st.columns(5)
c[0].metric("Наукаст ВВП", f"{gdpnow.iloc[-1]:+.1f}%", f"квартал {gdpnow.index[-1].quarter} · {gdpnow.index[-1].year}",
            delta_color="off", border=True,
            help="GDPNow (ФРБ Атланты): рост реального ВВП текущего квартала в годовом темпе, до официальных данных.")
c[1].metric("Рост ВВП за год", f"{gq.iloc[-1]:+.1f}%", f"тренд ≈ {trend.iloc[-1]:.1f}%", delta_color="off",
            border=True, help="Реальный ВВП к тому же кварталу прошлого года. Тренд — модель HLW.")
c[2].metric("Безработица", f"{u.iloc[-1]:.1f}%", f"{u.iloc[-1] - u[:u.index[-1] - pd.DateOffset(years=1)].iloc[-1]:+.1f} за год",
            delta_color="inverse", border=True, help="UNRATE. Естественный уровень по оценке CBO — "
                                                     f"{u_star.iloc[-1]:.1f}%.")
c[3].metric("Рынок труда", f"{lmci_level.iloc[-1]:+.2f}", f"импульс {lmci_mom.iloc[-1]:+.2f}", delta_color="off",
            border=True, help="Индикаторы ФРБ Канзас-Сити: уровень (сильнее/слабее среднего) и импульс "
                              "(улучшается/ухудшается). 0 — среднее.")
alarms = int((risk()["Тревога"] == "🔴 да").sum())
c[4].metric("Сигналы рецессии", f"{alarms} из {len(risk())}", "в тревоге", delta_color="off", border=True,
            help="Сколько моделей рецессии из раздела 4 сейчас выше своего порога.")

years = PERIODS[st.segmented_control("Период графиков", list(PERIODS), default="20 лет", key="period")
                or "20 лет"]

# ---------- 1. скорость ----------
st.header("1. Скорость: как быстро растёт экономика")
st.markdown("Рост реального ВВП — главный итог. Но ВВП выходит раз в квартал и с опозданием, поэтому рядом — "
            "**наукаст** текущего квартала и **недельный индекс**, который обновляется каждую неделю.")
learn.tags("совпадающий", "проверен на истории")
st.plotly_chart(line_chart({"Рост ВВП за год": cut(gq, years), "Недельный индекс WEI": cut(wei, years),
                            "Трендовый рост (HLW)": cut(trend, years)}, units="%", recessions=rec,
                           zero_line=True, height=380), width="stretch")

with learn.how_it_works():
    st.markdown("""
- **Трендовый (потенциальный) рост** — с какой скоростью экономика может расти долго: прирост рабочей силы +
  рост производительности. В США сейчас около 2–2,5% в год. Расти быстрее можно лишь временно — за счёт
  загрузки свободных мощностей и людей.
- **Наукаст** собирает всю вышедшую статистику квартала и пересчитывает оценку ВВП после каждого релиза.
  Средняя ошибка GDPNow — около ±1,2 п.п.: хорошо видит направление, хуже — точное число.
- **Пересмотры.** ВВП потом многократно уточняют. Первая оценка может отличаться от итоговой на 1–2 п.п.
""")


def ex_okun():
    uq = u.resample("QS").mean()
    d = pd.concat({"g": gq, "du": uq - uq.shift(4)}, axis=1, sort=True).dropna()
    slope, icpt = np.polyfit(d["g"], d["du"], 1)
    st.plotly_chart(dual_axis_chart(("Рост ВВП за год", cut(d["g"], years), "%"),
                                    ("Изменение безработицы за год", cut(d["du"], years), "п.п."),
                                    recessions=rec, invert_right=True), width="stretch")
    st.markdown(
        f"**Закон Оукена.** Когда экономика растёт быстрее нормы, компании нанимают и безработица падает; "
        f"медленнее — растёт. По данным с 1948 года каждый лишний процентный пункт роста ВВП снижает "
        f"безработицу примерно на **{-slope:.1f} п.п.** за год (корреляция {d['g'].corr(d['du']):.2f}). "
        f"Безработица стоит на месте при росте около {-icpt / slope:.1f}% — это средняя «норма» за всю историю; "
        f"сегодня, при стареющем населении, она ниже — ближе к трендовым ≈ {trend.iloc[-1]:.1f}%. "
        f"Правая ось перевёрнута, поэтому линии идут вместе.")


def ex_2022():
    q = ui.load("GDPC1")
    ann = ((q / q.shift(1)) ** 4 - 1) * 100
    g = pd.concat({"Рост ВВП, кв/кв в годовом темпе": ann["2021":"2023"],
                   "Занятость, изменение за год, млн": (ui.load("PAYEMS").diff(12) / 1000)["2021":"2023"]
                   .resample("QS").last()}, axis=1, sort=True)
    st.plotly_chart(dual_axis_chart(("Рост ВВП, кв/кв", g.iloc[:, 0], "%"),
                                    ("Новые рабочие места за год", g.iloc[:, 1], "млн"), recessions=rec),
                    width="stretch")
    st.markdown(
        f"Летом 2022 года по первым оценкам ВВП снижался два квартала подряд — по популярному правилу это "
        f"«техническая рецессия». Но за 2022 год экономика создала **≈ {(ui.load('PAYEMS')['2022-12-01'] - ui.load('PAYEMS')['2021-12-01']) / 1000:.1f} млн** "
        f"рабочих мест, а после пересмотров второй квартал стал положительным ({ann['2022-04-01']:+.1f}%). "
        f"Рецессию в США определяет не правило «двух кварталов», а комитет NBER по широкому набору данных — "
        f"занятость, доходы, производство.")


learn.examples([Example("Закон Оукена: рост ВВП ↔ безработица", ex_okun),
                Example("2022: «техническая рецессия», которой не было", ex_2022, normal=False)], key="speed")

# ---------- 2. загрузка ----------
st.header("2. Загрузка: выше или ниже потенциала")
st.markdown("Важна не только скорость, но и **уровень**: работает ли экономика выше своих возможностей "
            "(перегрев → давление на цены) или ниже (простаивают люди и мощности).")
learn.tags("совпадающий", "спорный")
st.plotly_chart(line_chart({"Разрыв выпуска (CBO)": cut(cbo, years), "Разрыв выпуска (HLW)": cut(hlw_gap, years),
                            "Безработица ниже естественной": cut((u_star.resample("MS").ffill()
                                                                 .reindex(u.index, method="ffill") - u).dropna(),
                                                                years)},
                           units="%", recessions=rec, zero_line=True, height=360), width="stretch")
st.caption("Выше нуля — экономика загружена сильнее нормы, ниже — недогружена. Третья линия — та же идея "
           "через рынок труда: насколько безработица ниже своего естественного уровня.")

with learn.how_it_works():
    st.markdown("""
- **Разрыв выпуска** = фактический ВВП / потенциальный − 1. Потенциал нельзя измерить, только оценить —
  поэтому CBO и модель HLW могут заметно расходиться. Отсюда метка «спорный».
- **Почему это важно дальше по цепочке.** Перегрев (разрыв > 0, безработица ниже естественной) толкает вверх
  зарплаты и цены — это вход в слой инфляции. Недогрузка, наоборот, гасит инфляцию.
- **Почему это важно для ФРС.** Разрыв на рынке труда входит в правило Тейлора (слой 2).
""")


def ex_two_views():
    ug = (u_star.resample("QS").ffill().reindex(cbo.index, method="ffill") - u.resample("QS").mean()
          .reindex(cbo.index)).dropna()
    d = pd.concat({"cbo": cbo, "ug": ug}, axis=1, sort=True).dropna()
    st.plotly_chart(dual_axis_chart(("Разрыв выпуска (CBO)", cut(d["cbo"], years), "%"),
                                    ("Безработица ниже естественной", cut(d["ug"], years), "п.п."), recessions=rec),
                    width="stretch")
    st.markdown(
        f"Две стороны одной монеты: когда ВВП выше потенциала, компаниям нужно больше людей и безработица "
        f"опускается ниже естественной. Корреляция двух мер — **{d['cbo'].corr(d['ug']):.2f}**. Поэтому ФРС "
        f"часто смотрит на рынок труда как на более надёжную (и быстрее выходящую) меру загрузки.")


def ex_disagree():
    g = pd.concat({"CBO": cbo["2015":], "HLW": hlw_gap["2015":]}, axis=1, sort=True).dropna()
    st.plotly_chart(line_chart({f"Разрыв выпуска ({k})": g[k] for k in g}, units="%", recessions=rec,
                               zero_line=True, height=320), width="stretch")
    st.markdown(
        f"Прямо сейчас две авторитетные оценки говорят разное: по CBO экономика **на {cbo.iloc[-1]:+.1f}%** "
        f"выше потенциала (перегрев), по модели HLW — {hlw_gap.iloc[-1]:+.1f}% (почти ровно у потенциала). "
        f"CBO считает потенциал «снизу» — из рабочей силы и капитала, HLW выводит его из того, ускоряется ли "
        f"инфляция. После 2020 года (иммиграция, сдвиги производительности) потенциал стал особенно неясен. "
        f"Урок: когда оценки расходятся, смотрите на то, что наблюдаемо, — инфляцию и рынок труда.")


learn.examples([Example("Разрыв выпуска и безработица — одно и то же", ex_two_views),
                Example("Сейчас: CBO видит перегрев, HLW — нет", ex_disagree, normal=False)], key="slack")

# ---------- 3. рынок труда ----------
st.header("3. Рынок труда")
st.markdown("Работа — главный источник дохода семей, а их расходы — около 70% экономики США. Пока люди "
            "работают и получают больше, спрос держится. Поэтому ухудшение рынка труда — самый важный "
            "признак того, что спад начался.")
learn.tags("совпадающий", "проверен на истории")
left, right = st.columns(2)
with left:
    st.markdown("**Сводно: уровень и импульс (ФРБ Канзас-Сити)**")
    st.plotly_chart(line_chart({"Уровень": cut(lmci_level, years), "Импульс": cut(lmci_mom, years)},
                               units="ст. откл.", recessions=rec, zero_line=True, height=320), width="stretch")
with right:
    st.markdown("**Первичные заявки на пособие, 4 недели**")
    st.plotly_chart(line_chart({"Заявки, тыс. в неделю": cut(ui.load("ICSA").rolling(4).mean() / 1000, years)},
                               units="тыс.", recessions=rec, height=320), width="stretch")

with learn.how_it_works():
    st.markdown("""
- **Уровень и импульс.** Уровень говорит, насколько рынок труда силён сейчас; импульс — улучшается он или
  ухудшается. Опасный сигнал — уровень ещё высокий, но импульс уже уходит в минус.
- **Заявки на пособие** — самые быстрые данные: выходят каждую неделю. Устойчивый рост означает, что
  компании начали увольнять.
- **Ловушка.** Безработица может расти не только из-за увольнений, но и из-за притока новых людей на рынок
  труда (иммиграция, возвращение пенсионеров) — это не спад.
""")


def ex_sahm():
    s = sig["SAHMREALTIME"]
    trig = s >= 0.5
    first = s[trig & ~trig.shift(1, fill_value=False)].index
    rows = []
    for a in starts():
        near = [d for d in first if abs(months_between(a, d)) <= 9]
        rows.append({"Рецессия началась": f"{a:%m.%Y}",
                     "Правило Сама сработало": f"{near[0]:%m.%Y}" if near else "—",
                     "Через сколько месяцев": months_between(a, near[0]) if near else None})
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    false = [d for d in first if d.year > 1968 and all(abs(months_between(a, d)) > 9 for a in starts())]
    st.markdown(
        "Правило Сама срабатывает, когда средняя безработица за 3 месяца поднимается на 0,5 п.п. над минимумом "
        "за год. Оно поймало **каждую** рецессию с 1969 года — обычно в первые месяцы. Это совпадающий сигнал: "
        "не «будет», а «уже началось». Ложные срабатывания: " + ", ".join(f"{d:%m.%Y}" for d in false) + ".")


def ex_sahm_2024():
    g = pd.concat({"Правило Сама": sig["SAHMREALTIME"]["2022":], "Безработица": u["2022":]}, axis=1)
    st.plotly_chart(dual_axis_chart(("Правило Сама", g.iloc[:, 0], "п.п."), ("Безработица", g.iloc[:, 1], "%"),
                                    recessions=rec), width="stretch")
    st.markdown(
        "Летом 2024 года правило сработало впервые с 1976 года без рецессии. Безработица выросла не из-за "
        "увольнений — заявки на пособие оставались низкими, — а из-за **притока рабочей силы**: иммигранты "
        "искали работу быстрее, чем экономика успевала её создавать. Сама Клаудия Сам назвала это вероятной "
        "ложной тревогой. Урок: смотрите, *почему* растёт безработица — увольнения или новые люди.")


learn.examples([Example("Правило Сама ловило каждую рецессию с 1969 года", ex_sahm),
                Example("2024: ложное срабатывание из-за притока рабочей силы", ex_sahm_2024, normal=False)],
               key="labor")

# ---------- 4. риск рецессии ----------
st.header("4. Риск рецессии: несколько моделей рядом")
st.markdown("Ни одна модель не надёжна сама по себе, поэтому — ансамбль. **Совпадающие** отвечают, идёт ли "
            "спад уже сейчас; **опережающие** — ждать ли его через год. У каждой указано, когда она ошибалась.")
learn.tags("опережающий", "проверен вне выборки")
st.dataframe(risk(), hide_index=True, width="stretch")
st.plotly_chart(line_chart({"По кривой доходности, через год": cut(sig["curve_prob"], years),
                            "По кредитному рынку, через год": cut(sig["ebp_prob"], years),
                            "Рецессия уже идёт (Шове–Пигер)": cut(sig["RECPROUSM156N"], years)},
                           units="%", recessions=rec, height=360), width="stretch")

with learn.how_it_works():
    st.markdown("""
- **Как читать вместе.** Сильнее всего сигнал, когда тревожат модели **разных типов**: кривая + кредит +
  первые признаки в совпадающих данных. Одна модель в тревоге — повод присмотреться, а не вывод.
- **Пороги условные.** 30% для опережающих моделей — уровень, выше которого они поднимались перед большинством
  рецессий; 50% для модели Шове–Пигера — её собственная граница «скорее да, чем нет».
- **Чего модели не видят.** Внешние шоки (пандемия 2020 года) не предсказывает никто: модели строятся на
  экономических связях, а не на событиях.
""")


def ex_cp():
    s = sig["RECPROUSM156N"]
    rows = []
    for a in starts():
        w = s[(s.index >= a - pd.DateOffset(months=3)) & (s.index <= a + pd.DateOffset(months=9))]
        hit = w[w > 50].index.min()
        rows.append({"Рецессия началась": f"{a:%m.%Y}",
                     "Модель > 50%": f"{hit:%m.%Y}" if pd.notna(hit) else "не поднялась выше 50%",
                     "Максимум, %": round(w.max())})
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.markdown(
        "Совпадающая модель Шове–Пигера смотрит на занятость, производство, доходы и продажи. Она поднимается "
        "выше 50% в первые месяцы рецессии и за всю историю **ни разу не дала ложной тревоги**. Её роль — "
        "быстро подтвердить спад, а не предсказать его.")


def ex_permits():
    p = sig["PERMIT_YOY"]
    rows = []
    for a in starts():
        w = p[(p.index < a) & (p.index >= a - pd.DateOffset(months=30))]
        f = w[w < -20].index.min()
        rows.append({"Рецессия началась": f"{a:%m.%Y}",
                     "Разрешения упали > 20%": f"{f:%m.%Y}" if pd.notna(f) else "—",
                     "За сколько месяцев": months_between(f, a) if pd.notna(f) else None})
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.markdown(
        "Жильё — самый чувствительный к ставкам сектор: ипотека дорожает → люди меньше покупают → застройщики "
        "берут меньше разрешений. Поэтому стройка обычно падает **первой** — за несколько месяцев или больше года "
        "до рецессии. Но не всегда: в 2001 и 2020 годах спад начался не с жилья.")


def ex_split():
    g = pd.concat({k: sig[k]["2021":"2025"] for k in ("curve_prob", "ebp_prob", "RECPROUSM156N")}, axis=1,
                  sort=True)
    g.columns = ["Кривая доходности", "Кредитный рынок", "Шове–Пигер (уже идёт)"]
    st.plotly_chart(line_chart({k: g[k].dropna() for k in g}, units="%", recessions=rec, height=320),
                    width="stretch")
    pm = sig["PERMIT_YOY"]["2022":"2023"]
    credit_months = int((g.iloc[:, 1] > growth.SIGNALS["ebp_prob"].threshold).sum())
    st.markdown(
        f"2022–2024: модели разошлись. Кривая доходности дала до **{g.iloc[:, 0].max():.0f}%**, разрешения на "
        f"строительство упали на {-pm.min():.0f}% — два опережающих сигнала в тревоге. А кредитный рынок лишь "
        f"коснулся порога: максимум {g.iloc[:, 1].max():.0f}%, выше 30% — всего {credit_months} мес. "
        f"Совпадающие данные оставались у нуля. Рецессии не было. "
        f"Ансамбль сработал лучше любой отдельной модели: «тревога» была у сигналов одного происхождения — "
        f"высоких ставок, — а не у экономики в целом.")


learn.examples([Example("Совпадающая модель подтверждает спад без ложных тревог", ex_cp),
                Example("Стройка падает первой", ex_permits),
                Example("2022–2024: модели разошлись", ex_split, normal=False)], key="risk")

learn.next_steps([6, 2], "Загрузка экономики с задержкой разгоняет или гасит инфляцию (слой 6), а инфляция "
                         "и занятость возвращаются в решения ФРС (слой 2) — цепочка замыкается.")
