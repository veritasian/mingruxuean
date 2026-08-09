import { webBoot } from '../controllers/web_boot.js';
import { create as geoCtl } from '../controllers/geo.controller.js';
webBoot('geo', { mount(model, api) { return geoCtl(model, { onPick: api.pick }); } });
