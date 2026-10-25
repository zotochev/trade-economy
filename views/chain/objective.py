"""Торговля: целевая функция — какой трейдер вы (самодиагностика → профиль → рекомендации) и как выглядят кривые
капитала при разном риске на сделку, вплоть до Келли."""
import pandas as pd
import streamlit as st

from core import learn, trading
from core.charts import line_chart


@st.cache_data(show_spinner="Моделирую кривые капитала…")
def run(p_win: float, rr: float, per_month: int, months: int):
    """rr — уже с учётом трения; риск — полный убыток сделки вместе с трением."""
    n = per_month * months
    k = trading.kelly(p_win, rr)
    plans = {"0,5%": 0.005, "1%": 0.01, "2%": 0.02}
    if k > 0:
        plans |= {f"½ Келли ({k / 2:.1%})": k / 2, f"Келли ({k:.1%})": k}
    rows, curves = {}, {}
    for name, r in plans.items():
        eq = trading.simulate(p_win, rr, r, n)
        rows[name] = trading.stats(eq, per_month)
        curves[name] = trading.bands(eq, per_month)
    return pd.DataFrame(rows).T, curves


@st.cache_data(show_spinner=False)
def overestimate(p_true: float, p_think: float, rr: float, n: int, per_month: int) -> pd.DataFrame:
    """Размер считали по завышенной доле удачных, а рынок дал настоящую."""
    k = trading.kelly(p_think, rr)
    rows = {}
    for name, r in {"1%": 0.01, f"½ Келли по оценке ({k / 2:.1%})": k / 2, f"Келли по оценке ({k:.1%})": k}.items():
        rows[name] = trading.stats(trading.simulate(p_true, rr, r, n, seed=1), per_month)
    return pd.DataFrame(rows).T


st.title("Целевая функция")
st.markdown("«Заработать денег» — бесполезная цель: она ничего не говорит о том, как торговать. У каждого своя "
            "**целевая функция** — что именно вы максимизируете и какую боль готовы терпеть. От неё зависят стиль, "
            "частота сделок, риск на сделку и цель в R. Ответьте на четыре вопроса — ниже профиль и то, как будет "
            "выглядеть ваш счёт.")

# ---------- 1. самодиагностика ----------
st.header("1. Какой вы трейдер")
c = st.columns(2)
answers = [c[i % 2].radio(q, list(opts), key=f"q{i}") for i, (q, opts) in enumerate(trading.QUESTIONS)]
score = trading.diagnose(answers)
best = max(score, key=score.get)
P = trading.PROFILES
pk = st.segmented_control("Профиль", list(P), default=best, format_func=lambda k: P[k].title, key=f"prof_{best}",
                          help="По ответам выбран ближайший профиль; можно посмотреть и другие.") or best
pr = P[pk]
learn.takeaway(f"{pr.title}. {pr.essence}", "good" if pk == best else "neutral")
if pk != best:
    st.caption(f"По вашим ответам ближе профиль «{P[best].title}».")
c = st.columns(4)
c[0].metric("Стиль", pr.style.split(":")[0], border=True, help=pr.style)
c[1].metric("Частота", pr.freq, border=True)
c[2].metric("Риск на сделку", pr.risk, border=True)
c[3].metric("Цель", pr.target, border=True, help="R — сколько вы рискуете в сделке (расстояние до стопа × размер).")
st.markdown(f"**Стиль:** {pr.style}.  \n⚠️ {pr.warning}")

# ---------- 2. кривые капитала ----------
st.header("2. Как будет выглядеть счёт")
st.markdown("Модель: сделки независимы, каждая либо приносит R × риск, либо теряет риск. Значения по умолчанию — "
            "типичные для профиля; подставьте свои.")
c = st.columns(4)
win = c[0].slider("Доля удачных сделок", 0.2, 0.7, pr.p_win, 0.01, key=f"w_{pk}", format="%.2f")
rr = c[1].slider("Прибыль к риску (R)", 0.5, 10.0, pr.rr, 0.1, key=f"r_{pk}")
per_month = c[2].slider("Сделок в месяц", 1, 40, pr.per_month, key=f"n_{pk}")
months = c[3].select_slider("Горизонт, мес", [6, 12, 24, 36], value=12, key="period")
cost = st.select_slider("Трение на сделку (комиссии, проскальзывание, фандинг), доля R", [0.0, 0.05, 0.1, 0.2],
                        value=0.05, key="cost", help="0,05 R при стопе 2% от цены — это 0,1% цены на круг: "
                                                     "типичные комиссии и проскальзывание на фьючерсах BTC.")
