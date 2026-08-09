import { webBoot } from '../controllers/web_boot.js';
import { create as rosterCtl } from '../controllers/roster.controller.js';
webBoot('roster', { mount(model, api) { return rosterCtl(model, { onPick: api.pick }); } });
