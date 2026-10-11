"""Графики лаборатории облигаций — в общем стиле дашборда."""
import numpy as np
import plotly.graph_objects as go

from core.charts import GRID, PALETTE, _base_layout, theme


def cashflows(t: np.ndarray, cf: np.ndarray, pv: np.ndarray, center: float, height: int = 340) -> go.Figure:
    """Выплаты по годам: сколько заплатят (контур) и сколько это стоит сегодня (заливка); вертикаль — центр тяжести."""
    c = PALETTE[theme()]
    width = max(min(0.8 / max(len(t) / max(t[-1], 0.25), 1), 0.8), 0.04)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=t, y=cf, width=width, name="Заплатят", marker=dict(color="rgba(0,0,0,0)",
                         line=dict(color=c[0], width=1.5)),
                         hovertemplate="через %{x:.2f} г.: заплатят %{y:.2f}<extra></extra>"))
    fig.add_trace(go.Bar(x=t, y=pv, width=width, name="Стоит сегодня", marker=dict(color=c[0], opacity=0.8),
                         hovertemplate="через %{x:.2f} г.: стоит сегодня %{y:.2f}<extra></extra>"))
    fig.add_vline(x=center, line_width=2, line_dash="dot", line_color=c[1],
                  annotation_text=f"центр тяжести {center:.1f} г.", annotation_position="top left")
    _base_layout(fig, height, legend=True)
    fig.update_layout(barmode="overlay", bargap=0)
    fig.update_xaxes(title_text="Через сколько лет выплата", rangemode="tozero")
    fig.update_yaxes(title_text="На 100 номинала", type="log" if cf.max() / max(cf.min(), 1e-9) > 40 else "linear")
    return fig


def price_yield(grid, prices, tangent, y0: float, p0: float, y1: float, p1: float, height: int = 340) -> go.Figure:
    """Цена от доходности: точная дуга, прямая по дюрации и две точки — до и после сдвига."""
    c = PALETTE[theme()]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=grid, y=prices, mode="lines", line=dict(width=2.5, color=c[0]), name="Точная цена",
                             hovertemplate="доходность %{x:.2f}% → цена %{y:.2f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=grid, y=tangent, mode="lines", line=dict(width=1.5, color=c[3], dash="dash"),
                             name="Оценка по дюрации", hovertemplate="по дюрации: %{y:.2f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[y0], y=[p0], mode="markers", marker=dict(size=11, color=c[0]), name="Сейчас",
                             hovertemplate="сейчас: %{x:.2f}% → %{y:.2f}<extra></extra>"))
    if abs(y1 - y0) > 1e-9:
        fig.add_trace(go.Scatter(x=[y1], y=[p1], mode="markers", marker=dict(size=11, color=c[1]),
                                 name="После сдвига", hovertemplate="после: %{x:.2f}% → %{y:.2f}<extra></extra>"))
    _base_layout(fig, height, legend=True)
    fig.update_xaxes(title_text="Доходность, %", ticksuffix="%")
    fig.update_yaxes(title_text="Цена (номинал 100)")
    return fig


def waterfall(steps: list[tuple[str, float]], total: str, units: str = "", height: int = 320) -> go.Figure:
    """Лесенка: первая ступень — база, дальше прибавки и вычеты, последняя — итог."""
    c = PALETTE[theme()]
    fig = go.Figure(go.Waterfall(
        x=[s[0] for s in steps] + [total], y=[s[1] for s in steps] + [0],
        measure=["absolute"] + ["relative"] * (len(steps) - 1) + ["total"],
        text=[f"{s[1]:+.2f}{units}" if i else f"{s[1]:.2f}{units}" for i, s in enumerate(steps)] + [""],
        textposition="outside", cliponaxis=False,
        increasing=dict(marker=dict(color=c[2])), decreasing=dict(marker=dict(color=c[7])),
        totals=dict(marker=dict(color=c[0])), connector=dict(line=dict(color=GRID[theme()])),
        hovertemplate="%{x}: %{y:.2f}" + units + "<extra></extra>"))
    _base_layout(fig, height, legend=False)
    fig.update_yaxes(ticksuffix=units)
    return fig


def lines(series: dict[str, tuple], x_title: str, y_title: str, vline: tuple[float, str] | None = None,
          point: tuple[float, float, str] | None = None, units: str = "%", height: int = 320) -> go.Figure:
    c = PALETTE[theme()]
    fig = go.Figure()
    for i, (name, (xs, ys)) in enumerate(series.items()):
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", name=name, line=dict(width=2, color=c[i]),
                                 hovertemplate=f"{name}: " + "%{y:.2f}" + units + "<extra>%{x:.1f}</extra>"))
    if vline:
        fig.add_vline(x=vline[0], line_width=1.5, line_dash="dot", line_color=c[3], annotation_text=vline[1],
                      annotation_position="top")
    if point:
        fig.add_trace(go.Scatter(x=[point[0]], y=[point[1]], mode="markers+text", text=[point[2]],
                                 textposition="top right", marker=dict(size=10, color=c[1]), showlegend=False,
                                 hoverinfo="skip"))
    _base_layout(fig, height, legend=True)
    fig.update_xaxes(title_text=x_title)
    fig.update_yaxes(title_text=y_title, ticksuffix=units)
    return fig
