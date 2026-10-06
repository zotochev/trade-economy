"""Вёрстка приборной панели одним HTML-блоком на CSS-сетке.

Шапка «Фаза цикла» + шесть колонок-групп по три прибора. Колонки используют
subgrid, поэтому плитки в одной строке всегда одной высоты. Каждая плитка —
стрелочный прибор с цветными зонами порогов, мини-график, перцентиль, статус.
Статус всегда = значок + слово + цвет; текст — нейтральными цветами.
"""
from __future__ import annotations

import math
from html import escape

import pandas as pd

from core.indicators import GROUPS, Result, group_status
from core.phase import Phase

STATUS_COLOR = {"good": "#0ca30c", "warning": "#fab219", "serious": "#ec835a",
                "critical": "#d03b3b", "neutral": "#9a998f", "extreme": "#7d6ee0"}
STATUS_ICON = {"good": "✓", "warning": "!", "serious": "▲", "critical": "✕", "neutral": "–", "extreme": "◆"}
KIND_SHORT = {"опережающий": "ОПЕРЕЖ.", "совпадающий": "СОВПАД.", "запаздывающий": "ЗАПАЗД."}
MONTHS = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]

TOKENS = {
    "light": dict(text="#0b0b0b", text2="#52514e", muted="#8a8984", series="#2a78d6", page="#ffffff",
                  card="#fbfbfa", border="#e6e5e0", hover="#2a78d6", grid="#e6e5e0", track="#e6e5e0",
                  rec="rgba(82,81,78,0.12)", hero="#f4f3ef", shadow="rgba(0,0,0,0.06)"),
    "dark": dict(text="#ffffff", text2="#c3c2b7", muted="#8f8e86", series="#3987e5", page="#0e1117",
                 card="#1a1a19", border="#2f2f2b", hover="#3987e5", grid="#33332f", track="#33332f",
                 rec="rgba(195,194,183,0.12)", hero="#20201e", shadow="rgba(0,0,0,0.4)"),
}


