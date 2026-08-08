#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_front.py —— 卷前三篇（原序、发凡、师说）入库

《明儒学案》正编六十三卷之前还有几篇总纲性的文字，按原书次序须收三篇：

  黄梨洲先生原序   黄宗羲自述编书缘起与「一本万殊」的宗旨，是全书的读法说明。
  发凡            黄宗羲总论有明一代学术源流与《明儒学案》的编纂体例。
  师说            刘宗周对二十五位明儒的评断，黄宗羲把它冠于全书之首，
                  等于先亮出师门的判教标准，后面六十三卷都是在这个尺度下展开的。

这三篇不是「卷」，所以不占用 1–63 的卷号，另立 front 序列（x1/x2/x3），
在目录里排到卷一之前，与原书次序一致（原序 → 发凡 → 师说 → 卷一）。
这样「六十三卷」这个不变量不被破坏，而读者进来第一眼看到的仍是原书本来的次序。

师说逐条评人，标题形如「王陽明守仁」（姓+号+名），
这里把它还原成人物 id 挂上去，读者点标题就能跳到人物卡。
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "data")
SRC = os.path.join(ROOT, "resources", "volumes")

sys.path.insert(0, os.path.join(ROOT, "scripts", "ingest"))
from normalize import canonical_name, norm_text                   # noqa: E402

# 原文文件 → 目录条目。label 是目录左栏的短标，name 是篇名。
FRONT = [
    {"id": "x1", "file": "front_x1.wiki", "label": "原序",
     "name_original": "黃梨洲先生原序",
     "note": "黄宗羲自序：一本万殊，学问不必强同"},
    {"id": "x2", "file": "front_x2.wiki", "label": "发凡",
     "name_original": "發凡",
     "note": "黄宗羲总论有明一代学术源流与《明儒学案》编纂体例"},
    {"id": "x3", "file": "front_x3.wiki", "label": "师说",
     "name_original": "師說",
     "note": "刘宗周评骘明儒二十五家，黄宗羲冠于全书之首"},
]


def read(p):
    with open(p, "r", encoding="utf-8") as f:
        return f.read()


def guess_id(part, persons):
    """
    「方正學孝孺」这类标题是 姓 + 号 + 名 三段拼接，名可能一字也可能两字，
    光凭字数切不准。所以按可能性从高到低试几种切法，命中人物库即收：

      姓+末二字   吴康斋与弼 → 吴与弼
      姓+末一字   曹月川端   → 曹端
      姓+号       王阳明守仁 → 王阳明（库里用通行名，不用本名王守仁）

    试的顺序就是准确度的顺序，先中先算，不会把两个人混成一个。
    """
    for cand in (part[0] + part[-2:], part[0] + part[-1], part[:3], part[:2]):
        pid = canonical_name(cand)[0]
        if pid in persons:
            return pid
    return None


def persons_in(text, persons):
    """师说逐条评人，把小标题还原成人物 id。一条标题可并列数人，全角空格分隔。"""
    out, seen = [], set()
    for head in re.findall(r"^==\s*([^=\n]+?)\s*==$", text, re.M):
        for part in re.split(r"[\u3000\s]+", norm_text(head)):
            part = part.strip()
            if len(part) < 3:
                continue
            pid = guess_id(part, persons)
            if pid and pid not in seen:
                seen.add(pid)
                out.append(pid)
    return out


def main():
    with open(os.path.join(DATA, "persons.json"), "r", encoding="utf-8") as f:
        persons = json.load(f)
    toc_path = os.path.join(DATA, "toc.json")
    with open(toc_path, "r", encoding="utf-8") as f:
        toc = json.load(f)

    outdir = os.path.join(DATA, "volumes")
    os.makedirs(outdir, exist_ok=True)
    front = []
    for spec in FRONT:
        raw = read(os.path.join(SRC, spec["file"]))
        text = norm_text(raw)
        name = norm_text(spec["name_original"])
        who = persons_in(text, persons)
        p = os.path.join(outdir, "%s.json" % spec["id"])
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"volume": spec["id"], "name": name, "text": text},
                      f, ensure_ascii=False)
        front.append({"id": spec["id"], "label": spec["label"], "name": name,
                      "name_original": spec["name_original"],
                      "chars": len(text), "persons": who, "note": spec["note"]})
        print("  写出 data/volumes/%-8s %6.1f KB  %-8s 关联 %d 人"
              % (spec["id"] + ".json", os.path.getsize(p) / 1024,
                 spec["label"], len(who)))

    toc["front"] = front
    toc.setdefault("meta", {})["front_count"] = len(front)
    with open(toc_path, "w", encoding="utf-8") as f:
        json.dump(toc, f, ensure_ascii=False, indent=1)
    print("  目录写入卷前 %d 篇（排在卷一之前）" % len(front))
    return 0


if __name__ == "__main__":
    sys.exit(main())
