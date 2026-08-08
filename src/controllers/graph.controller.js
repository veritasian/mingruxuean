/**
 * graph.controller.js —— 谱系总图控制器
 *
 * 决定「谁该高亮、镜头往哪看」，具体怎么画交给 graph.view，
 * 怎么缩放交给 pan-zoom 引擎。控制器自己不写一行 SVG。
 */
import { $, el } from '../core/dom.js';
import { on, EV } from '../core/bus.js';
import * as store from '../core/store.js';
import * as view from '../views/graph.view.js';

export function create(model, { onPick }) {
  const svgEl = $('#graph');
  const g = view.create(svgEl, model, {
    onPick: (id, node) => { focusPerson(id); onPick(id, node); },
  });
  g.repaintMarkers();

  buildLegend();
  buildSelect();

  $('#reset').addEventListener('click', () => {
    g.fitAll();
    g.clearHighlight();
    document.querySelectorAll('.legend .chip').forEach((c) => c.classList.remove('active'));
    $('#focusSel').value = '';
    store.set('focusedSchool', null);
  });

  const orderSel = $('#orderSel');
  if (orderSel) orderSel.addEventListener('change', () => g.setOrder(orderSel.value));

  svgEl.addEventListener('click', () => {
    if (g.pz.consumedClick()) return;
    g.clearHighlight();
  });

  on(EV.THEME_CHANGED, () => g.repaintMarkers());

  function buildLegend() {
    const box = $('#legend');
    box.innerHTML = '';
    for (const s of model.schools) {
      const n = (model.members[s.id] || []).length;
      const orphan = (model.orphanData.by_school || {})[s.id];
      const chip = el('span.chip', {
        dataset: { sch: s.id },
        title: orphan ? `${s.id}：${n} 人，其中孤点 ${orphan.orphans} 人` : `${s.id}：${n} 人`,
        html: `<span class="dot" style="background:${model.colorOf(s.id)}"></span>${s.id}（${n}）`,
      });
      chip.addEventListener('click', () => focusSchool(s.id));
      box.appendChild(chip);
    }
  }

  function buildSelect() {
    const sel = $('#focusSel');
    sel.innerHTML = '<option value="">— 全部学派 —</option>'
      + model.schools.map((s) => `<option value="${s.id}">${s.id}</option>`).join('');
    sel.addEventListener('change', () => {
      if (sel.value) focusSchool(sel.value);
      else { g.fitAll(); g.clearHighlight(); }
    });
  }

  function focusSchool(school) {
    const ids = model.members[school] || [];
    if (!ids.length) return;
    g.fitIds(ids);
    g.highlight(ids);
    document.querySelectorAll('.legend .chip')
      .forEach((c) => c.classList.toggle('active', c.dataset.sch === school));
    $('#focusSel').value = school;
    store.set('focusedSchool', school);
  }

  /** 选中一人，连带上溯师承、下延门人一起亮起来 */
  function focusPerson(id) {
    const keep = new Set([id, ...model.ancestors(id), ...model.descendants(id)]);
    g.highlight([...keep]);
  }

  return {
    enter({ params, query }) {
      if (query === 'all') g.fitAll();
      else if (params[0] && model.persons[params[0]]) {
        focusPerson(params[0]);
        g.center(params[0]);
      } else g.fitReadable();
    },
    locate(id) {
      focusPerson(id);
      g.center(id);
      return g.nodeEl(id);
    },
    view: g,
  };
}
