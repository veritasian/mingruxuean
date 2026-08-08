/**
 * pages/yangming.js —— 阳明心学页入口（yangming.html）
 * 无人物卡需求（needsCard=false），数据与样式只带本页。
 */
import { boot } from '../controllers/app.controller.js';
import { create as yangmingCtl } from '../controllers/yangming.controller.js';

boot('yangming', {
  needsCard: false,
  mount() {
    return yangmingCtl();
  },
});
