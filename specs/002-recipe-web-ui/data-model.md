# 数据模型：页面化访问（recipe-web-ui）

**日期**: 2026-08-15 | **规格**: [spec.md](./spec.md) | **数据契约**: [contracts/data-schema.md](./contracts/data-schema.md)

本功能**不引入新的持久化数据**——页面与 CLI 共享同一份 `recipes.json` 与 `history.json`（实体、校验规则、写入语义完全沿用 001 功能的数据契约）。本文件定义页面化新增的**运行时视图与交互模型**，以及数据在页面与核心模块间的流转。

## 持久化实体（沿用 001，不变）

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
| `recipe` | string | 非空 | history.json |
| `source` | string | `today` 或 `week` | history.json |

> 校验规则与错误语义完全沿用 `contracts/data-schema.md`，页面层不重复实现。

## 运行时视图模型（页面新增，不落盘）

页面渲染所需的聚合视图，由 `/api/state` 从核心模块组装返回：

### 今日状态（TodayState）

| 字段 | 类型 | 说明 |
|---|---|---|
| `decided` | bool | 今日是否已确定（`history.decided_for_date(今天)`） |
| `decidedRecipe` | string \| null | 已确定时的菜名快照 |
| `candidates` | Recipe[] \| null | 未确定时展示的候选菜（含推荐理由标注） |
| `reason` | string \| null | 推荐理由（如「避开最近 7 天」） |

### 周计划预览（WeekPreview）

| 字段 | 类型 | 说明 |
|---|---|---|
| `days` | { date: string, recipe: string }[] | 下个周一起 5 个工作日的候选菜单 |
| `conflictCount` | int | 与去重窗口冲突而被跳过的候选数（供提示） |

### 历史视图（HistoryView）

| 字段 | 类型 | 说明 |
|---|---|---|
| `records` | { date, recipe, source }[] | 按日期倒序，默认最近 30 天 |
| `rangeDays` | int | 当前时间范围（默认 30） |

## 交互操作模型（页面 → API → 核心模块）

| 页面动作 | API | 核心模块调用 | 数据影响 |
|---|---|---|---|
| 打开页面 | GET `/api/state` | `storage.load_recipes()` + `load_history()` + `history.decided_for_date()` | 只读 |
| 今日推荐 | POST `/api/today` `{action:"recommend", tags?, days?}` | `recommend.candidates()` | 只读 |
| 确认选择 | POST `/api/today` `{action:"confirm", choice: int}` | `history.add(今天, 菜名, "today")` | 写 history.json |
| 重新推荐 | POST `/api/today` `{action:"force"}` | 等价 `--force`，覆盖当日旧记录 | 写 history.json |
| 周计划预览 | POST `/api/week` `{action:"preview", tags?, days?}` | `recommend.week_plan()` | 只读 |
| 周计划写入 | POST `/api/week` `{action:"confirm"}` | `history.add(每日, 菜名, "week")` ×5 | 写 history.json |
| 添加食谱 | POST `/api/add` `{name, ingredients, tags, note}` | `recipes.add()` | 写 recipes.json |
| 删除食谱 | POST `/api/remove` `{name}` | `recipes.remove()` | 写 recipes.json |
| 历史查看 | GET `/api/history?days=N` | 历史查询（倒序） | 只读 |
| 关闭页面 | POST `/api/bye` | `server.shutdown()` | 生命周期（不写数据） |

## 状态流转

```
今日状态：
  未确定 ──recommend──▶ 候选展示（未确定）
  候选展示 ──confirm──▶ 已确定（decided=true, decidedRecipe=菜名）
  已确定 ──force──▶ 候选展示（重新推荐，覆盖当日旧记录）

周计划：
  预览（只读）──confirm──▶ 写入历史 ×5（一次性）──▶ 完成
  预览 ──cancel──▶ 不写入
```

## 校验与错误语义

- 所有写操作经核心模块（`recipes.add/remove`、`history.add`）完成，其内部校验与 `DataError` 语义不变。
- API 层将 `DataError` 转为 HTTP 400 + 中文消息（含出错字段/位置），页面展示为中文错误提示。
- 页面层不做业务校验（如重名判断、日期合法性）——一切以服务端核心模块为准，保证页面与 CLI 行为一致（spec SC-002）。

## 与 001 数据模型的差异

| 项 | 001（CLI） | 002（页面化） |
|---|---|---|
| 持久化实体 | 食谱 / 历史 | 不变（完全沿用） |
| 新增实体 | 无 | 运行时视图（TodayState / WeekPreview / HistoryView），不落盘 |
| 数据校验 | `storage.validate_*` | 复用同一套，页面不重复实现 |
| 写入 | 命令直接写 | 经 API handler 转调核心模块，语义一致 |
