/**
 * wikitext.js —— wikitext → HTML
 *
 * 维基文库的原文带着模板、脚注、表格和一堆排版标记，直接塞进页面
 * 会满屏花括号。这里按「先剥后转」的顺序清一遍：
 * 注释 → 脚注 → 表格 → 模板 → 文件/分类 → 内链 → 标题 → 诗行，
 * 最后才做 HTML 转义和粗斜体，顺序反了会把标签自己转掉。
 */
import { esc } from '../core/dom.js';

const H = '\u0001H\u0001';
const POEM_A = '\u0001P\u0001';
const POEM_B = '\u0001/P\u0001';

export function toHTML(src) {
  let s = String(src || '');

  s = s.replace(/<!--[\s\S]*?-->/g, '');
  s = s.replace(/<ref[\s\S]*?<\/ref>/g, '').replace(/<ref[^>]*\/\s*>/g, '');
  // onlyinclude/noinclude 是维基的转录开关，不是内容，留着会在正文里露出标签
  s = s.replace(/<\/?(only|no|)include(only)?>/gi, '');
  s = s.replace(/\{\|[\s\S]*?\|\}/g, '');
  // 模板可能嵌套，反复剥到不再变化为止（封顶 8 轮，防病态输入）
  for (let i = 0; i < 8; i++) {
    const next = s.replace(/\{\{[^{}]*\}\}/g, '');
    if (next === s) break;
    s = next;
  }
  s = s.replace(/\[\[(File|Image|文件|图像|圖像|Category|分类|分類|作者|Author):[\s\S]*?\]\]/gi, '');
  s = s.replace(/\[\[([^[\]|]*)\|([^[\]]*)\]\]/g, '$2');
  s = s.replace(/\[\[([^[\]]*)\]\]/g, '$1');
  s = s.replace(/^(={2,4})\s*(.*?)\s*\1\s*$/gm, `\n${H}$2\n`);
  s = s.replace(/<poem>([\s\S]*?)<\/poem>/g, (m, inner) => `\n${POEM_A}${inner}\n${POEM_B}\n`);

  s = esc(s);

  s = s.replace(/'''''([^']+)'''''/g, '<b><i>$1</i></b>');
  s = s.replace(/'''([^']+)'''/g, '<b>$1</b>');
  s = s.replace(/''([^']+)''/g, '<i>$1</i>');

  const out = [];
  let inPoem = false;
  for (const raw of s.split(/\n+/)) {
    const line = raw.trim();
    if (!line) continue;
    if (line.startsWith(POEM_A)) { out.push('<div class="poem">'); inPoem = true; continue; }
    if (line.startsWith(POEM_B)) { out.push('</div>'); inPoem = false; continue; }
    if (line.startsWith(H)) { out.push(`<h4>${line.slice(H.length)}</h4>`); continue; }
    out.push(inPoem ? `${line}<br/>` : `<p class="par">${line}</p>`);
  }
  if (inPoem) out.push('</div>');
  return out.join('');
}

/** 检索用的纯文本：去掉全部标记，只留可读汉字 */
export function toPlain(src) {
  let s = String(src || '');
  s = s.replace(/<!--[\s\S]*?-->/g, '').replace(/<ref[\s\S]*?<\/ref>/g, '');
  s = s.replace(/\{\|[\s\S]*?\|\}/g, '');
  for (let i = 0; i < 8; i++) {
    const next = s.replace(/\{\{[^{}]*\}\}/g, '');
    if (next === s) break;
    s = next;
  }
  s = s.replace(/\[\[([^[\]|]*)\|([^[\]]*)\]\]/g, '$2').replace(/\[\[([^[\]]*)\]\]/g, '$1');
  s = s.replace(/<[^>]+>/g, '').replace(/'{2,5}/g, '').replace(/={2,4}/g, '');
  return s;
}
