import { webBoot } from '../controllers/web_boot.js';
import { create as orphanCtl } from '../controllers/orphan.controller.js';
webBoot('orphan', { mount(model, api) { return orphanCtl(model, { onPick: api.pick, onShowInKG: api.showInKG }); } });
