"""Слой 8. Вынужденные потоки: кто обязан купить или продать по правилу, марже, календарю или мандату —
ближайшие события из календаря trade-news, справочник механизмов и проверка любого события на истории."""
from collections import defaultdict
from datetime import date, timedelta

import numpy as np
import pandas as pd
import streamlit as st

from core import flows as F
from core import learn, ui
from core.charts import band_chart, dual_axis_chart, grouped_bars, line_chart
from core.learn import Example
from core.series import BY_KEY
from core.transforms import yoy_pct

ASSETS = {"S&P 500": "^GSPC", "Nasdaq": "^IXIC", "Гособлигации 20+ лет (TLT)": "TLT", "Золото (GLD)": "GLD",
          "Биткоин": "BTC-USD", "Иен за доллар": "DEXJPUS", "Рублей за доллар (курс ЦБ)": "USDRUB_CBR"}
PERIODS = {"С 1990 года": "1990", "С 2010 года": "2010", "Последние 5 лет": None}
MARKETS = {"us_equity": "акции США", "us_rates": "ставки США", "fx": "валюты", "crypto": "крипта", "ru": "Россия"}
WEEKDAYS = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
TREND_ASSETS = {"S&P 500": "^GSPC", "Nasdaq": "^IXIC", "Гособлигации 20+ лет (TLT)": "TLT", "Золото": "GC=F",
                "Индекс доллара": "DTWEXBGS", "Иен за доллар": "DEXJPUS", "Биткоин": "BTC-USD"}


def cut_years(s: pd.Series, years: int) -> pd.Series:
    return s[s.index >= s.index[-1] - pd.DateOffset(years=years)]


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
            start, end = date.fromisoformat(e["date"]), date.fromisoformat(e.get("end_date") or e["date"])
            if start < today <= end and end > start:  # окно уже идёт: один раз, с периодом и объёмом, а не «новое сегодня»
                size = (f", {e['size']:+.1f} млрд ₽ в день" if e.get("size") is not None
                        and e.get("size_unit") == "rub_bn_day" else "")
                by_day[today].insert(0, f"{mark}Идёт {start:%d.%m}–{end:%d.%m}: {e['title']}{mark}{size}")
                continue
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

# ---------- 4. модельные потоки ----------
st.header("4. Что фонды обязаны делать по своим правилам")
st.markdown("Часть вынужденных потоков нигде не публикуется, но **правила известны** — значит, поток можно "
            "смоделировать. Это упрощённые модели: настоящие фонды сложнее, а их размеры известны только по оценкам "
            "банков. Модель показывает **направление и пороги**, а не точный объём.")
learn.tags("совпадающий", "проверен на истории")
spx = ui.load("^GSPC").dropna()
tab_vol, tab_trend, tab_fx, tab_q = st.tabs(["Таргет волатильности", "Трендовые фонды (CTA)",
                                             "Конец месяца: хедж валюты", "Конец квартала: пенсионные фонды"])

with tab_vol:
    vc = F.vol_control(spx)
    k = st.columns(3)
    k[0].metric("Волатильность S&P за 20 дней", f"{vc['vol'].iloc[-1]:.1f}%", "в годовом выражении",
                delta_color="off", border=True)
    k[1].metric("Доля акций у модельного фонда", f"{vc['exposure'].iloc[-1]:.0%}",
                f"{vc['exposure'].iloc[-1] - vc['exposure'].iloc[-6]:+.0%} за неделю", delta_color="off", border=True,
                help="Таргет 10% годовой волатильности, плечо до 150%.")
    move = k[2].slider("Если завтра S&P сдвинется на, %", -8.0, 8.0, -3.0, 0.5, key="fl_move")
    now_e, new_e = F.vol_control_shock(spx, move)
    aum = st.slider("Сколько денег в таких стратегиях, млрд $ (допущение)", 50, 1000, 300, 50, key="fl_aum",
                    help="Публичных данных нет; банки оценивают по-разному, порядка сотен миллиардов. Подставьте "
                         "свою оценку — модель пересчитает объём в долларах.")
    st.markdown(f"После дня {move:+.1f}% модель пересчитает волатильность, и доля акций станет **{new_e:.0%}** вместо "
                f"{now_e:.0%}: это **{'продажа' if new_e < now_e else 'покупка'} {abs(new_e - now_e) * aum:,.0f} млрд $** "
                f"при капитале {aum} млрд $. Важно: сильный день в **любую** сторону поднимает волатильность — модель "
                f"продаёт и после резкого роста.")
    st.plotly_chart(line_chart({"Доля акций у модельного фонда": cut_years(vc["exposure"] * 100, 5),
                                "Волатильность S&P за 20 дней": cut_years(vc["vol"], 5)}, units="%",
                               recessions=ui.recessions(), height=280), width="stretch")

