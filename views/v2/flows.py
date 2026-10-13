"""Слой 8. Вынужденные потоки: кто обязан купить или продать по правилу, марже, календарю или мандату —
ближайшие события из календаря trade-news, справочник механизмов и проверка любого события на истории."""
from collections import defaultdict
from datetime import date, timedelta

import numpy as np
import pandas as pd
import streamlit as st

from core import flows as F
from core import learn, ui
from core.charts import band_chart, grouped_bars
from core.learn import Example
from core.series import BY_KEY

ASSETS = {"S&P 500": "^GSPC", "Nasdaq": "^IXIC", "Гособлигации 20+ лет (TLT)": "TLT", "Золото (GLD)": "GLD",
          "Биткоин": "BTC-USD", "Иен за доллар": "DEXJPUS", "Рублей за доллар (курс ЦБ)": "USDRUB_CBR"}
PERIODS = {"С 1990 года": "1990", "С 2010 года": "2010", "Последние 5 лет": None}
MARKETS = {"us_equity": "акции США", "us_rates": "ставки США", "fx": "валюты", "crypto": "крипта", "ru": "Россия"}
WEEKDAYS = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]


@st.cache_data(ttl=3600, show_spinner=False)
def upcoming(days: int = 14) -> list[dict] | None:
    try:
        return F.calendar(date.today(), date.today() + timedelta(days=days))
    except Exception:  # trade-news недоступен — экран работает без календаря
        return None


@st.cache_data(ttl=3600, show_spinner="Считаю события на истории…")
def run_study(kind: str, key: str, start: str | None, window: int) -> F.Study:
    p = ui.load(key).dropna()
    p = p[start:] if start else p[p.index >= p.index[-1] - pd.DateOffset(years=5)]
    return F.study(p, F.event_dates(kind, p.index), window)


def digest(events: list[dict]) -> dict[date, list[str]]:
    """События по дням, массовые типы — одной строкой: отчёты, локапы, тихие периоды выкупа."""
    by_day: dict[date, list[str]] = defaultdict(list)
    bulk: dict[tuple[date, str], list[str]] = defaultdict(list)
    today = date.today()
    blackout = [e for e in events if e["type"] == "buyback_blackout"]
    for e in events:
        d = max(date.fromisoformat(e["date"]), today)
        if e["type"] in ("earnings", "ipo_lockup"):
            bulk[(d, e["type"])].append(", ".join(e["assets"]) or e["title"])
        elif e["type"] != "buyback_blackout":
            mark = "**" if e.get("major") else ""
            est = " _(оценка)_" if e.get("precision") == "estimated" else ""
            by_day[d].append(f"{mark}{e['title']}{mark}{est} — {e['details']}" if e.get("details") else
                             f"{mark}{e['title']}{mark}{est}")
    for (d, t), names in bulk.items():
        label = "Отчёты" if t == "earnings" else "Конец локапа IPO (оценка)"
        by_day[d].append(f"{label}: {', '.join(sorted(set(names))[:12])}" + (" и др." if len(set(names)) > 12 else ""))
    if blackout:
        open_now = [e for e in blackout if (e.get("end_date") or e["date"]) >= today.isoformat()
                    and e["date"] <= today.isoformat()]
        if open_now:
            by_day[today].insert(0, f"**{len(open_now)} компаний в тихом периоде выкупа** — меньше покупок "
                                    f"собственных акций до их отчётов")
    return dict(sorted(by_day.items()))


# ---------- шапка ----------
learn.layer_header(8, "Слои 1–7 отвечают, **куда** тянет фундамент. Этот слой — о том, **кто и когда толкает цену "
                      "независимо от фундамента**: индексные фонды, маркетмейкеры, пенсионные фонды, трейдеры с "
                      "плечом, государство. Их сделки диктует правило или календарь, а не мнение о цене, — поэтому "
                      "их можно предвидеть.")

events = upcoming()
week = [e for e in (events or []) if e["date"] <= (date.today() + timedelta(days=7)).isoformat()]
majors = [e for e in week if e.get("major") and e["type"] not in ("ipo_lockup", "earnings", "buyback_blackout")]
blackouts = sum(1 for e in (events or []) if e["type"] == "buyback_blackout"
                and e["date"] <= date.today().isoformat() <= (e.get("end_date") or e["date"]))
if events is None:
    learn.takeaway("Календарь вынужденных потоков сейчас недоступен (сервис trade-news не отвечает). Справочник и "
                   "проверка на истории ниже работают.")
elif majors:
    learn.takeaway("На этой неделе: " + "; ".join(f"{e['title']} ({WEEKDAYS[date.fromisoformat(e['date']).weekday()]}"
                                                  f" {e['date'][8:]}.{e['date'][5:7]})" for e in majors[:5]) +
                   (f". {blackouts} крупных компаний в тихом периоде выкупа." if blackouts else "."), "warn")
