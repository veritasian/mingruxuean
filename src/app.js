/**
 * app.js —— 入口
 *
 * 全站只有这里是「开始执行」的地方。取数、装配、报错兜底三件事，
 * 其余一概交给 app.controller。
 */
import { loadCore } from './data/repository.js';
import { boot } from './controllers/app.controller.js';
import * as store from './core/store.js';

async function main() {
  store.restore();
  try {
    const core = await loadCore();
    const app = boot(core);
    // 调试时在控制台摸数据用；不是给业务代码调的
    window.__MRXA_APP__ = app;
  } catch (err) {
    console.error('[明儒学案] 启动失败', err);
    const box = document.querySelector('.wrap') || document.body;
    const tip = document.createElement('div');
    tip.style.cssText = 'margin:60px auto;max-width:560px;padding:22px 26px;'
      + 'border:1px solid #d9cfc0;border-left:3px solid #A23B2E;background:#fffdf8;'
      + 'font-size:14px;line-height:2;color:#3b332a';
    tip.innerHTML = '<b>数据载入失败</b><br/>开发模式需要用本地服务器打开（浏览器不允许 '
      + 'file:// 下 fetch JSON）。<br/>在项目根目录执行 <code>python3 -m http.server 8080</code>，'
      + '再访问 <code>http://localhost:8080/index.html</code>。<br/>'
      + `<span style="font-size:12px;color:#7a7268">${String(err && err.message || err)}</span>`;
    box.prepend(tip);
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', main);
} else {
  main();
}
