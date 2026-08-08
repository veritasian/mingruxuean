/**
 * roster.view.js —— 人物总录
 *
 * 每个学案先给一棵「师承世系」（家谱式缩进树），再铺人物名片。
 * 树只画学案内部的师承；跨学案的老师用「（师：某某）」注在名字后面，
 * 否则一条线拉到别的学案去，缩进树就没法看了。
 */
import { el, clear } from '../core/dom.js';

export function render(container, model, { onPick } = {}) {
  clear(container);
  for (const school of model.schools) {
    const ids = model.members[school.id] || [];
    if (!ids.length) continue;
    container.appendChild(schoolBlock(school, ids, model, onPick));
  }
  return container;
}

function schoolBlock(school, ids, model, onPick) {
  const det = el('details.school', { open: true });
  const color = model.colorOf(school.id);
  det.appendChild(el('summary', {
    html: `<span class="dot" style="background:${color}"></span>${school.id}`
      + `<span class="cnt">${ids.length} 人</span>`,
  }));

  det.appendChild(el('div.tree-cap', { text: '师承世系（家谱）· 上为祖师，下为弟子' }));
  det.appendChild(buildTree(school, ids, model, onPick));

  const grid = el('div.cards');
  ids.forEach((id) => grid.appendChild(card(id, model, onPick)));
  det.appendChild(grid);
  return det;
}

/** 学案内的父子关系；一人多师时取第一位同门老师作为树上的父 */
function buildTree(school, ids, model, onPick) {
  const memberSet = new Set(ids);
  const founderSet = new Set((school.founders || []).filter((n) => memberSet.has(n)));
  const parent = new Map();
  const children = new Map();
  ids.forEach((id) => children.set(id, []));

  ids.forEach((id) => {
    const inside = model.teachersOf(id).filter((t) => memberSet.has(t));
    parent.set(id, inside.length ? inside[0] : null);
  });
  ids.forEach((id) => {
    const p = parent.get(id);
    if (p && !founderSet.has(id) && children.has(p)) children.get(p).push(id);
  });

  const rootsBase = ids.filter((id) => !parent.get(id));
  const roots = founderSet.size
    ? [...ids.filter((id) => founderSet.has(id)), ...rootsBase.filter((id) => !founderSet.has(id))]
    : rootsBase;

  const ul = el('ul.tree');
  const seen = new Set();
  roots.forEach((r) => ul.appendChild(node(r)));
  return ul;

  function node(id) {
    const p = model.persons[id];
    const li = el('li');
    if (seen.has(id)) { li.appendChild(el('span.te', { text: `${p.name}（见上）` })); return li; }
    seen.add(id);

    const outside = model.teachersOf(id).filter((t) => !memberSet.has(t) && model.persons[t]);
    const life = lifeText(p);
    const name = el('span.tn', { text: p.name });
    name.addEventListener('click', (e) => { e.stopPropagation(); if (onPick) onPick(id, name); });
    li.appendChild(name);
    if (life) li.appendChild(el('span.te', { text: ` ${life}` }));
    if (founderSet.has(id)) li.appendChild(el('span.te.ext', { text: `〔${model.roleTag(id)}〕` }));
    if (p.zi) li.appendChild(el('span.te', { text: `，字${p.zi}` }));
    if (outside.length) {
      li.appendChild(el('span.te.ext', {
        text: ` （师：${outside.map((t) => model.persons[t].name).join('、')}）`,
      }));
    }
    if (model.degreeOf(id) === 0) li.appendChild(el('span.te.orphan-mark', { text: ' ·孤点' }));

    const kids = children.get(id) || [];
    if (kids.length) {
      const sub = el('ul');
      kids.forEach((c) => sub.appendChild(node(c)));
      li.appendChild(sub);
    }
    return li;
  }
}

function lifeText(p) {
  const l = p.life || {};
  if (l.raw) return `生卒 ${l.raw}${l.age ? `（${l.age}）` : ''}`;
  return l.age || '';
}

function card(id, model, onPick) {
  const p = model.persons[id];
  const line = [lifeText(p), p.origin && p.origin.raw].filter(Boolean).join(' ｜ ');
  const badge = model.isFounder(id) ? `<span class="fb">${model.roleBadge(id)}</span>` : '';
  const c = el('div.pcard', {
    html: `<div class="pn">${p.name}</div>${badge}<div class="pz">${line || '&nbsp;'}</div>`
      + (p.title ? `<div class="pr">${p.title}</div>` : ''),
  });
  c.addEventListener('click', (e) => { e.stopPropagation(); if (onPick) onPick(id, c); });
  return c;
}
