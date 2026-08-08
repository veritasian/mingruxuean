/**
 * kg.view.js —— 知识图谱（D3 v3 力导向）
 *
 * 散落态默认铺开，点谁就把谁的师、弟子、同门收拢到眼前，其余淡出。
 * 布局交给 force 引擎，这里只做「画节点/画边/改样式」。
 *
 * 高度跟随浏览器窗口：viewBox 与像素 1:1，窗口一变就重新量，
 * 力布局同步 resize —— 否则换个屏幕节点就挤在左上角。
 */
import { clear } from '../core/dom.js';
import { createForce, adjacencyOf } from '../engines/force.engine.js';

const ARROW = '<marker id="kg-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerUnits="strokeWidth"'
  + ' markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
  + '<path d="M0,1 L9,5 L0,9 z" fill="#B43232"/></marker>';

export function create(svgEl, model, { onPick, d3 = window.d3 } = {}) {
  if (!d3) {
    svgEl.innerHTML = '<text x="24" y="40" fill="#A23B2E" font-size="14">'
      + '知识图谱依赖 D3 库，请保持联网（自动从 d3js.org / jsdelivr 加载）。</text>';
    return null;
  }
  clear(svgEl);
  let W = 1100; let H = 700;

  const nodeMap = new Map();
  const nd = (id) => {
    if (!nodeMap.has(id)) {
      const p = model.persons[id];
      nodeMap.set(id, {
        id, name: p.name, school: p.school,
        founder: model.isFounder(id), color: model.colorOf(p.school),
        orphan: model.degreeOf(id) === 0,
      });
    }
    return nodeMap.get(id);
  };
  // 孤点也要进图 —— 它们本身就是要讲的现象，不能因为没边就不画
  Object.keys(model.persons).forEach(nd);

  // relations.json 里 from=徒、to=师。这里刻意反过来接：
  // source=师、target=徒，箭头（marker-end）才会落在徒身上，
  // 与谱系总图「连线自师指向徒」一致。两页方向不一样会读出完全相反的意思。
  const links = model.edgeList().map((r) => ({
    source: nd(r.to), target: nd(r.from),
    teacher: r.to, disciple: r.from,
    rela: r.type === '私淑' ? '私淑' : '师',
    weak: !r.cited, type: r.type, cited: r.cited,
  }));
  const nodes = [...nodeMap.values()];
  const adj = adjacencyOf(links);

  const root = d3.select(svgEl);
  root.append('defs').html(ARROW);
  const container = root.append('g').attr('id', 'kgZoom');
  const edgeLayer = container.append('g');
  const labelLayer = container.append('g');
  const nodeLayer = container.append('g');

  const force = createForce({ nodes, links, width: W, height: H, d3 });

  const edgeSel = edgeLayer.selectAll('.kg-edge').data(links).enter().append('path')
    .attr('class', (d) => `kg-edge${d.weak ? ' weak' : ''}`)
    .attr('fill', 'none')
    .attr('marker-end', 'url(#kg-arrow)')
    .style('stroke', (d) => (d.type === '私淑' ? '#3f9e76' : '#B43232'))
    .style('stroke-width', 1.2)
    .style('stroke-dasharray', (d) => (d.type === '私淑' ? '5 4' : (d.weak ? '2 3' : null)))
    .style('opacity', (d) => (d.weak ? 0.22 : 0.34));

  const labelSel = labelLayer.selectAll('.kg-elabel').data(links).enter().append('text')
    .attr('class', 'kg-elabel')
    .style('font-size', '9px').style('fill', '#9a8')
    .style('text-anchor', 'middle').style('pointer-events', 'none')
    .style('paint-order', 'stroke').style('stroke', '#fff').style('stroke-width', '2.5px')
    .style('opacity', 0.3)
    .text((d) => d.rela);

  let moved = false;
  const drag = force.drag(() => { moved = false; }).on('drag', () => { moved = true; });
  const nodeSel = nodeLayer.selectAll('.kg-node').data(nodes).enter().append('g')
    .attr('class', (d) => `kg-node${d.orphan ? ' kg-orphan' : ''}`)
    .call(drag)
    .on('click', function click(d) {
      if (moved) { moved = false; return; }
      if (onPick) onPick(d.id, this);
    });

  nodeSel.append('circle')
    .attr('r', (d) => (d.founder ? 17 : (d.orphan ? 8 : 12)))
    .attr('fill', (d) => d.color)
    .attr('fill-opacity', (d) => (d.orphan ? 0.35 : 1))
    .attr('stroke', (d) => (d.founder ? '#fff' : 'rgba(255,255,255,.85)'))
    .attr('stroke-dasharray', (d) => (d.orphan ? '3 2' : null))
    .attr('stroke-width', (d) => (d.founder ? 3 : 1.5));

  nodeSel.append('text')
    .attr('dy', '.35em').attr('text-anchor', 'middle')
    .style('font-size', (d) => (d.founder ? '13px' : (d.orphan ? '9px' : '10.5px')))
    .style('font-weight', (d) => (d.founder ? '600' : '400'))
    .style('fill', (d) => (d.orphan ? '#7a7268' : '#33294a'))
    .style('paint-order', 'stroke').style('stroke', '#fff')
    .style('stroke-width', '3px').style('stroke-linejoin', 'round')
    .style('pointer-events', 'none')
    .text((d) => d.name);

  const zoom = d3.behavior.zoom().scaleExtent([0.15, 6]).on('zoom', () => {
    container.attr('transform', `translate(${d3.event.translate})scale(${d3.event.scale})`);
  });
  root.call(zoom);

  function zoomStep(factor) {
    const s = zoom.scale(); const t = zoom.translate();
    const k = Math.max(0.15, Math.min(6, s * factor));
    const cx = W / 2; const cy = H / 2;
    const tx = cx - (cx - t[0]) * (k / s); const ty = cy - (cy - t[1]) * (k / s);
    zoom.scale(k).translate([tx, ty]);
    container.attr('transform', `translate(${tx},${ty})scale(${k})`);
  }

  force.onTick(() => {
    edgeSel.attr('d', (d) => `M${d.source.x},${d.source.y}L${d.target.x},${d.target.y}`);
    labelSel.attr('x', (d) => (d.source.x + d.target.x) / 2)
      .attr('y', (d) => (d.source.y + d.target.y) / 2);
    nodeSel.attr('transform', (d) => `translate(${d.x},${d.y})`);
  });

  let started = false;
  function resize() {
    const shell = svgEl.parentNode;
    if (shell && shell.classList && shell.classList.contains('kg-shell')) {
      const top = shell.getBoundingClientRect().top + (window.pageYOffset || 0);
      const avail = Math.round(window.innerHeight - top - 28);
      shell.style.height = `${Math.max(400, Math.min(avail, Math.round(window.innerHeight * 0.92)))}px`;
    }
    const r = svgEl.getBoundingClientRect();
    const w = Math.round(r.width) || W; const h = Math.round(r.height) || H;
    if (w < 80 || h < 80) return;                        // 标签页隐藏时不量
    if (Math.abs(w - W) < 2 && Math.abs(h - H) < 2) return;
    W = w; H = h;
    svgEl.setAttribute('viewBox', `0 0 ${W} ${H}`);
    force.sim.size([W, H]);
    if (started) force.sim.alpha(0.28);
  }

  resize();
  force.start();
  started = true;

  let focused = null;
  return {
    resize,
    start() { force.start(); },
    stop() { force.stop(); },
    focusedId: () => focused,
    nodeEl(id) { return nodeSel.filter((d) => d.id === id).node(); },
    focus(id) {
      focused = id;
      const near = adj.get(id) || new Set();
      edgeSel.style('stroke-width', (o) => ((o.source.id === id || o.target.id === id) ? 3 : 0.4))
        .style('opacity', (o) => ((o.source.id === id || o.target.id === id) ? 0.95 : 0.05));
      labelSel.style('opacity', (o) => ((o.source.id === id || o.target.id === id) ? 0.95 : 0.03));
      nodeSel.style('opacity', (o) => ((o.id === id || near.has(o.id)) ? 1 : 0.1));
    },
    clearFocus() {
      focused = null;
      edgeSel.style('stroke-width', 1.2).style('opacity', (o) => (o.weak ? 0.22 : 0.34));
      labelSel.style('opacity', 0.3);
      nodeSel.style('opacity', 1);
    },
    /** 只留孤点：讲「孤点现象」时用 */
    showOrphansOnly(on) {
      nodeSel.style('opacity', (o) => (on ? (o.orphan ? 1 : 0.06) : 1));
      edgeSel.style('opacity', (o) => (on ? 0.03 : (o.weak ? 0.22 : 0.34)));
      labelSel.style('opacity', on ? 0.02 : 0.3);
    },
    zoomIn() { zoomStep(1.3); },
    zoomOut() { zoomStep(1 / 1.3); },
    zoomReset() { zoom.scale(1).translate([0, 0]); container.attr('transform', 'translate(0,0)scale(1)'); },
    counts: { nodes: nodes.length, links: links.length },
    /** 供测试与排错：连线的实际朝向（source 应为师，target 应为徒） */
    edges: () => links.map((l) => ({
      source: l.source.id, target: l.target.id,
      teacher: l.teacher, disciple: l.disciple, type: l.type,
    })),
  };
}
