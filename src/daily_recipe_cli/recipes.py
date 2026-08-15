"""食谱库业务操作：添加、删除、按标签过滤、查重。"""

from __future__ import annotations

from daily_recipe_cli import storage
from daily_recipe_cli.storage import DataError


def add(name: str, ingredients: list[str], tags: list[str], note: str = "") -> dict:
    """添加食谱；菜名重复（大小写不敏感）抛 DataError。"""
    recipes = storage.load_recipes()
    name = name.strip()
    if any(r["name"].lower() == name.lower() for r in recipes):
        raise DataError(f"食谱已存在：{name}")
    new = {
        "name": name,
        "ingredients": list(ingredients),
        "tags": list(tags),
        "note": note,
    }
    recipes.append(new)
    storage.validate_recipes(recipes)
    storage.save_json(storage.recipes_path(), recipes)
    return new


def remove(name: str) -> dict | None:
    """删除食谱；不存在返回 None。不影响历史记录（历史存菜名快照）。"""
    recipes = storage.load_recipes()
    lowered = name.lower()
    target = next((r for r in recipes if r["name"].lower() == lowered), None)
    if target is None:
        return None
    remaining = [r for r in recipes if r["name"].lower() != lowered]
    storage.save_json(storage.recipes_path(), remaining)
    return target


def filter_by_tags(recipes: list[dict], tags: list[str]) -> list[dict]:
    """按标签过滤；条件可叠加（须同时满足）。空条件返回全部。"""
    tag_set = set(tags)
    if not tag_set:
        return recipes
    return [r for r in recipes if tag_set <= set(r["tags"])]
