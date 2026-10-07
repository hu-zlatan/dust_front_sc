# Dust Front RTS 简体中文汉化

## 文本位置

游戏文本在 `Dust Front RTS_Data/resources.assets` 中的两个 TextAsset（CSV，表头 `Keys,Russian,English`）：

| TextAsset | 条目数 |
|---|---|
| `Localization_DUST_FRONT - Main` | 619 |
| `Localization_DUST_FRONT - Tutorial-locals` | 70 |

## 工具

需要 Python 3 和 `pip install UnityPy`。

```sh
# 导出两张表为 CSV
python tools/loc_tool.py export resources.assets work/csv
# 把修改后的 CSV 写回，生成新的 resources.assets
python tools/loc_tool.py import resources.assets work/csv work/resources.assets
```

`import` 只替换这两个 TextAsset，其它对象逐字节保持不变。
