"""Общий стиль графиков: тонкие линии, ненавязчивая сетка, серые полосы рецессий,
перекрестие с подсказкой по наведению. Цвета — из эталонной палитры dataviz."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Категориальная палитра: слоты в фиксированном порядке, отдельно для светлой и тёмной темы
PALETTE = {
    "light": ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"],
    "dark": ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"],
}
RECESSION_FILL = {"light": "rgba(82,81,78,0.12)", "dark": "rgba(195,194,183,0.12)"}
GRID = {"light": "#e6e5e0", "dark": "#33332f"}


def theme() -> str:
    t = getattr(st.context, "theme", None)
    return "dark" if t is not None and t.type == "dark" else "light"


def recession_spans(usrec: pd.Series) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Отрезки дат, где USREC == 1 (конец — начало первого месяца после рецессии)."""
    spans, start = [], None
    for date, v in usrec.items():
        if v == 1 and start is None:
            start = date
        elif v != 1 and start is not None:
            spans.append((start, date))
            start = None
    if start is not None:
        spans.append((start, usrec.index[-1]))
    return spans


def _base_layout(fig: go.Figure, height: int, legend: bool) -> go.Figure:
    mode = theme()
    fig.update_layout(
        height=height, margin=dict(l=8, r=8, t=8, b=8), showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor=GRID[mode], gridwidth=1, zeroline=False)
    return fig


def curve_chart(curves: dict[str, pd.Series], height: int = 340) -> go.Figure:
    """Кривые доходности: x — срок в годах (лог-шкала), y — доходность, %.
    Первая кривая (сейчас) — акцент с маркерами, остальные — тоньше, для контекста."""
    mode = theme()
    colors = PALETTE[mode]
    fig = go.Figure()
    for i, (name, c) in enumerate(curves.items()):
        labels = [f"{m:g} г." if m >= 1 else f"{round(m * 12):g} мес." for m in c.index]
        fig.add_trace(go.Scatter(
            x=c.index, y=c.values, name=name, mode="lines+markers",
            line=dict(width=3 if i == 0 else 2, color=colors[i]),
            marker=dict(size=8 if i == 0 else 6, color=colors[i]),
            customdata=labels, hovertemplate="%{customdata}: %{y:.2f}%<extra>" + name + "</extra>",
        ))
    _base_layout(fig, height, legend=True)
    ticks = [1 / 12, 0.25, 0.5, 1, 2, 5, 7, 10, 20, 30]
    fig.update_xaxes(type="log", tickvals=ticks,
                     ticktext=["1м", "3м", "6м", "1г", "2г", "5л", "7л", "10л", "20л", "30л"])
    fig.update_yaxes(ticksuffix="%")
    fig.update_layout(hovermode="x unified")
    return fig


def price_yield_chart(yields, prices, y0: float, p0: float, y1: float, p1: float, height: int = 300) -> go.Figure:
    """Цена облигации от доходности: выпуклая кривая, текущая точка и точка после сдвига."""
    mode = theme()
    c = PALETTE[mode]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=yields, y=prices, mode="lines", line=dict(width=2, color=c[0]),
                             name="Цена", hovertemplate="доходность %{x:.2f}% → цена %{y:.2f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[y0], y=[p0], mode="markers+text", marker=dict(size=10, color=c[0]),
                             text=["сейчас"], textposition="top right", name="Сейчас",
                             hovertemplate="%{x:.2f}% → %{y:.2f}<extra>сейчас</extra>"))
    if abs(y1 - y0) > 1e-9:
        fig.add_trace(go.Scatter(x=[y1], y=[p1], mode="markers+text", marker=dict(size=10, color=c[1]),
                                 text=["после сдвига"], textposition="top right", name="После сдвига",
                                 hovertemplate="%{x:.2f}% → %{y:.2f}<extra>после сдвига</extra>"))
    _base_layout(fig, height, legend=False)
    fig.update_xaxes(title_text="Доходность, %", ticksuffix="%")
    fig.update_yaxes(title_text="Цена (номинал 100)")
    return fig


def hbar_chart(labels: list[str], values: list[float], units: str = "%", height: int = 200,
               signed: bool = True) -> go.Figure:
    """Горизонтальные столбцы одного цвета, подписи значений у концов."""
    mode = theme()
    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h", marker=dict(color=PALETTE[mode][0], cornerradius=4),
        width=0.5, text=[f"{v:{'+' if signed else ''}.1f}{units}" for v in values], textposition="outside",
        hovertemplate="%{y}: %{x:" + ("+" if signed else "") + ".2f}" + units + "<extra></extra>", cliponaxis=False,
    ))
    _base_layout(fig, height, legend=False)
    fig.update_yaxes(autorange="reversed", gridcolor="rgba(0,0,0,0)")
    fig.update_xaxes(showgrid=True, gridcolor=GRID[mode], ticksuffix=units, zeroline=True,
                     zerolinecolor=GRID[mode])
    return fig


