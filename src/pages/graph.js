/**
 * pages/graph.js —— 谱系总图页入口（graph.html）
 */
import { boot } from '../controllers/app.controller.js';
import { create as graphCtl } from '../controllers/graph.controller.js';

boot('graph', {
  mount(model, api) {
    return graphCtl(model, { onPick: api.pick });
  },
});