with tab_trend:
    rows = []
    for name, key in TREND_ASSETS.items():
        p = ui.load(key).dropna()
        t = F.trend(p).iloc[-1]
        flips = F.trend_flips(p)
        last = float(p.iloc[-1])
        nearest = min(flips.items(), key=lambda kv: abs(kv[1] / last - 1))
        sig = float(t["signal"])
        rows.append({"Актив": name, "Сигнал (−1…+1)": round(sig, 2),
                     "Трендовые фонды": "в покупке" if sig > 0.25 else "в продаже" if sig < -0.25 else "нейтрально",
                     "Ближайший уровень разворота": f"{nearest[1]:,.2f}",
                     "Горизонт": f"{nearest[0]} дн.", "До уровня": f"{(nearest[1] / last - 1) * 100:+.1f}%"})
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.markdown("Сигнал — среднее направлений тренда за месяц, квартал, полгода и год. **Уровень разворота** — цена, "
                "ниже (или выше) которой сменится знак одного из горизонтов, и трендовые фонды начнут "
                "сокращать позицию. Пробой нескольких уровней подряд — момент, когда их продажи складываются.")

with tab_fx:
    usd = ui.load("DTWEXBGS").dropna()
    split = F.month_end_split(spx, usd)
    res = {n: F.study(usd, split[k_], 3) for n, k_ in (("S&P за месяц сильно вырос", "up"),
                                                        ("S&P за месяц упал", "down"))}
    df = pd.DataFrame({n: {"день −1": r.daily.loc[-1, "Средняя, %"], "последний день месяца": r.daily.loc[0, "Средняя, %"],
                           "первые 2 дня нового": F.window_effect(r, 1, 2)[0]} for n, r in res.items()}).T
    mtd = F.period_to_date(spx, "M")
    st.metric("S&P с начала месяца", f"{mtd:+.1f}%",
              "в верхней трети — ждём продажу доллара" if mtd >= split["thresholds"][1] else
              "в нижней трети" if mtd <= split["thresholds"][0] else "в середине — сигнала нет",
              delta_color="off", border=True)
    st.plotly_chart(grouped_bars(df, units="%", height=280), width="stretch")
    eff, t_ = F.window_effect(res["S&P за месяц сильно вырос"], -1, 0)
    st.markdown(f"Иностранцы, которые держат акции США и хеджируют доллар, после роста акций должны **продать "
                f"больше долларов** — хедж пересматривают в конце месяца. На истории: в месяцы сильного роста S&P "
                f"широкий индекс доллара в последние два дня месяца в среднем **{eff:+.2f}%** (t = {t_:.1f}) сверх "
                f"обычного. Это совпадает с исследованием Melvin и Prins (2015) о лондонском фиксинге.")

with tab_q:
    bonds = ui.load("DGS10").dropna()
    bond_q = float((bonds.shift(1) / 252 - 7.5 * bonds.diff())[spx.index[-1].to_period("Q").start_time:].sum())
    gap = F.period_to_date(spx, "Q") - bond_q
    st.metric("Акции минус облигации с начала квартала", f"{gap:+.1f} п.п.",
              "пенсионным фондам продавать акции" if gap > 0 else "пенсионным фондам докупать акции",
              delta_color="off", border=True)
    st.markdown("По правилам фонды должны продать часть того, что обогнало. Но простой тест на истории этого "
                "эффекта **не видит** (раздел 3, пример «Ребалансировка конца квартала»): фонды ребалансируют "
                "заранее и фьючерсами, а другие участники встают перед потоком. Показываем как ориентир направления, "
                "не как сигнал.")

