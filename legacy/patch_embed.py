#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Patch gen_html.py for embedded-book (offline) mode."""
import io

p = "gen_html.py"
src = io.open(p, encoding="utf-8").read()

# 1) 搜索条
old_bar = """    <div class="searchbar">
      <input id="q" type="text" placeholder="检索全文（本地向量索引：字符二元组 TF-IDF）"/>
      <button class="btn" id="qBtn">检索</button>
      <button class="btn" id="qClear">清空</button>
      <button class="btn" id="pullAll">一键缓存全部卷次</button>
      <button class="btn" id="wipeCache">清空缓存</button>
      <span class="hint" id="pullStatus"></span>
    </div>"""
new_bar = """    <div class="searchbar">
      <input id="q" type="text" placeholder="检索全文（本地向量索引：字符二元组 TF-IDF）"/>
      <button class="btn" id="qBtn">检索</button>
      <button class="btn" id="qClear">清空</button>
      __PULLBAR__
    </div>"""
assert old_bar in src, "bar not found"
src = src.replace(old_bar, new_bar)

# 2) PULLBAR_HTML 条件生成
old_books = """    print("Embedded BOOKS:", len(_books), "volumes,", sum(len(b["text"]) for b in _books), "chars")
else:
    BOOKS_JS = "[]"
    print("No all.json yet; reader will fetch at runtime.")"""
new_books = '''    print("Embedded BOOKS:", len(_books), "volumes,", sum(len(b["text"]) for b in _books), "chars")
    PULLBAR_HTML = '<span class="hint">63 卷全文已内嵌 · 离线可读 · 全文检索就绪</span>'
else:
    BOOKS_JS = "[]"
    PULLBAR_HTML = '<button class="btn" id="pullAll">一键缓存全部卷次</button><button class="btn" id="wipeCache">清空缓存</button><span class="hint" id="pullStatus"></span>'
    print("No all.json yet; reader will fetch at runtime.")'''
assert old_books in src, "books block not found"
src = src.replace(old_books, new_books)
src = src.replace("__PULLBAR__", "{{PULLBAR_HTML}}")

# 3) 事件绑定空值保护
src = src.replace(
    'document.getElementById("pullAll").addEventListener("click",pullAll);',
    'const _pa=document.getElementById("pullAll"); if(_pa) _pa.addEventListener("click",pullAll);')
src = src.replace(
    'document.getElementById("wipeCache").addEventListener("click",()=>{',
    'const _wc=document.getElementById("wipeCache"); if(_wc) _wc.addEventListener("click",()=>{')

# 4) loadVolume 优先内嵌
old_cache = """  // cache?
  let text=null;
  try{ text=localStorage.getItem(cacheKey(v)); }catch(e){}
  if(text){ renderVolume(item,text); addToIndex(v,text); return; }"""
new_cache = """  // 优先内嵌全文（离线）
  const emb = BOOKS.find(b=>b.v===v);
  if(emb && emb.text){ renderVolume(item,emb.text); addToIndex(v,emb.text); return; }
  // 其次本地缓存（运行时拉取模式）
  let text=null;
  try{ text=localStorage.getItem(cacheKey(v)); }catch(e){}
  if(text){ renderVolume(item,text); addToIndex(v,text); return; }"""
assert old_cache in src, "cache block not found"
src = src.replace(old_cache, new_cache)

# 5) 启动全量建索引
old_init = '// 启动时把已缓存的卷次重建入索引（实现"全量检索"）\nrebuildIndexFromCache();'
new_init = '''// 启动时：内嵌全文 → 全量建索引；否则从缓存重建
if(BOOKS && BOOKS.length){
  BOOKS.forEach(b=>{ if(b.text) addToIndex(b.v, b.text); });
}else{
  rebuildIndexFromCache();
}'''
assert old_init in src, "init block not found"
src = src.replace(old_init, new_init)

# 6) 渲染替换加入 PULLBAR
old_loop = 'for ph, val in [("/*DATA*/", DATA_JS), ("/*TIME*/", TIME_JS), ("/*GEO*/", GEO_JS), ("/*TOC*/", TOC_JS), ("/*BOOKS*/", BOOKS_JS)]:'
new_loop = 'for ph, val in [("/*DATA*/", DATA_JS), ("/*TIME*/", TIME_JS), ("/*GEO*/", GEO_JS), ("/*TOC*/", TOC_JS), ("/*BOOKS*/", BOOKS_JS), ("{{PULLBAR_HTML}}", PULLBAR_HTML)]:'
assert old_loop in src, "loop block not found"
src = src.replace(old_loop, new_loop)

io.open(p, "w", encoding="utf-8").write(src)
print("patched OK")
