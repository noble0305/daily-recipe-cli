# Quickstart: shopping-list

**日期**: 2026-08-15 | **阶段**: 1 | **计划**: [plan.md](./plan.md) | **规格**: [spec.md](./spec.md)

## 前提

已有 `daily-recipe-cli` 环境（`uv sync` 完成）。购物清单是纯计算视图，基于已确定的带饭安排（历史记录）聚合食材。

## 生成购物清单

```bash
# 聚合未来 7 天（含今日）已安排菜的食材，去重排序并标注来源
uv run recipe shopping-list

# 只看今日已确定那道菜的采购项
uv run recipe shopping-list --today

# 自定义窗口：未来 3 天
uv run recipe shopping-list --days 3

# 不合并重复食材（同一食材每出现于一道菜就单独列出）
uv run recipe shopping-list --no-merge
```

## 页面化访问

```bash
# 启动页面服务并打开浏览器
uv run recipe serve

# 在页面「购物清单」区域查看清单；「仅今日」切换与「合并/不合并」切换等价于 --today / --no-merge
```

## 预期输出示例

未来 7 天已安排「番茄牛腩」（牛腩、番茄、洋葱、土豆）与「番茄炒蛋」（番茄、鸡蛋）：

```text
购物清单（未来 7 天，共 5 项）：
  土豆 ← 番茄牛腩
  洋葱 ← 番茄牛腩
  番茄 ← 番茄牛腩、番茄炒蛋
  牛腩 ← 番茄牛腩
  鸡蛋 ← 番茄炒蛋
```

## 空态

未来 7 天无已安排记录时：

```text
未来 7 天暂无已安排的菜。先用 recipe today 确定今天的菜，或 recipe week 规划下周。
```

## 数据

- 购物清单**不新增数据文件**，仅实时读取 `recipes.json` 与 `history.json`（目录 `~/.daily-recipe-cli/`，`RECIPE_CLI_DIR` 可覆写）。
- 若某道已安排菜不在食谱库中，会在输出末尾提示「已跳过」并列出该菜，不影响其他菜。

## 开发

```bash
uv run pytest            # 运行全部测试（含购物清单聚合逻辑）
```
