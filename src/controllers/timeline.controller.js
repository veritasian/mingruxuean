/**
 * timeline.controller.js —— 时间线控制器
 *
 * 只管两件事：按皇帝筛选、把筛出来的人列在下面。
 * 画图的活在 timeline.view 里。
 */
import { $, clear } from '../core/dom.js';
import * as view from '../views/timeline.view.js';

export function create(model, { onPick }) {
  const svgEl = $('#tline');
  const empSel = $('#empSel');
  const empList = $('#empList');
  let bars = new Map();
  let built = false;

  function build() {
    if (built) return;
    built = true;
    const r = view.render(svgEl, model, {
      onPick,
      onEmperor: (era) => filter(era),
    });
    bars = r.bars;
    empSel.innerHTML = '<option value="">— 全部 —</option>'
      + (model.timeline.emperors || [])
        .map((e) => `<option value="${e.era}">${e.n}代 ${e.era}（${e.start}–${e.end}）</option>`)
        .join('');
  }

  function filter(era) {
    build();
    empSel.value = era;
    svgEl.querySelectorAll('.tbar')
      .forEach((r) => r.classList.toggle('dim', r.getAttribute('data-em') !== era));
    const hits = new Set(view.renderEmperorList(empList, model, era, { onPick }));
    bars.forEach((b, id) => b.classList.toggle('dim', !hits.has(id)));
  }

  function reset() {
    empSel.value = '';
    svgEl.querySelectorAll('.tbar').forEach((r) => r.classList.remove('dim'));
    bars.forEach((b) => b.classList.remove('dim'));
    clear(empList);
  }

  empSel.addEventListener('change', () => (empSel.value ? filter(empSel.value) : reset()));
  $('#empReset').addEventListener('click', reset);

  return {
    enter({ params }) {
      build();
      if (params[0]) filter(params[0]);
    },
    barEl: (id) => bars.get(id) || null,
  };
}
