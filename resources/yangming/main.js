/* =========================================================
   阳明心学 · 交互脚本
   - 肆~拾肆 四象限数据渲染
   - IntersectionObserver 渐入
   - 导航 active 态
   - 矩阵单元格 3D 倾斜
   - 便签随机角度
   ========================================================= */

(() => {
  const emptyQuads = () => [
    { pos: 'tl', color: 'red', title: '', lines: [], note: '' },
    { pos: 'tr', color: 'yellow', title: '', lines: [], note: '' },
    { pos: 'bl', color: 'green', title: '', lines: [], note: '' },
    { pos: 'br', color: 'red', title: '', lines: [], note: '' }
  ];

  const QUADS = [
    {
      id: 'ch4',
      body: { char: '理', hint: '体' },
      use: { char: '心', hint: '用' },
      q: [
        { pos: 'tl', color: 'red', title: '执相逐物', lines: ['安排思索', '见闻觉知'], note: '论气不论性，不明' },
        { pos: 'tr', color: 'yellow', title: '寂然不动', lines: ['廓然大公', '感而遂通', '物而顺应'], note: '君子之学' },
        { pos: 'bl', color: 'green', title: '', lines: [], note: '' },
        { pos: 'br', color: 'red', title: '枯木寒潭', lines: ['寸草不生', '佛老落空'], note: '论性不论气，不备' }
      ]
    },
    {
      id: 'ch5',
      body: { char: '知', hint: '体' },
      use: { char: '行', hint: '用' },
      q: [
        { pos: 'tl', color: 'red', title: '行而不知', lines: ['冥行妄作'], note: '' },
        { pos: 'tr', color: 'yellow', title: '知行合一', lines: ['圣境'], note: '知之切，反身之门' },
        { pos: 'bl', color: 'green', title: '不知不行', lines: ['匹夫之愚'], note: '' },
        { pos: 'br', color: 'red', title: '知而不行', lines: ['悬空思索'], note: '' }
      ]
    },
    { id: 'ch6', body: { char: '中', hint: '体' }, use: { char: '和', hint: '用' }, q: [
      { pos: 'tl', color: 'red', title: '有和无中', lines: ['明诚功夫'], note: '容易乡愿' },
      { pos: 'tr', color: 'yellow', title: '致中和', lines: ['天地位'], note: '诚明' },
      { pos: 'bl', color: 'green', title: '', lines: [], note: '' },
      { pos: 'br', color: 'red', title: '有中无和', lines: ['明诚功夫'], note: '难成功业' }
    ] },
    { id: 'ch7', body: { char: '明德', hint: '体' }, use: { char: '亲民', hint: '用' }, q: [
      { pos: 'tl', color: 'red', title: '功利之徒', lines: ['五伯'], note: '' },
      { pos: 'tr', color: 'yellow', title: '止于至善', lines: [], note: '' },
      { pos: 'bl', color: 'green', title: '', lines: [], note: '' },
      { pos: 'br', color: 'red', title: '虚无主义', lines: ['二氏'], note: '' }
    ] },
    { id: 'ch8', body: { char: '定', hint: '体' }, use: { char: '慧', hint: '用' }, q: [
      { pos: 'tl', color: 'red', title: '有慧无定', lines: ['执相逐物'], note: '' },
      { pos: 'tr', color: 'yellow', title: '定慧等持', lines: ['菩提即生'], note: '' },
      { pos: 'bl', color: 'green', title: '', lines: [], note: '' },
      { pos: 'br', color: 'red', title: '有定无慧', lines: ['枯木死灰'], note: '' }
    ] },
    { id: 'ch9', body: { char: '止', hint: '体' }, use: { char: '观', hint: '用' }, q: [
      { pos: 'tl', color: 'red', title: '观而不止', lines: ['病在散乱'], note: '' },
      { pos: 'tr', color: 'yellow', title: '止观不二', lines: ['菩提顿现'], note: '' },
      { pos: 'bl', color: 'green', title: '', lines: [], note: '' },
      { pos: 'br', color: 'red', title: '止而不观', lines: ['病在昏沉'], note: '' }
    ] },
    { id: 'ch10', body: { char: '无', hint: '体' }, use: { char: '有', hint: '用' }, q: [
      { pos: 'tl', color: 'red', title: '有而不无', lines: ['心被境夺'], note: '' },
      { pos: 'tr', color: 'yellow', title: '有无不二', lines: ['道德等持'], note: '' },
      { pos: 'bl', color: 'green', title: '', lines: [], note: '' },
      { pos: 'br', color: 'red', title: '无而不有', lines: ['心被空夺'], note: '' }
    ] },
    { id: 'ch11', body: { char: '性', hint: '体' }, use: { char: '命', hint: '用' }, q: [
      { pos: 'tl', color: 'red', title: '有命无性', lines: ['养心不中'], note: '' },
      { pos: 'tr', color: 'yellow', title: '性命双修', lines: ['理气中和'], note: '' },
      { pos: 'bl', color: 'green', title: '', lines: [], note: '' },
      { pos: 'br', color: 'red', title: '有性无命', lines: ['养身不和'], note: '' }
    ] },
    { id: 'ch12', body: { char: '虚', hint: '体' }, use: { char: '实', hint: '用' }, q: [
      { pos: 'tl', color: 'red', title: '有实无虚', lines: ['病在形势'], note: '' },
      { pos: 'tr', color: 'yellow', title: '虚实相生', lines: ['画成妙境'], note: '' },
      { pos: 'bl', color: 'green', title: '', lines: [], note: '' },
      { pos: 'br', color: 'red', title: '有虚无实', lines: ['气势过旺'], note: '' }
    ] },
    { id: 'ch13', body: { char: '正', hint: '体' }, use: { char: '奇', hint: '用' }, q: [
      { pos: 'tl', color: 'red', title: '有奇无正', lines: ['落于奸诈'], note: '' },
      { pos: 'tr', color: 'yellow', title: '奇正相生', lines: ['灵机妙用'], note: '' },
      { pos: 'bl', color: 'green', title: '', lines: [], note: '' },
      { pos: 'br', color: 'red', title: '有正无奇', lines: ['落于木纳'], note: '' }
    ] },
    { id: 'ch14', body: { char: '形', hint: '体' }, use: { char: '势', hint: '用' }, q: [
      { pos: 'tl', color: 'red', title: '有势无形', lines: ['终归消散'], note: '' },
      { pos: 'tr', color: 'yellow', title: '形势和一', lines: ['山水大成'], note: '' },
      { pos: 'bl', color: 'green', title: '', lines: [], note: '' },
      { pos: 'br', color: 'red', title: '有形无势', lines: ['难成大气'], note: '' }
    ] }
  ];

  const renderQuads = () => {
    QUADS.forEach((data) => {
      const wrap = document.querySelector(`[data-quad="${data.id}"]`);
      if (!wrap) return;

      const frame = document.createElement('div');
      frame.className = 'quad-frame';
      frame.setAttribute('data-reveal', '');

      const topCap = document.createElement('div');
      topCap.className = 'quad-cap quad-cap-top';
      topCap.innerHTML = `<span class="quad-tail quad-tail-v"></span><span class="quad-circle">${data.use.char}</span><span class="quad-hint">${data.use.hint}</span>`;

      const rightCap = document.createElement('div');
      rightCap.className = 'quad-cap quad-cap-right';
      rightCap.innerHTML = `<span class="quad-tail quad-tail-h"></span><span class="quad-circle">${data.body.char}</span><span class="quad-hint">${data.body.hint}</span>`;

      const board = document.createElement('div');
      board.className = 'quad-board';

      board.innerHTML = `
        <div class="quad-axis quad-axis-y"></div>
        <div class="quad-axis quad-axis-x"></div>
      `;

      data.q.forEach((q) => {
        const qEl = document.createElement('div');
        qEl.className = `quad-quadrant qq-${q.pos}`;
        qEl.setAttribute('data-reveal', '');

        const linesHtml = q.lines.length ? q.lines.map((l) => `<p>${l}</p>`).join('') : '';
        const noteHtml = q.note ? `<small>${q.note}</small>` : '';
        const titleHtml = q.title ? `<strong>${q.title}</strong>` : '';
        const contentHtml = titleHtml || linesHtml || noteHtml ? `${titleHtml}${linesHtml}${noteHtml}` : '';

        if (contentHtml) {
          qEl.innerHTML = `<div class="quad-sticky qs-${q.color}">${contentHtml}</div>`;
        }
        board.appendChild(qEl);
      });

      frame.appendChild(topCap);
      frame.appendChild(rightCap);
      frame.appendChild(board);

      const foot = document.createElement('p');
      foot.className = 'quad-foot';
      foot.textContent = '横轴为体 · 纵轴为用 · 中道合一';

      wrap.appendChild(frame);
      wrap.appendChild(foot);
    });
  };

  const reveal = (els) => {
    if (!('IntersectionObserver' in window)) {
      els.forEach((el) => el.classList.add('is-in'));
      return;
    }
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-in');
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
    );
    els.forEach((el) => io.observe(el));
  };

  const activeNav = () => {
    const sections = Array.from({ length: 14 }, (_, i) => document.getElementById(`ch${i + 1}`)).filter(Boolean);
    const links = new Map(
      Array.from(document.querySelectorAll('.site-nav a')).map((a) => [
        a.getAttribute('href').replace('#', ''),
        a
      ])
    );
    if (!sections.length) return;

    const onScroll = () => {
      const y = window.scrollY + window.innerHeight * 0.35;
      let cur = sections[0].id;
      sections.forEach((s) => {
        if (s.offsetTop <= y) cur = s.id;
      });
      links.forEach((a, id) => {
        a.style.color = id === cur ? 'var(--cl-text)' : '';
      });
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  };

  const tiltOnHover = () => {
    const cells = document.querySelectorAll('.cell');
    cells.forEach((cell) => {
      cell.addEventListener('mousemove', (e) => {
        const r = cell.getBoundingClientRect();
        const x = (e.clientX - r.left) / r.width - 0.5;
        const y = (e.clientY - r.top) / r.height - 0.5;
        cell.style.transform = `translateY(-3px) perspective(600px) rotateX(${-y * 4}deg) rotateY(${x * 4}deg)`;
      });
      cell.addEventListener('mouseleave', () => {
        cell.style.transform = '';
      });
    });
  };

  const stickyPeel = () => {
    const stickies = document.querySelectorAll('.sticky, .quad-sticky');
    stickies.forEach((el) => {
      const r0 = Math.random() * 2 - 1;
      el.style.transform = `rotate(${r0}deg)`;
    });
  };

  document.addEventListener('DOMContentLoaded', () => {
    renderQuads();
    reveal(document.querySelectorAll('[data-reveal]'));
    activeNav();
    tiltOnHover();
    stickyPeel();
  });
})();
