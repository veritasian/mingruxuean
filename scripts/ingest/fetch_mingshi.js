#!/usr/bin/env node
// 取回《明史》儒林传卷282、283 原文 → resources/mingshi/v282.wiki / v283.wiki
// 与 legacy/extract_books.js 同款通道：Node 原生 fetch + MediaWiki action=query API；429 尊重 Retry-After
const fs = require("fs");
const path = require("path");
const API = "https://zh.wikisource.org/w/api.php?action=query&prop=revisions&rvprop=content&rvslots=main&format=json&formatversion=2&origin=*&titles=";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const OUT = path.join(__dirname, "..", "..", "resources", "mingshi");

async function fetchPage(page) {
  const url = API + encodeURIComponent(page);
  for (let attempt = 0; attempt < 5; attempt++) {
    const res = await fetch(url, { headers: { "User-Agent": "Mozilla/5.0 (batch extractor; educational)" } });
    if (res.status === 429) {
      const ra = parseInt(res.headers.get("retry-after") || "30", 10);
      const wait = Math.min(90, Math.max(ra, 10));
      console.log("  429 -> wait " + wait + "s");
      await sleep(wait * 1000);
      continue;
    }
    if (!res.ok) throw new Error("HTTP " + res.status);
    const j = await res.json();
    const pg = (j.query && j.query.pages && j.query.pages[0]) || {};
    if (pg.missing) throw new Error("PAGE MISSING: " + page);
    const rev = (pg.revisions && pg.revisions[0]) || {};
    const slot = (rev.slots && rev.slots.main) || {};
    return (slot.content || slot["*"] || "").trim();
  }
  throw new Error("429 retries exhausted: " + page);
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  for (const [vol, page] of [["282", "明史/卷282"], ["283", "明史/卷283"]]) {
    const t0 = Date.now();
    const text = await fetchPage(page);
    fs.writeFileSync(path.join(OUT, "v" + vol + ".wiki"), text, "utf-8");
    console.log("v" + vol + " ok, " + text.length + " chars, " + ((Date.now() - t0) / 1000).toFixed(1) + "s");
    await sleep(1800);
  }
})().catch((e) => { console.error(e.message); process.exit(1); });
