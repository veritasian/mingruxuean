#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
yangming_data.py —— 阳明心学内容入库 → data/yangming.json

来源：resources/yangming/（用户手稿页面的存档，index.html + main.js）。

页面内容是「静态图 + 数据驱动图」的混合：
  ch1 思维模型  静态镜像图（明镜/磨镜两路）
  ch2 根器论    三教 × 三阶 矩阵
  ch3–ch14      通用四象限图（正文在 main.js 的 QUADS 数据里，由脚本生成）

本脚本把「标题结构」从存档的 index.html 直接读出来（单一真相），
把「图表内容」按结构化的 Python 数据转录进 data/yangming.json，
并交叉校验：存档里章节的 序号/篇名 必须与这里的一致，
不一致就报错，防止存档更新后悄悄对不上。

产物字段：
  hero      四句教四行
  chapters  14 章，kind ∈ flow/matrix/quad
  outro     尾注两行
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "resources", "yangming", "index.html")
OUT = os.path.join(ROOT, "data", "yangming.json")

# 存档 HTML 的章节结构（正则抓：id / 序号 / 篇名 / 副题）
RE_CH = re.compile(
    r'<section class="chapter" id="(ch\d+)"[^>]*>\s*'
    r'<header class="chapter-head">\s*'
    r'<span class="chapter-num">([^<]+)</span>\s*'
    r'<h3>([^<]+)</h3>\s*(?:<p>([^<]*)</p>)?')

RE_HERO = re.compile(r'<h2 class="hero-title">\s*(.*?)\s*</h2>', re.S)
RE_HERO_LINE = re.compile(r'<span>([^<]+)</span>')
RE_EYEBROW = re.compile(r'<p class="hero-eyebrow">([^<]+)</p>')
RE_OUTRO = re.compile(r'<p class="outro-(?:line|sub)">([^<]+)</p>')

# 章节正文：id → kind + 内容。标题/副题一律以存档 HTML 为准，这里只核对序号与篇名。
NUM_TITLE = {
    "ch1": ("壹", "思维模型"), "ch2": ("贰", "根器论"), "ch3": ("叁", "体用论（中道）"),
    "ch4": ("肆", "心即理"), "ch5": ("伍", "知行合一"), "ch6": ("陆", "中庸架构"),
    "ch7": ("柒", "大学架构"), "ch8": ("捌", "定慧不二"), "ch9": ("玖", "止观不二"),
    "ch10": ("拾", "有无不二"), "ch11": ("拾壹", "性命不二"), "ch12": ("拾贰", "虚实不二"),
    "ch13": ("拾叁", "正奇不二"), "ch14": ("拾肆", "形势不二"),
}

BODIES = {
    "ch1": {
        "kind": "flow",
        "flow": {
            "awakeTag": "明镜喻", "awakeCap": "觉者之心",
            "deludeTag": "磨镜喻", "deludeCap": "迷人之心",
            "mid1": "致知 · 为善", "mid2": "格物 · 去恶",
            "awakeCols": [
                {"cap": "镜体本明（体）",
                 "rows": ["无善无恶", "廓然大公", "寂然不动"], "emph": [1, 2],
                 "note": "道心惟微（洁净精微）"},
                {"cap": "照物无遗（用）",
                 "rows": ["知善知恶", "物来顺应", "感而遂通"], "emph": [1, 2],
                 "note": "允执阙中（体中用和）"},
            ],
            "deludeCols": [
                {"cap": "磨镜功夫",
                 "rows": ["去恶为善", "惟精惟一（戒慎恐惧）"], "know": 1, "note": ""},
                {"cap": "明镜染尘",
                 "rows": ["有善有恶", "人心惟危（过犹不及）", "有=刻意执著"], "emph": [1, 2], "note": ""},
            ],
        },
    },
    "ch2": {
        "kind": "matrix",
        "matrix": {
            "cols": [
                {"char": "儒", "en": "Confucianism", "dot": "ru"},
                {"char": "佛", "en": "Buddhism", "dot": "fo"},
                {"char": "道", "en": "Daoism", "dot": "dao"},
            ],
            "rows": [
                {"level": "上 · 100%", "fig": "run",
                 "cells": [
                     {"t": "生知安行", "s": "尽心知性知天", "cls": "green"},
                     {"t": "上根器", "s": "六祖顿门", "cls": "yellow"},
                     {"t": "上士闻道", "s": "勤而行之", "cls": "blue"}]},
                {"level": "中 · 80%", "fig": "walk",
                 "cells": [
                     {"t": "学知力行", "s": "存心养性事天", "cls": "green"},
                     {"t": "中根器", "s": "渐修渐悟", "cls": "yellow"},
                     {"t": "中士闻道", "s": "若存若亡", "cls": "blue"}]},
                {"level": "下 · 20%", "fig": "crawl",
                 "cells": [
                     {"t": "困知勉行", "s": "夭寿不二修身", "cls": "green"},
                     {"t": "下根器", "s": "渐修渐修", "cls": "yellow"},
                     {"t": "下士闻道", "s": "大笑之", "cls": "blue"}]},
            ],
        },
    },
    "ch3": {
        "kind": "quad",
        "quad": {
            "use": ["用", "觉 · 心"], "body": ["体", "离 · 性"],
            "foot": "Progress × Result = 体用合一之阶。",
            "q": [
                {"pos": "tl", "cls": "red", "title": "有觉无离", "lines": ["落于功利"]},
                {"pos": "tr", "cls": "yellow", "title": "觉离不二", "lines": ["圣境"]},
                {"pos": "bl", "cls": "green", "title": "不觉不离", "lines": ["凡"]},
                {"pos": "br", "cls": "red", "title": "有离无觉", "lines": ["落于枯寂"]},
            ],
        },
    },
}

