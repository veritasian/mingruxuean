/**
 * theme.controller.js —— 纸墨风格切换
 *
 * 主题只是把 data-theme 写在 <html> 上，具体颜色全在 tokens.css。
 * 有一个例外：SVG 的 marker 不吃 CSS 变量，箭头颜色得手动刷，
 * 所以切完主题要广播一声，让谱系图自己去重画箭头。
 */
import { $, el } from '../core/dom.js';
import { emit, EV } from '../core/bus.js';
import * as store from '../core/store.js';

const THEMES = [['zen', '朱印'], ['ink', '水墨'], ['white', '纯白']];
const VALID = new Set(THEMES.map((t) => t[0]));

export function create() {
  const box = $('#themeSw');
  for (const [id, label] of THEMES) {
    const b = el('button', { dataset: { t: id }, text: label });
    b.addEventListener('click', () => apply(id));
    box.appendChild(b);
  }

  function apply(t) {
    if (!VALID.has(t)) return;
    document.documentElement.dataset.theme = t;
    store.set('theme', t);
    box.querySelectorAll('button').forEach((x) => x.classList.toggle('on', x.dataset.t === t));
    emit(EV.THEME_CHANGED, t);
  }

  // 优先级：地址栏 ?theme= > 上次选择 > 默认朱印
  const q = new URLSearchParams(location.search).get('theme');
  apply(VALID.has(q) ? q : (store.get('theme') || 'zen'));

  return { apply, current: () => store.get('theme') };
}
