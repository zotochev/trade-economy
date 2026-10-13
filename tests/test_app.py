"""Прогон всех рядов × всех преобразований через UI: uv run python tests/test_app.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from streamlit.testing.v1 import AppTest

from core.series import CATALOG, GROUPS

ROOT = Path(__file__).resolve().parent.parent

at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
assert not at.exception, at.exception  # по умолчанию — новая версия, карта
at.radio(key="version").set_value("Старая").run()
assert not at.exception, at.exception  # панель старой версии

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
at.radio(key="version").set_value("Новая").run()
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
check_layer("views/v2/market_rates.py", ["decomp", "expect", "curve", "bonds"], "рыночные ставки")
check_layer("views/v2/credit.py", ["fcig", "spread", "banks", "recession"], "финансовые условия")
check_layer("views/v2/growth.py", ["speed", "slack", "labor", "risk"], "рост и риск рецессии")
check_layer("views/v2/inflation.py", ["level", "breadth", "mix", "phillips"], "инфляция")
check_layer("views/v2/flows.py", ["study", "models", "positions"], "вынужденные потоки")
for kind in ["quarter_end", "opex_monthly", "vix_expiry", "russell_recon", "year_end", "ru_tax_period"]:
    at.selectbox(key="fl_kind").set_value(kind).run()
    assert not at.exception, (kind, at.exception)
for key in ["ES", "NQ", "TY", "JY", "BTC"]:
    at.selectbox(key="fl_cot").set_value(key).run()
    assert not at.exception, (key, at.exception)
for asset in ["Биткоин", "Иен за доллар", "Рублей за доллар (курс ЦБ)"]:
    at.selectbox(key="fl_asset").set_value(asset).run()
    assert not at.exception, (asset, at.exception)
check_layer("views/v2/markets.py", ["identity", "value", "mix", "gold"], "рынки")

for page in ["views/sectors.py", "views/stock.py", "views/regime.py"]:  # «Подробнее о рынках»
    at.switch_page(page).run()
    assert not at.exception, (page, at.exception)

# лаборатория облигаций: все примеры, все типы, ориентиры по рейтингу, режим реальной облигации
at.switch_page("views/bond_lab.py").run()
assert not at.exception, at.exception
for b in [b for b in at.button if b.key and b.key.startswith("bl_p_")]:
    b.click().run()
    assert not at.exception, (b.key, at.exception)
for kind in ["fixed", "zero", "floating", "tips"]:
    at.selectbox(key="bl_kind").set_value(kind).run()
    assert not at.exception, (kind, at.exception)
for r in at.selectbox(key="bl_rating").options:
    at.selectbox(key="bl_rating").set_value(r).run()
    assert not at.exception, (r, at.exception)
at.slider(key="bl_years").set_value(1.0).run()
at.slider(key="bl_delta").set_value(-2.0).run()
assert not at.exception, at.exception
# от спреда к цене и обратно: цифры не должны скакать, настройки — сбрасываться
at.slider(key="bl_shock").set_value(2.0).run()
at.selectbox(key="bl_kind").set_value("fixed").run()
at.slider(key="bl_spread").set_value(1.5).run()
at.segmented_control(key="bl_known").set_value("Цена → считаем доходность").run()
assert not at.exception, at.exception
assert abs(float(at.metric[2].value.split()[0]) - 1.5) < 0.02, at.metric[2].value  # спред восстановлен из цены
at.number_input(key="bl_price").set_value(90.0).run()
at.segmented_control(key="bl_term").set_value("Датой погашения").run()
at.slider(key="bl_delta").set_value(-1.0).run()
assert not at.exception, at.exception
assert at.slider(key="bl_shock").value == 2.0, "сдвиг ставки сбросился"
assert at.number_input(key="bl_price").value == 90.0, "цена сбросилась"
for kind in ["zero", "tips", "floating"]:
    at.selectbox(key="bl_kind").set_value(kind).run()
    assert not at.exception, ("по цене", kind, at.exception)
at.checkbox(key="bl_call").check().run()
at.button(key="bl_mpd").click().run()
assert not at.exception, at.exception
# Россия: облигации Мосбиржи по тикеру — сверка доходности с биржей, оферта, амортизация, ошибка тикера
at.segmented_control(key="bl_market").set_value("Россия").run()
assert not at.exception, at.exception
for ticker in ["SU26238RMFS4", "RU000A0GN9A7", "SU52002RMFS1", "SU29008RMFS8", "RU000A0JS4Z7"]:
    at.text_input(key="bl_ticker").set_value(ticker).run()
    at.button(key="bl_load").click().run()
    assert not at.exception, (ticker, at.exception)
    assert not at.error, (ticker, [e.value for e in at.error])
    ours = float(at.metric[1].value.rstrip("%"))
    if at.metric[1].delta and at.metric[1].delta.startswith("биржа"):
        theirs = float(at.metric[1].delta.split()[1].rstrip("%"))
        assert abs(ours - theirs) < 0.2, (ticker, ours, theirs)
    print(f"  {ticker}: {ours:.2f}% ({at.metric[1].delta})")
at.segmented_control(key="bl_known").set_value("Спред → считаем цену").run()
assert not at.exception, at.exception
at.button(key="bl_unlink").click().run()
at.text_input(key="bl_ticker").set_value("НЕТТАКОГО").run()
at.button(key="bl_load").click().run()
assert not at.exception and at.error, "ошибка тикера должна показываться, а не ронять страницу"
at.segmented_control(key="bl_market").set_value("США").run()
assert not at.exception, at.exception
print("лаборатория облигаций ок")
at.switch_page("views/v2/help.py").run()
assert not at.exception, at.exception
at.text_input(key="glossary_q").set_value("ставка").run()
assert not at.exception, at.exception
print("справка ок")
