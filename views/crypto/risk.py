"""Крипта, блок 9. Риск-менеджмент и устройство торгов: как перевести модель в решения — размер позиции от стопа,
асимметрия потерь, серии убытков, опасные дни и события."""
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from core import crypto, flows, learn, ui
from core.charts import line_chart
from core.learn import Example

HORIZONS = {"за день": 1, "за неделю": 7, "за месяц": 30}
EVENT_TYPES = {"cb_meeting": "Заседание центробанка", "opex_monthly": "Экспирация опционов", "month_end": "Конец месяца",
               "quarter_end": "Конец квартала", "vix_expiry": "Экспирация VIX", "index_rebalance": "Ребалансировка индексов"}


@st.cache_data(ttl=3600, show_spinner=False)
def streak_table(p_win: float) -> pd.DataFrame:
    return pd.DataFrame({f"{k} подряд": [crypto.max_streak_odds(p_win, n, k) for n in (20, 50, 100)]
                         for k in (3, 5, 7, 10)}, index=["за 20 сделок", "за 50 сделок", "за 100 сделок"])


@st.cache_data(ttl=3600, show_spinner=False)
def events():
    try:
        ev = flows.calendar(date.today(), date.today() + timedelta(days=30))
    except Exception:
        return None
    return [e for e in ev if e["type"] in EVENT_TYPES]


def usd(x: float) -> str:
    return f"${x:,.0f}".replace(",", " ")


# ---------- данные ----------
df = crypto.candles(ui.load)
price = float(ui.load("BTC-USD").dropna().iloc[-1])
wd = crypto.weekday_stats(ui.load)
worst_col = wd.columns[1]
fri_mon = int(wd.loc[["Пт", "Пн"], worst_col].sum())
weekend = int(wd.loc[["Сб", "Вс"], worst_col].sum())
total_worst = int(wd[worst_col].sum())

# ---------- шапка ----------
learn.crypto_header(crypto.BY_NUM[9], len(crypto.BLOCKS),
                    "Все блоки выше объясняют рынок. Этот — про вас: как поставить так, чтобы ошибка стоила "
                    "заранее известную сумму, а серия ошибок не уничтожила счёт. Профессионалы ошибаются часто — "
                    "они выживают за счёт размера позиции, а не за счёт угадывания.")

learn.takeaway(f"Правило одной строки: решите, сколько готовы потерять в сделке (обычно 0,5–2% счёта), поставьте стоп "
               f"там, где идея перестаёт быть верной, и только из этого посчитайте размер позиции. Даже при половине "
               f"удачных сделок 5 убытков подряд за сотню сделок случаются в {crypto.max_streak_odds(0.5, 100, 5):.0f}% "
               f"случаев — счёт должен это пережить.", "neutral")

# ---------- 1. калькулятор ----------
st.header("1. Размер позиции от стопа")
st.markdown("Сначала — где стоп и сколько вы готовы потерять. Размер позиции — следствие. Плечо — тоже следствие: оно "
            "нужно, только если позиция больше счёта.")
c = st.columns(4)
acc = c[0].number_input("Счёт, $", min_value=100.0, value=10_000.0, step=500.0, key="rm_acc")
risk = c[1].select_slider("Готов потерять за сделку, % счёта", [0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0], value=1.0,
                          key="rm_risk")
stop = c[2].select_slider("Стоп от цены входа, %", [1, 2, 3, 5, 7, 10, 15, 20], value=5, key="rm_stop")
side = c[3].segmented_control("Позиция", ["лонг", "шорт"], default="лонг", key="rm_side") or "лонг"
pos = crypto.position(acc, risk, stop)
stop_price = price * (1 - stop / 100) if side == "лонг" else price * (1 + stop / 100)
move = crypto.adverse_move(df, 7, "long" if side == "лонг" else "short")
hit_week = float((move >= stop).mean() * 100)
c = st.columns(4)
c[0].metric("Размер позиции", f"${pos['size']:,.0f}".replace(",", " "), f"{pos['size'] / price:.4f} BTC",
            delta_color="off", border=True)