def line_chart(series: dict[str, pd.Series], units: str = "",
               recessions: list[tuple] | None = None, zero_line: bool = False,
               height: int = 420) -> go.Figure:
    mode = theme()
    colors = PALETTE[mode]
    fig = go.Figure()
    start = min(s.index[0] for s in series.values())
    for (a, b) in recessions or []:
        if b >= start:
            fig.add_vrect(x0=max(a, start), x1=b, fillcolor=RECESSION_FILL[mode],
                          line_width=0, layer="below")
    for i, (name, s) in enumerate(series.items()):
        fig.add_trace(go.Scatter(
            x=s.index, y=s.values, name=name, mode="lines",
            line=dict(width=2, color=colors[i]),
            hovertemplate="%{y:,.2f} " + units + "<extra>" + name + "</extra>",
        ))
    if zero_line:
        fig.add_hline(y=0, line_width=1, line_color=GRID[mode])
    fig.update_layout(
        height=height, margin=dict(l=8, r=8, t=8, b=8),
        hovermode="x unified", showlegend=len(series) > 1,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(showgrid=False, showspikes=True, spikemode="across",
                     spikethickness=1, spikedash="solid", spikecolor=GRID[mode])
    fig.update_yaxes(gridcolor=GRID[mode], gridwidth=1, zeroline=False, ticksuffix="")
    return fig


# ---------- режим экономики ----------

DIVERGING = {"light": ("#e34948", "#f0efec", "#2a78d6"), "dark": ("#e66767", "#383835", "#3987e5")}


def regime_colors() -> dict[str, str]:
    """Цвет режима = категориальный слот в фиксированном порядке (идентичность, не оценка)."""
    from core.regime import REGIMES
    return dict(zip(REGIMES, PALETTE[theme()]))


def quadrant_chart(g: pd.Series, i: pd.Series, months: int = 24, height: int = 420) -> go.Figure:
    """Квадрант рост × инфляция: фон четвертей, траектория за N месяцев, текущая точка."""
    mode = theme()
    colors = regime_colors()
    df = pd.concat({"g": g, "i": i}, axis=1).dropna().iloc[-months:]
    lim = max(1.6, float(df.abs().max().max()) * 1.15)
    fig = go.Figure()
    quads = [("Восстановление", 0, lim, -lim, 0), ("Перегрев", 0, lim, 0, lim),
             ("Стагфляция", -lim, 0, 0, lim), ("Замедление", -lim, 0, -lim, 0)]
    for name, x0, x1, y0, y1 in quads:
        fig.add_shape(type="rect", x0=x0, x1=x1, y0=y0, y1=y1, line_width=0,
                      fillcolor=colors[name], opacity=0.10, layer="below")
        fig.add_annotation(x=(x0 + x1) / 2, y=y1 - lim * 0.06 if y1 > 0 else y0 + lim * 0.06, text=f"<b>{name}</b>",
                           showarrow=False, font=dict(size=13, color=colors[name]))
    fig.add_hline(y=0, line_width=1, line_color=GRID[mode])
    fig.add_vline(x=0, line_width=1, line_color=GRID[mode])
    labels = [d.strftime("%m.%Y") for d in df.index]
    fig.add_trace(go.Scatter(x=df["g"], y=df["i"], mode="lines+markers", name="Траектория",
                             line=dict(width=2, color=GRID[mode] if mode == "light" else "#77766f"),
                             marker=dict(size=6, color="#8a8984"), customdata=labels,
                             hovertemplate="%{customdata}<br>рост %{x:+.2f} · инфляция %{y:+.2f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[df["g"].iloc[-1]], y=[df["i"].iloc[-1]], mode="markers+text",
                             marker=dict(size=16, color=PALETTE[mode][0], line=dict(width=2, color="white")),
                             text=[f"сейчас ({labels[-1]})"], textposition="top center", name="Сейчас",
                             hovertemplate="сейчас<br>рост %{x:+.2f} · инфляция %{y:+.2f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[df["g"].iloc[0]], y=[df["i"].iloc[0]], mode="text", text=[labels[0]],
                             textposition="bottom center", showlegend=False, hoverinfo="skip"))
    _base_layout(fig, height, legend=False)
    fig.update_xaxes(range=[-lim, lim], title_text="Рост: замедляется ← → ускоряется", zeroline=False, showgrid=False)
    fig.update_yaxes(range=[-lim, lim], title_text="Инфляция: замедляется ↓ ↑ ускоряется", showgrid=False)
    return fig


def regime_ribbon(regime: pd.Series, recessions: list[tuple] | None = None, height: int = 130) -> go.Figure:
    """Лента режимов по месяцам: один столбик на месяц, цвет — режим."""
    colors = regime_colors()
    mode = theme()
    fig = go.Figure()
    for name, color in colors.items():
        x = regime[regime == name]
        fig.add_trace(go.Bar(x=x.index, y=[1] * len(x), name=name, marker=dict(color=color, line_width=0),
                             width=31 * 24 * 3600 * 1000, hovertemplate="%{x|%m.%Y}: " + name + "<extra></extra>"))
    for a, b in recessions or []:
        if b >= regime.index[0]:
            fig.add_shape(type="rect", x0=max(a, regime.index[0]), x1=b, y0=1.05, y1=1.25, line_width=0,
                          fillcolor="#8a8984")
    _base_layout(fig, height, legend=True)
    fig.update_layout(barmode="overlay", bargap=0)
    fig.update_yaxes(visible=False, range=[0, 1.3])
    fig.update_xaxes(showgrid=False)
    return fig


def heatmap(table: pd.DataFrame, hover: pd.DataFrame, highlight: str | None = None,
            height: int | None = None, scale_title: str = "% год.") -> go.Figure:
    """Тепловая карта «актив × режим»: синий — рост, красный — падение, серый — около нуля."""
    mode = theme()
    neg, mid, pos = DIVERGING[mode]
    z = table.values.astype(float)
    m = float(np.nanmax(np.abs(z))) if np.isfinite(z).any() else 1
    text = [[("—" if not np.isfinite(v) else f"{v:+.1f}") for v in row] for row in z]
    cols = [f"<b>▶ {c}</b>" if c == highlight else c for c in table.columns]
    fig = go.Figure(go.Heatmap(
        z=z, x=cols, y=list(table.index), zmin=-m, zmax=m, colorscale=[[0, neg], [0.5, mid], [1, pos]],
        text=text, texttemplate="%{text}", textfont=dict(size=12), customdata=hover.values,
        hovertemplate="%{y} · %{x}<br>%{customdata}<extra></extra>", xgap=2, ygap=2,
        colorbar=dict(title=scale_title, thickness=10, len=0.6),
    ))
    _base_layout(fig, height or 28 * len(table) + 60, legend=False)
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(side="top", showgrid=False, tickangle=0, tickfont=dict(size=11))
    return fig


# ---------- оценка рынка ----------

def cape_scatter(cape: pd.Series, fwd: pd.Series, current: float, fit_line=None, height: int = 380) -> go.Figure:
    """CAPE (x) против реальной доходности следующих 10 лет (y); вертикаль — текущий CAPE."""
    mode = theme()
    c = PALETTE[mode]
    df = pd.concat({"cape": cape, "fwd": fwd}, axis=1).dropna()
    fig = go.Figure(go.Scatter(
        x=df["cape"], y=df["fwd"], mode="markers", name="Месяц",
        marker=dict(size=5, color=c[0], opacity=0.35),
        customdata=[d.strftime("%m.%Y") for d in df.index],
        hovertemplate="%{customdata}: CAPE %{x:.1f} → следующие 10 лет %{y:+.1f}% в год<extra></extra>"))
    if fit_line is not None:
        xs = np.linspace(df["cape"].min(), max(df["cape"].max(), current) * 1.02, 100)
        fig.add_trace(go.Scatter(x=xs, y=[fit_line(x) for x in xs], mode="lines", name="Регрессия",
                                 line=dict(width=2, color=c[1]), hoverinfo="skip"))
    fig.add_vline(x=current, line_width=2, line_color=c[1], line_dash="solid",
                  annotation_text=f"сейчас {current:.1f}", annotation_position="bottom left")
    fig.add_hline(y=0, line_width=1, line_color=GRID[mode])
    _base_layout(fig, height, legend=False)
    fig.update_xaxes(title_text="CAPE в момент покупки", showgrid=False)
    fig.update_yaxes(title_text="Реальная доходность след. 10 лет, % год.", ticksuffix="%")
    return fig


def bucket_chart(table: pd.DataFrame, current_bucket: str | None, height: int = 380) -> go.Figure:
    """Медиана и размах последующей доходности по корзинам CAPE."""
    mode = theme()
    c = PALETTE[mode]
    t = table.dropna(subset=["Медиана, % год."])
    colors = [c[1] if b == current_bucket else c[0] for b in t.index]
    labels = [f"{b}<br><b>{m:+.1f}%</b>" for b, m in zip(t.index, t["Медиана, % год."])]
    fig = go.Figure(go.Bar(
        x=labels, y=t["Медиана, % год."], marker=dict(color=colors, cornerradius=4), width=0.55,
        error_y=dict(type="data", symmetric=False, array=t["Лучший, % год."] - t["Медиана, % год."],
                     arrayminus=t["Медиана, % год."] - t["Худший, % год."], color=GRID[mode] if mode == "dark" else "#8a8984",
                     thickness=1.5, width=6),
        customdata=np.stack([t["Худший, % год."], t["Лучший, % год."], t["Доля < 0, %"], t["Месяцев"]], axis=1),
        hovertemplate="медиана %{y:+.1f}%<br>худший %{customdata[0]:+.1f}%, лучший %{customdata[1]:+.1f}%"
                      "<br>доля отрицательных 10-летий %{customdata[2]:.0f}% · месяцев %{customdata[3]}<extra></extra>"))
    fig.add_hline(y=0, line_width=1, line_color=GRID[mode])
    _base_layout(fig, height, legend=False)
    fig.update_xaxes(title_text="CAPE в момент покупки · медиана следующих 10 лет")
    fig.update_yaxes(title_text="Реальная доходность след. 10 лет, % год.", ticksuffix="%")
    return fig


def xy_lines(series: dict[str, tuple], x_title: str, y_title: str, marker: tuple | None = None,
             height: int = 320) -> go.Figure:
    """Несколько линий y(x) на одной оси; series: имя → (xs, ys)."""
    mode = theme()
    c = PALETTE[mode]
    fig = go.Figure()
    for i, (name, (xs, ys)) in enumerate(series.items()):
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", name=name, line=dict(width=2, color=c[i]),
                                 hovertemplate=f"{name}: " + "x=%{x:.2f} → %{y:.1f}<extra></extra>"))
    if marker is not None:
        fig.add_trace(go.Scatter(x=[marker[0]], y=[marker[1]], mode="markers+text", text=[marker[2]],
                                 textposition="top right", marker=dict(size=10, color=c[1]), showlegend=False,
                                 hoverinfo="skip"))
    _base_layout(fig, height, legend=True)
    fig.update_xaxes(title_text=x_title, showgrid=False)
    fig.update_yaxes(title_text=y_title)
    fig.update_layout(hovermode="x unified")
    return fig


