#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parse 江右派 drawio JSON + HTML into a clean 明儒学案 dataset (v3).

Outputs:
  xuean_data.json:
    {
      schools, school_members, people,   # same as before
      edges,                               # list of [teacher_id, student_id]  (arrowed only)
      tongmen,                             # list of [id1, id2]  (NO-arrow edges = 同门/peer)
      school_arrow_edges                   # list of [school_node_id, person_id]  (school→founder anchors)
    }
"""
import json, re, html, os

BASE = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = "/Users/andy/Downloads/江右派.json"
HTML_PATH = "/Users/andy/Downloads/江右派.drawio.html"
OUT_PATH = os.path.join(BASE, "xuean_data.json")

# ----- read raw cells -----
with open(JSON_PATH, encoding="utf-8") as f:
    doc = json.load(f)
cells = doc["pages"][0]["cells"]
labels = {}
for c in cells:
    if c.get("type") == "node":
        labels[c["id"]] = c.get("label", "")
    elif c.get("type") == "edge":
        pass

# ----- read HTML for arrow info + coords -----
with open(HTML_PATH, encoding="utf-8") as f:
    htmltext = f.read()
m = re.search(r'data-mxgraph="(.*?)"', htmltext, re.S)
mg = json.loads(html.unescape(m.group(1)))
xml = mg.get("xml", "")
blocks = re.split(r'<mxCell', xml)

coords = {}
arrows = {}  # edge_id -> True if endArrow present
edge_src_tgt = {}  # edge_id -> (src, tgt)
school_label_node_ids = set()  # nodes that hold a school header
for b in blocks:
    idm = re.search(r'id="([^"]+)"', b)
    if not idm:
        continue
    cid = idm.group(1)
    gm = re.search(r'x="([\d.\-]+)"\s+y="([\d.\-]+)"', b)
    if gm:
        coords[cid] = (float(gm.group(1)), float(gm.group(2)))
    if 'edge="1"' in b:
        s_m = re.search(r'source="([^"]+)"', b)
        t_m = re.search(r'target="([^"]+)"', b)
        st_m = re.search(r'style="([^"]*)"', b)
        style = st_m.group(1) if st_m else ''
        arrows[cid] = 'endArrow=' in style
        if s_m and t_m:
            edge_src_tgt[cid] = (s_m.group(1), t_m.group(1))

# ----- which cells are school headers? -----
SCHOOL_KEYS = ("学案", "江右派")
school_ids = [cid for cid, lab in labels.items()
              if any(k in lab for k in SCHOOL_KEYS) and cid in coords]
school_label_node_ids = set(school_ids)
for cid in school_ids:
    school_label_node_ids.add(cid)

# ----- parse labels into useful fields -----
TWO_CHAR_SURN = {"欧阳","诸葛","司马","上官","夏侯","东方","令狐","钟离","尉迟",
    "慕容","司徒","端木","万俟","闻人","公羊","澹台","公孙","轩辕","宇文","长孙",
    "鲜于","耶律","赫连","皇甫","拓跋","完颜","独孤","南郭","百里","段干","梁丘",
    "左丘","东郭","微生","子车","亓官","巫马","公西","壤驷","夏侯"}

SHI_SET = {"文庄","文贞","文忠","文靖","文毅","文简","文恭","文洁","文定","文端",
    "文肃","文敬","文清","文介","贞襄","恭简","恭节","端文","端毅","康僖","忠介",
    "忠端","忠宪","忠简","忠宣","庄靖","庄简","昭简","安简","荣简","正肃","清献",
    "清敏","正献","文宪","文昭","文懿","文和","文恪","文修","文通","文康","文达",
    "文成","文敏","文裕","文穆","庄肃","荣恪","僖敏","惠敏","恭毅","襄毅","昭毅",
    "武毅","威毅","敏肃","恪慎","诚孝","正学","正谊","清恪","勤恪","文恪"}
GUAN_SET = {"太子太保","太子太傅","太保","太傅","少保","少傅","尚书","侍郎","郎中",
    "员外","主事","中书","侍读","侍讲","给事中","给事","给谏","给练","御史","中丞",
    "提学","副使","参政","佥事","佥宪","都督","郡守","太常","大常","太仆","鸿胪",
    "光禄","通政","教谕","学正","训导","长史","县令","州同","运使","吏目","郡丞",
    "广文","明经","孝廉","文选","文林","承务","征仕","徵君","处士","布衣","解元",
    "状元","进士","行人","司务","典簿","教授","学录","库使","太史","宫谕","洗马",
    "寺丞","少卿","大参","方伯","宪副","宪使","臬使","兵备","粮储","驿传","提举",
    "别驾","推官","知县","县丞","教读","山长","掌教","学博","儒官","隐君","征君",
    "文苑","逸士","高士","善士","义士","孝子","节妇","贞女"}

def strip_prefix(s):
    title, role = "", ""
    changed = True
    while changed:
        changed = False
        for p in SHI_SET:
            if s.startswith(p) and len(s) > len(p):
                title += p; s = s[len(p):]; changed = True; break
        if changed:
            continue
        for p in sorted(GUAN_SET, key=len, reverse=True):
            if s.startswith(p) and len(s) > len(p):
                role += p; s = s[len(p):]; changed = True; break
    return s, title, role

def parse_label(raw):
    parts = [p.strip() for p in raw.replace("\r", "").split("\n") if p.strip()]
    head = parts[0] if parts else ""
    zi = birth = age = hao = ""
    for p in parts[1:]:
        if p.startswith("字"):
            zi = p[1:].strip("，,。 ")
        elif p.startswith("号"):
            hao = p[1:].strip("，,。 ")
        elif "人" in p and not p.startswith("年"):
            birth = p.strip()
        elif p.startswith("年") or "年" in p:
            age = p.strip()
    name = head
    title = role = ""
    if "先生" in head:
        pre, post = head.split("先生", 1)
        pre2, title, role = strip_prefix(pre)
        post = post.strip("，,。 ")
        if pre2[:2] in TWO_CHAR_SURN:
            sur = pre2[:2]; hao2 = pre2[2:]
        else:
            sur = pre2[:1]; hao2 = pre2[1:]
        name = sur + post
        if hao2:
            hao = hao2
    else:
        s2, title, role = strip_prefix(head)
        mm = re.match(r'^([一-龥]{2,4}?)字(.+?)(?:号(.+?))?([一-龥]*人.*)?$', s2)
        if mm:
            name = mm.group(1)
            zi = (zi or mm.group(2) or "").strip("，,。 ")
            hao = (hao or mm.group(3) or "").strip("，,。 ")
            if mm.group(4):
                birth = birth or mm.group(4).strip()
        else:
            name = s2
    return {"name": name, "zi": zi, "birth": birth, "age": age,
            "title": title, "role": role, "hao": hao, "head": head}

# ----- alias map for short-hand node labels (in NAME space, not ID space) -----
# These resolve a 2-3 char label to a canonical person name.
ALIAS_TO_NAME = {
    "南野": "欧阳德", "欧阳南野": "欧阳德",
    "龙溪": "王畿",
    "绪山": "邹守益", "钱绪山": "钱德洪",
    "东廓": "邹守益", "邹东廓": "邹守益",
    "甘泉": "湛若水",
    "聂双江": "聂豹",
    "刘晴川": "刘魁",
    "唐荆川": "唐顺之",
    "罗近溪": "罗汝芳",
    "耿天台": "耿定向",
    "白沙": "陈献章",
    "徐波石": "徐樾",
    "刘师泉": "刘邦采",
}

# Some full labels contain the alias as a substring; map full canonical id
# (from earlier parses) to standard canonical display name.
ID_TO_CANONICAL_NAME = {
    "16": "欧阳德",
    "17": "邹守益",
    "266": "王畿",
    "264": "钱德洪",
    "136": "刘魁",
    "225": "唐顺之",
    "342": "罗汝芳",
    "345": "耿定向",
    "306": "徐樾",
    "305": "刘邦采",
    "184": "邹守益",
    "124": "聂豹",
}

def name_from_label(lab):
    """Return canonical person name for any label, or None if it isn't a person."""
    s = lab.strip()
    if not s: return None
    if s in ALIAS_TO_NAME:
        return ALIAS_TO_NAME[s]
    # full canonical person label like '文庄欧阳南野先生德'
    info = parse_label(s)
    n = info["name"]
    if n and n not in {"崇仁学案","白沙学案","河东学案","三原学案","浙中王门学案","江右派",
                       "江右王门学案","南中王门学案","楚中王门学案","北方王门学案","粤闽王门学案",
                       "止修学案","泰州学案","甘泉学案","蕺山学案","东林学案"}:
        return n
    return None

