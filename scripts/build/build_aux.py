#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_aux.py —— 把地理、生卒、目录三份辅助数据迁到新 id 上

旧数据的键是 drawio 的 `aZOgffvFExYyYC5foWOi-213` 这类不稳定 id，
重新导一次图就全变了。统一换成以姓名为主键的稳定 id。

生卒数据自带 method 字段（史载 / 书载·进士 / 推算（依师承代次） / 不详），
这是现成的溯源信息，必须原样保留 —— 推算出来的年份和史书明载的年份
在图上长得一样，但可信度差着量级，前端要能区分。
"""
import json
import os
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "data")
LEGACY = os.path.join(ROOT, "legacy")

sys.path.insert(0, os.path.join(ROOT, "scripts", "ingest"))
from normalize import canonical_name, norm_text                   # noqa: E402


def load(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def dump(o, p):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(o, f, ensure_ascii=False, indent=1)
    print("  写出 %-30s %8.1f KB" % (os.path.relpath(p, ROOT),
                                     os.path.getsize(p) / 1024))


def main():
    persons = load(os.path.join(DATA, "persons.json"))
    id_map = load(os.path.join(DATA, "id_map.json"))
    today = date.today().isoformat()

    def resolve(x):
        if x in persons:
            return x
        if x in id_map and id_map[x] in persons:
            return id_map[x]
        n = canonical_name(x)[0]
        return n if n in persons else None

    # ---- 地理 ----
    g = load(os.path.join(LEGACY, "data_geo.json"))
    geo, lost_geo = {}, []
    for k, v in g["geo"].items():
        pid = resolve(k)
        (geo.setdefault(pid, v) if pid else lost_geo.append(k))
    dump({"$schema": "./schema/geo.schema.json",
          "meta": {"built_at": today, "count": len(geo),
                   "unmapped": len(lost_geo),
                   "note": "prov/city/note 为今地名比定，raw 为原书籍贯原文"},
          "places": geo,
          "birth_patterns": g.get("birth_map", {})},
         os.path.join(DATA, "geo.json"))

    # ---- 生卒 / 活跃期 ----
    t = load(os.path.join(LEGACY, "data_timeline.json"))
    period, lost_t, by_method = {}, [], {}
    for k, v in t["period"].items():
        pid = resolve(k)
        if not pid:
            lost_t.append(k)
            continue
        period[pid] = v
        by_method[v.get("method", "不详")] = by_method.get(v.get("method", "不详"), 0) + 1
    dump({"$schema": "./schema/timeline.schema.json",
          "meta": {"built_at": today, "count": len(period),
                   "unmapped": len(lost_t), "by_method": by_method,
                   "note": "method 标明年份来源：史载最可信，推算仅供排布参考"},
          "emperors": t["emperors"],
          "period": period},
         os.path.join(DATA, "timeline.json"))

    # ---- 目录 ----
    toc_raw = load(os.path.join(LEGACY, "analysis.json")).get("anchors")
    books = load(os.path.join(ROOT, "resources", "volumes", "all.json"))
    book_index = load(os.path.join(DATA, "intermediate", "book_index.json"))
    per_vol = {}
    for pid, a in book_index.items():
        per_vol.setdefault(a["volume"], []).append((a["seq"], pid))
    toc = []
    for b in books:
        v = b["v"]
        toc.append({"volume": v,
                    "name": norm_text(b["name"]),
                    "name_original": b["name"],
                    "chars": len(b["text"]),
                    "persons": [p for _, p in sorted(per_vol.get(v, []))]})
    dump({"$schema": "./schema/toc.schema.json",
          "meta": {"built_at": today, "volume_count": len(toc),
                   "total_chars": sum(x["chars"] for x in toc)},
          "volumes": toc},
         os.path.join(DATA, "toc.json"))

    # ---- 原文按卷切分（前端按需加载，不再一次性塞 1MB 进 HTML）----
    outdir = os.path.join(DATA, "volumes")
    os.makedirs(outdir, exist_ok=True)
    total = 0
    for b in books:
        p = os.path.join(outdir, "v%02d.json" % b["v"])
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"volume": b["v"], "name": norm_text(b["name"]),
                       "text": norm_text(b["text"])}, f, ensure_ascii=False)
        total += os.path.getsize(p)
    print("  写出 data/volumes/v01..v%02d.json          %8.1f KB（共 %d 卷）"
          % (books[-1]["v"], total / 1024, len(books)))

    if lost_geo or lost_t:
        print("  未能映射：地理 %d · 生卒 %d" % (len(lost_geo), len(lost_t)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
