"""Dust Front RTS 本地化表导出 / 回写工具。

游戏的文本存放在 resources.assets 里的两个 TextAsset（CSV，列为 Keys,Russian,English）:
  - "Localization_DUST_FRONT - Main"
  - "Localization_DUST_FRONT - Tutorial-locals"

用法:
  python tools/loc_tool.py export <resources.assets> <输出目录>
  python tools/loc_tool.py import <resources.assets> <CSV目录> <输出的resources.assets>

import 会把 CSV 目录里同名的 .csv 原样写回对应 TextAsset，其它对象不动。
"""
import struct
import sys
from pathlib import Path

import UnityPy

TABLES = (
    "Localization_DUST_FRONT - Main",
    "Localization_DUST_FRONT - Tutorial-locals",
)


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


if __name__ == "__main__":
    cmd, *args = sys.argv[1:] or [""]
    if cmd == "export" and len(args) == 2:
        export(*args)
    elif cmd == "import" and len(args) == 3:
        import_(*args)
    else:
        sys.exit(__doc__)
