/**
 * app.controller.js —— 总装
 *
 * 这里是唯一知道「一共有几个视图」的地方。每个视图控制器只认自己那一块，
 * 页签切换、路由注册、人物卡片的跨视图跳转，都收在这一层。
 *
 * 页签不再各自 toggle class 互相干扰 —— 全部走路由：
 * 点页签 = 改地址栏，地址栏变了才切换视图。单向，好追。
 */
import { $, $$ } from '../core/dom.js';
import { on, EV } from '../core/bus.js';
import * as store from '../core/store.js';
import * as router from '../router/index.js';
import * as card from '../views/person-card.view.js';
import { createModel } from '../data/model.js';

import { create as themeCtl } from './theme.controller.js';
import { create as graphCtl } from './graph.controller.js';
import { create as rosterCtl } from './roster.controller.js';
import { create as timelineCtl } from './timeline.controller.js';
import { create as geoCtl } from './geo.controller.js';
import { create as kgCtl } from './kg.controller.js';
import { create as bookCtl } from './book.controller.js';
import { create as orphanCtl } from './orphan.controller.js';
import { create as yangmingCtl } from './yangming.controller.js';

const VIEWS = [
  ['kg', '知识图谱'], ['graph', '谱系总图'], ['roster', '人物线索'], ['time', '时间线索'],
  ['geo', '地理线索'], ['orphan', '孤点现象'], ['book', '学案原文'], ['yangming', '阳明心学'],
];

export function boot(core) {
  const model = createModel(core);
  store.set('data', model, { silent: true });
  themeCtl();
  card.mount();

  const pick = (id, anchor) => { store.selectPerson(id); card.show(id, anchor); };
  const ctl = {
    graph: graphCtl(model, { onPick: pick }),
    roster: rosterCtl(model, { onPick: pick }),
    time: timelineCtl(model, { onPick: pick }),
    geo: geoCtl(model, { onPick: pick }),
    kg: kgCtl(model, { onPick: pick }),
    book: bookCtl(model, { onPick: pick }),
    orphan: null,
    yangming: yangmingCtl(),
  };
  ctl.orphan = orphanCtl(model, {
    onPick: pick,
    onShowInKG: () => { router.go('kg'); setTimeout(() => ctl.kg.showOrphans(), 60); },
  });

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
    onLocate: (where, id) => locate(where, id),
  });

  function locate(where, id) {
    router.go(where, [id]);
    setTimeout(() => {
      const anchor = ctl[where] && ctl[where].locate ? ctl[where].locate(id) : null;
      if (anchor) card.show(id, anchor);
      const shell = $(where === 'kg' ? '.kg-shell' : '.graph-shell');
      if (shell) shell.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 90);
  }

  buildTabs();
  registerRoutes();
  router.migrateLegacyHash();
  router.start();

  on(EV.ROUTE_CHANGED, ({ name }) => {
    $$('#tabs button').forEach((b) => b.classList.toggle('on', b.dataset.t === name));
    $$('section.tab').forEach((s) => s.classList.toggle('on', s.id === `sec-${name}`));
  });

  function buildTabs() {
    const tabs = $('#tabs');
    tabs.innerHTML = VIEWS
      .map(([id, label]) => `<button data-t="${id}">${label}</button>`).join('');
    tabs.addEventListener('click', (e) => {
      const b = e.target.closest('button[data-t]');
      if (b) router.go(b.dataset.t);
    });
  }

  function registerRoutes() {
    for (const [name, title] of VIEWS) {
      const c = ctl[name];
      router.register(name, {
        title,
        onEnter: (route) => { card.hide(); if (c && c.enter) c.enter(route); },
        onLeave: () => { if (c && c.leave) c.leave(); },
      });
    }
  }

  reportCoverage(model);
  return { model, ctl, router };
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
