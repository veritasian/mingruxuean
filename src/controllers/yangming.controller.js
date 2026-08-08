/**
 * yangming.controller.js —— 阳明心学专页控制器
 *
 * 职责：取数据 → 渲染 → 滚动监听（ScrollSpy）驱动置顶章节目录高亮。
 * 进入本视图时挂监听，离开即摘，不跨页泄漏。
 */
import { $ } from '../core/dom.js';
import { loadYangming } from '../data/repository.js';
import * as view from '../views/yangming.view.js';

export function create() {
  const root = $('#yangmingRoot');
  let side = null;
  let ids = [];
  let active = false;
  let raf = 0;
  let io = null;

  async function enter() {
    active = true;
    const data = await loadYangming();
    const r = view.render(root, data, { onNav: (id) => jump(id) });
    side = r.side;
    ids = (data.chapters || []).map((c) => c.id);
    if (data.outro && data.outro.length) ids.push('ym-outro');
    reveal();
    document.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  function leave() {
    active = false;
    document.removeEventListener('scroll', onScroll);
    if (raf) cancelAnimationFrame(raf);
    raf = 0;
    if (io) { io.disconnect(); io = null; }
  }

  /** 渐入：滚进视口的区块淡入，复刻原页 IntersectionObserver 效果 */
  function reveal() {
    const els = root.querySelectorAll('.ym-reveal');
    if (!('IntersectionObserver' in window)) {
      els.forEach((n) => n.classList.add('is-in'));
      return;
    }
    io = new IntersectionObserver((entries) => {
      entries.forEach((en) => {
        if (en.isIntersecting) {
          en.target.classList.add('is-in');
          io.unobserve(en.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    els.forEach((n) => io.observe(n));
  }

  /** 滚动监听：取视口 30% 处所在章节为当前项 */
  function onScroll() {
    if (!active) return;
    if (raf) cancelAnimationFrame(raf);
    raf = requestAnimationFrame(() => {
      const probe = window.innerHeight * 0.3;
      let cur = ids[0] || '';
      for (const id of ids) {
        const n = document.getElementById(`ym-${id}`);
        if (n && n.getBoundingClientRect().top <= probe) cur = id;
      }
      // 滚到底时直接亮最后一项：尾部内容不足一屏，末章到不了探测线
      if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 6) {
        cur = ids[ids.length - 1] || cur;
      }
      view.markSide(side, cur);
    });
  }

  function jump(id) {
    const n = document.getElementById(`ym-${id}`);
    if (!n) return;
    n.scrollIntoView({ behavior: 'smooth', block: 'start' });
    view.markSide(side, id);
  }

  return { enter, leave };
}
