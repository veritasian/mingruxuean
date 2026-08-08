/**
 * app.controller.js —— 每页启动器（boot）
 *
 * 站点是多页面结构：每个分类一个独立 HTML，本文件是它们共用的启动逻辑。
 * 页面入口（src/pages/*.js）各自 import 自己的视图控制器，通过 mount 注入，
 * 所以这里不认识任何具体视图 —— 也不会把 8 个视图的代码都拉进同一页。
 *
 * 启动顺序：
 *   1. 还原持久化（主题）
 *   2. 旧链接（#content/kg、#v12 …）重定向到新页面
 *   3. 主题切换器
 *   4. 由 window.__MRXA__（本页内联的数据切片）构建模型
 *   5. 人物卡（本页需要才挂）
 *   6. 读地址栏参数（?focus= / ?v= / ?orphans / ?all）→ enter
 */
import { $ } from '../core/dom.js';
import * as store from '../core/store.js';
import { createModel } from '../data/model.js';
import { coreFromInline } from '../data/repository.js';
import { create as themeCtl } from './theme.controller.js';
import { redirectLegacy } from '../router/index.js';
import * as card from '../views/person-card.view.js';

const PAGE_FILE = {
  kg: 'index.html', graph: 'graph.html', roster: 'roster.html',
  time: 'time.html', geo: 'geo.html', orphan: 'orphan.html',
  book: 'book.html', yangming: 'yangming.html',
};

export function boot(pageId, { needsCard = true, mount } = {}) {
  store.restore();
  if (redirectLegacy()) return null;            // 旧书签 → 新页面，本页不再启动

  themeCtl();

  // 内联数据是原始 JSON（relations 是 {relations:[], meta:{}}），
  // 先经 repository 同步装配成 core（数组 + period/place 挂回人物），再建模型
  const model = createModel(coreFromInline(window.__MRXA__));
  store.set('data', model, { silent: true });

  const api = {
    /** 弹人物卡（本页浮层） */
    pick(id, anchor) { store.selectPerson(id); if (needsCard) card.show(id, anchor); },
    /** 人物卡「在 X 定位」：跳到那个分类的页面并聚焦 */
    locate(where, id) {
      const file = PAGE_FILE[where] || 'index.html';
      if (file === currentFile()) {
        const a = ctl && ctl.locate ? ctl.locate(id) : null;
        if (a && needsCard) card.show(id, a);
        return;
      }
      location.href = `${file}?focus=${encodeURIComponent(id)}`;
    },
    /** 孤点页「去图谱只看孤点」 */
    showInKG() { location.href = 'index.html?orphans=1'; },
  };

  let ctl = mount ? mount(model, api) : null;

  if (needsCard) {
    card.mount();
    card.setContext({
      persons: model.persons,
      colorOf: model.colorOf,
      isFounder: model.isFounder,
      roleBadge: model.roleBadge,
      teachersOf: model.teachersOf,
      studentsOf: model.studentsOf,
      relationsOf: model.relationsOf,
      orphanOf: model.orphanOf,
      onSelect: (id) => store.selectPerson(id),
      onLocate: (where, id) => api.locate(where, id),
    });
  }

  reportCoverage(model);

  const { params, query } = readParams();
  if (ctl && ctl.enter) ctl.enter({ params, query });

  if (query === 'orphans' && ctl && ctl.showOrphans) {
    setTimeout(() => ctl.showOrphans(), 80);
  } else if (params[0] && ctl && ctl.locate) {
    // ?focus=：等 enter 先聚焦，再把人物卡也弹出来（原单页「定位」行为）。
    // kg 的 enter 已经自己弹了卡，这里检测到已显示就跳过，避免重弹。
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

/** 把 ?focus= / ?v= / ?orphans / ?all 还原成控制器认识的 {params, query} */
function readParams() {
  const q = new URLSearchParams(location.search);
  const params = [];
  let query = '';
  const f = q.get('focus');
  const v = q.get('v');
  if (f) params.push(f);
  else if (v) params.push(v);
  if (q.get('all')) query = 'all';
  else if (q.get('orphans')) query = 'orphans';
  return { params, query };
}

function currentFile() {
  return location.pathname.split('/').pop() || 'index.html';
}

/** 把数据规模写进副标题，读者一眼知道自己在看多大的一张图 */
function reportCoverage(model) {
  const el = $('#coverage');
  if (!el) return;
  const m = model.meta || {};
  const o = model.orphanData.meta || {};
  el.textContent = `${model.schools.length} 学案 · ${model.personList.length} 人 · `
    + `${m.count || 0} 条关系（${m.cited || 0} 条有原文出处）· 孤点 ${o.orphan_count || 0}`;
}
