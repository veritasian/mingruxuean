/**
 * literature.controller.js —— 心学文献页控制器
 *
 * 正文已由构建期预渲染成静态 HTML（prerender.literature_html），
 * 本控制器只做两件事（渐进增强，无 JS 也能读）：
 *   1. 目录滚动高亮（IntersectionObserver）：当前可见标题对应的目录项加 .on
 *   2. 平滑滚动到锚点（由 CSS scroll-behavior + 标题 scroll-margin-top 实现）
 */
export function create() {
  const body = document.querySelector('.lit-body');
  if (!body) return {};

  const headings = Array.from(body.querySelectorAll('h1, h2, h3'))
    .filter((h) => h.id);
  if (!headings.length) return {};

  const links = Array.from(document.querySelectorAll('.lit-toc a, .lit-nav a'));
  const linkFor = (id) =>
    document.querySelector('.lit-toc a[href="#' + id + '"], .lit-nav a[href="#' + id + '"]');

  let current = null;
  const setActive = (id) => {
    if (id === current) return;
    current = id;
    links.forEach((a) => a.classList.remove('on'));
    const a = linkFor(id);
    if (a) a.classList.add('on');
  };

  const io = new IntersectionObserver((entries) => {
    const visible = entries
      .filter((e) => e.isIntersecting)
      .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
    if (visible.length) setActive(visible[0].target.id);
  }, { rootMargin: '-72px 0px -68% 0px', threshold: 0 });

  headings.forEach((h) => io.observe(h));
  setActive(headings[0].id);

  // 点击目录平滑滚动到对应标题（标题已设 scroll-margin-top，不被顶栏遮住）
  links.forEach((a) => {
    a.addEventListener('click', (e) => {
      const href = a.getAttribute('href') || '';
      if (!href.startsWith('#')) return;
      const el = document.getElementById(href.slice(1));
      if (!el) return;
      e.preventDefault();
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      history.replaceState(null, '', '#' + el.id);
    });
  });

  return {};
}
