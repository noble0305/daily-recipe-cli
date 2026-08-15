# Data Model: daily-recipe-cli

**Date**: 2026-08-15 | **Phase**: 1 | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## 实体关系

```text
Recipe (食谱) 1 ──── N  History (历史记录，按天一条)
   ▲
   │ 首次运行拷贝
DefaultRecipes (包内初始库)

Preference (偏好过滤) —— 仅当次命令生效，不持久化
```

## 实体与字段

### Recipe（食谱）

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| `name` | string | ✅ | 唯一（大小写不敏感去重）；1~30 字符 |
| `ingredients` | string[] | ✅ | 至少 1 项；每项非空 |
| `tags` | string[] | ✅ | 至少 1 项；推荐约定使用「荤/素/快手/费时/汤/主食」等 |
| `note` | string | ❌ | 一句话做法，默认空字符串 |

### HistoryEntry（历史记录）

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| `date` | string | ✅ | 格式 `YYYY-MM-DD`；同一文件内唯一 |
| `recipe` | string | ✅ | 当时选中的菜名快照（记录时不查库，删除食谱不影响历史） |
| `source` | string | ✅ | 枚举：`today`（今日推荐确认）或 `week`（周规划写入） |

### 数据文件容器

- `recipes.json`：顶层为数组 `Recipe[]`
- `history.json`：顶层为数组 `HistoryEntry[]`（按日期升序维护，或读取时排序）

## 状态与不变式

- 用户数据目录默认 `~/.daily-recipe-cli/`，可用环境变量 `RECIPE_CLI_DIR` 覆写（便于测试隔离）。
- 首次运行任一命令时，若 `recipes.json` 不存在，从包内 `default_recipes.json` 拷贝；`history.json` 不存在则创建空数组。
- 写入采用「先写临时文件再原子替换」，避免中途崩溃损坏数据。
- 删除食谱不影响已有历史记录（历史存菜名快照）。
- 当天已选：`history.json` 中已存在当天 `date` 条目时，`recipe today` 默认提示已确定；`--force` 允许覆盖当天条目。

## 派生数据

- 去重窗口内已选集合：由 `history.json` 按 `date >= today - N天` 过滤派生，不单独存储。
- 推荐候选：由 `recipes.json` 过滤（标签 + 去重窗口）后按种子随机打乱生成，不存储中间态。
