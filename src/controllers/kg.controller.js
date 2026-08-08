/**
 * kg.controller.js —— 知识图谱控制器
 *
 * 力布局很吃 CPU，所以离开这一页就 stop()，回来再 start()。
 * 这个开关必须由控制器管：视图不知道自己是不是正被人看着。
 */
import { $ } from '../core/dom.js';
import * as view from '../views/kg.view.js';

const HINT_IDLE = '点击任意人物：其师、弟子、私淑者被高亮，其余淡出 · 滚轮缩放 · 拖背景平移 · 拖节点移动';

export function create(model, { onPick, onRoute }) {
  const svgEl = $('#kg');
  const hint = $('#kgHint');
  let kg = null;
  let orphanOnly = false;

  function build() {
    if (kg) return kg;
    kg = view.create(svgEl, model, {
      onPick: (id, node) => {
        if (kg.focusedId() === id) { kg.clearFocus(); updateHint(); return; }
        kg.focus(id);
        updateHint();
        onPick(id, node);
      },
    });
    if (!kg) return null;
    bindToolbar();
    updateHint();
    return kg;
  }

  function bindToolbar() {
    $('#kgZoomIn').addEventListener('click', () => kg.zoomIn());
    $('#kgZoomOut').addEventListener('click', () => kg.zoomOut());
    $('#kgZoomReset').addEventListener('click', () => kg.zoomReset());
    $('#kgReset').addEventListener('click', () => {
      kg.clearFocus();
      orphanOnly = false;
      $('#kgOrphan').classList.remove('on');
      updateHint();
    });
    const ob = $('#kgOrphan');
    if (ob) {
      ob.addEventListener('click', () => {
        orphanOnly = !orphanOnly;
        ob.classList.toggle('on', orphanOnly);
        kg.clearFocus();
        kg.showOrphansOnly(orphanOnly);
        updateHint();
      });
    }
    window.addEventListener('resize', () => kg && kg.resize());
  }

  function updateHint() {
    if (!hint) return;
    const id = kg && kg.focusedId();
    if (orphanOnly) {
      const n = model.orphanData.meta.orphan_count;
      hint.textContent = `只显示孤点：${n} 人不与任何师承相连 · `
        + '其中多数是编纂设计使然，详见「孤点现象」一页';
      return;
    }
    if (!id) {
      const c = kg ? kg.counts : { nodes: 0, links: 0 };
      hint.textContent = `${HINT_IDLE} · 共 ${c.nodes} 人 ${c.links} 条关系`;
      return;
    }
    const p = model.persons[id];
    const deg = model.degreeOf(id);
    hint.textContent = `焦点：${p.name}（${p.school}）· 相连 ${deg} 人 · 再点同一人或「散开」复位`;
  }

  return {
    enter({ params }) {
      const g = build();
      if (!g) return;
      g.resize();
      g.start();
      const name = params[0];
      if (name && model.persons[name]) {
        setTimeout(() => { g.focus(name); updateHint(); onPick(name, g.nodeEl(name)); }, 120);
      }
    },
    leave() { if (kg) kg.stop(); },
    locate(id) {
      const g = build();
      if (!g) return null;
      g.focus(id);
      updateHint();
      return g.nodeEl(id);
    },
    /** 从孤点现象页跳过来时，直接进入只看孤点的状态 */
    showOrphans() {
      const g = build();
      if (!g) return;
      orphanOnly = true;
      $('#kgOrphan').classList.add('on');
      g.showOrphansOnly(true);
      updateHint();
      if (onRoute) onRoute('kg');
    },
    /** 排错与测试用：拿到已构建的视图对象 */
    get view() { return kg; },
  };
}
