import { webBoot } from '../controllers/web_boot.js';
import { create as timelineCtl } from '../controllers/timeline.controller.js';
webBoot('time', { mount(model, api) { return timelineCtl(model, { onPick: api.pick }); } });
