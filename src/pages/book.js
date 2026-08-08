/**
 * pages/book.js —— 学案原文页入口（book.html）
 * 本页是唯一内联 volumes（63 卷 + 卷前三篇）的页面，体量最大。
 */
import { boot } from '../controllers/app.controller.js';
import { create as bookCtl } from '../controllers/book.controller.js';

boot('book', {
  mount(model, api) {
    return bookCtl(model, { onPick: api.pick });
  },
});
