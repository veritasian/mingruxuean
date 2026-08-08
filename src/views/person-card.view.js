/**
 * person-card.view.js —— 人物弹卡
 *
 * 全站唯一的人物详情出口。六个视图点人都弹它，所以它只认 id，
 * 不认「谁点的我」。锚点元素只用来算位置。
 *
 * 相较旧版多了一段「出处」：每条师承下面挂着卷次、章节、原文摘句。
 * 图上画的每一根线都要能说出它是从哪一句话里读出来的。
 */
import { el, esc, $ } from '../core/dom.js';
import { on, EV } from '../core/bus.js';

const HIDE_MS = 9000;
let root = null; let body = null; let timer = null; let ctx = null;

export function mount(container = document.body) {
  root = el('div.pc', { id: 'pc' });
  const x = el('button.pc-x', { text: '✕', onclick: hide });
  body = el('div', { id: 'pcBody' });
  root.append(x, body);
  container.appendChild(root);
  root.addEventListener('pointerenter', () => clearTimeout(timer));
  root.addEventListener('pointerleave', arm);
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') hide(); });
  document.addEventListener('pointerdown', (e) => {
    if (!root.classList.contains('show')) return;
    if (root.contains(e.target)) return;
    if (e.target.closest('.node,.pcard,.tn,.pbar,.pchip,.grow,.kg-node,.orphan-chip')) return;
    hide();
  }, true);
  on(EV.ROUTE_CHANGED, hide);
  return root;
}

export function setContext(next) { ctx = next; }

function arm() { clearTimeout(timer); timer = setTimeout(hide, HIDE_MS); }

export function hide() { clearTimeout(timer); if (root) root.classList.remove('show'); }

function lifeText(p) {
  const l = p.life || {};
  if (l.raw) return `生卒 ${l.raw}${l.age ? `（${l.age}）` : ''}`;
  return l.age || '';
}

function nameLinks(ids) {
  if (!ids || !ids.length) return '—';
  const P = ctx.persons;
  return ids.filter((x) => P[x]).map((x) => `<a data-go="${esc(x)}">${esc(P[x].name)}</a>`).join('、');
}

/** 一条边的证据。有原文摘句就摆原文，没有就至少说清卷次。 */
function evidenceRows(id) {
  const rels = ctx.relationsOf(id);
  if (!rels.length) return '';
  const rows = rels.slice(0, 6).map((r) => {
    const other = r.from === id ? r.to : r.from;
    const dir = r.from === id ? '师事' : '授业';
    const pv = (r.provenance || []).find((x) => x.quote) || (r.provenance || [])[0] || {};
    // 出处卷次分两个体系：明儒学案卷（1–63）与《明史》儒林传卷（282/283），
    // 混着显示会让人以为学案有 282 卷。
    const vol = pv.volume ? (pv.source === 'mingshi' ? `《明史》卷${pv.volume}` : `卷${pv.volume}`) : '';
    const sec = pv.section ? `·${esc(pv.section)}` : '';
    const quote = pv.quote ? `<q>${esc(String(pv.quote).slice(0, 46))}</q>` : '';
    const badge = r.cited ? '' : '<span class="pv-nc">待补出处</span>';
    return `<div class="pv-row"><span class="pv-d">${dir}</span>
      <b>${esc(ctx.persons[other] ? ctx.persons[other].name : other)}</b>
      <span class="pv-src">${vol}${sec}</span>${badge}
      <span class="pv-cf">${(r.confidence || 0).toFixed(2)}</span>${quote}</div>`;
  }).join('');
  const more = rels.length > 6 ? `<div class="pv-more">另有 ${rels.length - 6} 条</div>` : '';
  return `<details class="pv"><summary>关系出处（${rels.length}）</summary>${rows}${more}</details>`;
}

export function show(id, anchor) {
  if (!ctx || !root) return;
  const p = ctx.persons[id];
  if (!p) return;
  const meta = [p.zi && `字${p.zi}`, p.hao && `号${p.hao}`, p.origin && p.origin.raw]
    .filter(Boolean).join(' ｜ ');
  const life = lifeText(p);
  const per = p.period;
  const period = per && per.active
    ? `活跃约 ${per.active[0]}–${per.active[1]}（${esc(per.method || '')}）` : '';
  const g = p.place;
  const geo = g && g.prov && g.prov !== '不详'
    ? `籍贯 ${esc((p.origin && p.origin.raw) || '')} → 今${esc(g.prov)}${g.city ? `·${esc(g.city)}` : ''}` : '';

  const color = ctx.colorOf(p.school);
  let tags = `<span class="tag" style="border-color:${color};color:${color}">${esc(p.school)}</span>`;
  if (p.title) tags += `<span class="tag">${esc(p.title)}</span>`;
  if (ctx.isFounder(id)) tags += `<span class="tag" style="border-color:var(--accent);color:var(--accent)">${ctx.roleBadge(id)}</span>`;
  const orphan = ctx.orphanOf(id);
  if (orphan) tags += `<span class="tag tag-orphan">孤点·${esc(orphan.label)}</span>`;

  body.innerHTML = `<h3>${esc(p.name)}</h3>
    ${meta ? `<div class="pc-meta">${esc(meta)}</div>` : ''}
    ${p.mingshi && p.mingshi.style ? `<div class="pc-meta">学问 ${esc(p.mingshi.style)}（《明史》儒林传）</div>` : ''}
    ${life ? `<div class="pc-life">${esc(life)}</div>` : ''}
    ${period ? `<div class="pc-meta">${period}</div>` : ''}
    ${geo ? `<div class="pc-meta">${geo}</div>` : ''}
    <div class="pc-tags">${tags}</div>
    <div class="pc-rel"><b>师：</b>${nameLinks(ctx.teachersOf(id))}</div>
    <div class="pc-rel"><b>弟子：</b>${nameLinks(ctx.studentsOf(id))}</div>
    ${evidenceRows(id)}
    <div class="pc-foot"><button class="btn" data-act="graph">在总图定位</button>
      <button class="btn" data-act="kg">在图谱聚焦</button></div>`;

  body.querySelectorAll('a[data-go]').forEach((a) => a.addEventListener('click', (e) => {
    e.preventDefault(); e.stopPropagation();
    ctx.onSelect(a.dataset.go);
    show(a.dataset.go, a);
  }));
  body.querySelectorAll('button[data-act]').forEach((b) => b.addEventListener('click', () => {
    ctx.onLocate(b.dataset.act, id);
  }));

  place(anchor);
  root.classList.add('show');
  arm();
}

function place(anchor) {
  const r = anchor && anchor.getBoundingClientRect
    ? anchor.getBoundingClientRect()
    : { top: innerHeight / 2, bottom: innerHeight / 2, left: innerWidth / 2, width: 0, height: 0 };
  const pw = root.offsetWidth || 300; const ph = root.offsetHeight || 220;
  const x = Math.max(10, Math.min(innerWidth - pw - 10, r.left + r.width / 2 - pw / 2));
  let y = r.bottom + 12;
  if (y + ph > innerHeight - 10) y = Math.max(10, r.top - ph - 12);
  root.style.left = `${x}px`;
  root.style.top = `${y}px`;
}

export function element() { return root || $('#pc'); }
