/**
 * orphan.controller.js —— 孤点现象控制器
 *
 * 这一页几乎是静态的：数据在 orphans.json 里已经分好类，
 * 控制器只负责渲染一次，再把「去图谱看看」这个按钮接上。
 */
import { $, el } from '../core/dom.js';
import * as view from '../views/orphan.view.js';

export function create(model, { onPick, onShowInKG }) {
  const box = $('#orphanBody');
  let built = false;

  function build() {
    if (built) return;
    built = true;
    view.render(box, model, { onPick });
    const act = el('div.orphan-act');
    const btn = el('button.btn', { text: '在知识图谱中只看这些孤点' });
    btn.addEventListener('click', () => onShowInKG && onShowInKG());
    act.appendChild(btn);
    box.appendChild(act);
  }

  return { enter() { build(); } };
}
