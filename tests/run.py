#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run.py —— 一条命令跑完全部测试

    python3 tests/run.py            全跑（含真浏览器冒烟）
    python3 tests/run.py --no-web   跳过浏览器，只跑数据与源码检查

顺序有意为之：数据 → 源码 → 打包 → 浏览器。
越靠前的越便宜、定位越准。数据错了就没必要再往下走 —— 后面全会跟着红，
反而把真正的病灶淹掉。
"""
import argparse
import importlib
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from harness import run_module, report  # noqa: E402

NODE = '/Users/andy/.workbuddy/binaries/node/versions/22.22.2/bin/node'
NODE_MODULES = '/Users/andy/.workbuddy/binaries/node/workspace/node_modules'
SUITES = [('test_data', '数据层'), ('test_source', '源码结构'), ('test_build', '打包产物')]


def run_python_suites(stop_on_fail=True):
    total_fail = 0
    for mod_name, title in SUITES:
        mod = importlib.import_module(mod_name)
        passed, failed = run_module(mod)
        total_fail += report(title, passed, failed)
        if failed and stop_on_fail:
            print('\n  %s 未通过，后面的检查会被它带偏，先停在这里。' % title)
            return total_fail, True
    return total_fail, False


def run_browser_suite():
    env = dict(os.environ, NODE_PATH=NODE_MODULES)
    print('\n  【浏览器冒烟】')
    r = subprocess.run([NODE, str(HERE / 'smoke.mjs')], cwd=ROOT, env=env,
                       capture_output=True, text=True)
    for line in (r.stdout or '').rstrip().split('\n'):
        if line.strip():
            print('  ' + line)
    if r.returncode == 2:
        print('    ! 环境不具备（缺 Chrome 或 puppeteer-core），本项跳过')
        return 0
    if r.stderr.strip():
        print('    ' + r.stderr.strip().split('\n')[-1])
    return 1 if r.returncode else 0


def ensure_built():
    dist = ROOT / 'dist' / 'index.html'
    src_new = max((f.stat().st_mtime for f in (ROOT / 'src').rglob('*') if f.is_file()),
                  default=0)
    if not dist.exists() or dist.stat().st_mtime < src_new:
        print('  源码比产物新，先构建在线版……')
        subprocess.run([sys.executable, str(ROOT / 'scripts' / 'build' / 'online.py')],
                       cwd=ROOT, check=True)
        subprocess.run([sys.executable, str(ROOT / 'scripts' / 'build' / 'seo.py')],
                       cwd=ROOT, check=True)


def main():
    ap = argparse.ArgumentParser(description='明儒学案 · 测试')
    ap.add_argument('--no-web', action='store_true', help='跳过浏览器冒烟测试')
    ap.add_argument('--keep-going', action='store_true', help='某一组失败也继续往下跑')
    args = ap.parse_args()

    t0 = time.time()
    print('\n══ 明儒学案 · 自动化测试 ' + '═' * 34)
    ensure_built()
    fails, halted = run_python_suites(stop_on_fail=not args.keep_going)
    if not halted and not args.no_web:
        fails += run_browser_suite()

    print('\n' + '─' * 58)
    if fails:
        print('  %d 组检查未通过（耗时 %.1fs）' % (fails, time.time() - t0))
    else:
        print('  全部通过（耗时 %.1fs）' % (time.time() - t0))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
