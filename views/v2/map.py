"""Карта: экономика как цепочка передачи импульса — семь слоёв от структуры до цен активов.

У каждого слоя — не вопрос, а ответ на него по текущим данным и числа, из которых ответ следует.
"""
import pandas as pd
import streamlit as st

from core import learn, ui
from core.transforms import yoy_pct

# Как импульс передаётся от слоя к следующему: (что передаётся, типичный лаг)
LINKS = {
    1: ("задаёт «нейтральную» ставку и потолок роста", "годы"),
    2: ("рынок пересчитывает ожидания по ставкам", "дни"),
    3: ("ставки становятся ценой кредита, акций, жилья, доллара", "дни – недели"),
    4: ("дорогие или дешёвые деньги меняют расходы и найм", "6–18 мес."),
    5: ("загрузка экономики разгоняет или гасит цены", "6–24 мес."),
    6: ("инфляция и занятость возвращаются в решения ФРС (слой 2) и в цены активов", "сразу – кварталы"),
}
ICON = {"green": "🟢", "red": "🔴", "orange": "🟠", "blue": "🔵", "gray": "⚪"}


def ago(s: pd.Series, months: int) -> float:
    return float(s[:s.index[-1] - pd.DateOffset(months=months)].iloc[-1])


def answer(num: int) -> tuple[str, str, str]:
    """Ответ слоя на его вопрос: (вывод одной фразой, числа-обоснование, цвет)."""
    if num == 1:
        gdp = ui.load("GDP")
        debt = ui.load("GFDEGDQ188S")
        rate = (ui.load("A091RC1Q027SBEA") / (debt / 100 * gdp) * 100).dropna()
        g = yoy_pct(gdp).dropna()
        gap = float(rate.iloc[-1] - g.iloc[-1])
        head = ("Долг дешевле роста: экономика сама «перерастает» долг" if gap < 0 else
                "Долг дороже роста: долговая нагрузка растёт сама по себе")
        return (head, f"Госдолг {debt.iloc[-1]:.0f}% ВВП. Средняя ставка по долгу {rate.iloc[-1]:.1f}% против "
                      f"роста номинального ВВП {g.iloc[-1]:.1f}% (r − g = {gap:+.1f} п.п.).",
                "green" if gap < 0 else "orange")
    if num == 2:
        ffr = float(ui.load("DFF").iloc[-1])
        core = float(yoy_pct(ui.load("PCEPILFE")).dropna().iloc[-1])
        real = ffr - core
        if real > 2:
            head, color = "ФРС тормозит экономику", "red"
        elif real < 0.5:
            head, color = "ФРС разгоняет экономику", "green"
        else:
            head, color = "ФРС держит ставку около нейтральной — ни тормозит, ни разгоняет", "gray"
        return (head, f"Реальная ставка {real:+.1f}% = ставка {ffr:.2f}% − базовая инфляция {core:.1f}%. "
                      f"Нейтральной считают ≈ 0,5–2%, оценки сильно расходятся.", color)
    if num == 3:
        y10 = float(ui.load("DGS10").iloc[-1])
        tp = float(ui.load("THREEFYTP10").iloc[-1])
        slope = float(ui.load("T10Y3M").iloc[-1])
        if slope < 0:
            head, color = "Рынок ждёт снижения ставок: длинные ставки ниже коротких", "orange"
        elif tp > 0.5:
            head, color = "Рынок требует доплату за длинный долг: длинные ставки высоки из-за премии за риск", "orange"
        else:
            head, color = "Рынок ждёт ставки примерно на нынешнем уровне: кривая нормальная", "gray"
        return (head, f"10-летние {y10:.2f}%, из них премия за срок ≈ {tp:+.2f} п.п. (модель Кима–Райта). "
                      f"Наклон 10 лет − 3 мес.: {slope:+.2f} п.п.", color)
    if num == 4:
        imp = -float(ui.load("FCIG").iloc[-1])
        prob = float(ui.load("ebp_prob").iloc[-1])
        if imp > 0.25:
            head, color = "Деньги доступны и дёшевы — финансовые условия помогают росту", "green"
        elif imp < -0.25:
            head, color = "Деньги дороги — финансовые условия тормозят рост", "red"
        else:
            head, color = "Финансовые условия почти нейтральны для роста", "gray"
        return (head, f"Вклад в рост ВВП за год {imp:+.1f} п.п. (FCI-G). Риск рецессии по кредитному рынку "
                      f"{prob:.0f}%.", color)
    if num == 5:
        cp = float(ui.load("RECPROUSM156N").iloc[-1])
        sahm = float(ui.load("SAHMREALTIME").iloc[-1])
        bad = cp > 30 or sahm >= 0.5
        head = ("Экономика, похоже, входит в спад" if bad else "Спада не видно: экономика растёт")
        return (head, f"Вероятность, что рецессия уже идёт, — {cp:.0f}% (модель Шове–Пигера). "
                      f"Правило Сама {sahm:.2f} (тревога от 0,5).", "red" if bad else "green")
    if num == 6:
        core = yoy_pct(ui.load("PCEPILFE")).dropna()
        now, year = float(core.iloc[-1]), ago(core, 12)
        trend = "снижается" if now < year - 0.2 else "растёт" if now > year + 0.2 else "стоит на месте"
        if now > 2.5:
            head, color = f"Инфляция выше цели ФРС и {trend}", "orange"
        elif now < 1.5:
            head, color = f"Инфляция ниже цели ФРС и {trend}", "blue"
        else:
            head, color = "Инфляция у цели ФРС", "green"
        return (head, f"Базовая инфляция PCE {now:.1f}% г/г (цель 2%), год назад {year:.1f}%.", color)
    cape = ui.load("CAPE").dropna()
    spx = ui.load("^GSPC")
    above = float(spx.iloc[-1]) > float(spx.rolling(200).mean().iloc[-1])
    rich = cape.iloc[-1] > 30
    head = (("Акции дороги" if rich else "Акции оценены умеренно") + ", тренд " +
            ("восходящий" if above else "нисходящий"))
    return (head, f"Shiller CAPE {cape.iloc[-1]:.1f} при среднем за историю {cape.mean():.0f}. S&P 500 "
                  f"{'выше' if above else 'ниже'} 200-дневной средней.", "orange" if rich else "gray")


