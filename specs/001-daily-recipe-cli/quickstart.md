# Quickstart: daily-recipe-cli

**Date**: 2026-08-15 | **Phase**: 1 | **Plan**: [plan.md](./plan.md)

## 安装

```bash
# 克隆仓库
git clone https://github.com/noble0305/daily-recipe-cli.git
cd daily-recipe-cli

# 创建虚拟环境并安装（uv）
uv sync --dev

# 首次运行任意命令自动初始化数据目录（~/.daily-recipe-cli/）
uv run recipe today
```

## 每日使用

```bash
# 今晚定明天的饭：给出 1~3 道候选（避开最近 7 天已选）
uv run recipe today

# 确认选中的候选（示例：选第 1 个）
uv run recipe today 1

# 周末批量规划下周 5 个工作日
uv run recipe week

# 只看素菜候选
uv run recipe today --tags 素
```

## 食谱库管理

```bash
# 查看全部食谱
uv run recipe list

# 添加新菜
uv run recipe add "青椒肉丝" --ingredients 青椒 里脊肉 --tags 荤 快手 --note "大火快炒 5 分钟"

# 删除菜（不影响历史记录）
uv run recipe remove "青椒肉丝"

# 查看吃过的历史
uv run recipe history
```

## 高级

```bash
# 可复现：指定随机种子
uv run recipe today --seed 2026-08-15

# 调整去重窗口（默认 7 天）
uv run recipe today --days 14

# 今日已确定后强行重新推荐
uv run recipe today --force
```

## 数据

- 数据目录：`~/.daily-recipe-cli/`（环境变量 `RECIPE_CLI_DIR` 可覆写）
- `recipes.json`：食谱库，纯文本可直接手改
- `history.json`：历史记录
- 完整字段约束见 [contracts/data-schema.md](./contracts/data-schema.md)

## 开发

```bash
# 运行测试
uv run pytest

# 测试数据目录隔离：临时目录
RECIPE_CLI_DIR=/tmp/recipe-test uv run recipe today
```
