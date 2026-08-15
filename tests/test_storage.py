"""存储层测试：读写、原子性、首次初始化与非法数据处理。"""

from __future__ import annotations

import json
import os

import pytest

from daily_recipe_cli import storage
from daily_recipe_cli.storage import DataError, save_json


@pytest.fixture()
def data_dir(tmp_path, monkeypatch):
    """隔离的数据目录，避免污染真实用户数据。"""
    monkeypatch.setenv("RECIPE_CLI_DIR", str(tmp_path))
    return tmp_path


def test_save_and_load_roundtrip(data_dir):
    path = storage.recipes_path()
    data = [
        {"name": "番茄牛腩", "ingredients": ["牛腩"], "tags": ["荤"], "note": ""}
    ]
    save_json(path, data)
    assert storage.load_json(path) == data


def test_load_json_missing_file_returns_none(data_dir):
    assert storage.load_json(storage.recipes_path()) is None


def test_load_json_invalid_content_raises_chinese_error(data_dir):
    path = storage.recipes_path()
    path.write_text("{ not json", encoding="utf-8")
    with pytest.raises(DataError, match="不是有效的 JSON"):
        storage.load_json(path)


def test_save_json_creates_parent_dirs(data_dir):
    nested = storage.data_dir() / "a" / "b" / "x.json"
    save_json(nested, [])
    assert nested.exists()
    assert storage.load_json(nested) == []


def test_first_run_copies_default_recipes(data_dir):
    recipes = storage.load_recipes()
    assert len(recipes) >= 12
    assert all(r["name"] and r["ingredients"] and r["tags"] for r in recipes)
    # 源文件未被破坏，用户文件独立存在
    assert storage.recipes_path().exists()
    assert storage.default_recipes_path().exists()


def test_validate_recipes_top_level_must_be_array(data_dir):
    with pytest.raises(DataError, match="顶层应为数组"):
        storage.validate_recipes({"name": "x"})


def test_validate_recipes_requires_name(data_dir):
    with pytest.raises(DataError, match="缺少有效的「菜名」"):
        storage.validate_recipes([{"ingredients": ["a"], "tags": ["荤"]}])


def test_validate_recipes_duplicate_name(data_dir):
    item = {"name": "A", "ingredients": ["a"], "tags": ["荤"]}
    with pytest.raises(DataError, match="重复出现"):
        storage.validate_recipes([item, dict(item)])


def test_validate_recipes_duplicate_name_case_insensitive(data_dir):
    item = {"name": "A", "ingredients": ["a"], "tags": ["荤"]}
    other = dict(item, name="a")
    with pytest.raises(DataError, match="重复出现"):
        storage.validate_recipes([item, other])


def test_validate_recipes_bad_ingredients(data_dir):
    item = {"name": "A", "ingredients": [], "tags": ["荤"]}
    with pytest.raises(DataError, match="主要食材"):
        storage.validate_recipes([item])


def test_validate_recipes_bad_tags(data_dir):
    item = {"name": "A", "ingredients": ["a"], "tags": []}
    with pytest.raises(DataError, match="标签"):
        storage.validate_recipes([item])


def test_validate_history_bad_date(data_dir):
    with pytest.raises(DataError, match="日期"):
        storage.validate_history([{"date": "2026-13-40", "recipe": "x", "source": "today"}])


def test_validate_history_duplicate_date(data_dir):
    item = {"date": "2026-08-15", "recipe": "x", "source": "today"}
    with pytest.raises(DataError, match="重复出现"):
        storage.validate_history([item, dict(item)])


def test_validate_history_bad_source(data_dir):
    with pytest.raises(DataError, match="来源"):
        storage.validate_history([{"date": "2026-08-15", "recipe": "x", "source": "hack"}])


def test_load_history_missing_returns_empty(data_dir):
    assert storage.load_history() == []


def test_save_failure_cleans_temp_and_keeps_target(data_dir):
    """os.replace 失败（目标为目录）时临时文件被清理、目标不受影响。"""
    target = storage.data_dir() / "x.json"
    target.mkdir()
    (target / "keep.txt").write_text("keep", encoding="utf-8")
    with pytest.raises(OSError):
        save_json(target, [1, 2, 3])
    assert (target / "keep.txt").read_text(encoding="utf-8") == "keep"
    leftovers = list(storage.data_dir().glob("x.json.*.tmp"))
    assert leftovers == []
