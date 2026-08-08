/**
 * pages/geo.js —— 地理线索页入口（geo.html）
 */
import { boot } from '../controllers/app.controller.js';
import { create as geoCtl } from '../controllers/geo.controller.js';

boot('geo', {
  mount(model, api) {
    return geoCtl(model, { onPick: api.pick });
  },
});
