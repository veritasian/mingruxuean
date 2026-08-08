/**
 * pages/kg.js —— 知识图谱页入口（首页 index.html）
 * 只引入 kg 控制器；d3、kg 视图、kg 样式随它一起被打进本页。
 */
import { boot } from '../controllers/app.controller.js';
import { create as kgCtl } from '../controllers/kg.controller.js';

boot('kg', {
  mount(model, api) {
    return kgCtl(model, { onPick: api.pick });
  },
});