# ---------- сектора ----------

def rotation_chart(df: pd.DataFrame, x: str, y: str, x_title: str, y_title: str,
                   quadrants: tuple[str, str, str, str], height: int = 420) -> go.Figure:
    """Точки секторов в четырёх четвертях. quadrants: (правый верх, правый низ, левый низ, левый верх).
    df: индекс — подпись точки, колонки x и y."""
    mode = theme()
    c = PALETTE[mode]
    lim_x = max(float(df[x].abs().max()) * 1.2, 1)
    lim_y = max(float(df[y].abs().max()) * 1.2, 1)
    fig = go.Figure()
    for (label, xs, ys), color in zip(
            [(quadrants[0], 1, 1), (quadrants[1], 1, -1), (quadrants[2], -1, -1), (quadrants[3], -1, 1)],
            [c[2], c[3], c[7], c[0]]):
        fig.add_shape(type="rect", x0=0, x1=xs * lim_x, y0=0, y1=ys * lim_y, line_width=0,
                      fillcolor=color, opacity=0.08, layer="below")
        fig.add_annotation(x=xs * lim_x * 0.97, y=ys * lim_y * 0.95, text=f"<b>{label}</b>", showarrow=False,
                           xanchor="right" if xs > 0 else "left", font=dict(size=12, color=color))
    fig.add_hline(y=0, line_width=1, line_color=GRID[mode])
    fig.add_vline(x=0, line_width=1, line_color=GRID[mode])
    fig.add_trace(go.Scatter(
        x=df[x], y=df[y], mode="markers+text", text=list(df.index), textposition="top center",
        marker=dict(size=11, color=c[0], line=dict(width=2, color="white" if mode == "light" else "#1a1a19")),
        hovertemplate="%{text}<br>" + x_title + ": %{x:+.1f}<br>" + y_title + ": %{y:+.1f}<extra></extra>"))
    _base_layout(fig, height, legend=False)
    fig.update_xaxes(range=[-lim_x, lim_x], title_text=x_title, zeroline=False)
    fig.update_yaxes(range=[-lim_y, lim_y], title_text=y_title, showgrid=False)
    return fig


def grouped_bars(df: pd.DataFrame, units: str = "", height: int = 320) -> go.Figure:
    """Сгруппированные столбцы: строки df — категории по оси X (например, годы), колонки — серии."""
    mode = theme()
    c = PALETTE[mode]
    fig = go.Figure()
    for i, col in enumerate(df.columns):
        fig.add_trace(go.Bar(x=list(df.index), y=df[col], name=col, marker=dict(color=c[i], cornerradius=4),
                             hovertemplate=f"{col}: " + "%{y:,.1f}" + units + "<extra>%{x}</extra>"))
    fig.add_hline(y=0, line_width=1, line_color=GRID[mode])
    _base_layout(fig, height, legend=True)
    fig.update_layout(barmode="group", bargap=0.3, bargroupgap=0.08)
    fig.update_yaxes(ticksuffix=units)
    return fig
