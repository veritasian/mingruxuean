import { webBoot } from '../controllers/web_boot.js';
import { create as graphCtl } from '../controllers/graph.controller.js';
webBoot('graph', { mount(model, api) { return graphCtl(model, { onPick: api.pick }); } });
