/**
 * pan-zoom.engine.js —— SVG 缩放平移
 *
 * 只认两个东西：一个 <svg> 和它里面一个当视口的 <g>。
 * 谁在用、画的是什么，一概不知道 —— 所以谱系图和知识图谱能共用同一份。
 */
export function createPanZoom(svgEl, viewportEl, opt = {}) {
  const cfg = { min: 0.15, max: 3.2, step: 1.12, ...opt };
  let scale = 1, tx = 0, ty = 0;
  let dragging = false, sx = 0, sy = 0, stx = 0, sty = 0, moved = false;
  const listeners = new Set();

  function apply() {
    viewportEl.setAttribute('transform', `translate(${tx},${ty}) scale(${scale})`);
    listeners.forEach((fn) => fn({ scale, tx, ty }));
  }

  function clampScale(s) {
    return Math.max(cfg.min, Math.min(cfg.max, s));
  }

  function zoomAt(cx, cy, factor) {
    const next = clampScale(scale * factor);
    if (next === scale) return;
    // 让光标下的那个点保持不动，否则缩放会「跑」
    tx = cx - (cx - tx) * (next / scale);
    ty = cy - (cy - ty) * (next / scale);
    scale = next;
    apply();
  }

  function onWheel(e) {
    e.preventDefault();
    const r = svgEl.getBoundingClientRect();
    zoomAt(e.clientX - r.left, e.clientY - r.top,
      e.deltaY < 0 ? cfg.step : 1 / cfg.step);
  }

  function onDown(e) {
    if (e.button !== 0) return;
    dragging = true; moved = false;
    sx = e.clientX; sy = e.clientY; stx = tx; sty = ty;
    svgEl.classList.add('dragging');
  }

  function onMove(e) {
    if (!dragging) return;
    const dx = e.clientX - sx, dy = e.clientY - sy;
    if (Math.abs(dx) + Math.abs(dy) > 3) moved = true;
    tx = stx + dx; ty = sty + dy;
    apply();
  }

  function onUp() {
    dragging = false;
    svgEl.classList.remove('dragging');
  }

  svgEl.addEventListener('wheel', onWheel, { passive: false });
  svgEl.addEventListener('mousedown', onDown);
  window.addEventListener('mousemove', onMove);
  window.addEventListener('mouseup', onUp);

  return {
    /** 把一个包围盒放进视野 */
    fit(box, { minScale = 0.2, maxScale = 1.1, padding = 24 } = {}) {
      const w = svgEl.clientWidth || svgEl.parentNode.clientWidth || 1200;
      const h = svgEl.clientHeight || svgEl.parentNode.clientHeight || 800;
      const bw = Math.max(1, box.maxX - box.minX);
      const bh = Math.max(1, box.maxY - box.minY);
      scale = clampScale(Math.max(minScale,
        Math.min(maxScale, Math.min((w - padding * 2) / bw, (h - padding * 2) / bh))));
      tx = (w - bw * scale) / 2 - box.minX * scale;
      ty = (h - bh * scale) / 2 - box.minY * scale;
      apply();
    },
    zoomIn() { zoomAt(svgEl.clientWidth / 2, svgEl.clientHeight / 2, cfg.step); },
    zoomOut() { zoomAt(svgEl.clientWidth / 2, svgEl.clientHeight / 2, 1 / cfg.step); },
    reset() { scale = 1; tx = 0; ty = 0; apply(); },
    /** 拖动过就不该再算作点击 */
    consumedClick() { return moved; },
    get transform() { return { scale, tx, ty }; },
    onChange(fn) { listeners.add(fn); return () => listeners.delete(fn); },
    destroy() {
      svgEl.removeEventListener('wheel', onWheel);
      svgEl.removeEventListener('mousedown', onDown);
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
      listeners.clear();
    },
  };
}