def css(mode: str) -> str:
    t = TOKENS[mode]
    return f"""
:host, .ck {{ color:{t['text']}; font-family: inherit; }}
.ck {{ display:flex; flex-direction:column; gap:14px; }}
.ic {{ display:inline-flex; align-items:center; justify-content:center; width:18px; height:18px; flex:none;
       border-radius:50%; font-size:10px; font-weight:700; color:#0b0b0b; }}
.pill {{ display:inline-flex; align-items:center; gap:6px; font-size:13px; font-weight:600; white-space:nowrap; }}

/* --- шапка --- */
.hero {{ display:grid; grid-template-columns: minmax(260px,1.1fr) minmax(200px,0.7fr) minmax(300px,1.6fr);
         gap:24px; padding:18px 22px; border-radius:14px; background:{t['hero']}; border:1px solid {t['border']}; }}
.eyebrow {{ font-size:11px; letter-spacing:.08em; text-transform:uppercase; color:{t['muted']}; font-weight:600; }}
.phase {{ font-size:30px; font-weight:700; line-height:1.1; margin:4px 0 6px; }}
.phase-desc {{ font-size:13.5px; color:{t['text2']}; line-height:1.4; }}
.axes {{ display:flex; flex-direction:column; gap:10px; justify-content:center; }}
.axis {{ display:flex; justify-content:space-between; align-items:center; gap:10px;
         padding:8px 12px; border-radius:10px; background:{t['card']}; border:1px solid {t['border']}; }}
.axis b {{ font-size:14px; }}
.regime {{ font-size:13px; color:{t['text2']}; line-height:1.45; margin-top:12px; padding-top:10px;
           border-top:1px solid {t['border']}; }}
.regime b {{ color:{t['text']}; }}
.sigs {{ display:flex; flex-direction:column; gap:6px; }}
.sig {{ display:flex; align-items:center; gap:8px; font-size:13px; line-height:1.3; padding:5px 8px;
        border-radius:8px; cursor:pointer; }}
.sig:hover {{ background:{t['card']}; }}

/* --- сетка: колонки-группы на subgrid, плитки одной строки равной высоты --- */
.grid {{ display:grid; grid-template-columns: repeat(6, minmax(0,1fr)); grid-auto-rows:auto; column-gap:12px; row-gap:12px; }}
.group {{ display:grid; grid-template-rows: subgrid; grid-row: span 4; row-gap:12px; }}
.ghead {{ display:flex; justify-content:space-between; align-items:center; gap:6px; padding:2px 4px 0;
          border-bottom:2px solid {t['border']}; padding-bottom:8px; }}
.ghead .gname {{ font-size:14px; font-weight:700; }}
.ghead .pill {{ font-size:12px; }}

.tile {{ position:relative; display:grid; grid-template-rows: auto auto auto 1fr auto auto; gap:5px;
         padding:12px 14px 12px; border-radius:12px; background:{t['card']}; border:1px solid {t['border']};
         cursor:pointer; transition: border-color .15s, box-shadow .15s, transform .15s; outline:none; min-width:0; }}
.tile:hover, .tile:focus-visible {{ border-color:{t['hover']}; box-shadow:0 4px 14px {t['shadow']}; transform:translateY(-1px); }}
.tile:hover .open, .tile:focus-visible .open {{ opacity:1; }}
.open {{ position:absolute; right:10px; bottom:10px; font-size:12px; color:{t['hover']}; opacity:0; transition:opacity .15s; }}
.top {{ display:flex; justify-content:space-between; align-items:center; gap:6px; min-width:0; }}
.kind {{ font-size:10px; letter-spacing:.06em; font-weight:700; color:{t['muted']}; }}
.top .date {{ font-size:11px; color:{t['muted']}; }}
.name {{ font-size:14px; font-weight:650; line-height:1.25; min-height:2.5em; display:-webkit-box;
         -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }}
.metric {{ font-size:11.5px; color:{t['muted']}; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; margin-top:-4px; }}
.dial {{ display:flex; flex-direction:column; align-items:center; }}
.dial svg {{ width:100%; max-width:190px; height:auto; display:block; }}
.val {{ font-size:26px; font-weight:700; line-height:1; margin-top:2px; }}
.val small {{ font-size:12px; font-weight:500; color:{t['text2']}; margin-left:3px; }}
.delta {{ font-size:11.5px; color:{t['text2']}; margin-top:3px; }}
.status {{ margin-top:8px; padding:4px 10px; border-radius:999px; background:{t['page']}; border:1px solid {t['border']};
           max-width:100%; }}
.status .pill {{ font-size:13px; white-space:normal; text-align:left; line-height:1.2; }}
.spark {{ width:100%; height:34px; display:block; }}
.foot {{ display:flex; align-items:center; gap:8px; font-size:11px; color:{t['muted']}; min-height:18px; }}
.track {{ position:relative; flex:1; height:4px; border-radius:2px; background:{t['track']}; min-width:30px; }}
.mark {{ position:absolute; top:-3px; width:3px; height:10px; border-radius:2px; background:{t['text']}; }}
.date {{ white-space:nowrap; }}
.foot .pct {{ white-space:nowrap; }}
.date.stale {{ color:{STATUS_COLOR['serious']}; }}
.xbadge {{ display:inline-flex; align-items:center; gap:4px; font-size:11px; font-weight:600; color:{t['text']};
           white-space:nowrap; }}
.legend {{ display:flex; flex-wrap:wrap; gap:14px; font-size:12px; color:{t['text2']}; padding:2px 4px; }}

@media (max-width: 1400px) {{ .grid {{ grid-template-columns: repeat(3, minmax(0,1fr)); }}
                              .hero {{ grid-template-columns: 1fr 1fr; }} .hero .sigs-col {{ grid-column: span 2; }} }}
@media (max-width: 760px)  {{ .grid {{ grid-template-columns: minmax(0,1fr); }}
                              .hero {{ grid-template-columns: 1fr; }} .hero .sigs-col {{ grid-column: auto; }} }}
"""


def pill(status: str, label: str) -> str:
    return (f'<span class="pill"><span class="ic" style="background:{STATUS_COLOR[status]}">'
            f'{STATUS_ICON[status]}</span>{escape(label)}</span>')


def _fmt(v: float, digits: int) -> str:
    return f"{v:,.{digits}f}".replace(",", " ").replace("-", "−")


def _period(ts: pd.Timestamp, freq: str) -> str:
    if freq == "Q":
        return f"{['I', 'II', 'III', 'IV'][(ts.month - 1) // 3]} кв. {ts.year}"
    if freq == "M":
        return f"{MONTHS[ts.month - 1]} {ts.year}"
    return ts.strftime("%d.%m.%y")


# ---------- стрелочный прибор ----------

def _polar(cx, cy, r, t):
    """t: 0 — левый конец дуги, 1 — правый."""
    a = math.pi * (1 - t)
    return cx + r * math.cos(a), cy - r * math.sin(a)


def _arc(cx, cy, r, t0, t1):
    x0, y0 = _polar(cx, cy, r, t0)
    x1, y1 = _polar(cx, cy, r, t1)
    return f"M{x0:.2f},{y0:.2f} A{r},{r} 0 0 1 {x1:.2f},{y1:.2f}"


