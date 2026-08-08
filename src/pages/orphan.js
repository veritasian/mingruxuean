/**
 * pages/orphan.js —— 孤点现象页入口（orphan.html）
 */
import { boot } from '../controllers/app.controller.js';
import { create as orphanCtl } from '../controllers/orphan.controller.js';

boot('orphan', {
  mount(model, api) {
    return orphanCtl(model, { onPick: api.pick, onShowInKG: api.showInKG });
  },
});
