#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pipeline.py —— 一条命令跑完整个数据链路

    python3 scripts/pipeline.py            # 全跑
    python3 scripts/pipeline.py ingest     # 只跑摄取
    python3 scripts/pipeline.py build      # 只跑构建（数据已就绪时）

顺序不能乱：后一步都依赖前一步的产物。
    build_persons      legacy 人物 → 规范化
    link_book_sections 对齐原书 204 个章节，学派以原书为准
    reconcile_persons  合并重名、订正学派、补号 → data/persons.json
    extract_relations  63 卷正文挖师承 → relations.mined.json
    build_relations    三路来源合并 → data/relations.json
    analyze_orphans    孤点定性 → data/orphans.json
    build_aux          地理/生卒/目录/分卷正文
    bundle             打包成单文件 dist/明儒学案.html
"""
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable

STAGES = {
    "ingest": [
        ("规范化人物", "scripts/ingest/build_persons.py"),
        ("对齐原书章节", "scripts/ingest/link_book_sections.py"),
        ("订正与合并", "scripts/ingest/reconcile_persons.py"),
        ("抽取师承关系", "scripts/ingest/extract_relations.py"),
        ("《明史》数据源", "scripts/ingest/mingshi_data.py"),
    ],
    "build": [
        ("明史人物入库", "scripts/build/add_mingshi_persons.py"),
        ("合并关系来源", "scripts/build/build_relations.py"),
        ("孤点判读", "scripts/build/analyze_orphans.py"),
        ("辅助数据", "scripts/build/build_aux.py"),
        ("卷前三篇", "scripts/build/build_front.py"),
        ("阳明心学", "scripts/ingest/yangming_data.py"),
        ("打包单文件", "scripts/build/bundle.py"),
    ],
}


def run(label, script):
    print("\n\033[1m▸ %s\033[0m  (%s)" % (label, script))
    t0 = time.time()
    r = subprocess.run([PY, os.path.join(ROOT, script)], cwd=ROOT)
    if r.returncode != 0:
        print("\033[31m  ✗ 失败，链路中断\033[0m")
        sys.exit(r.returncode)
    print("  \033[32m✓\033[0m %.1fs" % (time.time() - t0))


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    stages = STAGES if which == "all" else {which: STAGES.get(which, [])}
    if not any(stages.values()):
        print("未知阶段：%s（可选 ingest / build / all）" % which)
        return 1
    t0 = time.time()
    for name, steps in stages.items():
        for label, script in steps:
            if not os.path.exists(os.path.join(ROOT, script)):
                print("  跳过（尚未实现）：%s" % script)
                continue
            run(label, script)
    print("\n\033[1m全部完成 %.1fs\033[0m" % (time.time() - t0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
