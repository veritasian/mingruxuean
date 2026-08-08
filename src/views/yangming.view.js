/**
 * yangming.view.js —— 阳明心学专页渲染（复刻原手稿页结构）
 *
 * 布局：左悬浮侧边栏（章节导航，高亮由控制器驱动）+ 右正文。
 * 正文复刻原版结构：
 *   flow   壹·思维模型：明镜/磨镜 双色带 + 镜像布局 + 长弧箭头
 *   matrix 贰·根器论：三教 × 三阶 矩阵（人形小图）
 *   quad   叁~拾肆：通用四象限（圆标 + hint + 坐标板 + 便签）
 * 动效：渐入（.ym-reveal → .is-in，控制器接 IO）、卡片 hover 3D 倾斜、
 *       便签随机旋转（--peel）。纯渲染，不存状态。
 */
import { $, el, clear, esc } from '../core/dom.js';

const LARROW = '<svg class="ym-larrow" viewBox="0 0 40 220" aria-hidden="true">'
  + '<line x1="20" y1="200" x2="20" y2="20" stroke="currentColor" stroke-width="1.5"/>'
  + '<polyline points="10,32 20,18 30,32" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>';
const CURVE = '<svg class="ym-curve" viewBox="0 0 80 80" aria-hidden="true">'
  + '<path d="M72 42 Q 40 6 8 42" fill="none" stroke="currentColor" stroke-width="1.5" stroke-dasharray="4 3"/>'
  + '<polyline points="14,38 8,42 14,46" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>';
const LONGCURVE = '<svg class="ym-long-curve" viewBox="0 0 120 520" preserveAspectRatio="none" aria-hidden="true">'
  + '<path d="M 30 480 Q 110 400 60 260 Q 10 140 60 60" fill="none" stroke="currentColor" stroke-width="1.5" stroke-dasharray="4 3"/>'
  + '<polyline points="54,68 60,58 66,68" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>';
const FIG = {
  run: '<svg class="ym-figure ym-figure-run" viewBox="0 0 64 64" aria-hidden="true">'
    + '<circle cx="42" cy="14" r="6" fill="currentColor"/>'
    + '<path d="M38 22 L20 30 L26 34 L18 50 L24 50 L30 38 L36 44 L34 56 L40 56 L42 42 L48 32 L54 24 L48 22 Z" fill="currentColor"/></svg>',
  walk: '<svg class="ym-figure ym-figure-walk" viewBox="0 0 64 64" aria-hidden="true">'
    + '<circle cx="34" cy="12" r="6" fill="currentColor"/>'
    + '<path d="M30 20 L20 34 L24 36 L28 50 L34 50 L30 36 L38 32 L44 42 L48 50 L54 48 L46 36 L46 24 L52 20 L48 16 L38 22 Z" fill="currentColor"/></svg>',
  crawl: '<svg class="ym-figure ym-figure-crawl" viewBox="0 0 64 64" aria-hidden="true">'
    + '<circle cx="20" cy="44" r="6" fill="currentColor"/>'
    + '<path d="M26 48 L36 46 L46 50 L48 56 L42 56 L38 52 L30 54 L26 58 L22 56 L26 50 L20 48 Z M40 38 L50 36 L52 42 L46 44 Z" fill="currentColor"/></svg>',
};

export function render(root, data, { onNav } = {}) {
  clear(root);
  root.appendChild(hero(data));
  const shell = el('div.ym-shell');
  shell.appendChild(nav(data, { onNav }));
  const main = el('div.ym-main');
  (data.chapters || []).forEach((c) => main.appendChild(chapter(c)));
  if (data.outro && data.outro.length) main.appendChild(outro(data.outro));
  shell.appendChild(main);
  root.appendChild(shell);
  return { side: $('.ym-nav', shell), main };
}

/* ---------- Hero：眉标 + 四句教渐次升起 ---------- */
function hero(data) {
  const h = el('section.ym-hero');
  const inner = el('div.ym-hero-inner');
  inner.appendChild(el('p.ym-hero-eyebrow', { text: data.eyebrow || '' }));
  const title = el('h2.ym-hero-title');
  (data.hero || []).forEach((l) => title.appendChild(el('span', { text: l })));
  inner.append(title, el('p.ym-hero-sub', { text: data.heroSub || '' }));
  inner.appendChild(el('div.ym-hero-scroll', { html: '<span></span>' }));
  h.appendChild(inner);
  return h;
}