with learn.how_it_works("Как работают эти правила"):
    st.markdown("""
- **Таргет волатильности.** Фонд держит риск постоянным: волатильность выросла вдвое — акций вдвое меньше. Продаёт
  в распродажу и докупает в спокойный рост, усиливая оба. Важно: он реагирует на **уже случившиеся** колебания.
- **Трендовые фонды (CTA).** Покупают то, что росло, и продают то, что падало, на нескольких горизонтах сразу.
  Уровни разворота известны всем — поэтому у них часто «сгущаются» стопы.
- **Хедж валюты.** Иностранец держит акции США на $100 и продал $100 вперёд. Акции выросли до $110 — нужно
  продать ещё $10. Хеджи пересматривают раз в месяц — отсюда давление на доллар в последние дни месяца.
- **Пенсионные фонды** держат доли (например, 60/40) и в конце квартала возвращают их.
""")


def ex_aug2024():
    vc_ = F.vol_control(spx)
    parts = {name: vc_.loc[a:b, "exposure"] * 100 for name, (a, b) in
             {"Февраль 2018": ("2018-01-15", "2018-03-15"), "Март 2020": ("2020-02-01", "2020-04-15"),
              "Август 2024": ("2024-07-10", "2024-09-10")}.items()}
    rows = {n: {"до": float(x.iloc[0]), "минимум": float(x.min())} for n, x in parts.items()}
    st.plotly_chart(grouped_bars(pd.DataFrame(rows).T, units="%", height=280), width="stretch")
    st.markdown(
        "Доля акций у модельного фонда перед тремя распродажами и в их худшей точке. В августе 2024 года волатильность "
        f"S&P за 20 дней выросла примерно вдвое — и модель сократила акции с {rows['Август 2024']['до']:.0f}% до "
        f"{rows['Август 2024']['минимум']:.0f}% капитала. Банк международных расчётов прямо называет фонды с "
        f"таргетом волатильности одним из усилителей того обвала (BIS Bulletin 90). В марте 2020 года модель ушла "
        f"почти в ноль.")


def ex_trend_good():
    tr = F.trend_returns(spx)
    rows = {}
    for name, (a, b) in {"2007–2009": ("2007-10", "2009-03"), "2022": ("2022-01", "2022-10")}.items():
        x = tr[a:b]
        rows[name] = {"Тренд": (np.exp(x["trend"].sum()) - 1) * 100, "Просто держать S&P": (np.exp(x["hold"].sum()) - 1) * 100}
    st.plotly_chart(grouped_bars(pd.DataFrame(rows).T, units="%", height=280), width="stretch")
    full = tr["1990":]
    dd = lambda x: float((np.exp(x.cumsum()) / np.exp(x.cumsum()).cummax()).min() * 100 - 100)
    st.markdown(
        f"В долгих распродажах тренд успевает развернуться и зарабатывает на падении. На всём периоде с 1990 года "
        f"модель на S&P даёт меньшую доходность, чем просто держать индекс "
        f"({full['trend'].mean() * 252 * 100:.1f}% против {full['hold'].mean() * 252 * 100:.1f}% в год), но худшая "
        f"просадка — {dd(full['trend']):.0f}% против {dd(full['hold']):.0f}%. Это и есть роль тренда — страховка в "
        f"затяжной кризис (Moskowitz, Ooi и Pedersen, 2012).")


def ex_trend_bad():
    tr = F.trend_returns(spx)
    rows = {}
    for name, (a, b) in {"Февраль–апрель 2018": ("2018-01-26", "2018-04-30"),
                         "Март–апрель 2020": ("2020-02-19", "2020-04-30")}.items():
        x = tr[a:b]
        rows[name] = {"Тренд": (np.exp(x["trend"].sum()) - 1) * 100, "Просто держать S&P": (np.exp(x["hold"].sum()) - 1) * 100}
    st.plotly_chart(grouped_bars(pd.DataFrame(rows).T, units="%", height=280), width="stretch")
    st.markdown("Резкий обвал и такой же быстрый отскок — худший сценарий для тренда: он продаёт уже внизу и "
                "откупает уже наверху. В 2018 году модель потеряла больше, чем рынок.")


