/**
 * web_boot.js —— 在线版启动器
 *
 * dist/ 离线版内联 window.__MRXA__ 直接启动；web/ 在线版需要先从
 * /data/ 拉取 JSON，再建模型、启动控制器。启动流程是 async 的，
 * 但页面内容已在 HTML 里预渲染，JS 只负责交互增强。
 */
import { $ } from '../core/dom.js';
import * as store from '../core/store.js';
import { loadCore } from '../data/repository.js';
import { createModel } from '../data/model.js';
import { create as themeCtl } from '../controllers/theme.controller.js';
import { redirectLegacy } from '../router/index.js';
import * as card from '../views/person-card.view.js';

const PAGE_FILE = {
  kg: 'index.html', graph: 'graph.html', roster: 'roster.html',
  time: 'time.html', geo: 'geo.html', orphan: 'orphan.html',
  book: 'chapter-Preface.html', yangming: 'yangming.html',
};

export async function webBoot(pageId, { needsCard = true, mount } = {}) {
  store.restore();
  if (redirectLegacy()) return null;
  themeCtl();
  const core = await loadCore();                           // fetch /data/*.json
  const model = createModel(core);
  store.set('data', model, { silent: true });
  const api = _makeApi(model, needsCard);
  let ctl = mount ? mount(model, api) : null;
  if (needsCard) _setupCard(model, api);
  _reportCoverage(model);
  const { params, query } = _readParams();
  if (ctl && ctl.enter) ctl.enter({ params, query });
  if (query === 'orphans' && ctl && ctl.showOrphans) setTimeout(() => ctl.showOrphans(), 80);
  else if (params[0] && ctl && ctl.locate) {
    const id = params[0];
    setTimeout(() => {
      if (needsCard && card.element() && card.element().classList.contains('show')) return;
      const a = ctl.locate(id);
      if (a && needsCard) card.show(id, a);
    }, 260);
  }
  window.__MRXA_APP__ = { model, ctl };
  return { model, ctl };
}

function _makeApi(model, needsCard) {
  let _ctl = null;
  return {
    get _setCtl(v) { _ctl = v; },
    pick(id, anchor) { store.selectPerson(id); if (needsCard) card.show(id, anchor); },
    locate(where, id) {
      const file = PAGE_FILE[where] || 'index.html';
      if (file === _currentFile()) {
        const a = _ctl && _ctl.locate ? _ctl.locate(id) : null;
        if (a && needsCard) card.show(id, a);
        return;
      }
      location.href = `${file}?focus=${encodeURIComponent(id)}`;
    },
    showInKG() { location.href = 'index.html?orphans=1'; },
  };
}

function _setupCard(model, api) {
  card.mount();
  card.setContext({
    persons: model.persons, colorOf: model.colorOf,
    isFounder: model.isFounder, roleBadge: model.roleBadge,
    teachersOf: model.teachersOf, studentsOf: model.studentsOf,
    relationsOf: model.relationsOf, orphanOf: model.orphanOf,
    onSelect: (id) => store.selectPerson(id),
    onLocate: (where, id) => api.locate(where, id),
  });
}

function _reportCoverage(model) {
  const el = $('#coverage');
  if (!el) return;
  const m = model.meta || {}; const o = model.orphanData.meta || {};
  el.textContent = `${model.schools.length} 学案 · ${model.personList.length} 人 · `
    + `${m.count || 0} 条关系（${m.cited || 0} 条有原文出处）· 孤点 ${o.orphan_count || 0}`;
}

function _readParams() {
  const q = new URLSearchParams(location.search);
  const params = []; let query = '';
  const f = q.get('focus'); const v = q.get('v'); const p = q.get('p');
  if (f) params.push(f); else if (v) params.push(v); else if (p) params.push(p);
  if (q.get('all')) query = 'all'; else if (q.get('orphans')) query = 'orphans';
  return { params, query };
}

function _currentFile() { return location.pathname.split('/').pop() || 'index.html'; }