else:
    learn.takeaway("На этой неделе крупных вынужденных потоков в календаре нет" +
                   (f"; {blackouts} крупных компаний в тихом периоде выкупа." if blackouts else "."))

c = st.columns(4)
c[0].metric("Крупных событий за 7 дней", len(majors) if events is not None else "—", border=True,
            help="Экспирации, конец месяца и квартала, ребалансировки индексов, крупные аукционы и разлоки, "
                 "решения ЦБ, анонсы Минфина РФ.")
c[1].metric("В тихом периоде выкупа", blackouts if events is not None else "—", "из ~70 крупнейших компаний",
            delta_color="off", border=True,
            help="Перед отчётом компании обычно не выкупают свои акции: одного постоянного покупателя меньше.")
c[2].metric("Разлоков токенов за 14 дней", sum(1 for e in (events or []) if e["type"] == "token_unlock"),
            delta_color="off", border=True, help="Крупные разлоки из DefiLlama: от 1% предложения и $5 млн.")
nxt = [e for e in (events or []) if e["type"] == "opex_quarterly"]
c[3].metric("До квартальной экспирации", f"{(date.fromisoformat(nxt[0]['date']) - date.today()).days} дн."
            if nxt else "> 2 недель", delta_color="off", border=True)

# ---------- 1. ближайшие потоки ----------
st.header("1. Ближайшие вынужденные потоки")
learn.tags("опережающий", "проверен на истории")
if events is None:
    st.info("Сервис trade-news не отвечает — календарь появится, когда он заработает.")
else:
    picked = st.pills("Рынки", list(MARKETS), format_func=MARKETS.get, selection_mode="multi",
                      default=list(MARKETS), key="fl_markets")
    shown = [e for e in events if e["market"] in (picked or MARKETS)]
    for d, lines in digest(shown).items():
        st.markdown(f"**{WEEKDAYS[d.weekday()]} {d:%d.%m}**  \n" + "  \n".join(f"• {x}" for x in lines))
    st.caption("Источник — календарь trade-news (обновляется каждые 6 часов). Жирным — крупные события. "
               "«Оценка» — дата рассчитана, а не объявлена.")
with learn.how_it_works():
    st.markdown("""
- **Экспирации.** Маркетмейкеры хеджируют проданные опционы акциями и фьючерсами. В день экспирации хеджи
  снимаются — рынок «отпускает», после неё движения часто становятся шире.
- **Конец месяца и квартала.** Пенсионные фонды и портфели 60/40 возвращают доли акций и облигаций; банки сжимают
  балансы перед отчётностью; иностранцы перестраивают валютные хеджи.
- **Тихий период выкупа.** За 2–4 недели до отчёта компании обычно не покупают свои акции. Доказательства, что это
  снижает доходность, слабые — но один крупный покупатель на время уходит.
- **Локапы, разлоки, аукционы** — новое предложение бумаг, токенов, облигаций.
- **Россия.** На 3-й рабочий день Минфин объявляет покупки или продажи валюты по бюджетному правилу; около 28-го
  экспортёры продают валюту под налоги.
""")

# ---------- 2. справочник ----------
st.header("2. Кто бывает вынужден")
st.markdown("""
Участник **вынужден**, если его сделку запускает не цена. Пять признаков:
1. **Правило вместо мнения** — мандат, индекс, модель риска, маржа.
2. **Известно когда** — календарь или порог.
3. **Нельзя ждать** — опоздание стоит дороже плохой цены.
4. **Размер сравним с ликвидностью** в этот момент.
5. **Правила публичны** — значит, другие встают перед потоком, и известные эффекты со временем слабеют.

Сильнее всего потоки, которые торгуют **в сторону движения** и разгоняют его: маржин-коллы, хедж короткой гаммы,
правила по волатильности.
""")
mech = pd.DataFrame(F.MECHANISMS, columns=["Группа", "Кто вынужден", "Что делает", "Когда", "Рынки", "Надёжность",
                                           "Где смотреть"])
groups = st.pills("Группы", list(dict.fromkeys(mech["Группа"])), selection_mode="multi", key="fl_groups")
st.dataframe(mech[mech["Группа"].isin(groups)] if groups else mech, hide_index=True, width="stretch", height=420)
st.caption("Сжатая версия отчёта «Что двигает цену и вынужденные участники» (reports/ в репозитории): там ~60 "
           "механизмов со ссылками на исследования и источниками данных.")

# ---------- 3. проверка на истории ----------
st.header("3. Проверить событие на истории")
st.markdown("Работает ли эффект на самом деле? Выберите событие и актив — увидите, как в среднем вела себя цена за "
            "дни до и после, **сверх обычного дрейфа** актива, и насколько это отличимо от случайности.")
