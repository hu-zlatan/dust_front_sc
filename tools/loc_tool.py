"""Dust Front RTS 本地化表导出 / 回写工具。

游戏的文本存放在 resources.assets 里的两个 TextAsset（CSV，列为 Keys,Russian,English）:
  - "Localization_DUST_FRONT - Main"
  - "Localization_DUST_FRONT - Tutorial-locals"

用法:
  python tools/loc_tool.py export <resources.assets> <输出目录>
  python tools/loc_tool.py import <resources.assets> <CSV目录> <输出的resources.assets>
  python tools/loc_tool.py check <原版resources.assets> <CSV目录>

import 会把 CSV 目录里同名的 .csv 原样写回对应 TextAsset，其它对象不动。
check 拿译文表和原版英文逐条比对：键是否一致、富文本标签、占位符、换行数，以及是否有未翻译条目。
"""
import collections
import csv
import io
import re
import struct
import sys
from pathlib import Path

import UnityPy

TABLES = (
    "Localization_DUST_FRONT - Main",
    "Localization_DUST_FRONT - Tutorial-locals",
)

TAG = re.compile(r"<[^<>]+>")
PLACEHOLDER = re.compile(r"\{\d+\}|%[sd]")
CJK = re.compile(r"[\u4e00-\u9fff]")


def _read_string(raw, off):
    n = struct.unpack_from("<i", raw, off)[0]
    s = raw[off + 4:off + 4 + n]
    return s, (off + 4 + n + 3) & ~3


def _pack_string(b):
    out = struct.pack("<i", len(b)) + b
    return out + b"\0" * (-len(out) % 4)


def _parse_text_asset(raw):
    # 类型树被剥离，按 2020.3 TextAsset 布局手动读取: m_Name, m_Script。
    # 只取声明长度内的内容，忽略某些补丁在末尾留下的 0 填充。
    name, off = _read_string(raw, 0)
    script, _ = _read_string(raw, off)
    return name.decode("utf-8"), script


def _tables(env):
    for obj in env.objects:
        if obj.type.name != "TextAsset":
            continue
        name, script = _parse_text_asset(obj.get_raw_data())
        if name in TABLES:
            yield obj, name, script


def export(assets, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for _, name, script in _tables(UnityPy.load(assets)):
        (out / f"{name}.csv").write_bytes(script)
        print(f"exported {name}.csv ({len(script)} bytes)")


def import_(assets, csv_dir, out_path):
    env = UnityPy.load(assets)
    for obj, name, _ in _tables(env):
        src = Path(csv_dir) / f"{name}.csv"
        if not src.exists():
            continue
        script = src.read_bytes()
        script.decode("utf-8")  # 非 UTF-8 直接报错，避免写坏
        obj.set_raw_data(_pack_string(name.encode("utf-8")) + _pack_string(script))
        print(f"imported {name}.csv ({len(script)} bytes)")
    Path(out_path).write_bytes(list(env.files.values())[0].save())
    print(f"wrote {out_path}")


def _rows(text):
    return list(csv.reader(io.StringIO(text, newline="")))


def check(orig_assets, csv_dir):
    errors = warnings = 0
    for _, name, script in _tables(UnityPy.load(orig_assets)):
        orig = _rows(script.decode("utf-8"))
        ours = _rows((Path(csv_dir) / f"{name}.csv").read_text(encoding="utf-8"))
        orig_keys = [r[0] for r in orig]
        our_keys = [r[0] for r in ours]
        if orig_keys != our_keys:
            missing = sorted(set(orig_keys) - set(our_keys))
            extra = sorted(set(our_keys) - set(orig_keys))
            print(f"[{name}] 键与原版不一致 缺少={missing} 多出={extra}")
            errors += 1
        zh = {r[0]: r[2] for r in ours if len(r) == 3}
        for key, _, en in orig[1:]:
            if key not in zh:
                continue
            t = zh[key]
            problems = []
            if collections.Counter(TAG.findall(en)) != collections.Counter(TAG.findall(t)):
                problems.append(f"标签 en={TAG.findall(en)} zh={TAG.findall(t)}")
            if collections.Counter(PLACEHOLDER.findall(en)) != collections.Counter(PLACEHOLDER.findall(t)):
                problems.append(f"占位符 en={PLACEHOLDER.findall(en)} zh={PLACEHOLDER.findall(t)}")
            if en.count("\n") != t.count("\n"):
                problems.append(f"换行数 en={en.count(chr(10))} zh={t.count(chr(10))}")
            if problems:
                print(f"[{name}] {key}: " + "; ".join(problems))
                errors += 1
            elif en.strip() and not CJK.search(t):
                print(f"[{name}] {key}: 疑似未翻译: {t[:60]!r}")
                warnings += 1
    print(f"{errors} 个错误, {warnings} 个警告")
    return errors == 0


if __name__ == "__main__":
    cmd, *args = sys.argv[1:] or [""]
    if cmd == "export" and len(args) == 2:
        export(*args)
    elif cmd == "import" and len(args) == 3:
        import_(*args)
    elif cmd == "check" and len(args) == 2:
        sys.exit(0 if check(*args) else 1)
    else:
        sys.exit(__doc__)
