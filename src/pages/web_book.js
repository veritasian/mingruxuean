import { webBoot } from '../controllers/web_boot.js';
import { create as bookCtl } from '../controllers/book.controller.js';
webBoot('book', { mount(model, api) { return bookCtl(model, { onPick: api.pick }); } });