c[1].metric("Убыток при стопе", f"${pos['risk']:,.0f}".replace(",", " "), f"стоп ${stop_price:,.0f}".replace(",", " "),
            delta_color="off", border=True)
c[2].metric("Нужное плечо", "без плеча" if pos["lev"] <= 1 else f"{pos['lev']:.1f}x",
            "позиция меньше счёта" if pos["lev"] <= 1 else "позиция / счёт", delta_color="off", border=True)
c[3].metric("Стоп выбило бы за неделю", f"{hit_week:.0f}%", "дней с 2017 года", delta_color="off", border=True,
            help="Как часто цена за 7 дней уходила против позиции на расстояние стопа — даже если потом шла в нужную "
                 "сторону.")
if pos["lev"] > 1 and crypto.liq_distance(pos["lev"]) <= stop:
    st.error(f"При плече {pos['lev']:.1f}x ликвидация наступит примерно через {crypto.liq_distance(pos['lev']):.1f}% — "
             f"раньше стопа на {stop}%. Уменьшите риск или сдвиньте стоп ближе.")
elif pos["lev"] > 1:
    st.info(f"Плечо {pos['lev']:.1f}x: ликвидация примерно через {crypto.liq_distance(pos['lev']):.1f}%, стоп сработает "
            f"раньше. Используйте изолированную маржу, чтобы ликвидация не задела остальной счёт (блок 1).")
learn.tags("совпадающий", "проверен на истории")

with learn.how_it_works():
    st.markdown(f"""
- **Формула.** Размер позиции = сколько готовы потерять / расстояние до стопа. Счёт {usd(acc)}, риск {risk}% —
  это {usd(pos['risk'])}; стоп {stop}% — позиция {usd(pos['size'])}.
- **Стоп ставят по смыслу, а не по деньгам.** Стоп — точка, где ваша идея оказалась неверной. Если такая точка далеко,
  позиция просто меньше.
- **Слишком близкий стоп выбивает шумом.** Таблица «стоп выбило бы за неделю» показывает, как часто обычные
  колебания проходят такое расстояние. Слишком близкий стоп — почти гарантированный убыток.
- **Стоп — не гарантия цены.** В каскаде он исполнится хуже (проскальзывание), в выходные и ночью — тоже (блок 1).
""")

# ---------- 2. математика потерь ----------
st.header("2. Почему выживание важнее прибыли")
learn.tags("совпадающий", "проверен на истории")
loss = pd.DataFrame({"Нужно для возврата, %": [l / (100 - l) * 100 for l in (10, 20, 30, 50, 75, 90)]},
                    index=[f"−{l}%" for l in (10, 20, 30, 50, 75, 90)])
c = st.columns(2)
with c[0]:
    st.markdown("**Потеря и возврат**")
    st.dataframe(loss.style.format("+{:.0f}"), width="stretch")
    st.caption("Чем глубже просадка, тем непропорционально больше нужно, чтобы вернуться.")
with c[1]:
    st.markdown("**После 10 убытков подряд**")
    after = pd.DataFrame({"Осталось от счёта, %": [100 * (1 - r / 100) ** 10 for r in (1, 2, 5, 10, 20)]},
                         index=[f"риск {r}% на сделку" for r in (1, 2, 5, 10, 20)])
    st.dataframe(after.style.format("{:.0f}"), width="stretch")
    st.caption("При риске 1–2% серия ошибок — неприятность, при 10–20% — конец счёта.")
win = st.select_slider("Доля удачных сделок", [0.3, 0.4, 0.5, 0.6, 0.7], value=0.5, key="rm_win",
                       format_func=lambda x: f"{x:.0%}")
st.markdown(f"**Вероятность серии убытков подряд** при {win:.0%} удачных сделок, %:")
st.dataframe(streak_table(win).style.format("{:.0f}"), width="stretch")
st.caption("Моделирование 4000 вариантов истории. Серии — не невезение, а свойство случайности: их надо ждать заранее.")

