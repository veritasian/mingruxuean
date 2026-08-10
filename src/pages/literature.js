/**
 * pages/literature.js —— 心学文献页入口（lit-*.html）
 * 正文已静态预渲染，无需人物卡、无需核心数据模型，只挂目录滚动高亮控制器。
 */
import { boot } from '../controllers/app.controller.js';
import { create as litCtl } from '../controllers/literature.controller.js';

boot('literature', {
  needsCard: false,
  needsData: false,
  mount() {
    return litCtl();
  },
});
