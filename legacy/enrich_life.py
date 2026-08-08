#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Enrich data_final.json with verified 生卒年 (birth–death years) for the
key founders and major figures of 明儒学案.

Sources: 蔡仁厚《中国哲学史》历代哲人生卒年表 + individual 百科/方志 entries,
cross-checked against the 年X (age-at-death) already recorded in the source
drawio labels. Only figures present in the dataset are enriched.
"""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "data_final.json")

# name -> 生卒年 (year range).  Widely-accepted historical dates.
LIFE = {
    "王阳明": "1472–1529",
    "陈献章": "1428–1500",
    "吴与弼": "1391–1469",
    "薛瑄":   "1389–1464",
    "吕柟":   "1479–1542",
    "王恕":   "1416–1508",
    "湛若水": "1466–1560",
    "刘宗周": "1578–1645",
    "王艮":   "1483–1541",
    "颜钧":   "1504–1596",
    "罗汝芳": "1515–1588",
    "顾宪成": "1550–1612",
    "高攀龙": "1562–1626",
    "徐爱":   "1487–1517",
    "王畿":   "1498–1583",
    "钱德洪": "1496–1574",
    "邹守益": "1491–1562",
    "欧阳德": "1496–1554",
    "聂豹":   "1487–1563",
    "罗洪先": "1504–1564",
    "黄省曾": "1490–1540",
    "胡居仁": "1434–1484",
    "娄谅":   "1422–1491",
    "赵贞吉": "1508–1576",
    "唐顺之": "1507–1560",
    "孙慎行": "1565–1636",
    "焦竑":   "1540–1620",
    "周汝登": "1547–1629",
    "黄绾":   "1477–1551",
    "王栋":   "1503–1581",
    "王襞":   "1511–1587",
    "张诩":   "1455–1514",
}

d = json.load(open(SRC, encoding="utf-8"))
P = d["people"]
byname = {p["name"]: p for p in P.values()}

added, skipped = [], []
for name, life in LIFE.items():
    if name in byname:
        byname[name]["life"] = life
        added.append(name)
    else:
        skipped.append(name)

json.dump(d, open(SRC, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("enriched (%d):" % len(added), " ".join(added))
if skipped:
    print("not in dataset (skipped):", " ".join(skipped))

# coverage report
have_life = sum(1 for p in P.values() if p.get("life"))
have_age = sum(1 for p in P.values() if p.get("age"))
print("life present: %d/%d | age present: %d/%d" % (have_life, len(P), have_age, len(P)))
