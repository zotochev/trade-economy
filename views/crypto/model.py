"""Модель крипты за 5 минут — по методу «Смыслы-Инварианты-Граф»: сначала из каких частей состоит рынок и зачем
каждая нужна, потом законы, которые всегда верны, потом как части связаны. Цифр — минимум."""
import streamlit as st

from core import crypto, learn, ui

KIND_COLOR = crypto.KIND_COLOR

# граф: (откуда, куда, что передаётся); узлы — контейнеры и цена
EDGES = [
    ("Среда: деньги и правила", "Двери для крупных денег", "аппетит к риску"),
    ("Среда: деньги и правила", "Доллары и биржи", "ставки → доход эмитентов"),
    ("Двери для крупных денег", "Цена биткоина", "покупка монет (минус арбитраж)"),
    ("Доллары и биржи", "Цена биткоина", "топливо для покупок"),
    ("Доллары и биржи", "Плечо", "залог"),
    ("Плечо", "Цена биткоина", "ликвидации"),
    ("Цена биткоина", "Плечо", "движение"),
    ("Монеты, держатели и циклы", "Цена биткоина", "продажи держателей и майнеров"),
    ("Цена биткоина", "Альткоины", "× бета больше 1"),
    ("Альткоины", "Плечо", "тонкий рынок, каскады"),
    ("Цена биткоина", "Ваш счёт", "прибыль или ликвидация"),
]


def graph() -> str:
    color = {c.title: "#4c78a8" for c in crypto.CONTAINERS}
    color["Цена биткоина"] = "#e45756"
    color["Ваш счёт"] = "#54a24b"
    nodes = "\n".join(f'"{n}" [shape=box, style="rounded,filled", fillcolor="{c}", fontcolor=white];'
                      for n, c in color.items())
    edges = "\n".join(f'"{a}" -> "{b}" [label="{w}", fontsize=10];' for a, b, w in EDGES)
    return f'digraph {{ rankdir=TB; bgcolor="transparent"; node [fontname="sans-serif"]; ' \
           f'edge [fontname="sans-serif", color="#888888", fontcolor="#888888"]; {nodes} {edges} }}'


def block_link(num: int, label: str | None = None) -> None:
    b = crypto.BY_NUM[num]
    if b.page:
        st.page_link(b.page, label=label or f"{b.order}. {b.title}", icon="➡️")
    else:
        st.markdown(f"➡️ {b.order}. {b.title} · :gray[в разработке]")


left, right = st.columns([5, 1], vertical_alignment="bottom")
left.title("Модель крипты за 5 минут")
with right:
    st.page_link(learn.CRYPTO_MAP, label="Что сейчас", icon="🗺️")
st.markdown(f"**Цель модели.** {crypto.GOAL}")
st.caption("Сначала — из каких частей состоит рынок и зачем каждая. Потом — законы, которые держат всю конструкцию. "
           "Потом — как части толкают друг друга. Цифры и проверки — внутри блоков. Это модель, а не торговые "
           "сигналы: она объясняет рынок, но не говорит, когда входить.")

# ---------- 1. смыслы ----------
st.header("1. Из чего состоит рынок")
for i, c in enumerate(crypto.CONTAINERS, 1):
    with st.container(border=True):
        left, right = st.columns([4, 2], vertical_alignment="center")
        with left:
            st.markdown(f"**{i}. {c.title}** — {c.why}  \n:gray[Определяет:] {c.defines}")
        with right:
            for n in c.blocks:
                block_link(n)

# ---------- 2. законы ----------
st.header("2. Законы, которые всегда верны")
st.markdown("Их можно не помнить в цифрах, но держать в голове как правила. Метка — насколько закон надёжен: "
            ":blue-badge[арифметика / механизм / факт] — следует из устройства, :green-badge[проверен на истории] "
            "— видно на данных, :orange-badge[спорный] — данных мало или связь ослабла.")
for i, law in enumerate([l for l in crypto.LAWS if l.core], 1):
    b = crypto.BY_NUM[law.block]
    left, right = st.columns([5, 2], vertical_alignment="center")
    with left:
        st.markdown(f"**{i}.** {law.text} :{KIND_COLOR[law.kind]}-badge[{law.kind}]"
                    + (f"  \n:gray[Оговорка: {law.caveat}]" if law.caveat else ""))
    with right:
        block_link(law.block, f"показано в блоке {b.order}")

# ---------- 3. граф ----------
st.header("3. Как части связаны")
st.graphviz_chart(graph(), width="stretch")
st.caption("Стрелка — что одна часть передаёт другой. «Ваш счёт» только читает рынок и на него не влияет. Внутренние "
           "шоки (крах биржи, запуск ETF) могут перекрыть среду — стрелки не показывают силу связи.")
st.markdown("**Петли — где цепочка возвращается в цену и сама себя усиливает.** Поэтому крипта ходит рывками: "
            "движение разгоняется, пока не кончится топливо.")
for name, what, num in crypto.LOOPS:
    st.markdown(f"- **{name}.** {what} :gray[(блок {crypto.BY_NUM[num].order})]")

# ---------- 4. что может убить позицию ----------
st.header("4. Что может уничтожить позицию с плечом")
st.markdown("""
- **Обычное движение.** Цена прошла 100/плечо % против вас — ликвидация. С плечом 10x это около 10%, а
  биткоин проходит столько за месяц очень часто (блок 1).
- **Каскад.** Ликвидации чужих позиций толкают цену к вашей — внутри дня, часто ночью или в выходные (блок 1).
- **Залог.** Стейблкоин или токен, которым обеспечена позиция, теряет привязку к доллару (блок 2).
- **Биржа.** Банкротство, взлом, остановка вывода, заморозка адресов — ваши монеты оказываются долгом биржи
  (блок 2).
- **Альткоин.** Разлок, разводнение или обнуление отдельного токена — сверх общего рынка (блок 3).
- **Размер позиции.** Даже правильная идея убивает счёт, если на одну сделку поставлено слишком много (блок 10).
""")

# ---------- живые сигналы ----------
st.divider()
st.markdown("**Два сигнала прямо сейчас** — подробности на «Что сейчас» и в блоках.")
c = st.columns(2)
try:
    head, color, f, pct = crypto.lev_verdict(ui.load)
    c[0].metric("Плечо", head.split(":")[0], f"фандинг {f:.1f}% годовых", delta_color="off", border=True)
except Exception as e:  # недоступный ряд не должен гасить страницу
    c[0].warning(f"Нет данных: {e}")
try:
    p = crypto.onchain(ui.load)["price"]
    dd = float((p.iloc[-1] / p.max() - 1) * 100)
    c[1].metric("Цикл", "медвежья фаза" if dd < -20 else "бычья фаза", f"{dd:.0f}% от вершины", delta_color="off",
                border=True)
except Exception as e:
    c[1].warning(f"Нет данных: {e}")