# ---------- 3. когда опасно ----------
st.header("3. Когда рынок опаснее")
st.markdown(f"Популярный миф — «обвалы бывают в выходные». По дням с 2019 года выходные **спокойнее** будней, и на "
            f"них пришлось {weekend} из {total_worst} самых резких падений. Опаснее всего пятница и понедельник — "
            f"{fri_mon} из {total_worst}: в пятницу закрываются рынки акций и уходят крупные участники, в понедельник "
            f"рынок отыгрывает новости выходных.")
learn.tags("совпадающий", "проверен на истории")
st.dataframe(wd.style.format({"Среднее движение за день, %": "{:.2f}", worst_col: "{:.0f}"}), width="stretch")
st.caption("Дни по UTC (в Москве — +3 часа). Самые резкие падения внутри дня — минимум к закрытию прошлого дня, с "
           "запуска фьючерсов Binance.")
ev = events()
if ev:
    st.markdown("**Ближайшие события, вокруг которых растёт волатильность** (календарь trade-news):")
    st.dataframe(pd.DataFrame([{"Дата": e["date"], "Событие": EVENT_TYPES[e["type"]], "Что": e["title"]} for e in ev]),
                 hide_index=True, width="stretch")
    st.caption("Решения ФРС двигают все рисковые активы (блок 4). Крупные разлоки токенов — блок 3.")
with learn.how_it_works("Правила, которые следуют из модели"):
    st.markdown("""
- **Не держать на бирже больше, чем нужно для торговли** — биржа может рухнуть (блок 2).
- **Изолированная маржа и маленькое плечо** — чтобы одна ошибка не забрала весь счёт (блок 1).
- **Меньше позиция перед решениями ФРС и на ночь пятницы** — каскады любят тонкий рынок.
- **Альткоины — меньшим размером:** при том же стопе их выбивает чаще (блок 3).
- **Записывать сделки.** Модель становится вашей, только когда вы проверяете её на своих решениях.
""")


# ---------- примеры ----------
def stop_story(day: str, stop_pct: int, text: str) -> None:
    d = pd.Timestamp(day)
    w = df[d - pd.Timedelta(days=10):d + pd.Timedelta(days=20)]
    entry = float(df["c"][:d].iloc[-2])
    low = float(df.loc[d:d + pd.Timedelta(days=1), "lo"].min())
    drop = (low / entry - 1) * 100
    c = st.columns(3)
    c[0].metric("Падение от закрытия накануне", f"{drop:.0f}%", border=True)
    c[1].metric(f"Лонг со стопом {stop_pct}%", "закрыт по стопу" if -drop >= stop_pct else "устоял", border=True)
    c[2].metric("Лонг с плечом 10x", "ликвидирован" if -drop >= crypto.liq_distance(10) else "устоял", border=True)
    st.plotly_chart(line_chart({"Закрытие": w["c"], "Минимум дня": w["lo"]}, units="$", height=260), width="stretch")
    st.markdown(text)


learn.examples([
    Example("10.10.2025: стоп и размер спасают", lambda: stop_story(
        "2025-10-10", 10,
        "Вечер пятницы, каскад ликвидаций. Позиция с риском 1% счёта и стопом 10% закрылась бы с убытком около 1% "
        "счёта (плюс проскальзывание). Позиция на весь счёт с плечом 10x была бы ликвидирована целиком.")),
    Example("12.03.2020: чёрный четверг", lambda: stop_story(
        "2020-03-12", 15,
        "Даже далёкий стоп сработал: за день цена прошла больше, чем обычно проходит за месяц. Выжили те, у кого "
        "размер позиции был рассчитан от стопа, а не те, кто угадал направление на год вперёд.")),
], key="risk")

st.divider()
st.markdown("**Дальше.** Это последний блок. Вернитесь к модели целиком и проверьте её на своих решениях.")
c = st.columns(2)
c[0].page_link(learn.CRYPTO_MODEL, label="Модель крипты", icon="🧠")
c[1].page_link("views/crypto/leverage.py", label="1. Плечо и ликвидации", icon="🎢")
