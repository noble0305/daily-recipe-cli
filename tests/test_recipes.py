"""食谱库操作测试：添加（重名提示）、列表、删除、标签过滤。"""

from __future__ import annotations

import pytest

from daily_recipe_cli import recipes, storage
from daily_recipe_cli.storage import DataError


@pytest.fixture()
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("RECIPE_CLI_DIR", str(tmp_path))
    return tmp_path


def test_add_appears_in_library(data_dir):
    recipes.add("自创新菜", ["鸡腿", "香菇"], ["荤", "快手"], "香菇蒸鸡腿")
    names = [r["name"] for r in storage.load_recipes()]
    assert "自创新菜" in names


def test_add_duplicate_raises(data_dir):
    recipes.add("A", ["a"], ["荤"], "")
    with pytest.raises(DataError, match="已存在"):
        recipes.add("A", ["b"], ["素"], "")


def test_add_duplicate_case_insensitive_raises(data_dir):
    recipes.add("自定义菜", ["a"], ["荤"], "")
    with pytest.raises(DataError, match="已存在"):
        recipes.add("自定义菜", ["a"], ["荤"], "")


def test_remove_deletes_recipe(data_dir):
    recipes.add("A", ["a"], ["荤"], "")
    assert recipes.remove("A") is not None
    assert "A" not in [r["name"] for r in storage.load_recipes()]


def test_remove_missing_returns_none(data_dir):
    assert recipes.remove("不存在的菜") is None


def test_remove_does_not_touch_history(data_dir):
    from daily_recipe_cli import history

    recipes.add("A", ["a"], ["荤"], "")
    history.add("2026-08-14", "A", source="today")
    recipes.remove("A")
    entries = storage.load_history()
    assert len(entries) == 1
    assert entries[0]["recipe"] == "A"


def test_filter_by_tags_single(data_dir):
    pool = [
        {"name": "A", "tags": ["荤", "快手"], "ingredients": [], "note": ""},
        {"name": "B", "tags": ["素", "快手"], "ingredients": [], "note": ""},
    ]
    result = recipes.filter_by_tags(pool, ["素"])
    assert [r["name"] for r in result] == ["B"]


def test_filter_by_tags_multiple_requires_all(data_dir):
    pool = [
        {"name": "A", "tags": ["荤", "快手"], "ingredients": [], "note": ""},
        {"name": "B", "tags": ["素", "快手"], "ingredients": [], "note": ""},
    ]
    result = recipes.filter_by_tags(pool, ["快手", "素"])
    assert [r["name"] for r in result] == ["B"]


def test_filter_by_tags_empty_returns_all(data_dir):
    pool = [{"name": "A", "tags": ["荤"], "ingredients": [], "note": ""}]
    assert recipes.filter_by_tags(pool, []) == pool
