#!/usr/bin/env node
// 批量取回《明儒學案》63 卷全文 → resources/volumes/all.json
// 走 Node 原生 fetch；限速 1.8s/卷；429 时尊重 Retry-After；每卷成功即落盘（断点续传）
const fs = require("fs");
const path = require("path");
const BASE = path.join(__dirname);
const API = "https://zh.wikisource.org/w/api.php?action=query&prop=revisions&rvprop=content&rvslots=main&format=json&formatversion=2&origin=*&titles=";
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
const OUT = path.join(BASE, "resources", "volumes", "all.json");

const toc = JSON.parse(fs.readFileSync(path.join(BASE, "resources", "toc.json"), "utf-8"));
let books = [];
if (fs.existsSync(OUT)) books = JSON.parse(fs.readFileSync(OUT, "utf-8"));

async function fetchVol(page) {
  const url = API + encodeURIComponent("明儒學案/" + page);
  const res = await fetch(url, { headers: { "User-Agent": "Mozilla/5.0 (batch extractor; educational)" } });
  if (res.status === 429) {
    const ra = parseInt((res.headers.get("retry-after") || "30"), 10);
    const wait = Math.min(90, Math.max(ra, 10));
    console.log("    429 -> 等待 " + wait + "s");
    await sleep(wait * 1000);
    throw new Error("429");
  }
  if (!res.ok) throw new Error("HTTP " + res.status);
  const j = await res.json();
  const pg = (j.query && j.query.pages && j.query.pages[0]) || {};
  const rev = (pg.revisions && pg.revisions[0]) || {};
  const slot = (rev.slots && rev.slots.main) || {};
  return (slot.content || slot["*"] || "").trim();
}

function save() {
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(books, null, 0), "utf-8");
}

(async () => {
  const t0 = Date.now();
  let done0 = 0, ok = 0;
  for (const item of toc) {
    let rec = books.find(b => b.v === item.v);
    if (!rec) { rec = { v: item.v, name: item.name, pt: item.pt, ps: item.ps, text: "" }; books.push(rec); }
    if (rec.text) { done0++; continue; }
    let attempts = 0;
    while (!rec.text && attempts < 8) {
      attempts++;
      try { rec.text = await fetchVol(item.name); }
      catch (e) {
        if (e.message !== "429") console.log("  fail 卷" + item.v + ": " + e.message);
        if (attempts >= 8) console.log("  giveup 卷" + item.v);
      }
      if (!rec.text) await sleep(1800);
    }
    if (rec.text) ok++;
    save();
    const el = ((Date.now() - t0) / 1000).toFixed(0);
    process.stdout.write("\r" + (done0 + ok) + "/" + toc.length + "  ok=" + ok + "  elapsed=" + el + "s");
    await sleep(1800);
  }
  const chars = books.reduce((s, b) => s + b.text.length, 0);
  const empty = books.filter(b => !b.text);
  console.log("\n完成: 总 " + books.length + " / 成功 " + (books.length - empty.length) +
              " / 剩余 " + empty.map(b => "卷" + b.v).join(",") + " / 字符 " + chars +
              " / " + ((Date.now() - t0) / 1000).toFixed(0) + "s");
})().catch(e => { console.error("FATAL", e); process.exit(1); });
