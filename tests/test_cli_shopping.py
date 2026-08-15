"""shopping-list 命令集成测试：CLI 输出、参数语义、空态与错误。

测试约定：用 RECIPE_CLI_DIR 指向临时目录（data_dir fixture），
绝不触碰真实 ~/.daily-recipe-cli。
"""

from __future__ import annotations

import datetime
import json

import pytest

from daily_recipe_cli import cli, storage


@pytest.fixture()
def data_dir(tmp_path, monkeypatch):
    """隔离的数据目录：recipes.json 与 history.json 均落在临时目录。"""
    monkeypatch.setenv("RECIPE_CLI_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture()
def seeded(data_dir):
    """预置食谱库与可控历史记录。"""
    recipes = [
        {"name": "番茄牛腩", "ingredients": ["牛腩", "番茄", "洋葱", "土豆"], "tags": ["荤", "费时"], "note": ""},
        {"name": "番茄炒蛋", "ingredients": ["番茄", "鸡蛋"], "tags": ["素", "快手"], "note": ""},
    ]
    storage.save_json(storage.recipes_path(), recipes)
    storage.save_json(storage.history_path(), [])
    return recipes


def run(args: list[str], capsys) -> tuple[int, str]:
    code = cli.main(args)
    captured = capsys.readouterr()
    return code, captured.out + captured.err


def _future_history(days_offsets: list[int], names: list[str]) -> None:
    """写入未来 offsets 天的历史记录（today 起第 offset 天）。"""
    today = datetime.date.today()
    entries = [
        {"date": (today + datetime.timedelta(days=offset)).isoformat(), "recipe": name, "source": "today"}
        for offset, name in zip(days_offsets, names)
    ]
    storage.save_json(storage.history_path(), entries)


def test_shopping_list_aggregates_and_merges(seeded, capsys):
    """默认聚合未来 7 天，去重合并并标注来源。"""
    _future_history([0, 1], ["番茄牛腩", "番茄炒蛋"])
    code, out = run(["shopping-list"], capsys)
    assert code == 0
    assert "番茄 ← 番茄牛腩、番茄炒蛋" in out  # 跨菜合并 + 来源标注
    assert "牛腩 ← 番茄牛腩" in out
    assert "鸡蛋 ← 番茄炒蛋" in out
    ingredient_lines = [l.strip() for l in out.splitlines() if " ← " in l]
    assert sum(1 for l in ingredient_lines if l.startswith("番茄 ←")) == 1  # 去重：番茄食材行只有一条


def test_shopping_list_empty_state(seeded, capsys):
    """空窗口：中文空态提示 + 指引，退出码 0。"""
    storage.save_json(storage.history_path(), [])
    code, out = run(["shopping-list"], capsys)
    assert code == 0
    assert "暂无已安排的菜" in out
    assert "today" in out and "week" in out  # 含命令指引


def test_shopping_list_today_only(seeded, capsys):
    """--today 只聚合今日。"""
    _future_history([0, 1], ["番茄牛腩", "番茄炒蛋"])
    code, out = run(["shopping-list", "--today"], capsys)
    assert code == 0
    assert "鸡蛋" not in out  # 第 1 天不在今日窗口
    assert "牛腩" in out


def test_shopping_list_days_param(seeded, capsys):
    """--days 自定义窗口。"""
    _future_history([0, 3], ["番茄牛腩", "番茄炒蛋"])
    code, out = run(["shopping-list", "--days", "3"], capsys)
    assert code == 0
    assert "鸡蛋" not in out  # 第 3 天超出 3 天窗口（含今日为第 0..2）
    assert "牛腩" in out


def test_shopping_list_no_merge(seeded, capsys):
    """--no-merge：同一食材按来源分别列出。"""
    _future_history([0, 1], ["番茄牛腩", "番茄炒蛋"])
    code, out = run(["shopping-list", "--no-merge"], capsys)
    assert code == 0
    assert out.count("番茄 ←") == 2  # 番茄各来源一条


def test_shopping_list_invalid_days(seeded, capsys):
    """--days 非正整数：中文错误，退出码 1。"""
    for bad in ("0", "-1"):
        code, out = run(["shopping-list", "--days", bad], capsys)
        assert code == 1
        assert "days" in out and "正整数" in out


def test_shopping_list_days_non_numeric(seeded, capsys):
    """--days 非数字：argparse 拦截，退出码 2。"""
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["shopping-list", "--days", "abc"])
    assert excinfo.value.code == 2


def test_shopping_list_skipped_recipe(seeded, capsys):
    """菜不在食谱库：跳过并提示，不影响其他菜。"""
    _future_history([0, 1], ["番茄牛腩", "不存在的菜"])
    code, out = run(["shopping-list"], capsys)
    assert code == 0
    assert "牛腩" in out
    assert "已跳过" in out and "不存在的菜" in out


def test_shopping_list_sorting(seeded, capsys):
    """输出按食材名排序（服务端确定性顺序）。"""
    _future_history([0], ["番茄牛腩"])
    code, out = run(["shopping-list"], capsys)
    assert code == 0
    lines = [l for l in out.splitlines() if " ← " in l]
    names = [l.split(" ← ")[0] for l in lines]
    assert names == sorted(names)
