/**
 * roster.controller.js —— 人物总录控制器
 *
 * 总录一次渲染 250 张卡片，进页面时才建，不在启动时抢时间。
 */
import { $ } from '../core/dom.js';
import * as view from '../views/roster.view.js';

export function create(model, { onPick }) {
  const box = $('#roster');
  let built = false;

  function build() {
    if (built) return;
    built = true;
    view.render(box, model, { onPick });
  }

  return {
    enter({ params }) {
      build();
      const id = params[0];
      if (!id || !model.persons[id]) return;
      const card = [...box.querySelectorAll('.pcard')]
        .find((c) => c.querySelector('.pn') && c.querySelector('.pn').textContent === model.persons[id].name);
      if (card) card.scrollIntoView({ behavior: 'smooth', block: 'center' });
    },
  };
}