# ----- people + school membership -----
persons = {}
for cid, lab in labels.items():
    if cid in school_ids or cid not in coords:
        continue
    nm = name_from_label(lab)
    if nm is None: continue
    persons[cid] = {"id": cid, "raw": lab.strip(), "name": nm,
                    "x": coords[cid][0], "y": coords[cid][1]}

def nearest_school(x, y):
    best, bd = None, 1e18
    for sid in school_ids:
        sx, sy = coords[sid]
        d = (x - sx) ** 2 + (y - sy) ** 2
        if d < bd:
            bd, best = d, sid
    return best
for pid, p in persons.items():
    p["school"] = labels[nearest_school(p["x"], p["y"])].strip()

# ----- walks edges in NAME space -----
arrow_edges = []
tongmen_pairs = []
school_anchors = []
for eid, (s, t) in edge_src_tgt.items():
    src_lab = labels.get(s, '').strip()
    tgt_lab = labels.get(t, '').strip()
    src_is_school_node = ('学案' in src_lab and src_lab in [labels[k].strip() for k in school_ids]) or src_lab == '江右派'
    tgt_is_school_node = ('学案' in tgt_lab and tgt_lab in [labels[k].strip() for k in school_ids]) or tgt_lab == '江右派'
    if src_is_school_node and not tgt_is_school_node:
        school_anchors.append([src_lab, name_from_label(tgt_lab)]); continue
    if tgt_is_school_node and not src_is_school_node:
        school_anchors.append([tgt_lab, name_from_label(src_lab)]); continue
    if src_is_school_node and tgt_is_school_node: continue
    n1 = name_from_label(src_lab)
    n2 = name_from_label(tgt_lab)
    if not n1 or not n2: continue
    if n1 == n2: continue  # self-loop artifact
    if arrows.get(eid, False):
        arrow_edges.append([n1, n2])
    else:
        tongmen_pairs.append([n1, n2])