# ch3–ch14 四象限，转录自存档 main.js 的 QUADS（体/用 + 四格）
QUADS = [
    ("ch4", ("理", "体"), ("心", "用"),
     [("tl", "red", "执相逐物", ["安排思索", "见闻觉知"], "论气不论性，不明"),
      ("tr", "yellow", "寂然不动", ["廓然大公", "感而遂通", "物而顺应"], "君子之学"),
      ("bl", "green", "", [], ""),
      ("br", "red", "枯木寒潭", ["寸草不生", "佛老落空"], "论性不论气，不备")]),
    ("ch5", ("知", "体"), ("行", "用"),
     [("tl", "red", "行而不知", ["冥行妄作"], ""),
      ("tr", "yellow", "知行合一", ["圣境"], "知之切，反身之门"),
      ("bl", "green", "不知不行", ["匹夫之愚"], ""),
      ("br", "red", "知而不行", ["悬空思索"], "")]),
    ("ch6", ("中", "体"), ("和", "用"),
     [("tl", "red", "有和无中", ["明诚功夫"], "容易乡愿"),
      ("tr", "yellow", "致中和", ["天地位"], "诚明"),
      ("bl", "green", "", [], ""),
      ("br", "red", "有中无和", ["明诚功夫"], "难成功业")]),
    ("ch7", ("明德", "体"), ("亲民", "用"),
     [("tl", "red", "功利之徒", ["五伯"], ""),
      ("tr", "yellow", "止于至善", [], ""),
      ("bl", "green", "", [], ""),
      ("br", "red", "虚无主义", ["二氏"], "")]),
    ("ch8", ("定", "体"), ("慧", "用"),
     [("tl", "red", "有慧无定", ["执相逐物"], ""),
      ("tr", "yellow", "定慧等持", ["菩提即生"], ""),
      ("bl", "green", "", [], ""),
      ("br", "red", "有定无慧", ["枯木死灰"], "")]),
    ("ch9", ("止", "体"), ("观", "用"),
     [("tl", "red", "观而不止", ["病在散乱"], ""),
      ("tr", "yellow", "止观不二", ["菩提顿现"], ""),
      ("bl", "green", "", [], ""),
      ("br", "red", "止而不观", ["病在昏沉"], "")]),
    ("ch10", ("无", "体"), ("有", "用"),
     [("tl", "red", "有而不无", ["心被境夺"], ""),
      ("tr", "yellow", "有无不二", ["道德等持"], ""),
      ("bl", "green", "", [], ""),
      ("br", "red", "无而不有", ["心被空夺"], "")]),
    ("ch11", ("性", "体"), ("命", "用"),
     [("tl", "red", "有命无性", ["养心不中"], ""),
      ("tr", "yellow", "性命双修", ["理气中和"], ""),
      ("bl", "green", "", [], ""),
      ("br", "red", "有性无命", ["养身不和"], "")]),
    ("ch12", ("虚", "体"), ("实", "用"),
     [("tl", "red", "有实无虚", ["病在形势"], ""),
      ("tr", "yellow", "虚实相生", ["画成妙境"], ""),
      ("bl", "green", "", [], ""),
      ("br", "red", "有虚无实", ["气势过旺"], "")]),
    ("ch13", ("正", "体"), ("奇", "用"),
     [("tl", "red", "有奇无正", ["落于奸诈"], ""),
      ("tr", "yellow", "奇正相生", ["灵机妙用"], ""),
      ("bl", "green", "", [], ""),
      ("br", "red", "有正无奇", ["落于木纳"], "")]),
    ("ch14", ("形", "体"), ("势", "用"),
     [("tl", "red", "有势无形", ["终归消散"], ""),
      ("tr", "yellow", "形势和一", ["山水大成"], ""),
      ("bl", "green", "", [], ""),
      ("br", "red", "有形无势", ["难成大气"], "")]),
]


