/**
 * pages/time.js —— 时间线索页入口（time.html）
 */
import { boot } from '../controllers/app.controller.js';
import { create as timelineCtl } from '../controllers/timeline.controller.js';

boot('time', {
  mount(model, api) {
    return timelineCtl(model, { onPick: api.pick });
  },
});
