"""Приборная панель: всё состояние экономики США на одном экране.

Вся панель — один HTML-блок (components.v2), чтобы сетка была ровной.
Клик по плитке или сигналу отправляет ключ прибора в Python → окно подробностей.
"""
import streamlit as st

from core import phase as phase_mod
from core import ui
from core.charts import theme
from core.cockpit_html import css, page
from core.details import current_regime, details, results

JS = """
export default function (component) {
  const { data, parentElement, setTriggerValue } = component;
  let root = parentElement.querySelector('.ck-root');
  if (!root) {
    root = document.createElement('div');
    root.className = 'ck-root';
    parentElement.appendChild(root);
    const open = (el) => { if (el && el.dataset.key) setTriggerValue('open', el.dataset.key); };
    root.addEventListener('click', (e) => open(e.target.closest('[data-key]')));
    root.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(e.target.closest('[data-key]')); }
    });
  }
  root.innerHTML = data;
}
"""


@st.cache_resource
def _component(mode: str):
    return st.components.v2.component(f"cockpit_{mode}", css=css(mode), js=JS)


mode = theme()
res, errors = results()
ph = phase_mod.classify(res)
html = page(res, errors, ph, current_regime(), ui.recessions(), mode)
out = _component(mode)(data=html, key="cockpit", on_open_change=lambda: None)
if out.open:
    details(out.open)
