#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hao.py —— 从原书章节标题反解「号」

《明儒学案》的章节标题是高度格式化的：

    [官职/谥号] + [姓] + [号] + 先生 + [名]
    聘君    吴  康斋  先生 与弼
    恭简    魏  庄渠  先生 校
    郎中    王  龙溪  先生 畿
            谢  西山  先生 复

原书自己就把「号」写在标题里，比任何外部资料都可靠，且可溯源到卷次。
drawio 里 26 人 hao 为空（含陈献章/湛若水/王畿/罗汝芳等关键宗师），
导致「白沙」「甘泉」「龙溪」这些原文最常用的称呼无法解析，师承抽不出来。
本模块用原书标题把这些窟窿补上。

另有一类是 hao 被错塞进 zi 字段：「登之号东溟」「惟藩，号蒙泉」，
用 split_zi_hao() 拆开。
"""
import re

COMPOUND_SURNAMES = {"欧阳", "司马", "诸葛", "上官", "夏侯", "皇甫", "尉迟", "公孙"}

# 号里不该出现的字：出现即说明切错了。
# 注意不能把数字一并禁掉 ——「唐一庵」「娄一斋」「罗一峰」都是正经的号。
_BAD_HAO_CHARS = set("先生字号，,。、；;（）()《》　 ")

# 官职/谥号前缀：drawio 解析时被连进号里（「聘君吴康斋」→ 号该是「康斋」）
def _is_dirty(h, name):
    if not h:
        return False
    return (len(h) > 3 or surname_of(name) in h
            or bool(set(h) & _BAD_HAO_CHARS))


def clean_hao(h, name):
    """把「君吴康斋」「政唐一庵」这类脏号切回「康斋」「一庵」。"""
    if not _is_dirty(h, name):
        return h
    sn = surname_of(name)
    pos = h.rfind(sn)
    if pos >= 0:
        h = h[pos + len(sn):]
    h = h.strip("　 ，,、")
    if 2 <= len(h) <= 3 and not (set(h) & _BAD_HAO_CHARS):
        return h
    return ""


def surname_of(name):
    if len(name) >= 3 and name[:2] in COMPOUND_SURNAMES:
        return name[:2]
    return name[:1]


def hao_from_section(section, name):
    """从章节标题反解号。解不出返回 ''。"""
    if not section or not name or "先生" not in section:
        return ""
    prefix, _, given = section.partition("先生")
    # 「名」部分应当是姓名去掉姓之后的尾巴，用它校验切分是否正确
    sn = surname_of(name)
    tail = name[len(sn):]
    given = given.strip()
    if given and tail and given != tail and not tail.endswith(given):
        return ""
    # 姓在 prefix 中最后一次出现之后即是号
    pos = prefix.rfind(sn)
    if pos < 0:
        return ""
    hao = prefix[pos + len(sn):].strip()
    if not (2 <= len(hao) <= 3):
        return ""
    if set(hao) & _BAD_HAO_CHARS:
        return ""
    return hao


def split_zi_hao(zi):
    """「登之号东溟」→ ('登之', '东溟')；「惟藩，号蒙泉」→ ('惟藩', '蒙泉')。"""
    if not zi or "号" not in zi:
        return zi, ""
    left, _, right = zi.partition("号")
    left = left.strip("，,、 ")
    right = right.strip("，,、 ")
    if not (2 <= len(right) <= 3) or (set(right) & _BAD_HAO_CHARS):
        right = ""
    return left, right


def hao_from_head(head, name):
    """head 恰好只写了号（如 陈献章 的 head='白沙'）时取之。"""
    head = (head or "").strip("，,、 ")
    if not head or head == name:
        return ""
    if not (2 <= len(head) <= 3):
        return ""
    if set(head) & _BAD_HAO_CHARS:
        return ""
    # head 含姓名任一字则不是纯号（如「魏校字子才」已被长度挡掉，这里防「王畿」型）
    if any(c in head for c in name):
        return ""
    return head


def derive(person, section=""):
    """返回 (hao, source)。按可靠性：原书标题 > 洗净的旧值 > zi 内嵌 > head。

    旧值不能无条件信任：drawio 把官职连进了号里（「聘君吴康斋」），
    这种脏号会让「康斋」这个原文最常用的称呼永远匹配不上。
    """
    name = person.get("name", "")
    legacy = person.get("hao", "")
    if legacy and not _is_dirty(legacy, name):
        return legacy, "legacy"
    if legacy:                                   # 脏号：优先用原书标题重解
        h = hao_from_section(section, name)
        if h:
            return h, "book_section"
        h = clean_hao(legacy, name)
        if h:
            return h, "cleaned"
        return "", ""
    h = hao_from_section(section, name)
    if h:
        return h, "book_section"
    _, h = split_zi_hao(person.get("zi", ""))
    if h:
        return h, "zi_field"
    h = hao_from_head(person.get("head", ""), name)
    if h:
        return h, "head_field"
    return "", ""


_HEAD_HAO_RE = re.compile(r"号([^\s，,。；;字]{2,3})")


def hao_from_head_text(head):
    """「萧彦号念渠」这种把号写在 head 里的。"""
    m = _HEAD_HAO_RE.search(head or "")
    if not m:
        return ""
    h = m.group(1)
    return "" if set(h) & _BAD_HAO_CHARS else h
