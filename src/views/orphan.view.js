/**
 * orphan.view.js —— 孤点现象
 *
 * 图上那些不连线的圆点，一直被当成「数据没做完」。做完这一轮抽取
 * 才看清楚：绝大多数孤点各有各的来由，真正待补的是很小的一撮。
 *
 * 分类与文案全部来自 data/orphans.json —— 这一页不自己下判断。
 * 后端新增一类（如「附于他人传后」），这里会自动多出一张卡，
 * 不会出现「Python 分了五类、页面只画四类、剩下的人凭空消失」。
 * 顺序按 PREFERRED 走：先讲不是缺口的，最后才讲缺口。
 */
import { el, clear, esc } from '../core/dom.js';

const PREFERRED = ['structural', 'horizontal', 'appendix', 'no_record', 'gap'];
const KIND_TONE = {
  structural: 'tone-book', horizontal: 'tone-net', appendix: 'tone-fold',
  no_record: 'tone-void', gap: 'tone-gap',
};
const CN_NUM = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十'];

/** 认得的排前面，认不得的排后面 —— 总之一个都不能丢 */
function kindsOf(data) {
  const all = Object.keys(data.kinds || {});
  const known = PREFERRED.filter((k) => all.includes(k));
  return known.concat(all.filter((k) => !PREFERRED.includes(k)));
}

const toneOf = (kind) => KIND_TONE[kind] || 'tone-void';

export function render(container, model, { onPick } = {}) {
  clear(container);
  const data = model.orphanData;
  const meta = data.meta || {};
  const order = kindsOf(data);
  const nk = CN_NUM[order.length] || String(order.length);

  container.appendChild(el('div.orphan-lead', {
    html: `<p class="lead-1">${esc(meta.headline || '')}</p>
      <p class="lead-2">全书 ${meta.person_count} 人，图上不连线者 ${meta.orphan_count} 人，
      占 ${(meta.orphan_count / meta.person_count * 100).toFixed(1)}%。
      把这 ${meta.orphan_count} 个点逐一读回原书，它们分成${nk}类；
      只有最后一类算本项目的账。</p>`,
  }));

  container.appendChild(summaryBar(data, order));

  const grouped = new Map(order.map((k) => [k, []]));
  const stray = [];
  for (const o of data.orphans || []) {
    if (grouped.has(o.kind)) grouped.get(o.kind).push(o);
    else stray.push(o);
  }
  if (stray.length) console.warn('[孤点] 未定义类别，已归入「其它」：', stray.map((o) => o.id));

  const grid = el('div.orphan-kinds');
  for (const kind of order) {
    grid.appendChild(kindCard(kind, data.kinds[kind] || {}, grouped.get(kind), model, onPick));
  }
  container.appendChild(grid);

  container.appendChild(el('div.tab-head', {
    html: '各学案孤点率 <small>比率高不等于做得差 —— 要看它属于哪一类</small>',
  }));
  container.appendChild(schoolBars(data, model));
  return container;
}

function summaryBar(data, order) {
  const meta = data.meta || {};
  const total = meta.orphan_count || 1;
  const bar = el('div.orphan-bar');
  for (const kind of order) {
    const n = (meta.by_kind || {})[kind] || 0;
    if (!n) continue;
    const seg = el(`span.oseg.${toneOf(kind)}`, {
      title: `${(data.kinds[kind] || {}).label || kind}：${n} 人`,
      html: `<b>${n}</b>`,
    });
    seg.style.flex = String(n);
    bar.appendChild(seg);
  }
  const legend = el('div.orphan-legend');
  for (const kind of order) {
    const n = (meta.by_kind || {})[kind] || 0;
    legend.appendChild(el('span.olg', {
      html: `<i class="${toneOf(kind)}"></i>${esc((data.kinds[kind] || {}).label || kind)}`
        + `<em>${n}</em><small>${(n / total * 100).toFixed(0)}%</small>`,
    }));
  }
  return el('div.orphan-summary', {}, [bar, legend]);
}

function kindCard(kind, info, list, model, onPick) {
  const box = el(`section.okard.${toneOf(kind)}`);
  box.appendChild(el('h4', {
    html: `${esc(info.label || kind)}<span class="on">${list.length} 人</span>`,
  }));
  box.appendChild(el('p.okard-desc', { text: info.desc || '' }));

  const chips = el('div.okard-chips');
  for (const o of list) {
    const where = [o.school, o.volume ? `卷${o.volume}` : '',
      o.appendix_of ? `附于「${o.appendix_of}」传后` : ''].filter(Boolean).join(' · ');
    const chip = el('span.orphan-chip', { title: where, text: o.name });
    chip.addEventListener('click', (e) => { e.stopPropagation(); onPick && onPick(o.id, chip); });
    chips.appendChild(chip);
  }
  box.appendChild(chips);

  if (kind === 'gap' && list.length) {
    const n = CN_NUM[list.length] || String(list.length);
    box.appendChild(el('p.okard-note', {
      text: `这${n}人原书立有本传，师承线索应当在正文里，只是本轮的正则与证伪规则还没读出来。`
        + '下一轮抽取的靶子就是他们。',
    }));
  }
  return box;
}

function schoolBars(data, model) {
  const rows = Object.entries(data.by_school || {})
    .filter(([, v]) => v.orphans > 0)
    .sort((a, b) => b[1].rate - a[1].rate);
  const wrap = el('div.oschool');
  for (const [school, v] of rows) {
    const row = el('div.osrow', {
      html: `<span class="osname" style="color:${model.colorOf(school)}">${esc(school)}</span>`
        + '<div class="ostrack"><span class="osfill"></span></div>'
        + `<span class="osnum">${v.orphans}/${v.total}　${(v.rate * 100).toFixed(0)}%</span>`,
    });
    const fill = row.querySelector('.osfill');
    fill.style.width = `${(v.rate * 100).toFixed(1)}%`;
    fill.style.background = model.colorOf(school);
    wrap.appendChild(row);
  }
  return wrap;
}