def ex_vol_after():
    vc_ = F.vol_control(spx)["exposure"]
    ch = vc_.diff(5)["1990":]
    ev_ = ch[ch <= ch.quantile(0.05)]
    keep, last = [], None
    for d in ev_.index:
        if last is None or (d - last).days >= 10:
            keep.append(d)
            last = d
    s_ = F.study(spx["1990":], keep, 10)
    k_ = pd.Index(s_.days)
    st.plotly_chart(band_chart({"S&P вокруг сильных продаж модели": pd.Series(s_.path, index=k_)},
                               (pd.Series(s_.lo, index=k_), pd.Series(s_.hi, index=k_), "95% интервал"), height=300),
                    width="stretch")
    after, t_a = F.window_effect(s_, 1, 5)
    st.markdown(
        f"{s_.n} эпизодов, когда модель за неделю сократила акции сильнее всего. Продажи идут **вместе** с падением "
        f"(дни до нуля), но дальнейшего падения не предсказывают: за 5 дней после — {after:+.2f}% (t = {t_a:.1f}). "
        f"Фонды с таргетом волатильности усиливают распродажу, пока она идёт, — но к моменту, когда модель «продала», "
        f"основной удар уже случился.")


learn.examples([Example("Таргет волатильности в распродажах 2018, 2020, 2024", ex_aug2024),
                Example("Тренд в долгих распродажах: 2008 и 2022", ex_trend_good),
                Example("Резкий разворот: тренд проигрывает", ex_trend_bad, normal=False),
                Example("Продажи модели не предсказывают дальнейшего падения", ex_vol_after, normal=False)],
               key="models")

# ---------- 5. позиционирование ----------
st.header("5. Кто уже в рынке и с каким плечом")
st.markdown("Вынужденный поток тем сильнее, чем больше **уже накоплено** позиций в одну сторону: перегруженную "
            "позицию закрывают все разом. Позиции видны с задержкой — по отчётам CFTC о фьючерсах (раз в неделю) и "
            "по маржинальному долгу клиентов брокеров (раз в месяц).")
learn.tags("совпадающий", "спорный")
rows = []
for key_, (name_, _) in F.COT.items():
    lev, am = ui.load(f"COT_{key_}_LEV").dropna(), ui.load(f"COT_{key_}_AM").dropna()
    zl, za = F.zscore(lev), F.zscore(am)
    rows.append({"Фьючерс": name_, "Фонды с плечом, % ОИ": round(float(lev.iloc[-1]), 1),
                 "отклонение от нормы (z)": round(float(zl.iloc[-1]), 1),
                 "за 4 недели, п.п.": round(float(lev.iloc[-1] - lev.iloc[-5]), 1),
                 "Управляющие активами, % ОИ": round(float(am.iloc[-1]), 1), "z ": round(float(za.iloc[-1]), 1)})
st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
st.caption(f"CFTC, отчёт Traders in Financial Futures за {ui.load('COT_ES_LEV').dropna().index[-1]:%d.%m.%Y}. % ОИ — "
           "чистая позиция (лонг − шорт) в процентах открытого интереса. z — отклонение от средней за 3 года: |z| ≥ 2 "
           "— позиция необычно перегружена.")
pick = st.selectbox("Фьючерс", list(F.COT), format_func=lambda k: F.COT[k][0], key="fl_cot")
st.plotly_chart(line_chart({"Фонды с плечом": cut_years(ui.load(f"COT_{pick}_LEV").dropna(), 10),
                            "Управляющие активами": cut_years(ui.load(f"COT_{pick}_AM").dropna(), 10)}, units="%",
                           recessions=ui.recessions(), zero_line=True, height=300), width="stretch")