/* ---------- 章节目录：置顶于正文上方，滚动监听高亮由控制器驱动 ---------- */
function nav(data, { onNav } = {}) {
  const n = el('nav.ym-nav', { 'aria-label': '阳明心学章节' });
  const items = (data.chapters || []).map((c) => ({ id: c.id, label: `${c.num}·${c.title}` }));
  if (data.outro && data.outro.length) items.push({ id: 'ym-outro', label: '附' });
  for (const it of items) {
    const a = el('a.ym-link.ym-nav-item', { dataset: { yg: it.id }, text: it.label });
    a.addEventListener('click', (e) => { e.preventDefault(); onNav && onNav(it.id); });
    n.appendChild(a);
  }
  return n;
}

/* ---------- 章节通用 ---------- */
function chapter(c) {
  const sec = el('section.ym-chapter', { id: `ym-${c.id}` });
  const head = el('header.ym-ch-head');
  head.appendChild(el('span.ym-ch-num', { text: c.num }));
  head.appendChild(el('h3.ym-ch-title', { text: c.title }));
  if (c.sub) head.appendChild(el('p.ym-ch-sub', { text: c.sub }));
  sec.appendChild(head);
  const body = bodyOf(c);
  if (body) sec.appendChild(body);
  return sec;
}

function bodyOf(c) {
  switch (c.kind) {
    case 'flow': return mirror(c.flow);
    case 'matrix': return matrix(c.matrix);
    case 'quad': return quad(c.quad);
    default: return null;
  }
}

/* ---------- 壹 · 思维模型：镜像布局 + 双色带 ---------- */
function mirror(f) {
  const lay = el('div.ym-mirror-layout.ym-reveal');
  const sideL = el('aside.ym-mirror-side-l');
  sideL.appendChild(el('div.ym-lblock', {
    html: `<span class="ym-lcircle ym-lcircle-awake">${esc(f.awakeTag)}</span>`
      + `<h4 class="ym-ltitle ym-ltitle-awake">${esc(f.awakeCap)}</h4>`,
  }));
  sideL.appendChild(el('div.ym-larrow', { html: LARROW }));
  sideL.appendChild(el('div.ym-lblock', {
    html: `<h4 class="ym-ltitle ym-ltitle-delude">${esc(f.deludeCap)}</h4>`
      + `<span class="ym-lcircle ym-lcircle-delude">${esc(f.deludeTag)}</span>`,
  }));
  lay.appendChild(sideL);
  const dia = el('div.ym-mirror-diagram');
  dia.appendChild(band(f.awakeCols, 'yellow'));
  dia.appendChild(conn(f.mid1));
  dia.appendChild(band(f.deludeCols, 'green'));
  dia.appendChild(conn(f.mid2, true));
  dia.appendChild(el('div.ym-long-curve', { html: LONGCURVE }));
  lay.appendChild(dia);
  return lay;
}

function band(cols, tone) {
  const b = el(`div.ym-band.ym-band-${tone}`);
  const inner = el('div.ym-band-inner');
  (cols || []).forEach((cd, i) => {
    inner.appendChild(subbox(cd));
    if (i === 0) inner.appendChild(el('div.ym-curve', { html: CURVE }));
  });
  b.appendChild(inner);
  return b;
}

function subbox(cd) {
  const rows = (cd.rows || []).map((t, i) => {
    const cls = ['ym-row', i === 0 ? 'ym-row-top' : (i === cd.rows.length - 1 ? 'ym-row-bot' : 'ym-row-mid')];
    if ((cd.emph || []).includes(i)) cls.push('ym-row-emph');
    if (cd.know === i) cls.push('ym-row-know');
    return `<div class="${cls.join(' ')}">${esc(t)}</div>`;
  }).join('');
  const n = cd.note || '';
  const m = n.match(/^(.+?)（(.+?)）$/);
  const note = n ? `<div class="ym-subbox-note"><span class="ym-sn-main">${esc(m ? m[1] : n)}</span>`
    + (m ? `<span class="ym-sn-sub">（${esc(m[2])}）</span>` : '') + '</div>' : '';
  return el('div.ym-subbox.ym-reveal', {
    html: `<div class="ym-subbox-head">${esc(cd.cap)}</div>`
      + `<div class="ym-subbox-rows">${rows}</div>${note}`,
  });
}

function conn(mid, bottom) {
  const [dot, label] = String(mid || '').split(' · ');
  return el(bottom ? 'div.ym-bot-conn' : 'div.ym-mid-conn', {
    html: `<span class="ym-reddot">${esc(dot || '')}</span><span class="ym-mid-label">${esc(label || '')}</span>`,
  });
}