def quad_chapter(cid, body, use, rows, sub_title):
    return {
        "id": cid, "num": sub_title[0], "title": sub_title[1], "kind": "quad",
        "quad": {
            "body": list(body), "use": list(use),
            "foot": "横轴为体 · 纵轴为用 · 中道合一",
            "q": [{"pos": p, "cls": c, "title": t, "lines": ln, "note": n}
                  for (p, c, t, ln, n) in rows],
        },
    }


def count_chars(obj):
    """统计纯文本字数（用于测试断言「内容非空」）"""
    if isinstance(obj, str):
        return len(obj)
    if isinstance(obj, dict):
        return sum(count_chars(v) for v in obj.values())
    if isinstance(obj, (list, tuple)):
        return sum(count_chars(v) for v in obj)
    return 0


def main():
    html = open(SRC, "r", encoding="utf-8").read()

    found = RE_CH.findall(html)
    by_id = {cid: (num, title, sub.strip()) for (cid, num, title, sub) in found}
    if set(by_id) != set(NUM_TITLE):
        raise SystemExit("章节集合与存档不符：缺 %s 多 %s"
                         % (sorted(set(NUM_TITLE) - set(by_id)),
                            sorted(set(by_id) - set(NUM_TITLE))))

    chapters = []
    for cid, (num, title) in NUM_TITLE.items():
        fnum, ftitle, sub = by_id[cid]
        if (fnum, ftitle) != (num, title):
            raise SystemExit("%s 篇名对不上：存档「%s %s」，期望「%s %s」"
                             % (cid, fnum, ftitle, num, title))
        ch = {"id": cid, "num": num, "title": ftitle, "sub": sub}
        if cid in BODIES:
            ch.update(BODIES[cid])
        else:
            body, use, rows = next(q for q in QUADS if q[0] == cid)[1:]
            ch.update(quad_chapter(cid, body, use, rows, (num, ftitle)))
        chapters.append(ch)

    hero = RE_HERO_LINE.findall(RE_HERO.search(html).group(1))
    if len(hero) != 4:
        raise SystemExit("四句教应是 4 句，读到 %d 句" % len(hero))
    eyebrow = (RE_EYEBROW.search(html) or [None, ""])[1].strip()
    outro = [m for m in RE_OUTRO.findall(html)]

    payload = {
        "title": "阳明心学", "subtitle": "自性论 · 根器论 · 体用论",
        "eyebrow": eyebrow, "hero": hero,
        "heroSub": "四句教 · 一面镜 · 三教九阶 · 一体四用",
        "chapters": chapters, "outro": outro,
        # 四句教下方的心学总纲说明：读者自述读图法（笔者读书心得）
        "note": [
            "以下图表源于笔者读书心得。学贵自得。通过图表的形式阐述一下繁琐的公案。"
            "图文意义重在启发。得鱼忘筌。如有引用请注明出处。",
            "中国古典文脉贵在中字。分成三论：自性论，根器论，体用论。",
            "五派：理气不二派，内理派，内气派，外理派，外气派。五派各有偏颇。"
            "只是因人而设。如同虚病实药，阴病阳药。人各有偏，各自调停救济而已。"
            "最终还是回到一个中，即不二。",
            "修证不二。即修即证。更无需刻意求修，求证。没有内外，也没有先后。"
            "明白体用不二的思维。",
            "再看四句教，首句言空，心体本空，自然第三句，应物不滞；"
            "次句言住，心体刻意，自然第四句，去此刻意。",
            "顿知渐修。惟精惟一。",
        ],
        "meta": {"source": "resources/yangming/index.html + main.js",
                 "chars": count_chars(chapters) + count_chars(hero) + count_chars(outro),
                 "kinds": sorted({c["kind"] for c in chapters})},
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print("  写出 data/yangming.json · %d 章 · %d 字 · kinds=%s"
          % (len(chapters), payload["meta"]["chars"], payload["meta"]["kinds"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