def gauge(res: Result, mode: str) -> str:
    t = TOKENS[mode]
    lo, hi = res.ind.domain
    W, H, cx, cy, r = 180, 100, 90, 92, 74

    def T(v):
        return min(max((v - lo) / (hi - lo), 0), 1)

    # зоны порогов, между зонами — зазор цвета фона (разделитель вместо обводки)
    edges = [lo] + [b[0] for b in res.bands if lo < b[0] < hi] + [hi]
    statuses = []
    for a, b in zip(edges[:-1], edges[1:]):
        mid = (a + b) / 2
        st = next((s for lim, s, _ in res.bands if mid < lim), res.ind.top[0])
        statuses.append(st)
    gap = 0.006
    arcs = "".join(
        f'<path d="{_arc(cx, cy, r, T(a) + (gap if i else 0), T(b) - (gap if i < len(statuses) - 1 else 0))}" '
        f'stroke="{STATUS_COLOR[s]}" stroke-width="9" fill="none" opacity="0.85"/>'
        for i, ((a, b), s) in enumerate(zip(zip(edges[:-1], edges[1:]), statuses)))
    nt = T(res.value)
    nx, ny = _polar(cx, cy, r - 16, nt)
    tip = "" if lo <= res.value <= hi else f'<text x="{cx}" y="{cy - 22}" text-anchor="middle" font-size="10" fill="{t["muted"]}">за шкалой</text>'
    lx, ly = _polar(cx, cy, r, 0)
    rx, ry = _polar(cx, cy, r, 1)
    return f"""<svg viewBox="0 0 {W} {H}" role="img" aria-label="{escape(res.ind.name)}: {_fmt(res.value, res.ind.digits)}">
  {arcs}
  <line x1="{cx}" y1="{cy}" x2="{nx:.2f}" y2="{ny:.2f}" stroke="{t['text']}" stroke-width="3" stroke-linecap="round"/>
  <circle cx="{cx}" cy="{cy}" r="5" fill="{t['text']}"/>
  <text x="{lx + 2}" y="{ly + 8}" font-size="9.5" fill="{t['muted']}" text-anchor="start">{_fmt(lo, 0)}</text>
  <text x="{rx - 2}" y="{ry + 8}" font-size="9.5" fill="{t['muted']}" text-anchor="end">{_fmt(hi, 0)}</text>
  {tip}
</svg>"""


def sparkline(s: pd.Series, recessions: list[tuple], mode: str, years: int = 5) -> str:
    t = TOKENS[mode]
    s = s.dropna()
    s = s[s.index >= s.index[-1] - pd.DateOffset(years=years)]
    if len(s) > 300:
        s = s.resample("W").last().dropna()
    x0, x1 = s.index[0].value, s.index[-1].value
    lo, hi = float(s.min()), float(s.max())
    pad = (hi - lo) * 0.1 or 1
    lo, hi = lo - pad, hi + pad
    W, H = 200, 34

    def X(ts):
        return (pd.Timestamp(ts).value - x0) / (x1 - x0) * W if x1 > x0 else 0

    def Y(v):
        return H - (v - lo) / (hi - lo) * H

    parts = []
    for a, b in recessions:
        if b >= s.index[0] and a <= s.index[-1]:
            xa, xb = max(X(a), 0), min(X(b), W)
            parts.append(f'<rect x="{xa:.1f}" y="0" width="{xb - xa:.1f}" height="{H}" fill="{t["rec"]}"/>')
    if lo < 0 < hi:
        parts.append(f'<line x1="0" x2="{W}" y1="{Y(0):.1f}" y2="{Y(0):.1f}" stroke="{t["grid"]}" '
                     'stroke-width="1" vector-effect="non-scaling-stroke"/>')
    pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in s.items())
    parts.append(f'<polygon points="0,{H} {pts} {W},{H}" fill="{t["series"]}" opacity="0.10"/>')
    parts.append(f'<polyline points="{pts}" fill="none" stroke="{t["series"]}" stroke-width="2" '
                 'stroke-linejoin="round" stroke-linecap="round" vector-effect="non-scaling-stroke"/>')
    title = f"{years} лет: от {s.min():,.2f} до {s.max():,.2f}"
    return (f'<svg class="spark" viewBox="0 0 {W} {H}" preserveAspectRatio="none" role="img" '
            f'aria-label="{escape(title)}"><title>{escape(title)}</title>{"".join(parts)}</svg>')


# ---------- плитка, группа, шапка ----------