margin = ui.load("FINRA_MARGIN").dropna()
mg = yoy_pct(margin).dropna()
k = st.columns(2)
k[0].metric("Маржинальный долг (FINRA)", f"${margin.iloc[-1] / 1e6:.2f} трлн", f"{mg.iloc[-1]:+.0f}% за год",
            delta_color="off", border=True, help=f"Данные за {margin.index[-1]:%m.%Y}.")
k[1].metric("Рост быстрее, чем в", f"{(mg < mg.iloc[-1]).mean() * 100:.0f}% месяцев", "с 1998 года",
            delta_color="off", border=True)
spx_m = spx.resample("MS").last()
st.plotly_chart(line_chart({"Маржинальный долг, г/г": cut_years(mg, 30),
                            "S&P 500, г/г": cut_years(yoy_pct(spx_m).dropna(), 30)}, units="%",
                           recessions=ui.recessions(), zero_line=True, height=300), width="stretch")
with learn.how_it_works():
    st.markdown("""
- **Кто есть кто в отчёте CFTC.** *Управляющие активами* — пенсионные, страховые, паевые фонды: медленные деньги,
  обычно в лонге. *Фонды с плечом* — хедж-фонды и трендовые фонды: быстрые деньги, именно их закрытие позиций и
  создаёт резкие движения.
- **Шорт ≠ ставка на падение.** Большой шорт фондов с плечом в S&P и казначейских облигациях — в основном
  **базисный арбитраж**: шорт фьючерса против покупки самих бумаг. Поэтому смотрим не на уровень, а на отклонение
  от нормы (z).
- **Позиция — это топливо, а не спусковой крючок.** Перегруженная позиция показывает, насколько сильным будет
  движение, **если** что-то его запустит, — но не когда.
- **Маржинальный долг** — плечо частных инвесторов. Быстрый рост — плечо копится; при падении рынка — маржин-коллы.
""")


def ex_yen():
    lev = ui.load("COT_JY_LEV").dropna()["2024-03":"2024-10"]
    yen = (1 / ui.load("DEXJPUS").dropna())["2024-03":"2024-10"] * 100
    st.plotly_chart(dual_axis_chart(("Фонды с плечом в иене, % ОИ", lev, "%"), ("Иена, центов за 100 иен", yen, "")),
                    width="stretch")
    st.markdown(
        f"К концу июня 2024 года фонды с плечом держали шорт иены на {-lev.min():.0f}% открытого интереса — иена была "
        f"главной валютой фондирования керри-трейда. После повышения ставки Банком Японии 31 июля шорт закрыли за "
        f"пару недель почти до нуля ({-lev['2024-08-13']:.0f}%). Это вынужденная покупка иены — она разогнала её "
        f"укрепление и распродажу по всему миру 5 августа.")


def ex_margin():
    fwd = (spx_m.shift(-12) / spx_m - 1) * 100
    d = pd.concat({"g": mg, "fwd": fwd}, axis=1, sort=True).dropna()
    d["Рост маржинального долга за год"] = pd.qcut(d["g"], 4, labels=["нижняя четверть", "2-я", "3-я",
                                                                      "верхняя четверть"])
    t = d.groupby("Рост маржинального долга за год", observed=True)["fwd"].agg(["mean", "median"])
    t.columns = ["S&P за следующие 12 мес., среднее", "медиана"]
    st.plotly_chart(grouped_bars(t, units="%", height=280), width="stretch")
    hot = sorted(set(mg[mg >= 35].index.year))
    st.markdown(
        f"Когда маржинальный долг растёт быстрее всего, следующий год для S&P в среднем слабее. Рост больше 35% за год "
        f"был в {', '.join(map(str, hot))} годах — рядом с вершинами 2000, 2007 и 2021 годов, но иногда за год и "
        f"больше до них. Это предупреждение о накопленном плече, а не сигнал момента: окна по 12 месяцев "
        f"перекрываются, и независимых наблюдений здесь немного.")


