/**
 * geo.view.js —— 籍贯地理分布
 *
 * 三块：省份筛选 chips、分省人物列表、人数横条图。
 * 三块共用同一个「当前选中省」状态，由控制器持有 —— 视图只管画，
 * 不自己记住选了谁，否则三块很容易各记一份然后对不上。
 */
import { el, clear, esc } from '../core/dom.js';

/** 按今省聚合，人数多的排前面 */
export function groupByProvince(model) {
  const byProv = new Map();
  for (const p of model.personList) {
    const g = p.place;
    if (!g || !g.prov || g.prov === '不详') continue;
    if (!byProv.has(g.prov)) byProv.set(g.prov, []);
    byProv.get(g.prov).push(p.id);
  }
  return [...byProv.entries()]
    .sort((a, b) => b[1].length - a[1].length)
    .map(([prov, ids]) => ({
      prov,
      ids: ids.sort((a, b) => model.persons[a].name.localeCompare(model.persons[b].name, 'zh')),
    }));
}

export function renderChips(container, groups, { onSelect } = {}) {
  clear(container);
  for (const g of groups) {
    const c = el('span.gchip', {
      dataset: { pr: g.prov },
      html: `${esc(g.prov)}<span style="color:var(--ink-soft)">${g.ids.length}</span>`,
    });
    c.addEventListener('click', () => onSelect && onSelect(g.prov));
    container.appendChild(c);
  }
}

export function renderGrid(container, groups, model, { onPick } = {}) {
  clear(container);
  for (const g of groups) {
    const box = el('div.gprov', {
      dataset: { pr: g.prov },
      html: `<h4>${esc(g.prov)}<span class="cnt">${g.ids.length} 人</span></h4>`,
    });
    const list = el('div.glist');
    for (const id of g.ids) {
      const p = model.persons[id];
      const pl = p.place || {};
      const place = pl.city ? (pl.note ? `${pl.city}·${pl.note}` : pl.city) : (pl.note || '');
      const row = el('div.grow', {
        html: `<span class="gn">${esc(p.name)}</span><span class="gx">`
          + `${esc((p.origin && p.origin.raw) || '')}${place ? ` → <em>${esc(place)}</em>` : ''}</span>`,
      });
      row.addEventListener('click', () => onPick && onPick(id, row));
      list.appendChild(row);
    }
    box.appendChild(list);
    container.appendChild(box);
  }
}

export function renderBars(container, groups, { onSelect } = {}) {
  clear(container);
  const max = groups.length ? groups[0].ids.length : 1;
  for (const g of groups) {
    const row = el('div.geobar', {
      dataset: { pr: g.prov },
      html: `<span class="gb-name">${esc(g.prov)}</span>`
        + '<div class="gb-track"><span class="gb-fill"></span></div>'
        + `<span class="gb-num">${g.ids.length} 人</span>`,
    });
    row.querySelector('.gb-fill').style.width = `${(g.ids.length / max * 100).toFixed(1)}%`;
    row.addEventListener('click', () => onSelect && onSelect(g.prov));
    container.appendChild(row);
  }
}

/** 明代籍贯称谓 → 今地对照，取自 geo.json 的 birth_patterns */
export function renderMapTable(table, model) {
  const patterns = model.geo.birth_patterns || {};
  const keys = Object.keys(patterns).sort();
  const rows = keys.map((k) => {
    const v = patterns[k] || {};
    return `<tr><td>${esc(k)}</td><td>${esc(v.prov || '')}</td>`
      + `<td>${esc(v.city || '')}</td><td>${esc(v.note || '')}</td></tr>`;
  }).join('');
  table.innerHTML = '<tr><th>明代籍贯称谓</th><th>今省</th><th>今市（县）</th><th>备注</th></tr>' + rows;
}

/** 高亮某省；prov 为 null 时全部显示 */
export function applyFilter(chipBox, grid, bars, prov) {
  chipBox.querySelectorAll('.gchip').forEach((c) => c.classList.toggle('on', c.dataset.pr === prov));
  bars.querySelectorAll('.geobar').forEach((b) => b.classList.toggle('on', b.dataset.pr === prov));
  [...grid.children].forEach((ch) => {
    ch.style.display = !prov || ch.dataset.pr === prov ? '' : 'none';
  });
}