learn.tags("совпадающий", "проверен на истории")
a, b, c_, d_ = st.columns(4)
kind = a.selectbox("Событие", list(F.EVENTS), format_func=lambda k: F.EVENTS[k].title, key="fl_kind")
asset = b.selectbox("Актив", list(ASSETS), key="fl_asset",
                    index=list(ASSETS).index("Рублей за доллар (курс ЦБ)") if kind == "ru_tax_period" else 0)
period = c_.segmented_control("Период", list(PERIODS), default="С 1990 года", key="period") or "С 1990 года"
window = d_.slider("Дней до и после", 3, 15, 5, key="fl_window")
ev = F.EVENTS[kind]
st.caption(f"**Кто вынужден:** {ev.who}. **Дата:** {ev.rule}.")
try:
    s = run_study(kind, ASSETS[asset], PERIODS[period], window)
except ValueError as e:
    st.warning(f"Не получается посчитать: {e}.")
else:
    k = pd.Index(s.days)
    st.plotly_chart(band_chart({"Средняя избыточная доходность": pd.Series(s.path, index=k)},
                               (pd.Series(s.lo, index=k), pd.Series(s.hi, index=k), "95% интервал"), units="%",
                               height=340), width="stretch")
    st.caption(f"День 0 — день события ({ev.rule}). Накоплено с дня −{window}; из каждого дня вычтен обычный "
               f"дрейф актива ({s.drift:+.3f}% в день). Событий: {s.n}. {BY_KEY[ASSETS[asset]].name}.")
    pre, t_pre = F.window_effect(s, -3, -1)
    day0, t0 = F.window_effect(s, 0, 0)
    post, t_post = F.window_effect(s, 1, 3)
    m = st.columns(3)
    m[0].metric("3 дня до события", f"{pre:+.2f}%", f"t = {t_pre:.1f}", delta_color="off", border=True)
    m[1].metric("День события", f"{day0:+.2f}%", f"t = {t0:.1f}", delta_color="off", border=True)
    m[2].metric("3 дня после", f"{post:+.2f}%", f"t = {t_post:.1f}", delta_color="off", border=True)
    strong = [(n, v, t) for n, v, t in (("до события", pre, t_pre), ("в день события", day0, t0),
                                        ("после события", post, t_post)) if abs(t) >= 2]
    if strong:
        st.markdown("Заметное отклонение " + "; ".join(f"**{n}: {v:+.2f}%** (t = {t:.1f})" for n, v, t in strong) +
                    ". Но помните: проверяя много окон и событий, «значимые» результаты будут попадаться и "
                    "случайно — примерно 1 из 20 при t = 2. Надёжнее, если эффект держится в разных периодах и "
                    "на разных активах.")
    else:
        st.markdown("Отклонения не выходят за пределы случайного шума (|t| < 2): на этом активе и периоде эффект "
                    "события не виден.")
with learn.how_it_works("Как читать проверку"):
    st.markdown("""
- **Избыточная доходность** — доходность за день минус обычная средняя доходность актива. Иначе любой растущий
  актив «рос бы после события» просто потому, что он вообще растёт.
- **95% интервал** — где была бы средняя при случайном наборе тех же дней. Если ноль внутри полосы — эффект
  неотличим от шума.
- **t-статистика** — во сколько раз эффект больше своей ошибки. |t| ≥ 2 — заметно, ≥ 3 — уверенно.
- **Ловушка множественных проверок.** 8 событий × 7 активов × 3 периода × 3 окна — это сотни проверок. Пять
  процентов из них покажут t > 2 случайно. Верьте эффекту, если у него есть механизм и он повторяется.
""")


def ex_turn():
    rows = {}
    for name, start in (("1990–2009", "1990"), ("2010–н.в.", "2010")):
        p = ui.load("^GSPC").dropna()[start:("2009" if start == "1990" else None)]
        st_ = F.study(p, F.event_dates("month_end", p.index), 5)
        rows[name] = {"3 дня до конца месяца": F.window_effect(st_, -3, -1)[0],
                      "день конца месяца": F.window_effect(st_, 0, 0)[0],
                      "первый день нового месяца": F.window_effect(st_, 1, 1)[0],
                      "дни 2–3": F.window_effect(st_, 2, 3)[0]}
    df = pd.DataFrame(rows).T
    st.plotly_chart(grouped_bars(df, units="%", height=300), width="stretch")
    st.markdown(
        "Эффект смены месяца — один из самых старых календарных эффектов (Ariel, 1987; Lakonishok и Smidt, 1988). "
        f"Последние дни месяца и первый день нового S&P растёт сильнее обычного: в первый день месяца в среднем "
        f"{df.iloc[0, 2]:+.2f}% (1990–2009) и {df.iloc[1, 2]:+.2f}% (с 2010 года) сверх обычного дрейфа. Механизм — "
        f"вынужденные покупатели по календарю: зарплатные взносы в пенсионные планы и паевые фонды приходят в начале "
        f"месяца, фонды докупают акции на поступившие деньги. И заметьте, как эффект **ослаб** после 2010 года: о "
        f"нём знают все, и часть покупок делают заранее — так стареет любой публичный календарный эффект.")


