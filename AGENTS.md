# AGENTS.md

给在 `daily-recipe-cli` 中工作的 ZCode 代理的工作区指南。

## 项目是什么

单用户、完全离线的 Python 命令行工具（运行时零第三方依赖，仅标准库），用于推荐带饭食谱。**用户可见文本一律用中文**。CLI 命令为 `recipe`（入口 `daily_recipe_cli.cli:main`，见 `pyproject.toml`）。

子命令：`today` / `week` / `add` / `list` / `remove` / `history`。

## 目录结构

- `src/daily_recipe_cli/cli.py` — 薄 argparse 层；子命令处理函数不含业务逻辑。`main()` 统一捕获 `DataError`，把中文错误信息输出到 stderr 并返回退出码 1。
- `src/daily_recipe_cli/storage.py` — 数据目录解析、JSON 读写与校验。**所有命令都经此模块加载数据**，保证任何命令下非法数据都以中文 `DataError` 暴露。
- `src/daily_recipe_cli/recipes.py` — 食谱库操作（添加 / 删除 / 标签过滤）。
- `src/daily_recipe_cli/history.py` — 历史读写与「当日已确定」判断。
- `src/daily_recipe_cli/recommend.py` — 纯推荐逻辑（候选生成、周计划、去重窗口、种子洗牌），不做任何 I/O。
- `src/daily_recipe_cli/data/default_recipes.json` — 内置初始食谱库，首次运行复制到用户数据目录。
- `tests/` — pytest，核心逻辑均有覆盖。
- `specs/001-daily-recipe-cli/` — Spec 驱动开发文档（spec、tasks、contracts），非应用代码。
- `.specify/` / `.speckit/` — 工作流工具元数据，非应用代码，不要随意改动。

## 构建与测试

```bash
uv sync          # 创建虚拟环境并安装开发依赖（pytest）
uv run pytest    # 运行全部测试
```

Python 3.11+，hatchling 构建后端。**未配置 linter / formatter**——遵循现有风格（标准库 `from __future__ import annotations`、模块 docstring 用中文）。

## 数据契约（改动 storage 前必读）

`~/.daily-recipe-cli/` 存放 `recipes.json` 与 `history.json`；可用环境变量 `RECIPE_CLI_DIR` 覆写目录。这两个文件是纯文本、可手改的 JSON——完整 schema 与精确的中文错误信息见 `specs/001-daily-recipe-cli/contracts/data-schema.md`。关键规则：

- 绝不静默容错或覆盖非法数据——必须抛 `DataError`，中文信息要含出错字段/位置。
- 写入必须原子：先写 `<file>.tmp` 再 `os.replace()`；失败时清理临时文件。
- `history.json` 每条存**菜名快照**；删除食谱不得影响已有历史。
- `history.add` 覆盖同日期的旧记录（即 `--force` 语义）。

## 需要保持的行为规则

- 推荐可复现：用 `random.Random(seed)` 构造随机源。默认种子是当天日期；`week` 用 `今天 + "-week"`。同一种子 + 同一数据状态必须产出同一结果。
- 去重窗口（`--days`，默认 7）候选不足时折半放宽（7→3→1→0），并用 `widened`/`relaxed` 标志输出提示。
- 周计划从下个周一开始的连续 5 个工作日（`_next_weekday`），批内不重复。
- `week` 确认用 `input()` 读取；捕获 `EOFError`（非交互场景）视为「否」。

## 测试约定

测试绝不能碰真实的 `~/.daily-recipe-cli`。使用 `tests/test_storage.py` 中的 `data_dir` fixture 模式：`monkeypatch.setenv("RECIPE_CLI_DIR", str(tmp_path))`。

## 语言与提交约定

- **代码注释、模块 docstring、用户可见输出、文档一律中文**（用户可见输出尤其如此，见上）。
- **提交信息用中文**，保留 Conventional Commits 前缀风格（`feat:` / `fix:` / `docs:` / `test:` / `refactor:`），标题用中文概括改动。例如：`feat: 新增周计划命令`、`fix: 处理非交互场景下 week 确认的 EOF`。
- 用户可见行为变更需在 `CHANGELOG.md` 追加条目（中文）。

## 改动前先读的文档

- `README.md` — 用法与产品概述。
- `specs/001-daily-recipe-cli/contracts/data-schema.md` — 数据契约（见上）。
- `specs/001-daily-recipe-cli/spec.md` 与 `tasks.md` — 需求与任务拆解。
- `CHANGELOG.md` — 变更历史；用户可见变更需追加条目。
