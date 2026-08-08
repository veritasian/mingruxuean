#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate 明儒学案.html — v7 五页签单文件站
 谱系总图 / 人物总录 / 时间线(明代17帝) / 地理分布(籍贯→今地) / 学案原文(62卷, 运行时从 Wikisource 拉取+本地向量检索)
 3 主题 + 点击弹卡 保持.
"""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(BASE, "data_final.json"), encoding="utf-8"))
tl = json.load(open(os.path.join(BASE, "data_timeline.json"), encoding="utf-8"))
geo = json.load(open(os.path.join(BASE, "data_geo.json"), encoding="utf-8"))

PALETTE = ["#6b8e9e","#8a9a5b","#b08968","#9c6b4f","#a8322a","#c07a3e",
           "#7a8c3e","#5a7d7a","#8e6e9e","#4f7a8e","#9e8e6b","#35654d",
           "#b5523a","#6a4f7a","#3a6ea5"]
colors = {s: PALETTE[i % len(PALETTE)] for i, s in enumerate(data["schools"])}

DATA_JS = json.dumps({"people": data["people"], "schools": data["schools"],
                      "school_members": data["school_members"], "edges": data["edges"],
                      "tongmen": data.get("tongmen", []),
                      "founders": data["founders"], "colors": colors}, ensure_ascii=False)
TIME_JS = json.dumps(tl, ensure_ascii=False)
GEO_JS = json.dumps(geo, ensure_ascii=False)

_toc = json.load(open(os.path.join(BASE, "resources", "toc.json"), encoding="utf-8"))
TOC = [[t["v"], t["name"], t["pt"], t["ps"], t.get("name_s", t["name"])] for t in _toc]
TOC_JS = json.dumps(TOC, ensure_ascii=False)

# 若已批量取回全文（resources/volumes/all.json），一并内嵌为 /*BOOKS*/
_books_path = os.path.join(BASE, "resources", "volumes", "all.json")
if os.path.exists(_books_path):
    _books = json.load(open(_books_path, encoding="utf-8"))
    BOOKS_JS = json.dumps(_books, ensure_ascii=False)
    print("Embedded BOOKS:", len(_books), "volumes,", sum(len(b["text"]) for b in _books), "chars")
    PULLBAR_HTML = '<span class="hint">63 卷全文已内嵌 · 离线可读 · 全文检索就绪</span>'
else:
    BOOKS_JS = "[]"
    PULLBAR_HTML = '<button class="btn" id="pullAll">一键缓存全部卷次</button><button class="btn" id="wipeCache">清空缓存</button><span class="hint" id="pullStatus"></span>'
    print("No all.json yet; reader will fetch at runtime.")

HTML = r"""<!DOCTYPE html>
<html lang="zh" data-theme="zen">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>明儒学案 · 师承谱系 · 学案原文</title>
<style>
  /* ============ theme tokens ============ */
  :root{
    --paper:#F4F1E9; --paper2:#ECE6D8; --ink:#2A2823; --ink-soft:#6E685C;
    --accent:#A23B2E; --line:#DBD4C4; --card:#FBF8F0;
    --shadow:rgba(60,50,35,.12); --edge:#B9AE97; --edge-hl:#A23B2E; --moss:#7E8A6A;
    --grain:.03;
  }
  :root[data-theme="ink"]{
    --paper:#EDEAE3; --paper2:#E2DED4; --ink:#23221F; --ink-soft:#5C5950;
    --accent:#3E5566; --line:#CEC9BC; --card:#F6F4EE;
    --shadow:rgba(40,40,40,.10); --edge:#A8AB9E; --edge-hl:#3E5566; --moss:#6E7E6A;
    --grain:.022;
  }
  :root[data-theme="white"]{
    --paper:#FAFAF8; --paper2:#F1F0EC; --ink:#262626; --ink-soft:#757268;
    --accent:#B23A2C; --line:#E5E4DE; --card:#FFFFFF;
    --shadow:rgba(0,0,0,.06); --edge:#D0CFC9; --edge-hl:#B23A2C; --moss:#8A9A82;
    --grain:0;
  }
  *{box-sizing:border-box;}
  html,body{margin:0;padding:0;}
  body{
    font-family:"Yu Mincho","Hiragino Mincho ProN","Songti SC","Noto Serif CJK SC","Source Han Serif SC","STSong","SimSun",serif;
    color:var(--ink);
    background:radial-gradient(130% 90% at 50% -12%, var(--card) 0%, var(--paper) 58%, var(--paper2) 100%);
    background-attachment:fixed;min-height:100vh;
    transition:background .5s ease,color .5s ease;
  }
  body::before{
    content:"";position:fixed;inset:0;pointer-events:none;opacity:var(--grain);z-index:0;
    background-image:
      repeating-linear-gradient(0deg,#000 0 1px,transparent 1px 3px),
      repeating-linear-gradient(90deg,#000 0 1px,transparent 1px 3px);
  }
  .wrap{position:relative;z-index:1;width:100%;max-width:none;margin:0;padding:30px 20px 70px;}

  /* ---- theme switcher ---- */
  .theme-sw{position:fixed;top:14px;right:14px;z-index:60;display:flex;gap:3px;
    background:var(--card);border:1px solid var(--line);border-radius:22px;padding:4px;
    box-shadow:0 2px 12px var(--shadow);}
  .theme-sw button{border:none;background:transparent;padding:6px 13px;font-size:13px;
    font-family:inherit;color:var(--ink-soft);border-radius:18px;cursor:pointer;
    letter-spacing:2px;transition:.2s;}
  .theme-sw button:hover{color:var(--ink);}
  .theme-sw button.on{background:var(--accent);color:#fff;}

  /* ---- banner ---- */
  header.banner{position:relative;text-align:center;padding:36px 20px 22px;
    border-top:2px solid var(--ink);border-bottom:1px solid var(--line);}
  header.banner .seal{
    position:absolute;right:26px;top:24px;width:56px;height:56px;border:2px solid var(--accent);
    color:var(--accent);border-radius:6px;display:flex;align-items:center;justify-content:center;
    font-size:26px;line-height:1;transform:rotate(-6deg);opacity:.88;letter-spacing:-2px;font-weight:700;
  }
  h1.title{margin:0;font-size:44px;letter-spacing:16px;text-indent:16px;font-weight:600;}
  .subtitle{margin-top:8px;color:var(--ink-soft);font-size:13.5px;letter-spacing:4px;text-indent:4px;}

  /* ---- tabs ---- */
  nav.tabs{display:flex;justify-content:center;gap:6px;flex-wrap:wrap;margin:22px auto 6px;max-width:900px;}
  nav.tabs button{border:1px solid var(--line);background:var(--card);color:var(--ink-soft);
    border-radius:2px;padding:8px 20px;font-size:14.5px;letter-spacing:3px;font-family:inherit;cursor:pointer;transition:.2s;}
  nav.tabs button:hover{color:var(--ink);}
  nav.tabs button.on{background:var(--accent);border-color:var(--accent);color:#fff;}
  section.tab{display:none;margin-top:20px;}
  section.tab.on{display:block;}
  .tab-head{font-size:20px;letter-spacing:5px;margin:6px 0 14px;padding-left:13px;
    border-left:3px solid var(--accent);font-weight:600;}
  .tab-head small{font-size:12.5px;color:var(--ink-soft);letter-spacing:2px;font-weight:400;margin-left:10px;}

  /* ---- 门派总览 legend（含与谱系总图的间距） ---- */
  .legend{display:flex;flex-wrap:wrap;gap:8px;margin:0 2px 38px;}
  .legend .chip{display:inline-flex;align-items:center;gap:6px;padding:5px 12px;
    border:1px solid var(--line);border-radius:20px;background:var(--card);
    font-size:13px;letter-spacing:1px;cursor:pointer;transition:.2s;}
  .legend .chip:hover{outline:2px solid var(--accent);}
  .legend .chip.active{outline:2px solid var(--accent);}
  .legend .dot{width:11px;height:11px;border-radius:50%;flex:none;}

  /* ---- graph ---- */
  .graph-shell{position:relative;border:1px solid var(--line);border-radius:2px;
    background:linear-gradient(180deg,var(--card),var(--paper2));}
  .toolbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;padding:9px 12px;
    border-bottom:1px solid var(--line);}
  .btn{border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:2px;
    padding:5px 12px;font-size:13px;cursor:pointer;font-family:inherit;letter-spacing:.5px;}
  .btn:hover{opacity:.85;}
  select.btn{font-family:inherit;}
  .hint{font-size:12px;color:var(--ink-soft);margin-left:auto;letter-spacing:.5px;}
  #graph{width:100%;height:700px;display:block;cursor:grab;touch-action:none;}
  #graph.grabbing{cursor:grabbing;}
  .gcap{font-size:12.5px;color:var(--ink-soft);padding:10px 14px;letter-spacing:.5px;line-height:1.9;
    border-top:1px dashed var(--line);}
  .node circle{cursor:pointer;transition:opacity .15s;}
  .node text{font-size:12px;fill:var(--ink);pointer-events:none;paint-order:stroke;
    stroke:var(--paper2);stroke-width:3px;stroke-linejoin:round;
    font-family:"Yu Mincho","Songti SC","Noto Serif CJK SC","Source Han Serif SC",serif;}
  .col-head{font-size:13px;letter-spacing:2px;font-weight:600;
    font-family:"Yu Mincho","Songti SC","Noto Serif CJK SC","Source Han Serif SC",serif;
    paint-order:stroke;stroke:var(--paper2);stroke-width:3;stroke-linejoin:round;}
  .edge{stroke:var(--edge);stroke-width:1;opacity:.5;fill:none;marker-end:url(#arrow);}
  .edge.hl{stroke:var(--edge-hl);opacity:.95;stroke-width:2.4;marker-end:url(#arrow-hl);}
  .tongmen{stroke:var(--moss);stroke-width:1.2;opacity:.6;fill:none;stroke-dasharray:5 4;}
  .node.dim{opacity:.16;}
  .node.hl circle{stroke:var(--ink);stroke-width:2.2;}
  .node.root circle{stroke-dasharray:2 2;}
  .node.founder circle{stroke:var(--accent);stroke-width:2.6;}
  .node.founder text{font-weight:700;fill:var(--accent);}
  .node .ftag{font-size:10px;font-weight:700;letter-spacing:1px;fill:var(--accent);}

  /* ---- popover card ---- */
  .pc{position:fixed;z-index:80;width:322px;max-width:calc(100vw - 24px);
    background:var(--card);border:1px solid var(--line);border-radius:2px;
    box-shadow:0 10px 34px var(--shadow),0 1px 4px var(--shadow);
    padding:15px 17px 12px;opacity:0;transform:translateY(6px);pointer-events:none;
    transition:opacity .18s ease,transform .18s ease;}
  .pc.show{opacity:1;transform:none;pointer-events:auto;}
  .pc::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--accent);}
  .pc-x{position:absolute;top:7px;right:9px;cursor:pointer;color:var(--ink-soft);font-size:14px;
    line-height:1;background:none;border:none;padding:2px;}
  .pc-x:hover{color:var(--accent);}
  .pc h3{margin:2px 0 4px;font-size:22px;letter-spacing:3px;font-weight:700;}
  .pc .pc-meta{font-size:12.5px;color:var(--ink-soft);line-height:1.8;}
  .pc .pc-life{margin:7px 0;font-size:13px;color:var(--accent);font-weight:600;letter-spacing:1px;}
  .pc .pc-tags{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:9px;}
  .pc .tag{display:inline-block;padding:1px 8px;border:1px solid var(--line);border-radius:10px;
    font-size:12px;color:var(--ink-soft);}
  .pc .pc-rel{font-size:13px;line-height:2;border-top:1px dashed var(--line);padding-top:8px;margin-top:2px;}
  .pc .pc-rel b{color:var(--accent);font-weight:600;}
  .pc .pc-rel a{color:var(--accent);text-decoration:none;border-bottom:1px dotted var(--accent);cursor:pointer;}
  .pc .pc-foot{margin-top:10px;text-align:right;}
  .pc .pc-foot .btn{padding:4px 11px;font-size:12px;}

  /* ---- roster / tree ---- */
  details.school{border:1px solid var(--line);border-radius:2px;background:var(--card);
    margin-bottom:14px;overflow:hidden;}
  details.school>summary{cursor:pointer;padding:13px 18px;font-size:17px;letter-spacing:3px;
    font-weight:600;display:flex;align-items:center;gap:10px;list-style:none;}
  details.school>summary::-webkit-details-marker{display:none;}
  details.school>summary .dot{width:13px;height:13px;border-radius:50%;}
  details.school>summary .cnt{margin-left:auto;font-size:13px;color:var(--ink-soft);font-weight:400;}
  .tree-cap{font-size:12.5px;color:var(--ink-soft);letter-spacing:2px;padding:12px 18px 0;}
  .tree{list-style:none;padding-left:16px;margin:8px 0 6px;font-size:14px;}
  .tree ul{list-style:none;padding-left:24px;border-left:1px solid var(--line);margin-left:6px;}
  .tree li{position:relative;padding:4px 0 4px 18px;}
  .tree li::before{content:"";position:absolute;left:0;top:16px;width:15px;height:1px;background:var(--line);}
  .tree .tn{font-weight:600;letter-spacing:1px;cursor:pointer;}
  .tree .tn:hover{color:var(--accent);}
  .tree .te{font-size:12px;color:var(--ink-soft);}
  .tree .ext{color:var(--accent);}
  .cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:11px;padding:14px 18px 18px;}
  .pcard{border:1px solid var(--line);border-radius:2px;background:var(--card);padding:12px 14px;cursor:pointer;
    transition:.15s;position:relative;}
  .pcard:hover{box-shadow:0 2px 10px var(--shadow);transform:translateY(-1px);}
  .pcard .pn{font-size:18px;letter-spacing:1px;font-weight:600;}
  .pcard .pz{font-size:12px;color:var(--ink-soft);margin-top:4px;line-height:1.7;}
  .pcard .pz .life{color:var(--accent);font-weight:600;}
  .pcard .pr{font-size:12px;color:var(--accent);margin-top:6px;}
  .pcard .fb{position:absolute;top:9px;right:10px;font-size:11px;color:var(--accent);
    border:1px solid var(--accent);border-radius:10px;padding:1px 7px;letter-spacing:1px;}

  /* ---- timeline ---- */
  .tline-shell{border:1px solid var(--line);border-radius:2px;background:linear-gradient(180deg,var(--card),var(--paper2));}
  .tline-toolbar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;padding:9px 12px;border-bottom:1px solid var(--line);}
  .tline-wrap{overflow-x:auto;padding:8px;}
  #tline{display:block;min-width:1680px;}
  .tbar{cursor:pointer;}
  .tbar text{pointer-events:none;font-size:11px;fill:var(--ink);}
  .tbar.dim{opacity:.25;}
  .trow text{font-size:12.5px;fill:var(--ink-soft);letter-spacing:1px;pointer-events:none;}
  .pbar{cursor:pointer;}
  .pbar rect{transition:opacity .15s;}
  .pbar.dim{opacity:.12;}
  .tline-cap{font-size:12.5px;color:var(--ink-soft);padding:9px 14px;border-top:1px dashed var(--line);line-height:1.9;}
  #empList{margin:14px 0 4px;}
  .empgroup{border:1px solid var(--line);border-radius:2px;background:var(--card);padding:10px 14px;margin-bottom:10px;}
  .empgroup h4{margin:0 0 8px;font-size:14px;letter-spacing:2px;color:var(--accent);font-weight:600;}
  .empgroup .chips{display:flex;flex-wrap:wrap;gap:6px;}
  .pchip{display:inline-block;border:1px solid var(--line);border-radius:14px;padding:2px 10px;
    font-size:12.5px;cursor:pointer;background:var(--card);}
  .pchip:hover{outline:2px solid var(--accent);}
  .pchip .lif{color:var(--ink-soft);font-size:11px;margin-left:4px;}

  /* ---- geography ---- */
  .geo-sum{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px;}
  .gchip{display:inline-flex;align-items:center;gap:6px;padding:5px 12px;border:1px solid var(--line);
    background:var(--card);border-radius:20px;cursor:pointer;font-size:13px;}
  .gchip.on{outline:2px solid var(--accent);}
  .geogrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px;}
  .gprov{border:1px solid var(--line);border-radius:2px;background:var(--card);padding:12px 14px;}
  .gprov h4{margin:0 0 10px;font-size:15px;letter-spacing:2px;}
  .gprov h4 .cnt{color:var(--ink-soft);font-size:12px;font-weight:400;margin-left:6px;}
  .glist{display:flex;flex-direction:column;gap:7px;max-height:300px;overflow:auto;}
  .grow{display:flex;align-items:baseline;gap:8px;border-bottom:1px dashed var(--line);padding-bottom:5px;cursor:pointer;}
  .grow:hover .gn{color:var(--accent);}
  .grow .gn{font-size:14px;font-weight:600;}
  .grow .gx{font-size:11.5px;color:var(--ink-soft);}
  .grow .gx em{color:var(--accent);font-style:normal;}
  .map-tbl{width:100%;border-collapse:collapse;font-size:12.5px;}
  .map-tbl th,.map-tbl td{border:1px solid var(--line);padding:5px 9px;text-align:left;}
  .map-tbl th{background:var(--paper2);color:var(--ink-soft);font-weight:600;}

  /* ---- 籍贯柱状图 ---- */
  .geobars{display:flex;flex-direction:column;gap:7px;border:1px solid var(--line);
    border-radius:2px;background:var(--card);padding:16px 18px;margin:0 0 20px;}
  .geobar{display:flex;align-items:center;gap:12px;cursor:pointer;}
  .geobar:hover .gb-name{color:var(--accent);}
  .geobar .gb-name{width:66px;flex:none;text-align:right;font-size:13px;font-weight:600;letter-spacing:1px;}
  .geobar .gb-track{flex:1;height:20px;border:1px solid var(--line);border-radius:2px;
    background:var(--paper2);overflow:hidden;}
  .geobar .gb-fill{display:block;height:100%;width:0;background:var(--accent);opacity:.78;
    transition:width .7s cubic-bezier(.2,.7,.3,1);}
  .geobar .gb-num{width:52px;flex:none;font-size:12.5px;color:var(--ink-soft);}

  /* ---- book ---- */
  .book-shell{display:flex;gap:14px;align-items:flex-start;min-height:640px;}
  .toc-pane{width:270px;flex:none;border:1px solid var(--line);border-radius:2px;background:var(--card);
    max-height:82vh;overflow:auto;position:sticky;top:16px;padding:8px 0;}
  .toc-pane .toc-cap{padding:8px 14px 6px;font-size:13px;color:var(--ink-soft);letter-spacing:2px;
    border-bottom:1px dashed var(--line);position:sticky;top:0;background:var(--card);z-index:2;}
  .toc-item{display:flex;gap:8px;padding:7px 14px;cursor:pointer;border-bottom:1px dashed var(--line);}
  .toc-item:hover{background:var(--paper2);}
  .toc-item.on{background:var(--paper2);outline:1px solid var(--accent);}
  .toc-item .tv{flex:none;font-size:12px;color:var(--ink-soft);width:34px;}
  .toc-item .tn2{font-size:13.5px;font-weight:600;}
  .toc-item .tp{font-size:11.5px;color:var(--ink-soft);margin-top:1px;line-height:1.5;}
  .reader{flex:1;min-width:0;border:1px solid var(--line);border-radius:2px;background:var(--card);}
  .reader-head{padding:14px 18px;border-bottom:1px solid var(--line);}
  .reader-head h3{margin:0 0 8px;font-size:21px;letter-spacing:3px;}
  .reader-head .people{display:flex;flex-wrap:wrap;gap:6px;}
  .reader-body{padding:18px 24px 40px;line-height:2.05;font-size:15px;text-align:justify;}
  .reader-body h4{letter-spacing:2px;margin:26px 0 10px;font-size:17px;color:var(--accent);border-bottom:1px dashed var(--line);padding-bottom:6px;}
  .reader-body p{margin:0 0 12px;text-indent:2em;}
  .reader-body .par{margin:0 0 12px;text-indent:2em;}
  .reader-body .hit{background:rgba(162,59,46,.15);outline:1px solid var(--accent);}
  .reader-status{color:var(--ink-soft);font-size:13px;padding:30px;text-align:center;}
  .searchbar{display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap;align-items:center;}
  .searchbar input{flex:1;min-width:220px;border:1px solid var(--line);background:var(--card);color:var(--ink);
    padding:7px 12px;border-radius:2px;font-family:inherit;font-size:14px;}
  .searchbar .btn{white-space:nowrap;}
  #sres{display:none;border:1px solid var(--line);border-radius:2px;background:var(--card);margin-bottom:14px;max-height:380px;overflow:auto;}
  .sres-item{padding:10px 14px;border-bottom:1px dashed var(--line);cursor:pointer;}
  .sres-item:hover{background:var(--paper2);}
  .sres-item .shead{display:flex;gap:8px;align-items:baseline;}
  .sres-item .sv{font-size:12px;color:var(--ink-soft);}
  .sres-item .st{font-weight:700;font-size:14px;}
  .sres-item .sc{font-size:12px;color:var(--accent);margin-left:auto;}
  .sres-item .sp{font-size:12.5px;color:var(--ink-soft);margin-top:4px;line-height:1.8;}

  /* ---- knowledge graph ---- */
  .kg-shell{border:1px solid var(--line);border-radius:2px;background:linear-gradient(180deg,var(--card),var(--paper2));}
  .kg-toolbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;padding:9px 12px;border-bottom:1px solid var(--line);}
  #kg{width:100%;height:500px;display:block;touch-action:none;}
  .kg-node{cursor:pointer;}
  .kg-node text{font-size:17px;fill:var(--ink);pointer-events:none;paint-order:stroke;stroke:var(--paper2);stroke-width:3px;stroke-linejoin:round;
    font-family:"Yu Mincho","Songti SC","Noto Serif CJK SC","Source Han Serif SC",serif;}
  .kg-edge{stroke:var(--edge);stroke-width:1.2;opacity:.28;marker-end:url(#kg-arrow);}
  .kg-edge.on{stroke:var(--edge-hl);opacity:.9;stroke-width:1.6;}
  .kg-edge.tm{stroke:var(--moss);stroke-dasharray:5 4;marker:none;opacity:.55;}
  .kg-edge.tm.on{opacity:.95;stroke-width:1.6;}
  .kg-node.dim{opacity:.1;}
  .kg-node.dim text{opacity:.2;}
  .kg-node.kg-focus circle{stroke:var(--accent);stroke-width:2.8;}
  @media(max-width:780px){#kg{height:360px;}}
  footer{margin-top:44px;text-align:center;color:var(--ink-soft);font-size:12px;letter-spacing:1px;line-height:2;}
  @media(max-width:860px){
    .theme-sw{top:8px;right:8px;}
    .theme-sw button{padding:5px 10px;font-size:12px;}
    h1.title{font-size:30px;letter-spacing:9px;text-indent:9px;}
    #graph{height:460px;}
    .pc{width:calc(100vw - 20px);}
    .book-shell{flex-direction:column;}
    .toc-pane{width:100%;position:static;max-height:280px;}
  }
</style>
</head>
<body>
<div class="theme-sw" id="themeSw"></div>
<div class="wrap">
  <header class="banner">
    <div class="seal">学案</div>
    <h1 class="title">明儒学案</h1>
    <div class="subtitle">师承谱系 · 明代儒林 · 六十二卷学案全文</div>
    <nav class="tabs" id="tabs">
      <button data-t="graph" class="on">谱系总图</button>
      <button data-t="roster">人物总录</button>
      <button data-t="time">时间线</button>
      <button data-t="geo">地理分布</button>
      <button data-t="kg">知识图谱</button>
      <button data-t="book">学案原文</button>
    </nav>
  </header>

  <!-- ===== 谱系总图 ===== -->
  <section class="tab" id="sec-graph">
    <div class="tab-head">门派总览 <small>17 学案 · 250 人 · 点击学派可聚焦</small></div>
    <div class="legend" id="legend"></div>
    <div class="tab-head">谱系总图 <small>拖拽平移 · 滚轮缩放 · 点击人物弹卡</small></div>
    <div class="graph-shell">
      <div class="toolbar">
        <button class="btn" id="reset">总览</button>
        <label style="font-size:13px;color:var(--ink-soft)">聚焦学派：</label>
        <select class="btn" id="focusSel"></select>
        <span class="hint">实线带箭头=师生相传 · 绿虚线=同门</span>
      </div>
      <svg id="graph" xmlns="http://www.w3.org/2000/svg"></svg>
      <div class="gcap">读图法：每列为一个学案，列内上行为师、下行为徒（依代序排列）；跨列细线为学派间师承；绿色虚线为同门（同辈切磋，非师承）。点击任意人名，自动弹出人物卡片。</div>
    </div>
  </section>

  <!-- ===== 人物总录 ===== -->
  <section class="tab" id="sec-roster">
    <div class="tab-head">人物总录 <small>按学派编次 · 每派首列「师承世系」（家谱），再列人物名片</small></div>
    <div id="roster"></div>
  </section>

  <!-- ===== 时间线 ===== -->
  <section class="tab" id="sec-time">
    <div class="tab-head">明代年号时间线 <small>洪武 1368 — 崇祯 1644 · 人物按其活动年代落位</small></div>
    <div class="tline-shell">
      <div class="tline-toolbar">
        <span class="hint" style="margin-left:0">按皇帝筛选：</span>
        <select class="btn" id="empSel"></select>
        <button class="btn" id="empReset">清除筛选</button>
        <span class="hint">点时间条=该帝在位 · 点人物条=弹卡 · 实心=史载生卒，虚化=依师承推算</span>
      </div>
      <div class="tline-wrap"><svg id="tline" xmlns="http://www.w3.org/2000/svg" height="640"></svg></div>
      <div class="tline-cap">读图法：顶部十七段为明代诸帝年号；以下十六行为十六学案，行内彩条为该派人物在世活动的年代区间。点击任意彩条弹人物卡片；上方下拉框按皇帝筛选「哪个周期有哪些人物」。</div>
    </div>
    <div id="empList"></div>
  </section>

  <!-- ===== 地理分布 ===== -->
  <section class="tab" id="sec-geo">
    <div class="tab-head">籍贯地理分布 <small>明代籍贯 → 今省·市对照 · 点击人名弹卡</small></div>
    <div class="geo-sum" id="geoSum"></div>
    <div class="geogrid" id="geoGrid"></div>
    <div class="tab-head">籍贯人数柱状图 <small>按今省统计 · 横条长度即人数 · 点击横条可筛选</small></div>
    <div class="geobars" id="geoBars"></div>
    <div class="tab-head">明地 → 今地 对照表 <small>用于籍贯换算</small></div>
    <div class="graph-shell" style="padding:14px">
      <details><summary class="btn" style="list-style:none;cursor:pointer">展开对照表（明人籍贯称谓 → 今省市区）</summary>
      <div style="margin-top:10px;overflow:auto"><table class="map-tbl" id="mapTbl"></table></div></details>
    </div>
  </section>

  <!-- ===== 知识图谱（力导向） ===== -->
  <section class="tab on" id="sec-kg">
    <div class="tab-head">知识图谱 <small>散落态 · 点击人物即聚合其师承关系 · 可拖拽</small></div>
    <div class="kg-shell">
      <div class="kg-toolbar">
        <span class="hint" style="margin-left:0" id="kgHint">点击任意人物：与之有关的师/弟子/同门将聚合到中心，其余淡出外围</span>
        <button class="btn" id="kgReset" style="margin-left:auto">散开</button>
      </div>
      <svg id="kg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 700" preserveAspectRatio="xMidYMid meet"></svg>
    </div>
  </section>
  <!-- ===== 学案原文 ===== -->
  <section class="tab" id="sec-book">
    <div class="tab-head">明儒学案 · 六十二卷全文 <small>左目录 · 右阅读 · 全文向量检索 · 点击人物名弹卡</small></div>
    <div class="searchbar">
      <input id="q" type="text" placeholder="检索全文（本地向量索引：字符二元组 TF-IDF）"/>
      <button class="btn" id="qBtn">检索</button>
      <button class="btn" id="qClear">清空</button>
      {{PULLBAR_HTML}}
    </div>
    <div id="sres"></div>
    <div class="book-shell">
      <div class="toc-pane" id="tocPane">
        <div class="toc-cap">目录 · 六十二卷（含附案）</div>
      </div>
      <div class="reader" id="reader">
        <div class="reader-status" id="rstatus">点击左侧卷次，从维基文库实时取回原文（首次需联网，取回后自动缓存于本机浏览器，可离线再读）。</div>
      </div>
    </div>
  </section>

  <footer>明儒学案 · 师承谱系图与全文 ｜ 据原 drawio 图谱与维基文库（zh.wikisource.org）整理 ｜ 三种纸墨风格可切换</footer>
</div>

<div class="pc" id="pc"><button class="pc-x" id="pcX">✕</button><div id="pcBody"></div></div>

<script>
/* ================= 数据 ================= */
const DATA = /*DATA*/;
const P = DATA.people, SCHOOLS = DATA.schools, MEM = DATA.school_members, EDGES = DATA.edges, TONGMEN = DATA.tongmen || [], COLORS = DATA.colors, FOUNDERS = DATA.founders||{};
const TIME = /*TIME*/;
const GEO = /*GEO*/;
const TOC = /*TOC*/;
const BOOKS = /*BOOKS*/;
const dname=(it)=>it[4]||it[1];
const NAME2ID = {}; for(const id in P) NAME2ID[P[id].name] = id;
const FOUNDER_IDS = new Set();
for(const sch in FOUNDERS) FOUNDERS[sch].forEach(n=>{ if(NAME2ID[n]) FOUNDER_IDS.add(NAME2ID[n]); });
// 王门六派为阳明弟子分流，其顶部人物为「代表」而非祖师
const REPR_SCHOOLS = new Set(["浙中王门学案","江右王门学案","南中王门学案","楚中王门学案","北方王门学案","粤闽王门学案"]);
function roleTag(id){ return REPR_SCHOOLS.has(P[id]&&P[id].school) ? "代表" : "祖"; }
function roleBadge(id){ return REPR_SCHOOLS.has(P[id]&&P[id].school) ? "代表" : "创始人"; }
const SVGNS = "http://www.w3.org/2000/svg";

/* ================= 主题 ================= */
const THEMES=[["zen","朱印"],["ink","水墨"],["white","纯白"]];
const themeSw=document.getElementById("themeSw");
THEMES.forEach(([t,label])=>{
  const b=document.createElement("button"); b.dataset.t=t; b.textContent=label;
  b.addEventListener("click",()=>applyTheme(t));
  themeSw.appendChild(b);
});
function applyTheme(t){
  document.documentElement.dataset.theme=t;
  try{ localStorage.setItem("mx_theme",t); }catch(e){}
  themeSw.querySelectorAll("button").forEach(x=>x.classList.toggle("on",x.dataset.t===t));
  paintMarkers();
}
applyTheme((function(){
  const q=new URLSearchParams(location.search).get("theme");
  if(q && ["zen","ink","white"].includes(q)) return q;
  try{ return localStorage.getItem("mx_theme")||"zen"; }catch(e){ return "zen"; }
})());

/* ================= 页签 ================= */
const TABS=["graph","roster","time","geo","kg","book"];
const SEC={}; TABS.forEach(t=>SEC[t]=document.getElementById("sec-"+t));
document.getElementById("tabs").addEventListener("click",e=>{
  const b=e.target.closest("button[data-t]"); if(!b) return;
  switchTab(b.dataset.t);
});
function switchTab(t){
  TABS.forEach(x=>{
    SEC[x].classList.toggle("on",x===t);
    document.querySelector('#tabs button[data-t="'+x+'"]').classList.toggle("on",x===t);
  });
  if(t==="graph"){ setTimeout(fitReadable,60); }
  if(t==="kg"){ setTimeout(kgStart,60); } else { kgStop(); }
  hideCard();
}

/* ================= 谱系总图 ================= */
const depthMemo = {};
function depth(id, seen){
  if(depthMemo[id]!==undefined) return depthMemo[id];
  if(seen && seen.has(id)) return 0;
  const ts = P[id].teachers||[];
  if(!ts.length){ depthMemo[id]=0; return 0; }
  seen = seen||new Set();
  seen.add(id);
  let d=0; for(const t of ts){ if(P[t]) d=Math.max(d, depth(t,seen)+1); }
  depthMemo[id]=d; return d;
}
const COL_W = 168, ROW_H = 40, TOP = 46, LEFT = 74;
const pos = {};
SCHOOLS.forEach((sch, ci)=>{
  // 列内人物已由 book_order.py 按《明儒学案》书写顺序排好，此处保持稳定序
  const ids = (MEM[sch]||[]).slice();
  ids.forEach((id, ri)=>{ pos[id] = { x: LEFT + ci*COL_W + COL_W/2, y: TOP + ri*ROW_H, col: ci }; });
});
const svg = document.getElementById("graph");
const defs = document.createElementNS(SVGNS,"defs");
defs.innerHTML = `<marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5"
    markerUnits="strokeWidth" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
  <path d="M0,1 L9,5 L0,9 z" fill="#B9AE97"/></marker>
  <marker id="arrow-hl" viewBox="0 0 10 10" refX="8" refY="5"
    markerUnits="strokeWidth" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
  <path d="M0,1 L9,5 L0,9 z" fill="#A23B2E"/></marker>`;
svg.appendChild(defs);
const vp = document.createElementNS(SVGNS,"g"); vp.setAttribute("id","viewport");
svg.appendChild(vp);
const edgeLayer = document.createElementNS(SVGNS,"g");
const nodeLayer = document.createElementNS(SVGNS,"g");
vp.appendChild(edgeLayer); vp.appendChild(nodeLayer);
function paintMarkers(){
  const cs=getComputedStyle(document.documentElement);
  const e=cs.getPropertyValue("--edge").trim(), h=cs.getPropertyValue("--edge-hl").trim();
  const a=document.getElementById("arrow"), b=document.getElementById("arrow-hl");
  if(a&&a.firstElementChild) a.firstElementChild.setAttribute("fill",e);
  if(b&&b.firstElementChild) b.firstElementChild.setAttribute("fill",h);
}
SCHOOLS.forEach((sch, ci)=>{
  const cx = LEFT + ci*COL_W + COL_W/2;
  const t=document.createElementNS(SVGNS,"text");
  t.setAttribute("x",cx); t.setAttribute("y",26);
  t.setAttribute("text-anchor","middle");
  t.setAttribute("class","col-head");
  t.setAttribute("fill",COLORS[sch]||"#888");
  t.textContent=sch;
  const u=document.createElementNS(SVGNS,"line");
  u.setAttribute("x1",cx-44); u.setAttribute("x2",cx+44);
  u.setAttribute("y1",32); u.setAttribute("y2",32);
  u.setAttribute("stroke",COLORS[sch]||"#888");
  u.setAttribute("stroke-width","1"); u.setAttribute("opacity",".6");
  nodeLayer.parentNode.insertBefore(t, nodeLayer);
  nodeLayer.parentNode.insertBefore(u, nodeLayer);
});
const edgeEls = [];
EDGES.forEach(([t,s])=>{
  if(!pos[t]||!pos[s]) return;
  const a=pos[t], b=pos[s];
  const path = document.createElementNS(SVGNS,"path");
  const midY=(a.y+b.y)/2;
  path.setAttribute("d",`M${a.x},${a.y} C${a.x},${midY} ${b.x},${midY} ${b.x},${b.y}`);
  path.setAttribute("class","edge");
  edgeLayer.appendChild(path);
  edgeEls.push({el:path,t,s});
});
const tongmenEls = [];
TONGMEN.forEach(([a_id, b_id])=>{
  if(!pos[a_id]||!pos[b_id]) return;
  const a=pos[a_id], b=pos[b_id];
  const path = document.createElementNS(SVGNS,"path");
  const midY=(a.y+b.y)/2;
  path.setAttribute("d",`M${a.x},${a.y} C${a.x},${midY} ${b.x},${midY} ${b.x},${b.y}`);
  path.setAttribute("class","tongmen");
  edgeLayer.appendChild(path);
  tongmenEls.push({el:path,a:a_id,b:b_id});
});
const nodeEls = {};
Object.keys(pos).forEach(id=>{
  const p=P[id], c=pos[id];
  const g=document.createElementNS(SVGNS,"g"); g.setAttribute("class","node"); g.setAttribute("data-id",id);
  if(FOUNDER_IDS.has(id)) g.classList.add("founder");
  if(!p.teachers||!p.teachers.length) g.classList.add("root");
  const circ=document.createElementNS(SVGNS,"circle");
  const r = FOUNDER_IDS.has(id)?7.5:5.5;
  circ.setAttribute("cx",c.x); circ.setAttribute("cy",c.y); circ.setAttribute("r",r);
  circ.setAttribute("fill",COLORS[p.school]||"#888");
  g.appendChild(circ);
  const txt=document.createElementNS(SVGNS,"text");
  txt.setAttribute("x",c.x+10); txt.setAttribute("y",c.y+4);
  txt.textContent=p.name;
  g.appendChild(txt);
  if(FOUNDER_IDS.has(id)){
    const tag=document.createElementNS(SVGNS,"text");
    tag.setAttribute("class","ftag");
    tag.setAttribute("x",c.x); tag.setAttribute("y",c.y-12);
    tag.setAttribute("text-anchor","middle");
    tag.textContent=roleTag(id);
    g.appendChild(tag);
  }
  g.addEventListener("click",(e)=>{e.stopPropagation(); selectNode(id); showCard(id, g);});
  nodeLayer.appendChild(g);
  nodeEls[id]=g;
});
let scale=1, tx=0, ty=0;
function applyT(){ vp.setAttribute("transform",`translate(${tx},${ty}) scale(${scale})`); }
function bboxOf(ids){
  let minX=1e9,minY=1e9,maxX=-1e9,maxY=-1e9;
  ids.forEach(id=>{const p=pos[id];minX=Math.min(minX,p.x-20);minY=Math.min(minY,p.y-20);
    maxX=Math.max(maxX,p.x+90);maxY=Math.max(maxY,p.y+30);});
  return [minX,minY,maxX,maxY];
}
function fitBox([minX,minY,maxX,maxY], minS, maxS){
  const w=svg.clientWidth, h=svg.clientHeight, sw=maxX-minX, sh=maxY-minY;
  if(!sw||!sh||!w) return;
  const fit=Math.min(w/sw, h/sh);
  scale=Math.max(minS||0, Math.min(maxS||4, fit));
  tx=(w-sw*scale)/2 - minX*scale;
  ty=(h-sh*scale)/2 - minY*scale;
  applyT();
}
function fitAll(){ const bb=bboxOf(Object.keys(pos)); fitBox(bb, 0.2, 1.1); }
function fitReadable(){ const big=[...MEM["姚江学案"]||[], ...MEM["江右王门学案"]||[], ...MEM["泰州学案"]||[], ...MEM["浙中王门学案"]||[]]; fitBox(bboxOf(big), 1, 1.4); }
let dragging=false, sx=0, sy=0, stx=0, sty=0, moved=false;
svg.addEventListener("pointerdown",(e)=>{dragging=true;moved=false;sx=e.clientX;sy=e.clientY;stx=tx;sty=ty;
  svg.classList.add("grabbing"); svg.setPointerCapture(e.pointerId);});
svg.addEventListener("pointermove",(e)=>{ if(!dragging)return; if(Math.abs(e.clientX-sx)>3||Math.abs(e.clientY-sy)>3)moved=true;
  tx=stx+(e.clientX-sx); ty=sty+(e.clientY-sy); applyT();});
svg.addEventListener("pointerup",(e)=>{dragging=false;svg.classList.remove("grabbing");});
svg.addEventListener("pointerleave",()=>{dragging=false;svg.classList.remove("grabbing");});
svg.addEventListener("click",()=>{ if(moved)return; clearHL(); hideCard(); });
svg.addEventListener("wheel",(e)=>{e.preventDefault();
  const r=svg.getBoundingClientRect();
  const mx=e.clientX-r.left, my=e.clientY-r.top;
  const factor=e.deltaY<0?1.12:1/1.12;
  const ns=Math.max(0.2,Math.min(4,scale*factor));
  tx=mx-(mx-tx)*(ns/scale); ty=my-(my-ty)*(ns/scale);
  scale=ns; applyT();
},{passive:false});
let curHL=null;
function ancestors(id,set){ (P[id].teachers||[]).forEach(t=>{ if(P[t]&&!set.has(t)){set.add(t);ancestors(t,set);} }); }
function descendants(id,set){ (P[id].students||[]).forEach(s=>{ if(P[s]&&!set.has(s)){set.add(s);descendants(s,set);} }); }
function selectNode(id){
  const keep=new Set([id]); ancestors(id,keep); descendants(id,keep);
  Object.values(nodeEls).forEach(g=>g.classList.add("dim"));
  Object.values(nodeEls).forEach(g=>g.classList.remove("hl"));
  edgeEls.forEach(o=>o.el.classList.remove("hl"));
  keep.forEach(k=>{ if(nodeEls[k]){nodeEls[k].classList.remove("dim");nodeEls[k].classList.add("hl");} });
  edgeEls.forEach(o=>{ if(keep.has(o.t)&&keep.has(o.s)) o.el.classList.add("hl"); });
  curHL=id;
}
function clearHL(){
  Object.values(nodeEls).forEach(g=>{g.classList.remove("dim","hl");});
  edgeEls.forEach(o=>o.el.classList.remove("hl"));
  curHL=null;
}

/* ================= 弹卡 ================= */
const pop=document.getElementById("pc");
const pcBody=document.getElementById("pcBody");
// 弹卡自动关闭：8 秒后收起；鼠标悬停时暂停计时
let popTimer=null;
function armPop(){ clearTimeout(popTimer); popTimer=setTimeout(hideCard, 8000); }
pop.addEventListener("pointerenter",()=>clearTimeout(popTimer));
pop.addEventListener("pointerleave",armPop);
function lifeTok(p){
  if(p.life) return "生卒 " + p.life + (p.age?("（"+p.age+"）"):"");
  if(p.age) return p.age;
  return "";
}
function nameList(ids){ if(!ids||!ids.length) return "—";
  return ids.filter(x=>P[x]).map(x=>`<a data-go="${x}">${P[x].name}</a>`).join("、"); }
function showCard(id, anchor){
  const p=P[id]; if(!p) return;
  const zi=p.zi?`字${p.zi}`:"", hao=p.hao?`号${p.hao}`:"";
  const life=lifeTok(p);
  const per=TIME.period[id];
  let periodStr="";
  if(per && per.active) periodStr = `活跃约 ${per.active[0]}–${per.active[1]}（${per.method==="史载"?"史载":"推算"}）`;
  const g=GEO.geo[id];
  let geoStr="";
  if(g && g.prov && g.prov!=="不详") geoStr = `籍贯 ${p.birth||""} → 今${g.prov}${g.city?("·"+g.city):""}${g.note?("（"+g.note+"）"):""}`;
  let meta=[zi,hao,p.birth||""].filter(Boolean).join(" ｜ ");
  let tags="";
  tags+=`<span class="tag" style="border-color:${COLORS[p.school]};color:${COLORS[p.school]}">${p.school}</span>`;
  if(p.title) tags+=`<span class="tag">${p.title}</span>`;
  if(p.role) tags+=`<span class="tag">${p.role}</span>`;
  if(FOUNDER_IDS.has(id)) tags+=`<span class="tag" style="border-color:var(--accent);color:var(--accent)">${roleBadge(id)}</span>`;
  pcBody.innerHTML=`<h3>${p.name}</h3>
    ${meta?`<div class="pc-meta">${meta}</div>`:""}
    ${life?`<div class="pc-life">${life}</div>`:""}
    ${periodStr?`<div class="pc-meta">${periodStr}</div>`:""}
    ${geoStr?`<div class="pc-meta">${geoStr}</div>`:""}
    <div class="pc-tags">${tags}</div>
    <div class="pc-rel"><b>师：</b>${nameList(p.teachers)}</div>
    <div class="pc-rel"><b>弟子：</b>${nameList(p.students)}</div>
    <div class="pc-foot"><button class="btn" id="pcFocus">在图中定位</button></div>`;
  pcBody.querySelectorAll("a[data-go]").forEach(a=>a.addEventListener("click",e=>{
    e.preventDefault(); e.stopPropagation(); selectNode(a.dataset.go); showCard(a.dataset.go, a);
  }));
  pcBody.querySelector("#pcFocus").addEventListener("click",()=>{ switchTab("graph");
    setTimeout(()=>{ focusId(id); document.querySelector(".graph-shell").scrollIntoView({behavior:"smooth",block:"center"}); },80); });
  const r = (anchor.getBoundingClientRect ? anchor.getBoundingClientRect() : {top:innerHeight/2,left:innerWidth/2,width:0,height:0});
  const pw = pop.offsetWidth, ph = pop.offsetHeight;
  let x = Math.max(10, Math.min(innerWidth - pw - 10, r.left + r.width/2 - pw/2));
  let y = r.bottom + 12;
  if(y + ph > innerHeight - 10) y = Math.max(10, r.top - ph - 12);
  pop.style.left=x+"px"; pop.style.top=y+"px";
  pop.classList.add("show");
  armPop();
  curHL=id;
}
function hideCard(){ clearTimeout(popTimer); pop.classList.remove("show"); }
document.getElementById("pcX").addEventListener("click",hideCard);
document.addEventListener("pointerdown",(e)=>{
  if(!pop.classList.contains("show")) return;
  if(pop.contains(e.target)) return;
  if(e.target.closest(".node,.pcard,.tn,.pbar,.pchip,.grow")) return;
  hideCard();
}, true);
document.addEventListener("keydown",e=>{ if(e.key==="Escape") hideCard(); });
window.addEventListener("resize",()=>{ hideCard(); if(!curHL && SEC.graph.classList.contains("on")) fitReadable(); });
function focusId(id){
  const c=pos[id]; if(!c)return;
  const w=svg.clientWidth,h=svg.clientHeight;
  scale=Math.max(scale,1.4);
  tx=w/2 - c.x*scale; ty=h/2 - c.y*scale; applyT();
}

/* ================= 图例 ================= */
const legend=document.getElementById("legend");
SCHOOLS.forEach(sch=>{
  const chip=document.createElement("span"); chip.className="chip"; chip.dataset.sch=sch;
  chip.innerHTML=`<span class="dot" style="background:${COLORS[sch]}"></span>${sch}（${MEM[sch].length}）`;
  chip.addEventListener("click",()=>focusSchool(sch));
  legend.appendChild(chip);
});
const focusSel=document.getElementById("focusSel");
focusSel.innerHTML=`<option value="">— 全部学派 —</option>`+SCHOOLS.map(s=>`<option value="${s}">${s}</option>`).join("");
focusSel.addEventListener("change",()=>{ if(focusSel.value) focusSchool(focusSel.value); else {fitAll();clearHL();} });
function focusSchool(sch){
  const ids=MEM[sch]||[];
  if(!ids.length)return;
  const bb=bboxOf(ids); fitBox(bb, 1, 1.6);
  Object.values(nodeEls).forEach(g=>g.classList.add("dim"));
  ids.forEach(id=>{if(nodeEls[id]){nodeEls[id].classList.remove("dim");nodeEls[id].classList.add("hl");}});
  edgeEls.forEach(o=>o.el.classList.remove("hl"));
  document.querySelectorAll(".chip").forEach(c=>c.classList.toggle("active",c.dataset.sch===sch));
}

/* ================= 人物总录 ================= */
const roster=document.getElementById("roster");
SCHOOLS.forEach(sch=>{
  const ids=MEM[sch]; if(!ids.length)return;
  const det=document.createElement("details"); det.className="school"; det.open=true;
  const sum=document.createElement("summary");
  sum.innerHTML=`<span class="dot" style="background:${COLORS[sch]}"></span>${sch}<span class="cnt">${ids.length} 人</span>`;
  det.appendChild(sum);
  const memSet=new Set(ids);
  const fset=new Set((FOUNDERS[sch]||[]).map(n=>NAME2ID[n]).filter(Boolean));
  const inSchoolTeacher={}; const children={};
  ids.forEach(id=>{ children[id]=[];
    const ins=(P[id].teachers||[]).filter(t=>memSet.has(t));
    inSchoolTeacher[id]= ins.length?ins[0]:null;
  });
  ids.forEach(id=>{ const pt=inSchoolTeacher[id];
    if(pt!==null && !fset.has(id)) children[pt].push(id); });
  const baseRoots=ids.filter(id=>inSchoolTeacher[id]===null);
  const roots = fset.size ? [...ids.filter(id=>fset.has(id)), ...baseRoots.filter(id=>!fset.has(id))] : baseRoots;
  function treeNode(id){
    const p=P[id];
    const ext=(P[id].teachers||[]).filter(t=>!memSet.has(t)).map(t=>P[t].name);
    const li=document.createElement("li");
    const life=lifeTok(p);
    li.innerHTML=`<span class="tn">${p.name}</span>`+(life?`<span class="te"> ${life}</span>`:"")+
      (fset.has(id)?` <span class="te ext">〔${roleTag(id)}〕</span>`:"")+
      (p.zi?`<span class="te">，字${p.zi}</span>`:"")+
      (ext.length?` <span class="te ext">（师：${ext.join("、")}）</span>`:"");
    li.querySelector(".tn").addEventListener("click",(e)=>{e.stopPropagation();selectNode(id);showCard(id,li.querySelector(".tn"));});
    const ch=children[id];
    if(ch.length){ const ul=document.createElement("ul"); ch.forEach(c=>ul.appendChild(treeNode(c))); li.appendChild(ul); }
    return li;
  }
  const treeCap=document.createElement("div"); treeCap.className="tree-cap"; treeCap.textContent="师承世系（家谱）· 上为祖师，下为弟子";
  det.appendChild(treeCap);
  const tree=document.createElement("ul"); tree.className="tree";
  roots.forEach(r=>tree.appendChild(treeNode(r)));
  det.appendChild(tree);
  const grid=document.createElement("div"); grid.className="cards";
  ids.forEach(id=>{
    const p=P[id];
    const c=document.createElement("div"); c.className="pcard";
    const zi=p.zi?`字${p.zi}`:""; const hao=p.hao?`号${p.hao}`:"";
    const life=lifeTok(p);
    const line=[life?`<span class="life">${life}</span>`:"", p.birth].filter(Boolean).join(" ｜ ");
    const fb = FOUNDER_IDS.has(id)?`<span class="fb">${roleBadge(id)}</span>`:"";
    c.innerHTML=`<div class="pn">${p.name}</div>${fb}<div class="pz">${line||"&nbsp;"}</div>
      ${p.title?`<div class="pr">${p.title}</div>`:(p.role?`<div class="pr">${p.role}</div>`:"")}`;
    c.addEventListener("click",(e)=>{e.stopPropagation();selectNode(id);showCard(id,c);});
    grid.appendChild(c);
  });
  det.appendChild(grid);
  roster.appendChild(det);
});
document.getElementById("reset").addEventListener("click",()=>{fitAll();clearHL();
  document.querySelectorAll(".chip").forEach(c=>c.classList.remove("active"));focusSel.value="";});

/* ================= 时间线 ================= */
const tline=document.getElementById("tline");
const Y0=1368, Y1=1644, PX=9; // px per year
const tlW = (Y1-Y0)*PX;
const EMPERORS=TIME.emperors;
function tlx(y){ return 90 + (y-Y0)*PX; }
(function buildTimeline(){
  let g=document.createElementNS(SVGNS,"g");
  // emperor bands
  const bh=64, btop=10;
  EMPERORS.forEach((em,i)=>{
    const x0=tlx(em.start), x1=tlx(em.end);
    const r=document.createElementNS(SVGNS,"rect");
    r.setAttribute("x",x0); r.setAttribute("y",btop); r.setAttribute("width",Math.max(2,x1-x0)); r.setAttribute("height",bh);
    r.setAttribute("fill", i%2? "rgba(120,100,60,.10)" : "rgba(120,100,60,.20)");
    r.setAttribute("class","tbar"); r.setAttribute("data-em",em.era);
    const title=document.createElementNS(SVGNS,"title");
    title.textContent=`${em.n}代 ${em.era}帝（${em.name}） 在位 ${em.start}–${em.end}`;
    r.appendChild(title);
    r.addEventListener("click",()=>filterEmperor(em.era));
    g.appendChild(r);
    const t=document.createElementNS(SVGNS,"text");
    t.setAttribute("x",(x0+x1)/2); t.setAttribute("y",btop+18); t.setAttribute("text-anchor","middle");
    t.textContent=em.era; g.appendChild(t);
    const t2=document.createElementNS(SVGNS,"text");
    t2.setAttribute("x",(x0+x1)/2); t2.setAttribute("y",btop+34); t2.setAttribute("text-anchor","middle");
    t2.textContent=em.start+"–"+em.end; t2.setAttribute("font-size","9.5"); t2.setAttribute("fill","var(--ink-soft)");
    g.appendChild(t2);
  });
  // year gridlines
  for(let y=1370; y<=1640; y+=10){
    const x=tlx(y);
    const l=document.createElementNS(SVGNS,"line");
    l.setAttribute("x1",x); l.setAttribute("x2",x); l.setAttribute("y1",btop); l.setAttribute("y2",btop+bh);
    l.setAttribute("stroke","var(--line)"); l.setAttribute("opacity",".4");
    g.appendChild(l);
    const t=document.createElementNS(SVGNS,"text");
    t.setAttribute("x",x); t.setAttribute("y",btop+bh+12); t.setAttribute("text-anchor","middle");
    t.setAttribute("font-size","9"); t.setAttribute("fill","var(--ink-soft)");
    t.textContent=y; g.appendChild(t);
  }
  // school rows + person bars
  const rowH=30, rowTop=btop+bh+16;
  let py=rowTop;
  const barEls={};
  SCHOOLS.forEach(sch=>{
    const lab=document.createElementNS(SVGNS,"text");
    lab.setAttribute("x",6); lab.setAttribute("y",py+16); lab.setAttribute("class","trow");
    lab.textContent=sch;
    g.appendChild(lab);
    const ids=MEM[sch]||[];
    ids.forEach(id=>{
      const per=TIME.period[id];
      if(!per||!per.active) return;
      const [s,e]=per.active;
      const x0=tlx(s), x1=tlx(e);
      const g2=document.createElementNS(SVGNS,"g");
      g2.setAttribute("class","pbar"); g2.setAttribute("data-id",id);
      const r=document.createElementNS(SVGNS,"rect");
      r.setAttribute("x",x0); r.setAttribute("y",py+5); r.setAttribute("width",Math.max(3,x1-x0));
      const h = FOUNDER_IDS.has(id)?15:10;
      r.setAttribute("height",h);
      r.setAttribute("fill",COLORS[sch]);
      r.setAttribute("opacity", per.method==="史载"?"0.92":"0.45");
      if(FOUNDER_IDS.has(id)) r.setAttribute("stroke","var(--accent)");
      const title=document.createElementNS(SVGNS,"title");
      title.textContent=`${P[id].name}（${per.birth}–${per.death}，${per.method}） · ${sch}`;
      r.appendChild(title);
      g2.appendChild(r);
      if(FOUNDER_IDS.has(id)){
        const ft=document.createElementNS(SVGNS,"text");
        ft.setAttribute("x",x0+3); ft.setAttribute("y",py+9); ft.setAttribute("font-size","9");
        ft.setAttribute("fill","#fff");
        ft.textContent=roleTag(id);
        g2.appendChild(ft);
      }
      g2.addEventListener("click",(e)=>{e.stopPropagation(); selectNode(id); showCard(id, r);});
      g.appendChild(g2);
      barEls[id]=g2;
    });
    py+=rowH;
  });
  tline.setAttribute("width", tlW+120);
  tline.setAttribute("height", py+30);
  tline.appendChild(g);
  window.__barEls=barEls;
})();
// emperor filter
const empSel=document.getElementById("empSel");
empSel.innerHTML=`<option value="">— 全部 —</option>`+EMPERORS.map(e=>`<option value="${e.era}">${e.n}代 ${e.era}（${e.start}–${e.end}）</option>`).join("");
const empList=document.getElementById("empList");
function inReign(active, em){ return active && active[0] <= em.end && active[1] >= em.start; }
function filterEmperor(era){
  empSel.value=era;
  const em=EMPERORS.find(e=>e.era===era);
  document.querySelectorAll("#tline .tbar").forEach(r=>r.classList.remove("dim"));
  document.querySelectorAll("#tline .tbar[data-em]").forEach(r=>{ if(r.getAttribute("data-em")!==era) r.classList.add("dim"); });
  const bars=window.__barEls||{};
  Object.values(bars).forEach(b=>b.classList.add("dim"));
  const groups={};
  SCHOOLS.forEach(sch=>groups[sch]=[]);
  Object.keys(bars).forEach(id=>{
    const per=TIME.period[id];
    if(per && inReign(per.active, em)){ bars[id].classList.remove("dim"); if(P[id]) groups[P[id].school].push(id); }
  });
  empList.innerHTML="";
  const head=document.createElement("div"); head.className="tab-head";
  head.textContent=`${em.era}帝在位（${em.start}–${em.end}）时活跃的人物`;
  empList.appendChild(head);
  let n=0;
  SCHOOLS.forEach(sch=>{
    const ids=groups[sch]; if(!ids.length) return;
    const grp=document.createElement("div"); grp.className="empgroup";
    grp.innerHTML=`<h4><span class="dot" style="display:inline-block;width:11px;height:11px;border-radius:50%;background:${COLORS[sch]}"></span> ${sch}（${ids.length}）</h4>`;
    const chips=document.createElement("div"); chips.className="chips";
    ids.forEach(id=>{
      const per=TIME.period[id];
      const c=document.createElement("span"); c.className="pchip";
      c.innerHTML=`${P[id].name}${per.birth?`<span class="lif">${per.birth}–${per.death}</span>`:""}`;
      c.addEventListener("click",()=>{ selectNode(id); showCard(id,c); });
      chips.appendChild(c); n++;
    });
    grp.appendChild(chips);
    empList.appendChild(grp);
  });
  if(!n){ const d=document.createElement("div"); d.className="empgroup"; d.innerHTML="<h4>（该时期暂无已考年代的人物）</h4>"; empList.appendChild(d); }
}
empSel.addEventListener("change",()=>{ if(empSel.value) filterEmperor(empSel.value); else empReset(); });
document.getElementById("empReset").addEventListener("click",empReset);
function empReset(){
  empSel.value="";
  document.querySelectorAll("#tline .tbar").forEach(r=>r.classList.remove("dim"));
  Object.values(window.__barEls||{}).forEach(b=>b.classList.remove("dim"));
  empList.innerHTML="";
}

/* ================= 地理分布 ================= */
(function buildGeo(){
  const byProv={};
  Object.keys(P).forEach(id=>{
    const g=GEO.geo[id]; if(!g||!g.prov||g.prov==="不详") return;
    (byProv[g.prov]=byProv[g.prov]||[]).push(id);
  });
  const provs=Object.keys(byProv).sort((a,b)=>byProv[b].length-byProv[a].length);
  const sum=document.getElementById("geoSum");
  provs.forEach(pr=>{
    const c=document.createElement("span"); c.className="gchip"; c.dataset.pr=pr;
    c.innerHTML=`${pr}<span style="color:var(--ink-soft)">${byProv[pr].length}</span>`;
    c.addEventListener("click",()=>{
      document.querySelectorAll(".gchip").forEach(x=>x.classList.toggle("on",x.dataset.pr===pr));
      const gdiv=document.getElementById("geoGrid");
      [...gdiv.children].forEach(ch=>{
        const ok = ch.dataset.pr===pr;
        ch.style.display = pr? (ok?"":"none") : "";
      });
    });
    sum.appendChild(c);
  });
  const grid=document.getElementById("geoGrid");
  provs.forEach(pr=>{
    const box=document.createElement("div"); box.className="gprov"; box.dataset.pr=pr;
    const ids=byProv[pr].sort((a,b)=>(P[a].name||"").localeCompare(P[b].name||"","zh"));
    box.innerHTML=`<h4>${pr}<span class="cnt">${ids.length} 人</span></h4>`;
    const gl=document.createElement("div"); gl.className="glist";
    ids.forEach(id=>{
      const g=GEO.geo[id], p=P[id];
      const row=document.createElement("div"); row.className="grow";
      const place=g.city? (g.note? `${g.city}·${g.note}` : g.city) : (g.note||"");
      row.innerHTML=`<span class="gn">${p.name}</span><span class="gx">${p.birth||""}${place?` → <em>${place}</em>`:""}</span>`;
      row.addEventListener("click",()=>{ selectNode(id); showCard(id,row); });
      gl.appendChild(row);
    });
    box.appendChild(gl);
    grid.appendChild(box);
  });
  // 柱状图（横条=人数，点击横条与 chips 同款筛选）
  const bars=document.getElementById("geoBars");
  const max=provs.length?byProv[provs[0]].length:1;
  provs.forEach(pr=>{
    const row=document.createElement("div"); row.className="geobar";
    row.innerHTML=`<span class="gb-name">${pr}</span><div class="gb-track"><span class="gb-fill"></span></div><span class="gb-num">${byProv[pr].length} 人</span>`;
    row.querySelector(".gb-fill").style.width=(byProv[pr].length/max*100).toFixed(1)+"%";
    row.addEventListener("click",()=>{
      document.querySelectorAll(".gchip").forEach(x=>x.classList.toggle("on",x.dataset.pr===pr));
      [...grid.children].forEach(ch=>{ ch.style.display = ch.dataset.pr===pr ? "" : "none"; });
    });
    bars.appendChild(row);
  });
  // mapping table
  const tbl=document.getElementById("mapTbl");
  tbl.innerHTML=`<tr><th>明代籍贯称谓</th><th>今省</th><th>今市（县）</th><th>备注</th></tr>`;
  Object.keys(GEO.birth_map).sort().forEach(k=>{
    const v=GEO.birth_map[k];
    tbl.innerHTML+=`<tr><td>${k}</td><td>${v.prov}</td><td>${v.city}</td><td>${v.note||""}</td></tr>`;
  });
})();

/* ================= 学案原文（62卷） ================= */
const tocPane=document.getElementById("tocPane");
const reader=document.getElementById("reader");
const rstatus=document.getElementById("rstatus");
const API="https://zh.wikisource.org/w/api.php?action=query&prop=revisions&rvprop=content&rvslots=main&format=json&formatversion=2&origin=*&titles=";
// 目录
TOC.forEach(item=>{
  const d=document.createElement("div"); d.className="toc-item"; d.dataset.v=item[0];
  d.innerHTML=`<span class="tv">卷${["","一二三四五六七八九","十","十一","十二","十三","十四","十五","十六","十七","十八","十九","二十","廿一","廿二","廿三","廿四","廿五","廿六","廿七","廿八","廿九","三十","卅一","卅二","卅三","卅四","卅五","卅六","卅七","卅八","卅九","四十","四一","四二","四三","四四","四五","四六","四七","四八","四九","五十","五一","五二","五三","五四","五五","五六","五七","五八","五九","六十","六一","六二"][item[0]]||item[0]}</span>
    <div><div class="tn2">${dname(item)}</div><div class="tp">${item[3]}</div></div>`;
  d.addEventListener("click",()=>loadVolume(item[0]));
  tocPane.appendChild(d);
});
let curVol=null;
function esc(s){ return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
function wt2html(src){
  // strip html comments
  src=src.replace(/<!--[\s\S]*?-->/g,"");
  // strip refs
  src=src.replace(/<ref[\s\S]*?<\/ref>/g,"").replace(/<ref[^>]*\/\s*>/g,"");
  // strip tables {| ... |}
  src=src.replace(/\{\|[\s\S]*?\|\}/g,"");
  // strip templates (nested, up to 8 passes)
  for(let i=0;i<8;i++){ const n=src.replace(/\{\{[^{}]*\}\}/g,""); if(n===src) break; src=n; }
  // strip files / categories
  src=src.replace(/\[\[(File|Image|文件|图像|Category|分类|作者|Author):[\s\S]*?\]\]/gi,"");
  // links
  src=src.replace(/\[\[([^\[\]|]*)\|([^\[\]]*)\]\]/g,"$2");
  src=src.replace(/\[\[([^\[\]]*)\]\]/g,"$1");
  // headings
  src=src.replace(/^(={2,4})\s*(.*?)\s*\1\s*$/gm,"\n###H2###$2\n");
  // poem
  src=src.replace(/<poem>([\s\S]*?)<\/poem>/g,function(m,inner){ return "\n###POEM###"+inner.replace(/\n/g,"\n")+"\n###/POEM###"; });
  // escape
  src=esc(src);
  // markup
  src=src.replace(/'''''([^'']+)'''''/g,"<b><i>$1</i></b>");
  src=src.replace(/'''([^'']+)'''/g,"<b>$1</b>");
  src=src.replace(/''([^'']+)''/g,"<i>$1</i>");
  src=src.replace(/###H2###/g,'<h4>').replace(/\n/g,"</h4>\n");
  src=src.replace(/###POEM###/g,'<div class="poem">').replace(/###\/POEM###/g,'</div>');
  // paragraphs
  const lines=src.split(/\n+/).map(s=>s.trim()).filter(Boolean);
  let out="";
  lines.forEach(l=>{
    if(l.startsWith("<h4>")) { out+=l; return; }
    if(l.startsWith("<div class=\"poem\">")||l.startsWith("</div>")){ out+=l; return; }
    out+=`<p class="par">${l}</p>`;
  });
  return out;
}
function cacheKey(v){ return "mr_v_"+v; }
async function loadVolume(v){
  const item=TOC.find(x=>x[0]===v); if(!item) return;
  curVol=v;
  document.querySelectorAll(".toc-item").forEach(x=>x.classList.toggle("on",x.dataset.v==String(v)));
  // 本卷人物 chips (简体, 链接到数据)
  const people=(item[3]||"").split(/[\s、，,（）()]+/).filter(Boolean).map(n=>n.replace(/[（(].*?[)）]/g,""));
  let chipHtml="<div class='people'>";
  people.forEach(n=>{
    const id=NAME2ID[n];
    if(id){ chipHtml+=`<span class="pchip" data-go="${id}" style="color:var(--accent)">${n}</span>`; }
    else { chipHtml+=`<span class="pchip">${n}</span>`; }
  });
  chipHtml+="</div>";
  reader.innerHTML=`<div class="reader-head"><h3>卷${item[0]}　${dname(item)}</h3>${chipHtml}</div><div class="reader-status">正在取回原文…</div>`;
  reader.querySelectorAll(".pchip[data-go]").forEach(c=>c.addEventListener("click",e=>{e.stopPropagation();const id=c.dataset.go;selectNode(id);showCard(id,c);}));
  // 优先内嵌全文（离线）
  const emb = BOOKS.find(b=>b.v===v);
  if(emb && emb.text){ renderVolume(item,emb.text); addToIndex(v,emb.text); return; }
  // 其次本地缓存（运行时拉取模式）
  let text=null;
  try{ text=localStorage.getItem(cacheKey(v)); }catch(e){}
  if(text){ renderVolume(item,text); addToIndex(v,text); return; }
  const page="明儒學案/"+item[1];
  try{
    const res=await fetch(API+encodeURIComponent(page));
    const js=await res.json();
    const pg=(js.query&&js.query.pages&&js.query.pages[0])||{};
    const rev=(pg.revisions&&pg.revisions[0])||{};
    const slot=(rev.slots&&rev.slots.main)||{};
    text=slot.content||slot["*"]||"";
    if(!text) throw new Error("empty");
    try{ localStorage.setItem(cacheKey(v),text); }catch(e){}
    renderVolume(item,text); addToIndex(v,text);
  }catch(err){
    reader.innerHTML=`<div class="reader-head"><h3>卷${item[0]}　${dname(item)}</h3></div>
      <div class="reader-status">原文取回失败（需联网访问 zh.wikisource.org）。<br/>可直接在维基文库打开：<a href="https://zh.wikisource.org/wiki/${encodeURIComponent(page)}" target="_blank" style="color:var(--accent)">${page}</a><br/><span style="font-size:12px">${esc(String(err&&err.message||err))}</span></div>`;
  }
}
function renderVolume(item,text){
  const html=wt2html(text);
  reader.innerHTML=`<div class="reader-head"><h3>卷${item[0]}　${dname(item)}</h3><div class="people">${reader.querySelector(".people")?reader.querySelector(".people").outerHTML:""}</div></div>
    <div class="reader-body">${html}</div>`;
  // re-bind chips
  reader.querySelectorAll(".pchip[data-go]").forEach(c=>c.addEventListener("click",e=>{e.stopPropagation();const id=c.dataset.go;selectNode(id);showCard(id,c);}));
  rstatus.style.display="none";
}

/* ---- 本地向量索引（字符二元组 TF-IDF） ---- */
const VINDEX={ tf:{}, df:{}, n:0 }; // tf[term][vol], df[term], n volumes
function bigrams(s){
  const set=new Set(); const t=s.replace(/[\s\p{P}\p{S}]/gu,"");
  if(t.length===1){ set.add("_"+t); }
  for(let i=0;i<t.length-1;i++) set.add(t.slice(i,i+2));
  return [...set];
}
function addToIndex(v,text){
  const key="v"+v;
  if(VINDEX.tf[key]) return;
  const cnt={};
  bigrams(text).forEach(tr=>{ cnt[tr]=(cnt[tr]||0)+1; });
  VINDEX.tf[key]=cnt;
  Object.keys(cnt).forEach(tr=>{ (VINDEX.df[tr]=VINDEX.df[tr]||0); VINDEX.df[tr]++; });
  VINDEX.n++;
}
function searchVol(qbig, key){
  const cnt=VINDEX.tf[key]; if(!cnt) return 0;
  let s=0;
  qbig.forEach(tr=>{ if(cnt[tr]) s += (1+Math.log(cnt[tr]))*Math.log((VINDEX.n+1)/((VINDEX.df[tr]||0)+1)); });
  return s;
}
function doSearch(q){
  q=q.trim(); if(!q) return;
  const qbig=bigrams(q);
  const scored=[];
  TOC.forEach(item=>{ const key="v"+item[0]; if(!VINDEX.tf[key]) return;
    const s=searchVol(qbig,key); if(s>0.0001) scored.push({v:item[0],name:dname(item),score:s}); });
  scored.sort((a,b)=>b.score-a.score);
  const box=document.getElementById("sres");
  box.style.display="block";
  if(!scored.length){ box.innerHTML="<div class='sres-item'>无结果。注意：向量索引只覆盖「打开过」的卷次（已缓存），请先点开相关卷次，或点击「全部卷次入索引」。</div>";
    return; }
  box.innerHTML=scored.slice(0,12).map(r=>{
    const text=localStorage.getItem(cacheKey(r.v))||"";
    // find best paragraph
    let best="",bestSc=-1;
    (text.split(/\n+/)).forEach(par=>{ if(par.length<6) return;
      const pb=bigrams(par); let sc=0; qbig.forEach(tr=>{ if(pb.includes(tr)) sc++; });
      if(sc>bestSc){ bestSc=sc; best=par; } });
    const snip=esc(best.slice(0,90))+(best.length>90?"…":"");
    return `<div class="sres-item" data-v="${r.v}" data-p="${esc(best.slice(0,40))}">
      <div class="shead"><span class="sv">卷${r.v}</span><span class="st">${r.name}</span><span class="sc">相似度 ${r.score.toFixed(3)}</span></div>
      <div class="sp">${snip}</div></div>`;
  }).join("");
  box.querySelectorAll(".sres-item").forEach(el=>el.addEventListener("click",()=>{
    const v=+el.dataset.v; loadVolume(v).then(()=>{ setTimeout(()=>highlightHit(el.dataset.p),300); });
    box.style.display="none";
  }));
}
function highlightHit(prefix){
  const ps=[...reader.querySelectorAll(".par")];
  const el=ps.find(p=>p.textContent.replace(/^　+/,"").startsWith(prefix));
  if(el){ el.scrollIntoView({behavior:"smooth",block:"center"}); el.classList.add("hit"); setTimeout(()=>el.classList.remove("hit"),2500); }
}
document.getElementById("qBtn").addEventListener("click",()=>doSearch(document.getElementById("q").value));
document.getElementById("q").addEventListener("keydown",e=>{ if(e.key==="Enter") doSearch(e.target.value); });
document.getElementById("qClear").addEventListener("click",()=>{ document.getElementById("q").value=""; document.getElementById("sres").style.display="none"; });

/* ---- 一键全量缓存（拉取全部 63 卷 → localStorage → 全文索引就绪） ---- */
function rebuildIndexFromCache(){
  let n=0;
  TOC.forEach(item=>{
    try{ const t=localStorage.getItem(cacheKey(item[0])); if(t){ addToIndex(item[0],t); n++; } }catch(e){}
  });
  return n;
}
let pulling=false;
async function pullAll(){
  if(pulling) return;
  pulling=true;
  const btn=document.getElementById("pullAll"); btn.disabled=true;
  const st=document.getElementById("pullStatus");
  const total=TOC.length;
  let done=0, fail=0;
  try{ for(const k in localStorage){ if(k.indexOf("mr_v_")===0) done++; } }catch(e){}
  st.textContent=`正在拉取… 已有 ${done}/${total}`;
  for(const item of TOC){
    const key=cacheKey(item[0]);
    let has=false;
    try{ has=!!localStorage.getItem(key); }catch(e){}
    if(has){ done++; continue; }
    const page="明儒學案/"+item[1];
    try{
      const res=await fetch(API+encodeURIComponent(page));
      const js=await res.json();
      const pg=(js.query&&js.query.pages&&js.query.pages[0])||{};
      const rev=(pg.revisions&&pg.revisions[0])||{};
      const slot=(rev.slots&&rev.slots.main)||{};
      const text=slot.content||slot["*"]||"";
      if(text){ try{ localStorage.setItem(key,text); }catch(e){ st.textContent=`存储已满（约 5MB 上限），已缓存 ${done}/${total}`; break; } }
      done++;
    }catch(e){ fail++; done++; }
    st.textContent=`正在拉取… ${done}/${total}${fail?`（失败 ${fail}）`:""}`;
    await new Promise(r=>setTimeout(r,120));
  }
  const n=rebuildIndexFromCache();
  st.textContent=`完成：已缓存 ${n}/${total} 卷（可离线阅读；全文向量检索已就绪）。失败 ${fail} 卷可再次点击补拉。`;
  btn.disabled=false;
  pulling=false;
}
const _pa=document.getElementById("pullAll"); if(_pa) _pa.addEventListener("click",pullAll);
const _wc=document.getElementById("wipeCache"); if(_wc) _wc.addEventListener("click",()=>{
  let n=0;
  try{ const ks=[...Object.keys(localStorage)].filter(k=>k.indexOf("mr_v_")===0); ks.forEach(k=>{localStorage.removeItem(k); n++;}); }catch(e){}
  // reset index
  VINDEX.tf={}; VINDEX.df={}; VINDEX.n=0;
  document.getElementById("pullStatus").textContent=`已清除 ${n} 卷缓存（索引已重置）。`;
  if(curVol) loadVolume(curVol);
});
// 启动时：内嵌全文 → 全量建索引；否则从缓存重建
if(BOOKS && BOOKS.length){
  BOOKS.forEach(b=>{ if(b.text) addToIndex(b.v, b.text); });
}else{
  rebuildIndexFromCache();
}


/* ================= 知识图谱（力导向·点击聚合） ================= */
const KG_W=1100, KG_H=700, KG_CX=KG_W/2, KG_CY=KG_H/2;
let kgRunning=false, kgRAF=null, kgFocus=null, kgPin=null, kgDrag=null;
const kgNodes=[], kgNodeEls={}, kgLinks=[], kgFocusSet=new Set();
(function buildKG(){
  const svg=document.getElementById("kg");
  if(!svg) return;
  const defs=document.createElementNS(SVGNS,"defs");
  defs.innerHTML=`<marker id="kg-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerUnits="strokeWidth" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,1 L9,5 L0,9 z" fill="#A23B2E"/></marker>`;
  svg.appendChild(defs);
  const ids=Object.keys(P);
  ids.forEach((id,i)=>{
    const a=(i/ids.length)*Math.PI*2+Math.random()*0.2;
    const r=190+Math.random()*130;
    kgNodes.push({id,x:KG_CX+Math.cos(a)*r,y:KG_CY+Math.sin(a)*r,vx:0,vy:0,fx:0,fy:0});
  });
  EDGES.forEach(([t,s])=>kgLinks.push({a:t,b:s,type:"e",el:null}));
  TONGMEN.forEach(([a,b])=>kgLinks.push({a:a,b:b,type:"tm",el:null}));
  const elayer=document.createElementNS(SVGNS,"g");
  kgLinks.forEach(l=>{ const ln=document.createElementNS(SVGNS,"line");
    ln.setAttribute("class","kg-edge"+(l.type==="tm"?" tm":"")); elayer.appendChild(ln); l.el=ln; });
  svg.appendChild(elayer);
  const nlayer=document.createElementNS(SVGNS,"g");
  ids.forEach(id=>{
    const g=document.createElementNS(SVGNS,"g");
    g.setAttribute("class","kg-node"); g.setAttribute("data-id",id);
    const c=document.createElementNS(SVGNS,"circle");
    c.setAttribute("r",FOUNDER_IDS.has(id)?20:14);
    c.setAttribute("fill",COLORS[P[id].school]||"#888");
    if(FOUNDER_IDS.has(id)) c.setAttribute("stroke","var(--accent)");
    g.appendChild(c);
    const hit=document.createElementNS(SVGNS,"circle");
    hit.setAttribute("r",28); hit.setAttribute("fill","transparent");
    g.appendChild(hit);
    const t=document.createElementNS(SVGNS,"text");
    t.setAttribute("x",0); t.setAttribute("y",4);
    t.textContent=P[id].name;
    g.appendChild(t);
    g.addEventListener("pointerdown",(e)=>onKGDown(e,id));
    const init=kgNodes.find(x=>x.id===id);
    g.setAttribute("transform",`translate(${init.x},${init.y})`);
    nlayer.appendChild(g);
    kgNodeEls[id]=g;
  });
  svg.appendChild(nlayer);
  const reset=document.getElementById("kgReset");
  if(reset) reset.addEventListener("click",()=>{ kgFocus=null; kgPin=null; kgFocusSet.clear(); updateKGState(); });
})();
function kgStart(){ if(kgRunning) return; kgRunning=true; kgLoop(); }
function kgStop(){ kgRunning=false; if(kgRAF) cancelAnimationFrame(kgRAF); kgRAF=null; }
function kgSVGXY(e){ const svg=document.getElementById("kg"); const r=svg.getBoundingClientRect();
  return { x:(e.clientX-r.left)*KG_W/r.width, y:(e.clientY-r.top)*KG_H/r.height }; }
function onKGDown(e,id){
  e.stopPropagation();
  const p=kgSVGXY(e);
  kgDrag={id,sx:e.clientX,sy:e.clientY,moved:false,x:p.x,y:p.y};
  const svg=document.getElementById("kg");
  svg.setPointerCapture(e.pointerId);
  const move=(ev)=>{ if(!kgDrag) return;
    if(Math.abs(ev.clientX-kgDrag.sx)>4||Math.abs(ev.clientY-kgDrag.sy)>4) kgDrag.moved=true;
    const q=kgSVGXY(ev); kgDrag.x=q.x; kgDrag.y=q.y; };
  const up=(ev)=>{
    svg.removeEventListener("pointermove",move); svg.removeEventListener("pointerup",up);
    const n=kgNodes.find(x=>x.id===kgDrag.id);
    const wasClick=!kgDrag.moved;
    if(kgDrag.moved&&n){ n.x=kgDrag.x; n.y=kgDrag.y; n.vx=0; n.vy=0; }
    kgDrag=null;
    if(wasClick) kgToggle(id);
  };
  svg.addEventListener("pointermove",move);
  svg.addEventListener("pointerup",up);
}
function kgToggle(id){
  if(kgFocus===id){ kgFocus=null; kgPin=null; }
  else { kgFocus=id; const n=kgNodes.find(x=>x.id===id); kgPin={x:n.x,y:n.y};
    kgFocusSet.clear();
    kgLinks.forEach(l=>{ if(l.a===id||l.b===id){ kgFocusSet.add(l.a); kgFocusSet.add(l.b); } });
  }
  updateKGState();
  showCard(id, kgNodeEls[id]);
}
function updateKGState(){
  const hint=document.getElementById("kgHint");
  if(kgFocus) hint.textContent=`焦点：${P[kgFocus].name}（${P[kgFocus].school}）· 师承关系已聚合 · 点击其他人切换焦点，再点同点或「散开」复位`;
  else hint.textContent="点击任意人物：与之有关的师/弟子/同门将聚合到中心，其余淡出外围";
}
function kgLoop(){
  if(!kgRunning) return;
  const K_REP=5200, SPRING=0.05, REST=46, DAMP=0.82;
  const focus = kgFocus? kgNodes.find(x=>x.id===kgFocus): null;
  const n=kgNodes.length;
  for(let i=0;i<n;i++){ kgNodes[i].fx=0; kgNodes[i].fy=0; }
  for(let i=0;i<n;i++){ const a=kgNodes[i];
    for(let j=i+1;j<n;j++){ const b=kgNodes[j];
      let dx=a.x-b.x, dy=a.y-b.y;
      const d2=dx*dx+dy*dy;
      if(d2>90000) continue;
      const d=Math.sqrt(d2)||1, f=K_REP/d2;
      const fx=dx/d*f, fy=dy/d*f;
      a.fx+=fx; a.fy+=fy; b.fx-=fx; b.fy-=fy; } }
  if(focus){
    kgLinks.forEach(l=>{ if(l.type!=="e"||(l.a!==kgFocus&&l.b!==kgFocus)) return;
      const A=kgNodes.find(x=>x.id===l.a), B=kgNodes.find(x=>x.id===l.b);
      let dx=B.x-A.x, dy=B.y-A.y;
      const d=Math.sqrt(dx*dx+dy*dy)||1, f=(d-REST)*SPRING;
      const fx=dx/d*f, fy=dy/d*f;
      if(l.a!==kgFocus){ A.fx+=fx; A.fy+=fy; }
      if(l.b!==kgFocus){ B.fx-=fx; B.fy-=fy; } });
  }
  kgNodes.forEach(node=>{
    const isF=focus&&node.id===kgFocus, isR=focus&&kgFocusSet.has(node.id)&&!isF;
    let tx,ty,c;
    if(isF){ tx=kgPin?kgPin.x:KG_CX; ty=kgPin?kgPin.y:KG_CY; c=0.12; }
    else if(isR){ tx=KG_CX; ty=KG_CY; c=0.004; }
    else if(focus){ const dx=node.x-KG_CX, dy=node.y-KG_CY, d=Math.sqrt(dx*dx+dy*dy)||1;
      tx=KG_CX+dx/d*300; ty=KG_CY+dy/d*300; c=0.006; }
    else { tx=node.hx; ty=node.hy; c=0.012; }
    node.fx+=(tx-node.x)*c; node.fy+=(ty-node.y)*c;
  });
  kgNodes.forEach(node=>{
    if(kgDrag&&kgDrag.id===node.id){ node.x=kgDrag.x; node.y=kgDrag.y; node.vx=0; node.vy=0; return; }
    node.vx=(node.vx+node.fx)*DAMP; node.vy=(node.vy+node.fy)*DAMP;
    node.x+=node.vx; node.y+=node.vy;
    if(node.x<30) node.x=30; if(node.x>KG_W-30) node.x=KG_W-30;
    if(node.y<30) node.y=30; if(node.y>KG_H-30) node.y=KG_H-30;
  });
  kgLinks.forEach(l=>{
    const A=kgNodes.find(x=>x.id===l.a), B=kgNodes.find(x=>x.id===l.b);
    const on=!!focus&&(l.a===kgFocus||l.b===kgFocus);
    l.el.setAttribute("x1",A.x); l.el.setAttribute("y1",A.y);
    l.el.setAttribute("x2",B.x); l.el.setAttribute("y2",B.y);
    l.el.classList.toggle("on",on);
    l.el.setAttribute("opacity", focus?(on?0.95:0.04):(l.type==="tm"?0.55:0.28));
  });
  Object.keys(kgNodeEls).forEach(id=>{
    const g=kgNodeEls[id], node=kgNodes.find(x=>x.id===id);
    g.setAttribute("transform",`translate(${node.x},${node.y})`);
    const dim=!!focus&&!kgFocusSet.has(id);
    g.classList.toggle("dim",dim);
    g.classList.toggle("kg-focus", focus&&id===kgFocus);
    const t=g.querySelector("text");
    const showLbl=!!focus?(id===kgFocus||kgFocusSet.has(id)):FOUNDER_IDS.has(id);
    if(t) t.style.opacity=showLbl?"1":"0";
  });
  kgRAF=requestAnimationFrame(kgLoop);
}

/* ================= 启动 ================= */
fitReadable();
const _hb=location.hash.replace(/^#/,"");
if(["graph","roster","time","geo","kg","book"].includes(_hb)){ switchTab(_hb); }
if(_hb==="all"){ fitAll(); }
if(_hb.indexOf("v")===0){ const v=+_hb.slice(1); if(v){ switchTab("book"); loadVolume(v); } }
if(_hb.indexOf("kgf")===0){ const nm=decodeURIComponent(_hb.slice(3)); if(NAME2ID[nm]){ switchTab("kg"); setTimeout(()=>kgToggle(NAME2ID[nm]),80); } }
</script>
</body>
</html>
"""

for ph, val in [("/*DATA*/", DATA_JS), ("/*TIME*/", TIME_JS), ("/*GEO*/", GEO_JS), ("/*TOC*/", TOC_JS), ("/*BOOKS*/", BOOKS_JS), ("{{PULLBAR_HTML}}", PULLBAR_HTML)]:
    HTML = HTML.replace(ph, val)
out = os.path.join(BASE, "明儒学案.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)
print("Wrote", out, "size", len(HTML), "bytes")
