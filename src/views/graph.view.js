/**
 * graph.view.js —— 谱系总图（SVG 渲染）
 *
 * 只负责画和高亮，不决定「该高亮谁」——那是控制器的事。
 * 坐标来自 tree-layout 引擎，缩放来自 pan-zoom 引擎，
 * 这里剩下的就只有把点和线放上去。
 */
import { svg, clear } from '../core/dom.js';
import { layout, bounds, boundsOf, edgePath } from '../engines/tree-layout.engine.js';
import { createPanZoom } from '../engines/pan-zoom.engine.js';

const MARKERS = `
<marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerUnits="strokeWidth"
  markerWidth="7" markerHeight="7" orient="auto-start-reverse">
  <path d="M0,1 L9,5 L0,9 z" fill="#B9AE97"/></marker>
<marker id="arrow-hl" viewBox="0 0 10 10" refX="8" refY="5" markerUnits="strokeWidth"
  markerWidth="6" markerHeight="6" orient="auto-start-reverse">
  <path d="M0,1 L9,5 L0,9 z" fill="#A23B2E"/></marker>`;

export function create(svgEl, model, { onPick } = {}) {
  const defs = svg('defs', { html: MARKERS });
  const viewport = svg('g', { id: 'viewport' });
  const edgeLayer = svg('g', { class: 'edges' });
  const headLayer = svg('g', { class: 'heads' });
  const nodeLayer = svg('g', { class: 'nodes' });
  clear(svgEl);
  viewport.append(edgeLayer, headLayer, nodeLayer);
  svgEl.append(defs, viewport);

  const schools = model.schools.map((s) => ({ id: s.id, members: s.members }));
  let plan = layout({ schools, depth: model.depth, order: 'book' });
  const nodeEls = new Map();
  const edgeEls = [];
  const pz = createPanZoom(svgEl, viewport, { min: 0.18, max: 4 });

  function render() {
    clear(edgeLayer); clear(headLayer); clear(nodeLayer);
    edgeEls.length = 0; nodeEls.clear();
    drawHeads();
    drawEdges();
    drawNodes();
  }

  function drawHeads() {
    for (const c of plan.columns) {
      const color = model.colorOf(c.id);
      headLayer.append(
        svg('text', { x: c.x, y: 26, 'text-anchor': 'middle', class: 'col-head', fill: color, text: c.id }),
        svg('line', {
          x1: c.x - 44, x2: c.x + 44, y1: 32, y2: 32, stroke: color, 'stroke-width': 1, opacity: 0.6,
        }),
      );
    }
  }

  function drawEdges() {
    for (const r of model.edgeList()) {
      const a = plan.pos.get(r.from); const b = plan.pos.get(r.to);
      if (!a || !b) continue;
      // from = 弟子, to = 老师；线从师画到徒，箭头指向弟子
      const cls = `edge${r.type === '私淑' ? ' sishu' : ''}${r.cited ? '' : ' uncited'}`;
      const path = svg('path', { d: edgePath(b, a), class: cls });
      edgeLayer.appendChild(path);
      edgeEls.push({ el: path, from: r.from, to: r.to });
    }
  }

  function drawNodes() {
    for (const [id, c] of plan.pos) {
      const p = model.persons[id];
      if (!p) continue;
      const founder = model.isFounder(id);
      const g = svg('g', { class: 'node', 'data-id': id });
      if (founder) g.classList.add('founder');
      if (!model.teachersOf(id).length) g.classList.add('root');
      if (model.degreeOf(id) === 0) g.classList.add('orphan');
      g.append(svg('circle', {
        cx: c.x, cy: c.y, r: founder ? 7.5 : 5.5, fill: model.colorOf(p.school),
      }), svg('text', { x: c.x + 10, y: c.y + 4, text: p.name }));
      if (founder) {
        g.appendChild(svg('text', {
          class: 'ftag', x: c.x, y: c.y - 12, 'text-anchor': 'middle', text: model.roleTag(id),
        }));
      }
      g.addEventListener('click', (e) => {
        e.stopPropagation();
        if (pz.consumedClick()) return;
        if (onPick) onPick(id, g);
      });
      nodeLayer.appendChild(g);
      nodeEls.set(id, g);
    }
  }

  render();

  return {
    pz,
    layoutPlan: () => plan,
    /** 换排序方式（原书次序 / 代次），重排后保持当前视野 */
    setOrder(order) {
      plan = layout({ schools, depth: model.depth, order });
      render();
      pz.fit(bounds(plan.pos), { minScale: 0.2, maxScale: 1.1 });
    },
    fitAll() { pz.fit(bounds(plan.pos), { minScale: 0.18, maxScale: 1.1 }); },
    fitReadable() {
      const big = ['姚江学案', '江右王门学案', '泰州学案', '浙中王门学案']
        .flatMap((s) => model.members[s] || []);
      pz.fit(boundsOf(plan.pos, big.length ? big : [...plan.pos.keys()]), { minScale: 0.9, maxScale: 1.4 });
    },
    fitIds(ids) { pz.fit(boundsOf(plan.pos, ids), { minScale: 0.9, maxScale: 1.6 }); },
    center(id) {
      const c = plan.pos.get(id);
      if (!c) return;
      const t = pz.transform;
      const s = Math.max(t.scale, 1.4);
      pz.fit({ minX: c.x - 320 / s, maxX: c.x + 320 / s, minY: c.y - 200 / s, maxY: c.y + 200 / s },
        { minScale: s, maxScale: s });
    },
    highlight(ids) {
      const keep = new Set(ids);
      for (const [id, g] of nodeEls) {
        g.classList.toggle('dim', !keep.has(id));
        g.classList.toggle('hl', keep.has(id));
      }
      edgeEls.forEach((o) => o.el.classList.toggle('hl', keep.has(o.from) && keep.has(o.to)));
    },
    clearHighlight() {
      nodeEls.forEach((g) => g.classList.remove('dim', 'hl'));
      edgeEls.forEach((o) => o.el.classList.remove('hl'));
    },
    nodeEl: (id) => nodeEls.get(id) || null,
    /** 主题切换后箭头颜色要跟着走，marker 不吃 currentColor */
    repaintMarkers() {
      const cs = getComputedStyle(document.documentElement);
      const e = cs.getPropertyValue('--edge').trim();
      const h = cs.getPropertyValue('--edge-hl').trim();
      const a = defs.querySelector('#arrow path');
      const b = defs.querySelector('#arrow-hl path');
      if (a && e) a.setAttribute('fill', e);
      if (b && h) b.setAttribute('fill', h);
    },
  };
}
