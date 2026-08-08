/**
 * pages/roster.js —— 人物线索页入口（roster.html）
 */
import { boot } from '../controllers/app.controller.js';
import { create as rosterCtl } from '../controllers/roster.controller.js';

boot('roster', {
  mount(model, api) {
    return rosterCtl(model, { onPick: api.pick });
  },
});