# ----- attach teachers/students by name (lookup via persons[]) -----
name_to_pid = {}
for pid, p in persons.items():
    nm = p["name"]
    if nm in name_to_pid:
        # duplicate name → keep first, merge teachers/students
        keep = name_to_pid[nm]
    else:
        name_to_pid[nm] = pid
        continue
    # merge into existing
    if "teachers_extra" not in persons[keep]:
        persons[keep]["teachers_extra"] = []
        persons[keep]["students_extra"] = []
    persons[keep]["teachers_extra"].append(pid)
    persons[keep]["students_extra"].append(pid)

# for simplicity, just keep first occurrence per name
final_persons = {}
for pid, p in persons.items():
    final_persons[pid] = {
        "id": pid, "raw": p["raw"],
        "name": p["name"],
    }
# rebuild to keep first-per-name only
seen = set()
for pid in list(persons.keys()):
    nm = persons[pid]["name"]
    if nm in seen:
        del persons[pid]
    else:
        seen.add(nm)
for pid in persons:
    p = persons[pid]
    p["teachers"] = []
    p["students"] = []

def edge_with_name(n1, n2):
    """Get pid-by-name for both endpoints, returns (t_pid, s_pid) or None if either missing."""
    a = name_to_pid.get(n1); b = name_to_pid.get(n2)
    return a, b if (a and b) else (None, None)

for n1, n2 in arrow_edges:
    a, b = edge_with_name(n1, n2)
    if a and b:
        persons[b]["teachers"].append(a)
        persons[a]["students"].append(b)

# final people dict with parsed fields
final = {}
for pid, p in persons.items():
    info = parse_label(p["raw"])
    final[pid] = {
        "id": pid, "name": info["name"] or p["name"], "zi": info["zi"], "hao": info["hao"],
        "birth": info["birth"], "age": info["age"], "title": info["title"],
        "role": info["role"], "head": info["head"], "school": p["school"],
        "teachers": p["teachers"], "students": p["students"],
    }
for p in final.values():
    p["teachers"] = sorted({name_to_pid[n] for n in p["teachers"] if name_to_pid.get(n)})
    p["students"] = sorted({name_to_pid[n] for n in p["students"] if name_to_pid.get(n)})

# rebuild edges and tongmen by id
arrow_edges_ids = []
for n1, n2 in arrow_edges:
    a, b = edge_with_name(n1, n2)
    if a and b and a != b:
        arrow_edges_ids.append([a, b])
# dedup
arrow_edges_ids = [list(x) for x in {tuple(e) for e in arrow_edges_ids}]

tongmen_ids = []
for n1, n2 in tongmen_pairs:
    a, b = edge_with_name(n1, n2)
    if a and b and a != b:
        tongmen_ids.append([a, b])
tongmen_ids = [list(x) for x in {tuple(e) for e in tongmen_ids}]

schools = sorted({p["school"] for p in final.values()})
school_members = {s: [] for s in schools}
for pid, p in final.items():
    school_members[p["school"]].append(pid)

out = {"schools": schools, "school_members": school_members, "people": final,
       "edges": arrow_edges_ids,
       "tongmen": tongmen_ids,
       "school_anchors": school_anchors}
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("Schools:", len(schools), "| People:", len(final),
      "| Edges:", len(arrow_edges_ids), "| Tongmen pairs:", len(tongmen_ids))
print("=" * 60)
print("\n=== 同门 (no-arrow) pairs ===")
for a, b in tongmen_ids:
    print("  %s <-> %s" % (final[a]["name"], final[b]["name"]))
print("\n=== school-anchor edges (school header -> founder) ===")
for sid, who in school_anchors:
    print("  %s -> %s" % (sid, who))
print("\n=== arrow edges (%d) ===" % len(arrow_edges_ids))
for t, s in arrow_edges_ids:
    print("  %s -> %s" % (final[t]["name"], final[s]["name"]))
