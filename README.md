# Dust Front RTS 简体中文汉化

做法：用中文替换游戏的 English 列（游戏内选 English 即显示中文）。

译文沿用 B 站 UP「战争核心官方_艾尔」的汉化，另补译了原补丁漏掉的 `controls-text`（操作说明）。
`loc/` 下是当前的译文表，改译文直接改这里的 CSV，再用下面的工具写回游戏。

## 文本位置

游戏文本在 `Dust Front RTS_Data/resources.assets` 中的两个 TextAsset（CSV，表头 `Keys,Russian,English`）：

| TextAsset | 条目数 |
|---|---|
| `Localization_DUST_FRONT - Main` | 619 |
| `Localization_DUST_FRONT - Tutorial-locals` | 70 |

## 工具

需要 Python 3 和 `pip install UnityPy`。

```sh
# 把 loc/ 中的译文写回，生成汉化后的 resources.assets
python tools/loc_tool.py import resources.assets loc work/resources.assets
# 导出两张表为 CSV
python tools/loc_tool.py export resources.assets work/csv
```

`import` 只替换这两个 TextAsset，其它对象逐字节保持不变。

## 安装

备份 `Dust Front RTS_Data/resources.assets`，用生成的文件覆盖，进游戏把语言选为 English。
`import` 会整表替换。游戏更新后要先 `export` 新版的表，把新增或改动的条目合并进 `loc/`，再 `import`，否则新版新增的条目会丢失。
