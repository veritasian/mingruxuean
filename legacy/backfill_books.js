#!/usr/bin/env node
// 补拉失败的卷次：反复重试直到无空文本（间隔 500ms）
const fs = require("fs");
const path = require("path");
const BASE = path.join(__dirname);
const API = "https://zh.wikisource.org/w/api.php?action=query&prop=revisions&rvprop=content&rvslots=main&format=json&formatversion=2&origin=*&titles=";
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

const allPath = path.join(BASE, "resources", "volumes", "all.json");
const books = JSON.parse(fs.readFileSync(allPath, "utf-8"));

async function fetchVol(page) {
  const url = API + encodeURIComponent("明儒學案/" + page);
  const res = await fetch(url, { headers: { "User-Agent": "Mozilla/5.0" } });
  if (!res.ok) throw new Error("HTTP " + res.status);
  const j = await res.json();
  const pg = (j.query && j.query.pages && j.query.pages[0]) || {};
  const rev = (pg.revisions && pg.revisions[0]) || {};
  const slot = (rev.slots && rev.slots.main) || {};
  return (slot.content || slot["*"] || "").trim();
}

(async () => {
  for (let round = 1; round <= 10; round++) {
    const missing = books.filter(b => !b.text);
    if (!missing.length) break;
    console.log("round " + round + ": " + missing.length + " missing");
    for (const item of missing) {
      try {
        const t = await fetchVol(item.name);
        if (t) { item.text = t; console.log("  ok 卷" + item.v + " " + item.name); }
      } catch (e) { console.log("  fail 卷" + item.v + ": " + e.message); }
      await sleep(500);
    }
    fs.writeFileSync(allPath, JSON.stringify(books, null, 0), "utf-8");
  }
  const chars = books.reduce((s, b) => s + b.text.length, 0);
  const empty = books.filter(b => !b.text);
  console.log("done: 成功 " + (books.length - empty.length) + "/" + books.length +
              " 剩余空 " + empty.map(b => "卷" + b.v).join(",") + " 总字符 " + chars);
})().catch(e => { console.error("FATAL", e); process.exit(1); });