/* ---------- 贰 · 根器论：3×3 矩阵 ---------- */
function matrix(m) {
  const tbl = el('div.ym-matrix');
  const head = el('div.ym-mhead');
  head.appendChild(el('div.ym-mcorner', { text: '心行' }));
  (m.cols || []).forEach((c) => head.appendChild(el('div.ym-mcol', {
    html: `<span class="ym-dot ym-dot-${esc(c.dot)}"></span><strong>${esc(c.char)}</strong><em>${esc(c.en)}</em>`,
  })));
  tbl.appendChild(head);
  (m.rows || []).forEach((r) => {
    const row = el('div.ym-mrow.ym-reveal');
    row.appendChild(el('div.ym-mrowhead', {
      html: `${FIG[r.fig] || ''}<span class="ym-mlvl">${esc(r.level)}</span>`,
    }));
    (r.cells || []).forEach((c) => {
      const cell = el(`div.ym-mcell.ym-mcell-${c.cls}`, {
        html: `<strong>${esc(c.t)}</strong>${c.s ? `<p>${esc(c.s)}</p>` : ''}`,
      });
      cell.addEventListener('mousemove', (e) => tilt(cell, e));
      cell.addEventListener('mouseleave', () => { cell.style.transform = ''; });
      row.appendChild(cell);
    });
    tbl.appendChild(row);
  });
  return tbl;
}

function tilt(node, e) {
  const r = node.getBoundingClientRect();
  const x = (e.clientX - r.left) / r.width - 0.5;
  const y = (e.clientY - r.top) / r.height - 0.5;
  node.style.transform = `translateY(-3px) perspective(600px) rotateX(${(-y * 4).toFixed(2)}deg) rotateY(${(x * 4).toFixed(2)}deg)`;
}

/* ---------- 叁~拾肆 · 通用四象限 ---------- */
function quad(q) {
  const wrap = el('div.ym-quad-wrap');
  const frame = el('div.ym-quad-frame.ym-reveal');
  frame.appendChild(el('div.ym-quad-cap.ym-quad-cap-top', {
    html: `<span class="ym-quad-tail ym-quad-tail-v"></span><span class="ym-quad-circle">${esc(q.use[0])}</span><span class="ym-quad-hint">${esc(q.use[1])}</span>`,
  }));
  frame.appendChild(el('div.ym-quad-cap.ym-quad-cap-right', {
    html: `<span class="ym-quad-tail ym-quad-tail-h"></span><span class="ym-quad-circle">${esc(q.body[0])}</span><span class="ym-quad-hint">${esc(q.body[1])}</span>`,
  }));
  const board = el('div.ym-quad-board');
  board.appendChild(el('div.ym-quad-axis.ym-quad-axis-y'));
  board.appendChild(el('div.ym-quad-axis.ym-quad-axis-x'));
  (q.q || []).forEach((x) => board.appendChild(qu(x, 'ym-qq', 'ym-qs', 'ym-qq-')));
  frame.appendChild(board);
  frame.appendChild(el('p.ym-quad-foot', { text: q.foot }));
  wrap.appendChild(frame);
  return wrap;
}

/** 通用四象限格 + 便签 */
function qu(x, cellCls, stickyCls, posPrefix) {
  const cell = el(`div.${cellCls}.${posPrefix}${x.pos}`, {});
  if (x.title || (x.lines && x.lines.length) || x.note) {
    const s = el(`div.${stickyCls}.ym-s-${x.cls}`, {});
    s.style.setProperty('--peel', `${(Math.random() * 2 - 1).toFixed(2)}deg`);
    if (x.title) s.appendChild(el('strong', { text: x.title }));
    (x.lines || []).forEach((l) => s.appendChild(el('p', { text: l })));
    if (x.note) s.appendChild(el('small', { text: x.note }));
    cell.appendChild(s);
  }
  return cell;
}

/* ---------- 尾注 ---------- */
function outro(lines) {
  const o = el('section.ym-outro', { id: 'ym-outro' });
  lines.forEach((l, i) => o.appendChild(el(i === 0 ? 'p.ym-outro-line' : 'p.ym-outro-sub', { text: l })));
  return o;
}

/** 滚动监听高亮侧边栏当前章节 */
export function markSide(side, id) {
  if (!side) return;
  side.querySelectorAll('.ym-link')
    .forEach((a) => a.classList.toggle('on', a.dataset.yg === id));
}
