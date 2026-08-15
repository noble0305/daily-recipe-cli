# daily-recipe-cli

每日带饭食谱推荐命令行工具 —— 帮你解决「今天/下周带什么饭」的决策痛点。

## 这是什么

一个单用户、离线、纯标准库实现的命令行工具。核心思路：

- **前一晚决策**：`recipe today` 给出 1~3 道候选菜，自动避开最近 7 天吃过的菜（轮换不腻），确认后写入历史；
- **周末批量规划**：`recipe week` 一次生成未来 5 个工作日的菜单，一周内不重样；
- **食谱库自增**：内置 15 道「带饭友好」初始食谱（耐放、复热好吃），支持随时 `recipe add` 扩展，数据为纯文本 JSON 可直接手改。

本项目基于 [GitHub Spec Kit](https://github.com/github/spec-kit)（Spec-Driven Development 工作流）开发，需求规格见 `specs/001-daily-recipe-cli/`。

## 安装

要求：Python 3.11+ 与 [uv](https://docs.astral.sh/uv/)。

```bash
git clone https://github.com/noble0305/daily-recipe-cli.git
cd daily-recipe-cli
uv sync            # 创建虚拟环境并安装（含 recipe 命令）
uv run recipe today   # 首次运行自动初始化数据目录
```

## 每日使用

```bash
# 推荐今天的候选（避开最近 7 天已选）
uv run recipe today

# 确认第 1 个候选
uv run recipe today 1

# 周末批量规划下周 5 个工作日
uv run recipe week
```

## 食谱库管理

```bash
uv run recipe list                            # 查看全部食谱
uv run recipe list --tags 素                  # 只看素菜
uv run recipe add "香菇滑鸡" --ingredients 鸡腿 香菇 --tags 荤 快手 --note "蒸 20 分钟"
uv run recipe remove "香菇滑鸡"               # 删除（历史记录不受影响）
uv run recipe history                         # 查看吃过的历史
```

## 偏好与高级参数

```bash
uv run recipe today --tags 素 快手            # 按标签过滤（须同时满足）
uv run recipe today --days 14                 # 去重窗口改为 14 天
uv run recipe today --count 5                 # 候选数量改为 5
uv run recipe today --seed 2026-08-15         # 指定随机种子（同种子同结果）
uv run recipe today --force                   # 今日已确定后强行重新推荐
uv run recipe week --yes                      # 跳过确认直接写入
```

## 数据

- 数据目录：`~/.daily-recipe-cli/`（可用环境变量 `RECIPE_CLI_DIR` 覆写）
- `recipes.json`：食谱库，纯文本可直接手改
- `history.json`：历史记录（菜名快照，删除食谱不影响历史）
- 字段约束见 [数据契约](specs/001-daily-recipe-cli/contracts/data-schema.md)

## 开发

```bash
uv run pytest        # 运行全部测试（核心逻辑均有覆盖）
```

## 技术说明

- Python 3.11+，运行时零第三方依赖（仅标准库），完全离线
- 推荐可复现：同一种子 + 同一数据状态产出同一结果（默认按当天日期作种子）
- 去重窗口不足时自动放宽（7→3→1→0 天），并给出提示

## 许可

MIT