def ex_cot_noise():
    rows_ = []
    for key_, (name_, _) in F.COT.items():
        for g, gname in (("LEV", "фонды с плечом"), ("AM", "управляющие")):
            for side, sname in ((1, "крайний лонг"), (-1, "крайний шорт")):
                try:
                    s_ = F.extremes_study(ui.load, key_, g, side)
                except ValueError:
                    continue
                e, t = F.window_effect(s_, 1, 20)
                rows_.append({"Фьючерс": name_, "Группа": gname, "Позиция": sname, "Случаев": s_.n,
                              "Цена за 20 дней после, %": round(e, 2), "t": round(t, 1)})
    df_ = pd.DataFrame(rows_)
    st.dataframe(df_, hide_index=True, width="stretch")
    st.markdown(
        f"Крайние позиции (|z| ≥ 1,5) по всем фьючерсам и группам: ни в одном случае |t| не достигает 2 "
        f"(максимум {df_['t'].abs().max():.1f}). На горизонте месяца перегруженность сама по себе не предсказывает "
        f"цену — разворот случается, только когда приходит триггер (решение ЦБ, шок, маржин-колл). Используйте "
        f"позиционирование как оценку силы возможного движения, а не его направления.")


learn.examples([Example("Иена, 2024: фонды закрывают шорт", ex_yen),
                Example("Маржинальный долг перед вершинами", ex_margin),
                Example("Крайние позиции не предсказывают месяц вперёд", ex_cot_noise, normal=False)],
               key="positions")

# ---------- 6. Мосбиржа: физлица и юрлица ----------
st.header("6. Мосбиржа: физлица против юрлиц")
st.markdown("Мосбиржа каждый день публикует позиции **физлиц** и **юрлиц** во фьючерсах. Сумма их позиций всегда "
            "ноль: если физлица в лонге, юрлица ровно на столько же в шорте. Поэтому смотрим только на физлиц — на то, "
            "насколько их позиция отличается от обычной и как она меняется.")
learn.tags("совпадающий", "проверен на истории")
wk_rts = F.moex_weekly(ui.load, "RTS")
c_rts = float(wk_rts["pos"].corr(wk_rts["same"]))
rows = []
for a, (name_, pk, _) in F.MOEX.items():
    x = ui.load(f"MOEX_{a}_IND").dropna()
    rows.append({"Фьючерс": name_, "Физлица, % ОИ": round(float(x.iloc[-1]), 1),
                 "отклонение от нормы (z)": round(float(F.zscore_daily(x).iloc[-1]), 1),
                 "за 20 дней, п.п.": round(float(x.iloc[-1] - x.iloc[-21]), 1),
                 "Физлиц в лонге, % людей": round(float(ui.load(f"MOEX_{a}_PERSONS").dropna().iloc[-1]))})
learn.takeaway(f"Физлица на Мосбирже торгуют против движения: когда индекс РТС падает, они докупают фьючерс "
               f"(связь за неделю {c_rts:+.2f}). Двигают цену юрлица, а физлица дают им ликвидность. Предсказать "
               f"курс или индекс по крайним позициям физлиц не получается: проверка ниже.")
st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
st.caption(f"Мосбиржа через trade-news, данные за {ui.load('MOEX_Si_IND').dropna().index[-1]:%d.%m.%Y}. % ОИ — "
           "чистая позиция физлиц (лонг − шорт) в процентах открытого интереса. z — отклонение от средней за год. "
           "«Физлиц в лонге» — доля людей, а не денег: сколько из открытых счетов ставят на рост.")
pick_m = st.selectbox("Фьючерс", list(F.MOEX), format_func=lambda k: F.MOEX[k][0], key="fl_moex")
name_m, pk_m, what_m = F.MOEX[pick_m]
st.plotly_chart(dual_axis_chart(("Физлица, % ОИ", ui.load(f"MOEX_{pick_m}_IND").dropna(), "%"),
                                (what_m.capitalize(), ui.load(pk_m).dropna()["2021":], "")), width="stretch")