ex = win * (rr - cost) - (1 - win) * (1 + cost)
rr_eff = trading.with_cost(rr, cost)
k = trading.kelly(win, rr_eff)
c = st.columns(3)
c[0].metric("Ожидание на сделку", f"{ex:+.2f} R", border=True,
            help="Доля удачных × R − доля неудачных, минус трение. Меньше нуля — стратегия теряет при любом размере.")
c[1].metric("Келли", f"{k:.1%} счёта" if k > 0 else "0", border=True,
            help="f* = p − (1 − p) / R: риск на сделку, при котором счёт растёт быстрее всего в долгую. Больше Келли — "
                 "рост падает, а просадки растут.")
c[2].metric("Сделок за горизонт", per_month * months, border=True)
if ex <= 0:
    learn.takeaway("Преимущества нет: ожидание не выше нуля, и по Келли оптимальная ставка — ноль. Никакой размер "
                   "позиции это не исправит.", "bad")
else:
    table, curves = run(win, rr_eff, per_month, months)
    pick = st.radio("Риск на сделку", list(curves), index=1, horizontal=True, key="risk_pick")
    s = table.loc[pick]
    kelly_row = table.index[-1]
    tk = table.loc[kelly_row]
    learn.takeaway(f"При риске {pick} половина вариантов закончит {months} мес. с результатом "
                   f"{trading.fmt_pct(s.iloc[0])} или лучше, худшие 5% — {trading.fmt_pct(s.iloc[1])}. Типичная просадка по пути — "
                   f"{s.iloc[2]:.0f}%, подряд под водой — около {s.iloc[4]:.1f} мес.",
                   "warn" if s.iloc[5] > 20 else "good")
    st.plotly_chart(line_chart({k_: v for k_, v in curves[pick].items()}, units="% к старту", zero_line=True,
                               height=300), width="stretch")
    st.caption("Коридор 2000 смоделированных вариантов истории; по оси — месяцы.")
    fmt = {col: trading.fmt_pct if "Итог" in col else "{:.1f}" if "мес" in col else "{:.0f}" for col in table.columns}
    st.dataframe(table.style.format(fmt), width="stretch")
    st.caption(f"Полный Келли даёт медиану {trading.fmt_pct(tk.iloc[0])}, но типичную просадку {tk.iloc[2]:.0f}% — "
               "мало кто выдерживает такой путь психологически. Половина Келли — обычный компромисс.")

with learn.how_it_works():
    st.markdown("""
- **Ожидание решает «можно ли», размер — «как быстро и как больно».** Если ожидание ≤ 0, выигрыша нет ни при каком
  риске. Если > 0, риск на сделку меняет скорость роста и глубину просадок.
- **Келли — потолок, а не цель.** При риске больше Келли рост в долгую *падает*, при двух Келли — счёт в среднем
  стоит на месте при огромных колебаниях. Поэтому берут ½ Келли и меньше.
- **Преимущество всегда оценка.** Доля удачных, посчитанная на 30–50 сделках, легко ошибается на 10 п.п. Ниже видно,
  что будет, если её завысить.
- **Модель оптимистична.** Сделки в ней независимы; на деле ошибки идут пачками в неудобном режиме рынка, а комиссии,
  проскальзывание и фандинг съедают часть R. Реальные просадки — глубже.
- **Профиль задаёт допустимую боль.** Гладкости нужен малый риск и много сделок; матожиданию — буфер на серии
  убытков; часу внимания — сделки, которые не требуют экрана; сложному проценту — точное знание своего преимущества.
""")

# ---------- 3. когда ломается ----------
if ex > 0 and win - 0.1 > 0:
    st.header("3. Когда это ломается: преимущество завысили")
    p_true = round(win - 0.1, 2)
    st.markdown(f"Вы думаете, что удачных {win:.0%}, а на деле {p_true:.0%}. Размер посчитан по оценке, рынок играет "
                f"по правде. Настоящее ожидание — {p_true * (rr - cost) - (1 - p_true) * (1 + cost):+.2f} R.")
    bad = overestimate(p_true, win, rr_eff, per_month * months, per_month)
    st.dataframe(bad.style.format({col: trading.fmt_pct if "Итог" in col else "{:.1f}" if "мес" in col else "{:.0f}"
                                   for col in bad.columns}), width="stretch")
    st.caption("Риск 1% переживает ошибку оценки, полный Келли по завышенной оценке — обычно нет. Отсюда правило: "
               "при нулевом или неизвестном преимуществе оптимальная ставка — ноль.")
learn.help_link()