st.title("Карта экономики")
st.markdown("Экономика — не набор отдельных показателей, а **цепочка**: решение на одном уровне с задержкой "
            "передаётся на следующий. Читайте сверху вниз: где сейчас возник импульс и докуда он уже дошёл.")

with learn.how_it_works("Как читать карту"):
    st.markdown("""
- **Сверху — медленное, снизу — быстрое.** Структура экономики меняется годами, цены активов — каждую секунду.
- **У каждого слоя — ответ на его вопрос по свежим данным** и числа, из которых этот ответ следует.
  Это не прогноз и не совет, а подсказка, куда смотреть.
- **Стрелка между слоями** — что передаётся дальше и примерно за какое время. Лаги «долгие и переменчивые»:
  иногда импульс доходит за полгода, иногда за два.
- **Обратная связь.** Цепочка замкнута: инфляция и занятость возвращаются в решения ФРС, а цены акций и жилья —
  в финансовые условия (богатые семьи тратят больше).
- Слои, у которых пока нет своего экрана, ведут на старые экраны.
""")

for layer in learn.LAYERS:
    with st.container(border=True):
        left, right = st.columns([5, 1], vertical_alignment="center")
        with left:
            st.caption(f"Слой {layer.num} · {layer.title}")
            try:
                head, why, color = answer(layer.num)
                st.markdown(f"#### {ICON[color]} {head}")
                st.markdown(why)
            except Exception as e:  # один недоступный ряд не должен гасить всю карту
                st.warning(f"Нет данных: {e}")
        with right:
            if layer.page:
                st.page_link(layer.page, label="Открыть слой", icon="➡️")
            elif layer.old_page:
                st.page_link(layer.old_page, label="Пока: старый экран", icon="↗️")
    if layer.num in LINKS:
        what, lag = LINKS[layer.num]
        st.markdown(f"<div style='text-align:center;opacity:.75'>⬇️ {what} · <b>{lag}</b></div>",
                    unsafe_allow_html=True)
