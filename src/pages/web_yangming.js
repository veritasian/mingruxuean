import { webBoot } from '../controllers/web_boot.js';
import { create as yangmingCtl } from '../controllers/yangming.controller.js';
webBoot('yangming', { needsCard: false, mount() { return yangmingCtl(); } });