def ex_rebalance():
    spx = ui.load("^GSPC").dropna()["1989-10":]
    y = ui.load("DGS10").dropna()
    bond = (y.shift(1) / 252 - 7.5 * y.diff()).dropna()  # оценка дневной доходности 10-летних, %
    rows = []
    for d in F.event_dates("quarter_end", spx["1990":].index):
        q0 = d.to_period("Q").start_time
        seg, base = spx[q0:d], spx[:q0 - pd.Timedelta(days=1)]
        if len(seg) >= 5 and len(base):
            gap = (seg.iloc[-4] / base.iloc[-1] - 1) * 100 - bond[q0:seg.index[-4]].sum()
            rows.append((d, gap))
    g = pd.DataFrame(rows, columns=["d", "gap"])
    hi = g[g["gap"] >= g["gap"].quantile(2 / 3)]["d"].tolist()
    lo = g[g["gap"] <= g["gap"].quantile(1 / 3)]["d"].tolist()
    res = {name: F.study(spx, ds, 5) for name, ds in (("Акции обогнали облигации", hi),
                                                       ("Акции отстали от облигаций", lo))}
    k = pd.Index(res["Акции обогнали облигации"].days)
    st.plotly_chart(band_chart({n: pd.Series(r.path, index=k) for n, r in res.items()},
                               (pd.Series(res["Акции обогнали облигации"].lo, index=k),
                                pd.Series(res["Акции обогнали облигации"].hi, index=k), "95% интервал (обогнали)"),
                               height=320), width="stretch")
    up, t_up = F.window_effect(res["Акции обогнали облигации"], 1, 2)
    st.markdown(
        "Теория: если за квартал акции обогнали облигации, пенсионные фонды к концу квартала **продают** акции, "
        "чтобы вернуть доли. Harvey и соавторы (NBER, 2025) находят это по оценкам потоков фондов: −0,17% акциям "
        "на следующий день. Наш простой тест — треть кварталов с самым большим отрывом акций против трети с самым "
        f"маленьким — эффекта **не видит**: после «перегретых» кварталов S&P в дни +1…+2 в среднем даже растёт на "
        f"{up:+.2f}% (t = {t_up:.1f}). Возможные причины: фонды ребалансируют заранее и фьючерсами, на поток встают "
        f"другие участники, а грубая мера «акции минус облигации» плохо оценивает реальный объём продаж. Вывод: "
        f"механизм реальный, но простой календарный сигнал из него не получается.")


def ex_many():
    p = ui.load("^GSPC").dropna()["1990":]
    rows, hits, total = [], 0, 0
    for kind_, ev_ in F.EVENTS.items():
        if kind_ == "ru_tax_period":
            continue
        st_ = F.study(p, F.event_dates(kind_, p.index), 5)
        sig = int((st_.daily["t"].abs() >= 2).sum())
        hits, total = hits + sig, total + len(st_.daily)
        rows.append({"Событие": ev_.title, "Событий": st_.n, "Дней с |t| ≥ 2 из 11": sig,
                     "Самый сильный день": f"{st_.daily['t'].abs().idxmax():+d} (t = "
                                           f"{st_.daily['t'].loc[st_.daily['t'].abs().idxmax()]:.1f})"})
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.markdown(
        f"Проверили 7 событий по 11 дней на S&P с 1990 года — {total} проверок. «Значимыми» (|t| ≥ 2) оказались "
        f"{hits}; чистая случайность дала бы около {total * 0.05:.0f}. Поэтому один день с t = 2 — ещё не "
        f"открытие. Убедительно, когда эффект собирается в окно (несколько дней подряд), есть механизм и он "
        f"держится в разные периоды.")


learn.examples([Example("Эффект смены месяца", ex_turn),
                Example("Ребалансировка конца квартала: исследование видит, простой тест — нет", ex_rebalance,
                        normal=False),
                Example("Ловушка множественных проверок", ex_many, normal=False)], key="study")

learn.next_steps([7, 4], "Вынужденные потоки ускоряют любое звено цепочки, но сильнее всего видны в ценах активов "
                         "(слой 7) и в финансовых условиях (слой 4): распродажа по марже сама ужесточает условия.")