with learn.how_it_works():
    st.markdown("""
- **Кто есть кто.** *Физлица* — частные инвесторы, обычно с небольшими счетами. *Юрлица* — банки, фонды,
  брокеры и компании, в том числе экспортёры и импортёры, которые страхуют валютную выручку и платежи.
- **Почему физлица против движения.** Частный инвестор чаще покупает подешевевшее («отскочит») и продаёт
  подорожавшее. Юрлица, наоборот, двигаются вместе с ценой: хеджи, стоп-лоссы, потоки клиентов. Это не значит,
  что физлица всегда проигрывают, — они берут на себя риск, который юрлица сбрасывают.
- **Когда это становится вынужденным потоком.** Физлица торгуют с плечом. Если цена долго идёт против них,
  брокер закрывает позиции принудительно — и эти продажи (или покупки) ускоряют движение.
- **Ограничения.** Курс доллара — официальный курс ЦБ: биржевые торги долларом остановлены в июне 2024 года.
  История — с 2021 года (юань — с апреля 2022), поэтому крайних случаев немного.
""")


def ex_moex_contra():
    t = pd.DataFrame({name_: {per: round(float(w.loc[per]["pos"].corr(w.loc[per]["same"])), 2)
                              for per in ("2021–2023", "2024–2026")}
                      for a, (name_, _, _) in F.MOEX.items()
                      for w in [F.moex_weekly(ui.load, a).rename(index=lambda d: "2021–2023" if d.year <= 2023
                                                                  else "2024–2026")]}).T
    st.plotly_chart(grouped_bars(t, height=280), width="stretch")
    st.markdown(
        f"Связь между изменением позиции физлиц и движением цены за ту же неделю. Отрицательная — физлица действуют "
        f"против цены. В индексе РТС она сильная и одинаковая в обоих периодах ({t.iloc[1, 0]:+.2f} и "
        f"{t.iloc[1, 1]:+.2f}), в долларе слабее ({t.iloc[0, 0]:+.2f} и {t.iloc[0, 1]:+.2f}): курс ЦБ двигают "
        f"не фьючерсы, а потоки экспортёров и импортёров. Неделя за неделей — {len(F.moex_weekly(ui.load, 'RTS'))} "
        f"независимых наблюдений по РТС, это не случайность.")


def ex_moex_noise():
    rows_ = []
    for a, (name_, _, what) in F.MOEX.items():
        for side, sname in ((1, "крайний лонг"), (-1, "крайний шорт")):
            try:
                s_ = F.moex_extremes_study(ui.load, a, side)
            except ValueError:
                continue
            e5, t5 = F.window_effect(s_, 1, 5)
            e, t = F.window_effect(s_, 1, 20)
            rows_.append({"Фьючерс": name_, "Позиция физлиц": sname, "Случаев": s_.n,
                          "Цена за 5 дней после, %": round(e5, 2), "t (5 дней)": round(t5, 1),
                          "за 20 дней, %": round(e, 2), "t (20 дней)": round(t, 1)})
    df_ = pd.DataFrame(rows_)
    st.dataframe(df_, hide_index=True, width="stretch")
    nxt = {F.MOEX[a][0]: round(float(w["pos"].corr(w["next"])), 2)
           for a in F.MOEX for w in [F.moex_weekly(ui.load, a)]}
    st.markdown(
        f"Крайние позиции физлиц (|z| ≥ 1,5) за 20 дней: максимум |t| = {df_['t (20 дней)'].abs().max():.1f}, "
        f"случаев по {df_['Случаев'].min()}–{df_['Случаев'].max()}. Пара значений с |t| около 2 при "
        f"{2 * len(df_)} проверках — столько и выпадает случайно. Изменение позиции за неделю тоже не подсказывает "
        f"следующую неделю: связь {', '.join(f'{k} {v:+.2f}' for k, v in nxt.items())}. По юаню она заметна в "
        f"2022–2023 годах и пропадает позже. Позиции физлиц показывают, кто держит риск, но не куда пойдёт цена.")


learn.examples([Example("Физлица покупают падение", ex_moex_contra),
                Example("Крайние позиции физлиц не предсказывают цену", ex_moex_noise, normal=False)],
               key="moex")

learn.next_steps([7, 4], "Вынужденные потоки ускоряют любое звено цепочки, но сильнее всего видны в ценах активов "
                         "(слой 7) и в финансовых условиях (слой 4): распродажа по марже сама ужесточает условия.")
