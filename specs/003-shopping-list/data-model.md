# 数据模型：购物清单生成（shopping-list）

**日期**: 2026-08-15 | **规格**: [spec.md](./spec.md) | **数据契约**: [contracts/data-schema.md](./contracts/data-schema.md)

本功能**不引入新的持久化数据**——购物清单是对既有 `recipes.json` 与 `history.json` 的纯计算聚合视图，不落盘。本文件定义购物清单的**运行时视图与聚合规则**，以及数据在 CLI / 页面与核心模块间的流转。

## 持久化实体（沿用 001/002，不变）

### 食谱（Recipe）

| 字段 | 类型 | 约束 | 来源 |
|---|---|---|---|
| `name` | string | 非空、≤30 字符、唯一（大小写不敏感） | recipes.json |
| `ingredients` | string[] | 非空数组 | recipes.json |
| `tags` | string[] | 非空数组 | recipes.json |
| `note` | string | 可省略 | recipes.json |

### 历史记录（History）

| 字段 | 类型 | 约束 | 来源 |
|---|---|---|---|
| `date` | string | `YYYY-MM-DD` 合法日期、不重复 | history.json |
| `recipe` | string | 非空（菜名快照） | history.json |
| `source` | string | `today` 或 `week` | history.json |

> 校验规则与错误语义完全沿用 `contracts/data-schema.md`（见 001 功能），本功能不重复实现。

## 运行时视图模型（购物清单，不落盘）

购物清单由核心聚合函数实时计算，CLI 与页面共用同一份输出结构：

### 清单条目（ShoppingItem）

| 字段 | 类型 | 说明 |
|---|---|---|
| `ingredient` | string | 食材名（以食谱 `ingredients` 原始字符串为据，精确匹配） |
| `sources` | string[] | 来自哪些菜（菜名快照，去重后的列表） |

### 购物清单（ShoppingList）

| 字段 | 类型 | 说明 |
|---|---|---|
| `windowDays` | int | 聚合窗口天数（默认 7，含今日） |
| `items` | ShoppingItem[] | 按食材名排序后的清单条目 |
| `skippedRecipes` | string[] | 因不在食谱库或食材非法而被跳过的菜名（空数组表示无跳过） |
| `empty` | bool | 窗口内无已安排菜时为 true（空态） |

## 聚合规则

1. **窗口过滤**：取历史记录中 `date` 在 `[今天, 今天 + (windowDays - 1)]` 闭区间内的条目。`--today` 等价于 `windowDays = 1`。
2. **去重合并**：遍历窗口内每道菜，将其 `ingredients` 逐项加入聚合表；同名字符串只保留一次，来源菜并入 `sources`（保持稳定顺序）。
3. **排序**：条目按 `ingredient` 字符串排序输出（CLI 中文按 UTF-8 字节序；页面端与 CLI 一致以服务端返回顺序为准）。
4. **跳过处理**：菜名在 `recipes.json` 中不存在、或 `ingredients` 缺失/非数组时，该菜整体跳过并记入 `skippedRecipes`，不影响其他菜聚合（spec 边界情况）。
5. **确定性**：纯计算、无随机源，同数据状态必然产出同一清单（宪法原则 III）。

## 数据流转

| 入口 | 调用路径 | 数据影响 |
|---|---|---|
| CLI `recipe shopping-list [--days N] [--today] [--no-merge]` | `shopping.py` 聚合函数 + `storage.load_recipes()` + `storage.load_history()` | 只读 |
| 页面 GET `/api/shopping-list` | `server._api_shopping_list()` → 同上一聚合函数 | 只读 |

`--no-merge`（P3）：关闭来源合并——同一食材每出现于一道菜就单独列一条（`sources` 仅含该菜），不做去重。默认关闭合并语义相反，默认开启去重合并。

## 与 001/002 数据模型的差异

| 项 | 001（CLI）/ 002（页面） | 003（购物清单） |
|---|---|---|
| 持久化实体 | 食谱 / 历史 | 不变（完全沿用） |
| 新增实体 | 无 | 运行时视图（ShoppingList / ShoppingItem），不落盘 |
| 数据校验 | `storage.validate_*` | 复用同一套；聚合层仅对「菜名不在库 / 食材缺失」做跳过而非报错 |
| 写入 | 命令/API 直接写 | **本功能无写入**，纯只读计算 |
