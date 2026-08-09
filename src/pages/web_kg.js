/**
 * pages/web_kg.js —— 知识图谱页（Web 版）
 */
import { webBoot } from '../controllers/web_boot.js';
import { create as kgCtl } from '../controllers/kg.controller.js';

webBoot('kg', {
  mount(model, api) {
    return kgCtl(model, { onPick: api.pick });
  },
});
