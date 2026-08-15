"""数据存储层：数据目录解析、JSON 读写、原子写入与数据校验。

所有命令的入口统一通过本模块加载数据，保证非法数据在任何命令下
都以中文错误暴露，而不是静默容错或崩溃。
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_DATA_DIR = "~/.daily-recipe-cli"
RECIPES_FILE = "recipes.json"
HISTORY_FILE = "history.json"

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class DataError(Exception):
    """数据文件非法或缺失时的业务错误，message 为中文说明。"""


def data_dir() -> Path:
    """返回用户数据目录；RECIPE_CLI_DIR 环境变量存在时优先。"""
    env = os.environ.get("RECIPE_CLI_DIR")
    return Path(env).expanduser() if env else Path(DEFAULT_DATA_DIR).expanduser()


def default_recipes_path() -> Path:
    """返回包内捆绑的初始食谱库路径。"""
    return Path(__file__).parent / "data" / "default_recipes.json"


def recipes_path() -> Path:
    return data_dir() / RECIPES_FILE


def history_path() -> Path:
    return data_dir() / HISTORY_FILE


def load_json(path: Path) -> Any:
    """读取 JSON 文件；文件不存在返回 None，内容非法抛 DataError。"""
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise DataError(f"数据文件 {path.name} 不是有效的 JSON（第 {e.lineno} 行）") from e


def save_json(path: Path, data: Any) -> None:
    """原子写入：先写临时文件再替换，避免中途失败损坏原数据。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=path.parent, prefix=f"{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def load_recipes() -> list[dict]:
    """加载并校验食谱库；首次运行自动从包内初始库拷贝。"""
    path = recipes_path()
    if not path.exists():
        _init_default_recipes(path)
    data = load_json(path)
    return validate_recipes(data)


def _init_default_recipes(path: Path) -> None:
    src = default_recipes_path()
    if not src.exists():
        raise DataError(f"缺少包内初始食谱库 {src.name}，无法初始化")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(src, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise DataError(f"初始食谱库 {src.name} 损坏（第 {e.lineno} 行）") from e
    save_json(path, data)


def load_history() -> list[dict]:
    """加载并校验历史记录；不存在时视为空。"""
    path = history_path()
    if not path.exists():
        return []
    data = load_json(path)
    return validate_history(data)


def validate_recipes(data: Any) -> list[dict]:
    """校验 recipes.json 结构；非法时抛 DataError（含定位）。"""
    if not isinstance(data, list):
        raise DataError(f"食谱库格式错误：顶层应为数组")
    seen: set[str] = set()
    for i, item in enumerate(data):
        idx = i + 1
        if not isinstance(item, dict):
            raise DataError(f"食谱库格式错误：第 {idx} 条应为对象")
        name = item.get("name")
        if not isinstance(name, str) or not name.strip():
            raise DataError(f"食谱库格式错误：第 {idx} 条缺少有效的「菜名」")
        name = name.strip()
        if len(name) > 30:
            raise DataError(f"食谱库格式错误：第 {idx} 条菜名「{name}」超过 30 字符")
        key = name.lower()
        if key in seen:
            raise DataError(f"食谱库格式错误：菜名「{name}」重复出现")
        seen.add(key)
        ingredients = item.get("ingredients")
        if (
            not isinstance(ingredients, list)
            or not ingredients
            or not all(isinstance(x, str) and x.strip() for x in ingredients)
        ):
            raise DataError(f"食谱库格式错误：第 {idx} 条（{name}）的「主要食材」无效")
        tags = item.get("tags")
        if (
            not isinstance(tags, list)
            or not tags
            or not all(isinstance(x, str) and x.strip() for x in tags)
        ):
            raise DataError(f"食谱库格式错误：第 {idx} 条（{name}）的「标签」无效")
        note = item.get("note", "")
        if not isinstance(note, str):
            raise DataError(f"食谱库格式错误：第 {idx} 条（{name}）的「做法」无效")
        item["name"] = name
        item["note"] = note
    return data


def validate_history(data: Any) -> list[dict]:
    """校验 history.json 结构；非法时抛 DataError（含定位）。"""
    if not isinstance(data, list):
        raise DataError(f"历史记录格式错误：顶层应为数组")
    seen: set[str] = set()
    for i, item in enumerate(data):
        idx = i + 1
        if not isinstance(item, dict):
            raise DataError(f"历史记录格式错误：第 {idx} 条应为对象")
        date = item.get("date")
        if not isinstance(date, str) or not _valid_date(date):
            raise DataError(f"历史记录格式错误：第 {idx} 条日期「{date}」无效")
        if date in seen:
            raise DataError(f"历史记录格式错误：日期「{date}」重复出现")
        seen.add(date)
        recipe = item.get("recipe")
        if not isinstance(recipe, str) or not recipe.strip():
            raise DataError(f"历史记录格式错误：第 {idx} 条缺少菜名")
        source = item.get("source")
        if source not in ("today", "week"):
            raise DataError(f"历史记录格式错误：第 {idx} 条来源「{source}」无效")
    return data


def _valid_date(s: str) -> bool:
    if not _DATE_RE.match(s):
        return False
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return True
    except ValueError:
        return False
