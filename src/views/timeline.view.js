/**
 * timeline.view.js —— 明代年号时间线
 *
 * 顶上十七段是诸帝在位区间，底下每行一个学案，行内彩条是人物的活动年代。
 * 实心=史载生卒，半透明=依师承代次推算 —— 这个区分必须画出来，
 * 不然「推算」会被当成史实读。
 */
import { svg, el, clear } from '../core/dom.js';

const Y0 = 1368; const Y1 = 1644; const PX = 9;
const BAND_H = 64; const BAND_TOP = 10; const ROW_H = 30;

const x = (y) => 90 + (y - Y0) * PX;

export function render(svgEl, model, { onPick, onEmperor } = {}) {
  clear(svgEl);
  const g = svg('g');
  const emperors = model.timeline.emperors || [];
  const period = model.timeline.period || {};

  emperors.forEach((em, i) => {
    const x0 = x(em.start); const x1 = x(em.end);
    const r = svg('rect', {
      x: x0, y: BAND_TOP, width: Math.max(2, x1 - x0), height: BAND_H,
      fill: i % 2 ? 'rgba(120,100,60,.10)' : 'rgba(120,100,60,.20)',
      class: 'tbar', 'data-em': em.era,
    });
    r.appendChild(svg('title', { text: `${em.n}代 ${em.era}帝（${em.name}） 在位 ${em.start}–${em.end}` }));
    r.addEventListener('click', () => onEmperor && onEmperor(em.era));
    g.append(r,
      svg('text', { x: (x0 + x1) / 2, y: BAND_TOP + 18, 'text-anchor': 'middle', text: em.era }),
      svg('text', {
        x: (x0 + x1) / 2, y: BAND_TOP + 34, 'text-anchor': 'middle',
        'font-size': 9.5, fill: 'var(--ink-soft)', text: `${em.start}–${em.end}`,
      }));
  });

  for (let y = 1370; y <= 1640; y += 10) {
    g.append(svg('line', {
      x1: x(y), x2: x(y), y1: BAND_TOP, y2: BAND_TOP + BAND_H, stroke: 'var(--line)', opacity: 0.4,
    }), svg('text', {
      x: x(y), y: BAND_TOP + BAND_H + 12, 'text-anchor': 'middle',
      'font-size': 9, fill: 'var(--ink-soft)', text: y,
    }));
  }

  const bars = new Map();
  let py = BAND_TOP + BAND_H + 16;
  for (const school of model.schools) {
    g.appendChild(svg('text', { x: 6, y: py + 16, class: 'trow', text: school.id }));
    for (const id of model.members[school.id] || []) {
      const per = period[id];
      if (!per || !per.active) continue;
      const [s, e] = per.active;
      const founder = model.isFounder(id);
      const grp = svg('g', { class: 'pbar', 'data-id': id });
      const rect = svg('rect', {
        x: x(s), y: py + 5, width: Math.max(3, x(e) - x(s)), height: founder ? 15 : 10,
        fill: model.colorOf(school.id),
        opacity: per.method === '史载' ? 0.92 : 0.42,
        stroke: founder ? 'var(--accent)' : null,
      });
      rect.appendChild(svg('title', {
        text: `${model.persons[id].name}（${per.birth ?? '?'}–${per.death ?? '?'}，${per.method}） · ${school.id}`,
      }));
      grp.appendChild(rect);
      if (founder) {
        grp.appendChild(svg('text', {
          x: x(s) + 3, y: py + 9, 'font-size': 9, fill: '#fff', text: model.roleTag(id),
        }));
      }
      grp.addEventListener('click', (ev) => { ev.stopPropagation(); if (onPick) onPick(id, rect); });
      g.appendChild(grp);
      bars.set(id, grp);
    }
    py += ROW_H;
  }

  svgEl.setAttribute('width', (Y1 - Y0) * PX + 120);
  svgEl.setAttribute('height', py + 30);
  svgEl.appendChild(g);
  return { bars, emperors };
}

/** 某帝在位期间的人物名单 */
export function renderEmperorList(container, model, era, { onPick } = {}) {
  clear(container);
  const em = (model.timeline.emperors || []).find((e) => e.era === era);
  if (!em) return [];
  const period = model.timeline.period || {};
  const hits = [];
  container.appendChild(el('div.tab-head', {
    text: `${em.era}帝在位（${em.start}–${em.end}）时活跃的人物`,
  }));

  for (const school of model.schools) {
    const ids = (model.members[school.id] || []).filter((id) => {
      const per = period[id];
      return per && per.active && per.active[0] <= em.end && per.active[1] >= em.start;
    });
    if (!ids.length) continue;
    hits.push(...ids);
    const grp = el('div.empgroup', {
      html: `<h4><span class="dot" style="display:inline-block;width:11px;height:11px;`
        + `border-radius:50%;background:${model.colorOf(school.id)}"></span> ${school.id}（${ids.length}）</h4>`,
    });
    const chips = el('div.chips');
    ids.forEach((id) => {
      const per = period[id];
      const c = el('span.pchip', {
        html: `${model.persons[id].name}`
          + (per.birth ? `<span class="lif">${per.birth}–${per.death ?? ''}</span>` : ''),
      });
      c.addEventListener('click', () => onPick && onPick(id, c));
      chips.appendChild(c);
    });
    grp.appendChild(chips);
    container.appendChild(grp);
  }
  if (!hits.length) {
    container.appendChild(el('div.empgroup', { html: '<h4>（该时期暂无已考年代的人物）</h4>' }));
  }
  return hits;
}
