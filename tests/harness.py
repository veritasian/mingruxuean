#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
harness.py —— 极小的断言框架

不引 pytest：这个项目只有 python3 + 一份源码，
测试必须「clone 下来直接能跑」。三十行够用了。

约定：测试文件里所有 test_ 开头的函数会被自动发现，
函数体内用 check(...) 断言，返回值当作这条用例的说明打印出来。
"""
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Failure(AssertionError):
    pass


def check(cond, msg):
    """断言。失败时抛 Failure，由 run_module 统一收集"""
    if not cond:
        raise Failure(msg)
    return True


def check_eq(got, want, msg):
    if got != want:
        raise Failure('%s：期望 %r，实得 %r' % (msg, want, got))
    return True


def sample(items, n=6):
    """报错时列几个例子出来，光说「有 37 处不合规」没法定位"""
    items = list(items)
    head = '、'.join(str(x) for x in items[:n])
    return head + ('… 等 %d 项' % len(items) if len(items) > n else '')


def run_module(mod):
    """跑一个测试模块里的全部 test_*，返回 (通过数, 失败列表)"""
    names = sorted(n for n in dir(mod) if n.startswith('test_'))
    passed, failed = [], []
    for name in names:
        fn = getattr(mod, name)
        label = (fn.__doc__ or name).strip().split('\n')[0]
        try:
            note = fn()
            passed.append((label, note or ''))
        except Failure as e:
            failed.append((label, str(e)))
        except Exception:
            failed.append((label, traceback.format_exc(limit=3).strip().split('\n')[-1]))
    return passed, failed


def report(title, passed, failed):
    print('\n  【%s】' % title)
    width = max([len(p[0]) for p in passed + failed] or [4])
    for label, note in passed:
        print('    ✓ %s  %s' % (label.ljust(width), note))
    for label, note in failed:
        print('    ✗ %s  %s' % (label.ljust(width), note))
    return len(failed)


def main(mod, title):
    passed, failed = run_module(mod)
    n = report(title, passed, failed)
    sys.exit(1 if n else 0)
