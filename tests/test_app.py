"""Прогон всех рядов × всех преобразований через UI: uv run python tests/test_app.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from streamlit.testing.v1 import AppTest

from core.series import CATALOG, GROUPS

ROOT = Path(__file__).resolve().parent.parent

at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
assert not at.exception, at.exception  # панель

from core import data
from core.indicators import INDICATORS, evaluate
from core.phase import classify
res = {i.key: evaluate(i, data.load) for i in INDICATORS}
assert classify(res).name
print(f"панель: {len(res)} приборов, фаза «{classify(res).name}»")

# окно «Подробнее» для каждого прибора (клик внутри HTML-блока AppTest нажать не умеет)
for i in INDICATORS:
    dt = AppTest.from_string(f"""
import sys; sys.path.insert(0, {str(ROOT)!r})
from core.details import render_details
render_details({i.key!r})
""", default_timeout=120).run()
    assert not dt.exception, (i.key, dt.exception)
print("окно подробностей: все приборы ок")

at.switch_page("views/regime.py").run()
assert not at.exception, at.exception
for m in at.segmented_control[0].options:
    at.segmented_control[0].set_value(m).run()
    assert not at.exception, (m, at.exception)
    at.toggle[0].set_value(False).run()
    assert not at.exception, (m, "без лага", at.exception)
    at.toggle[0].set_value(True).run()
print("режим экономики ок")

at.switch_page("views/rates.py").run()
assert not at.exception, at.exception
for v in [(1, 0.0, 0.0, -3.0), (30, 10.0, 12.0, 3.0), (10, 4.0, 4.0, 0.0)]:  # края ползунков
    for sl, x in zip(at.slider, v):
        sl.set_value(x)
    at.run()
    assert not at.exception, (v, at.exception)
for p in at.segmented_control[0].options:
    at.segmented_control[0].set_value(p).run()
    assert not at.exception, (p, at.exception)
print("ставки и облигации ок")

at.switch_page("views/liquidity.py").run()
assert not at.exception, at.exception
for p in at.segmented_control[0].options:
    at.segmented_control[0].set_value(p).run()
    assert not at.exception, (p, at.exception)
print("ликвидность и долг ок")

at.switch_page("views/valuation.py").run()
assert not at.exception, at.exception
for v in [(-1.0, 0.0, 4.0), (5.0, 8.0, 0.0), (1.0, 1.0, 2.0)]:  # края ползунков, включая r ≤ g
    for sl, x in zip(at.slider, v):
        sl.set_value(x)
    at.run()
    assert not at.exception, (v, at.exception)
for p in at.segmented_control[0].options:
    at.segmented_control[0].set_value(p).run()
    assert not at.exception, (p, at.exception)
print("оценка рынка ок")

at.switch_page("views/sectors.py").run()
assert not at.exception, at.exception
for p in at.segmented_control[0].options:
    at.segmented_control[0].set_value(p).run()
    assert not at.exception, (p, at.exception)
print("акции и сектора ок")

at.switch_page("views/stock.py").run()
assert not at.exception, at.exception
for tk in ["XOM", "JPM", "NVDA", "ZZZZZZ"]:  # цикличная, банк, рост, несуществующий тикер
    at.text_input(key="ticker").set_value(tk).run()
    assert not at.exception, (tk, at.exception)
assert at.error, "для несуществующего тикера должна быть ошибка"
print("отдельная акция ок")

at.switch_page("views/explorer.py").run()
assert not at.exception, at.exception
for g in GROUPS:
    at.selectbox[0].set_value(g).run()
    for k in [s.key for s in CATALOG if s.group == g]:
        at.selectbox[1].set_value(k).run()
        assert not at.exception, (k, at.exception)
        for tr in at.selectbox[2].options:
            at.selectbox[2].set_value(tr).run()
            assert not at.exception, (k, tr, at.exception)
at.switch_page("views/data_status.py").run()
assert not at.exception, at.exception
print(f"OK: {len(CATALOG)} рядов, страница данных — {len(at.dataframe[0].value)} строк")

# ---------- новая версия: цепочка слоёв ----------
at.radio(key="version").set_value("Новая (в разработке)").run()
assert not at.exception, at.exception
at.switch_page("views/v2/map.py").run()
assert not at.exception, at.exception
assert not at.warning, [w.value for w in at.warning]  # у каждого слоя карты есть ответ
print("карта ок")


def check_layer(page: str, examples: list[str], name: str) -> None:
    """Экран слоя: все периоды, все группы примеров и каждый пример внутри группы."""
    at.switch_page(page).run()
    assert not at.exception, at.exception
    for p in at.segmented_control(key="period").options:
        at.segmented_control(key="period").set_value(p).run()
        assert not at.exception, (page, p, at.exception)
    for ex in examples:
        at.toggle(key=f"ex_{ex}").set_value(True).run()
        assert not at.exception, (ex, at.exception)
        for kind in at.segmented_control(key=f"exk_{ex}").options:
            at.segmented_control(key=f"exk_{ex}").set_value(kind).run()
            assert not at.exception, (ex, kind, at.exception)
            for r in [r for r in at.radio if r.key and r.key.startswith(f"exr_{ex}_")]:
                for opt in r.options:
                    r.set_value(opt).run()
                    assert not at.exception, (ex, kind, opt, at.exception)
    print(f"{name} ок")


check_layer("views/v2/structure.py", ["supply", "rstar", "debt", "private"], "структура и долг")
check_layer("views/v2/policy.py", ["stance", "rules", "market", "balance"], "политика ФРС")
check_layer("views/v2/market_rates.py", ["decomp", "expect", "curve"], "рыночные ставки")
check_layer("views/v2/credit.py", ["fcig", "spread", "banks", "recession"], "финансовые условия")
check_layer("views/v2/growth.py", ["speed", "slack", "labor", "risk"], "рост и риск рецессии")
check_layer("views/v2/inflation.py", ["level", "breadth", "mix", "phillips"], "инфляция")
check_layer("views/v2/markets.py", ["identity", "value", "mix", "gold"], "рынки")

at.switch_page("views/v2/help.py").run()
assert not at.exception, at.exception
at.text_input(key="glossary_q").set_value("ставка").run()
assert not at.exception, at.exception
print("справка ок")