def tile(res: Result, recessions: list[tuple], mode: str) -> str:
    ind, s = res.ind, res.r.series.dropna()
    last_date = s.index[-1]
    past = s[s.index <= last_date - pd.DateOffset(months=ind.delta_months)]
    if len(past):
        d = res.value - float(past.iloc[-1])
        arrow = "▲" if d > 0 else "▼" if d < 0 else "■"
        delta = f"{arrow} {_fmt(d, ind.digits) if d < 0 else '+' + _fmt(d, ind.digits)} за {ind.delta_months} мес."
    else:
        delta = "&nbsp;"
    spark_src = res.r.spark if res.r.spark is not None else s
    xbadge = ""
    if res.extreme:
        txt = "Ист. минимум" if res.extreme == "low" else "Ист. максимум"
        note = ind.extreme_low if res.extreme == "low" else ind.extreme_high
        xbadge = (f'<span class="xbadge" title="{escape(note or txt)}"><span class="ic" '
                  f'style="background:{STATUS_COLOR["extreme"]};width:14px;height:14px;font-size:8px">◆</span>{txt}</span>')
    stale = " stale" if res.stale else ""
    stale_title = "Данные давно не обновлялись" if res.stale else "Последнее наблюдение"
    tip = res.r.extra or ind.how_to_read
    return f"""<div class="tile" data-key="{ind.key}" role="button" tabindex="0" title="{escape(tip)}">
  <div class="top"><span class="kind" title="{ind.kind} индикатор">{KIND_SHORT[ind.kind]}</span>
    <span class="date{stale}" title="{stale_title}">{_period(last_date, ind.freq)}</span></div>
  <div class="name">{escape(ind.name)}</div>
  <div class="metric">{escape(ind.metric)}</div>
  <div class="dial">{gauge(res, mode)}
    <div class="val">{_fmt(res.value, ind.digits)}<small>{escape(ind.units)}</small></div>
    <div class="delta">{delta}</div>
    <div class="status">{pill(res.status, res.label)}</div>
  </div>
  {sparkline(spark_src, recessions, mode)}
  <div class="foot">
    <div class="track" title="{res.percentile:.0f}-й перцентиль: доля наблюдений с {s.index[0]:%Y} г. ниже текущего">
      <div class="mark" style="left:calc({res.percentile:.0f}% - 1.5px)"></div></div>
    {xbadge or f'<span class="pct">{res.percentile:.0f}-й перцентиль</span>'}
  </div>
  <span class="open">подробнее ↗</span>
</div>"""


def hero(phase: Phase, regime, mode: str) -> str:
    sigs = "".join(
        f'<div class="sig" data-key="{s.key}" role="button" tabindex="0"><span class="ic" '
        f'style="background:{STATUS_COLOR[s.status]}">{STATUS_ICON[s.status]}</span>{escape(s.text)}</div>'
        for s in phase.signals) or '<div class="sig">Тревожных сигналов нет</div>'
    reg = ""
    if regime is not None:
        rg, best, worst = regime
        fmt = lambda items: ", ".join(f"{escape(n.split(' (')[0].split(' — ')[0])} {v:+.0f}%" for n, v in items)
        reg = (f'<div class="regime">Режим: <b>{escape(rg.name)}</b> — {escape(rg.description)}, '
               f'{rg.months} мес. · данные за {MONTHS[rg.as_of.month - 1]} {rg.as_of.year}<br>'
               f'Исторически в нём лучше: {fmt(best)}; хуже: {fmt(worst)} (% годовых)</div>')
    return f"""<div class="hero">
  <div><div class="eyebrow">Фаза цикла</div><div class="phase">{escape(phase.name)}</div>
       <div class="phase-desc">{escape(phase.description)}</div>{reg}</div>
  <div class="axes">
    <div class="axis"><b>Экономика</b>{pill(*phase.economy)}</div>
    <div class="axis"><b>Рынок</b>{pill(*phase.market)}</div>
  </div>
  <div class="sigs-col"><div class="eyebrow" style="margin-bottom:6px">Главные сигналы</div><div class="sigs">{sigs}</div></div>
</div>"""


def page(results: dict[str, Result], errors: dict[str, str], phase: Phase, regime,
         recessions: list[tuple], mode: str) -> str:
    cols = []
    for g in GROUPS:
        rs = [r for r in results.values() if r.ind.group == g]
        head = pill(*group_status([r.status for r in rs])) if rs else ""
        tiles = "".join(tile(r, recessions, mode) for r in rs)
        tiles += "".join(f'<div class="tile"><div class="name">{escape(k)}</div><div class="metric">{escape(e)}</div></div>'
                         for k, e in errors.items() if k.startswith(g + ":"))
        cols.append(f'<div class="group"><div class="ghead"><span class="gname">{escape(g)}</span>{head}</div>{tiles}</div>')
    legend = "".join(f'<span>{pill(s, l)}</span>' for s, l in
                     [("good", "попутный ветер"), ("warning", "внимание"), ("serious", "напряжение"),
                      ("critical", "сильный встречный ветер"), ("neutral", "нейтрально"), ("extreme", "исторический экстремум")])
    return (f'<div class="ck">{hero(phase, regime, mode)}<div class="grid">{"".join(cols)}</div>'
            f'<div class="legend">{legend}<span>· ОПЕРЕЖ./СОВПАД./ЗАПАЗД. — тип индикатора · серые полосы — рецессии · '
            f'полоска внизу — перцентиль в истории</span></div></div>')
