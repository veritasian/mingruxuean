/**
 * geo.controller.js —— 地理分布控制器
 *
 * chips、列表、横条三块共用一个「当前省」。状态放在这里，
 * 三块视图各自都不记 —— 记三份迟早对不上。
 */
import { $ } from '../core/dom.js';
import * as view from '../views/geo.view.js';

export function create(model, { onPick }) {
  const chipBox = $('#geoSum');
  const grid = $('#geoGrid');
  const bars = $('#geoBars');
  const table = $('#mapTbl');
  let groups = null;
  let selected = null;

  function build() {
    if (groups) return;
    groups = view.groupByProvince(model);
    view.renderChips(chipBox, groups, { onSelect: toggle });
    view.renderGrid(grid, groups, model, { onPick });
    view.renderBars(bars, groups, { onSelect: toggle });
    view.renderMapTable(table, model);
  }

  /** 再点一次同一个省 = 取消筛选 */
  function toggle(prov) {
    selected = selected === prov ? null : prov;
    view.applyFilter(chipBox, grid, bars, selected);
  }

  return {
    enter({ params }) {
      build();
      if (params[0]) { selected = params[0]; view.applyFilter(chipBox, grid, bars, selected); }
    },
    stats: () => (groups || []).map((g) => ({ prov: g.prov, count: g.ids.length })),
  };
}
