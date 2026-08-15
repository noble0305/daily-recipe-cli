"""页面服务（server.py）测试：HTTP API 层。

测试约定：用 RECIPE_CLI_DIR 指向临时目录（与 test_storage.py 的
data_dir fixture 模式一致），绝不触碰真实 ~/.daily-recipe-cli。
"""

from __future__ import annotations

import http.client
import json
import threading
from datetime import date

import pytest

from daily_recipe_cli import storage, server


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    """隔离的数据目录：recipes.json 与 history.json 均落在临时目录。"""
    monkeypatch.setenv("RECIPE_CLI_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def seeded_library(data_dir):
    """预置一份稳定食谱库（3 道）与空历史，供各用例使用。"""
    recipes = [
        {"name": "番茄牛腩", "ingredients": ["牛腩", "番茄"], "tags": ["荤", "费时"], "note": "炖 1 小时"},
        {"name": "日式咖喱鸡", "ingredients": ["鸡腿肉", "土豆"], "tags": ["荤", "快手"], "note": "20 分钟"},
        {"name": "凉拌黄瓜", "ingredients": ["黄瓜"], "tags": ["素", "快手"], "note": "即拌即食"},
    ]
    storage.save_json(storage.recipes_path(), recipes)
    storage.save_json(storage.history_path(), [])
    return recipes


@pytest.fixture
def server_client(data_dir):
    """启动真实 HTTP 服务（随机端口），返回 (client, base_url)。

    测试不依赖浏览器：直接用 http.client 打 API。teardown 关闭服务。
    """
    httpd = server.serve(open_browser=False, idle_timeout=0)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    port = httpd.server_address[1]
    client = http.client.HTTPConnection("127.0.0.1", port, timeout=10)

    def _request(method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
        payload = json.dumps(body) if body is not None else None
        headers = {"Content-Type": "application/json"} if payload else {}
        client.request(method, path, body=payload, headers=headers)
        resp = client.getresponse()
        data = resp.read()
        try:
            parsed = json.loads(data) if data else {}
        except json.JSONDecodeError:
            parsed = {"raw": data.decode("utf-8", errors="replace")}
        return resp.status, parsed

    yield _request

    httpd.shutdown()
    thread.join(timeout=5)
    client.close()
    httpd.server_close()


def test_fixture_smoke(server_client, seeded_library):
    """冒烟：fixture 能起服务并请求首页。"""
    status, _ = server_client("GET", "/")
    assert status == 200


def test_state_returns_aggregate(server_client, seeded_library):
    """GET /api/state：返回食谱库、今日未确定。"""
    status, body = server_client("GET", "/api/state")
    assert status == 200
    data = body["data"]
    assert len(data["recipes"]) == 3
    assert data["today"]["decided"] is False
    assert data["today"]["decidedRecipe"] is None
    assert data["historyDays"] == 30


def test_state_decided_after_confirm(server_client, seeded_library):
    """今日确认后 /api/state 反映已确定状态（与 history 数据一致）。"""
    status, body = server_client("POST", "/api/today", {"action": "recommend"})
    assert status == 200
    choice = body["data"]["candidates"][0]["name"]
    status, body = server_client("POST", "/api/today", {"action": "confirm", "choice": 1})
    assert status == 200
    assert body["data"]["decidedRecipe"] == choice

    status, body = server_client("GET", "/api/state")
    assert body["data"]["today"]["decided"] is True
    assert body["data"]["today"]["decidedRecipe"] == choice


def test_state_broken_json_returns_400(server_client, data_dir):
    """数据文件损坏：/api/state 返回 400 中文错误，不崩溃不覆盖。"""
    import os

    from daily_recipe_cli import storage

    bad = data_dir / "recipes.json"
    bad.write_text("{ 这不是合法 JSON", encoding="utf-8")
    storage.save_json(storage.history_path(), [])

    status, body = server_client("GET", "/api/state")
    assert status == 400
    assert body["ok"] is False
    assert "recipes.json" in body["error"]
    # 数据文件未被覆盖
    assert bad.read_text(encoding="utf-8") == "{ 这不是合法 JSON"


def test_bye_shuts_down_server(server_client):
    """POST /api/bye：返回 bye 并触发服务关闭（线程随后退出）。"""
    status, body = server_client("POST", "/api/bye")
    assert status == 200
    assert body["data"]["bye"] is True


# ---------------------------------------------------------------------------
# US1 今日推荐（T008）
# ---------------------------------------------------------------------------

def test_today_recommend_returns_candidates(server_client, seeded_library):
    """recommend：返回 1~3 道候选与推荐理由。"""
    status, body = server_client("POST", "/api/today", {"action": "recommend"})
    assert status == 200
    data = body["data"]
    assert data["decided"] is False
    assert 1 <= len(data["candidates"]) <= 3
    assert "避开最近 7 天" in data["reason"]
    # 候选来自食谱库
    names = {r["name"] for r in seeded_library}
    assert all(c["name"] in names for c in data["candidates"])


def test_today_confirm_writes_history(server_client, seeded_library):
    """confirm：写入历史（source=today），/api/state 反映已确定。"""
    status, body = server_client("POST", "/api/today", {"action": "recommend"})
    first = body["data"]["candidates"][0]["name"]

    status, body = server_client("POST", "/api/today", {"action": "confirm", "choice": 1})
    assert status == 200
    assert body["data"]["decidedRecipe"] == first

    from daily_recipe_cli import storage
    entries = storage.load_history()
    assert len(entries) == 1
    assert entries[0]["recipe"] == first
    assert entries[0]["source"] == "today"
    assert entries[0]["date"] == date.today().isoformat()


def test_today_confirm_out_of_range_400(server_client, seeded_library):
    """confirm 越界序号：400 中文错误，不写历史。"""
    status, body = server_client("POST", "/api/today", {"action": "confirm", "choice": 99})
    assert status == 400
    assert "序号无效" in body["error"]

    from daily_recipe_cli import storage
    assert storage.load_history() == []


def test_today_force_overwrites(server_client, seeded_library):
    """已确定后 recommend 返回 forceAvailable；force 可重推并覆盖旧记录。"""
    server_client("POST", "/api/today", {"action": "recommend"})
    server_client("POST", "/api/today", {"action": "confirm", "choice": 1})

    # 已确定后再 recommend：提示已确定 + forceAvailable
    status, body = server_client("POST", "/api/today", {"action": "recommend"})
    assert status == 200
    assert body["data"]["decided"] is True
    assert body["data"]["forceAvailable"] is True

    # force 重推：候选重新出现，确认后当日记录被覆盖（仍 1 条）
    status, body = server_client("POST", "/api/today", {"action": "force"})
    assert status == 200
    assert body["data"]["decided"] is False
    status, body = server_client("POST", "/api/today", {"action": "confirm", "choice": 1})
    assert status == 200

    from daily_recipe_cli import storage
    entries = storage.load_history()
    assert len(entries) == 1  # 当日覆盖，不重复新增


def test_today_empty_library_400(server_client, data_dir):
    """食谱库为空：recommend 返回 400 中文提示。"""
    from daily_recipe_cli import storage
    storage.save_json(storage.recipes_path(), [])
    storage.save_json(storage.history_path(), [])

    status, body = server_client("POST", "/api/today", {"action": "recommend"})
    assert status == 400
    assert "食谱库为空" in body["error"]


# ---------------------------------------------------------------------------
# US2 食谱库（T012）
# ---------------------------------------------------------------------------

def test_add_recipe_success(server_client, seeded_library):
    """POST /api/add：添加成功并出现在 /api/state。"""
    status, body = server_client(
        "POST", "/api/add",
        {"name": "清蒸鲈鱼", "ingredients": ["鲈鱼", "姜"], "tags": ["荤", "快手"], "note": "水开后蒸 8 分钟"},
    )
    assert status == 200
    assert body["data"]["recipe"]["name"] == "清蒸鲈鱼"

    status, state = server_client("GET", "/api/state")
    assert any(r["name"] == "清蒸鲈鱼" for r in state["data"]["recipes"])


def test_add_duplicate_400(server_client, seeded_library):
    """重名添加：400「已存在」，不覆盖。"""
    status, body = server_client(
        "POST", "/api/add",
        {"name": "番茄牛腩", "ingredients": ["牛腩"], "tags": ["荤"]},
    )
    assert status == 400
    assert "已存在" in body["error"]

    status, state = server_client("GET", "/api/state")
    assert len(state["data"]["recipes"]) == 3


def test_remove_recipe_success(server_client, seeded_library):
    """POST /api/remove：删除成功且历史不受影响。"""
    from daily_recipe_cli import storage
    storage.save_json(storage.history_path(), [{"date": "2026-08-10", "recipe": "番茄牛腩", "source": "today"}])

    status, body = server_client("POST", "/api/remove", {"name": "番茄牛腩"})
    assert status == 200
    assert body["data"]["removed"] == "番茄牛腩"

    # 历史不受影响（菜名快照）
    entries = storage.load_history()
    assert len(entries) == 1
    assert entries[0]["recipe"] == "番茄牛腩"


def test_remove_missing_400(server_client, seeded_library):
    """删除不存在的菜：400 中文错误。"""
    status, body = server_client("POST", "/api/remove", {"name": "不存在的菜"})
    assert status == 400
    assert "未找到食谱" in body["error"]


# ---------------------------------------------------------------------------
# US3 周计划（T015）
# ---------------------------------------------------------------------------

def test_week_preview_returns_five_days(server_client, seeded_library):
    """preview：返回 5 个工作日、批内不重复、不写历史。"""
    status, body = server_client("POST", "/api/week", {"action": "preview"})
    assert status == 200
    data = body["data"]
    assert len(data["days"]) == 5
    recipes = [d["recipe"] for d in data["days"] if d["recipe"]]
    assert len(set(recipes)) == len(recipes)  # 批内不重复

    from daily_recipe_cli import storage
    assert storage.load_history() == []  # 预览不写入


def test_week_confirm_writes_five(server_client, seeded_library):
    """confirm：写入历史（每道可用菜一条，source=week，批内不重复）。

    注：预置库只有 3 道菜，5 个工作日中最多填满 3 天（窗口放宽到 0 后
    仍不足的天为 None，不写入）——这是 recommend.week_plan 的既定行为。
    """
    status, body = server_client("POST", "/api/week", {"action": "confirm"})
    assert status == 200
    assert body["data"]["written"] == 3  # 3 道菜 → 3 天

    from daily_recipe_cli import storage
    entries = storage.load_history()
    assert len(entries) == 3
    assert all(e["source"] == "week" for e in entries)
    assert len({e["recipe"] for e in entries}) == len(entries)  # 批内不重复


def test_week_empty_library_400(server_client, data_dir):
    """食谱库为空：confirm 返回 400 且不写入。"""
    from daily_recipe_cli import storage
    storage.save_json(storage.recipes_path(), [])
    storage.save_json(storage.history_path(), [])

    status, body = server_client("POST", "/api/week", {"action": "confirm"})
    assert status == 400
    assert "无法生成计划" in body["error"]
    assert storage.load_history() == []


# ---------------------------------------------------------------------------
# US4 历史（T018）
# ---------------------------------------------------------------------------

def test_history_default_30_days_desc(server_client, seeded_library):
    """GET /api/history：默认 30 天、按日期倒序、来源标注。"""
    from daily_recipe_cli import storage
    storage.save_json(storage.history_path(), [
        {"date": "2026-08-10", "recipe": "番茄牛腩", "source": "today"},
        {"date": "2026-08-12", "recipe": "日式咖喱鸡", "source": "week"},
        {"date": "2025-01-01", "recipe": "凉拌黄瓜", "source": "today"},  # 超窗，应被排除
    ])

    status, body = server_client("GET", "/api/history")
    assert status == 200
    data = body["data"]
    assert data["rangeDays"] == 30
    assert len(data["records"]) == 2
    assert [e["date"] for e in data["records"]] == ["2026-08-12", "2026-08-10"]  # 倒序
    assert data["records"][0]["source"] == "week"


def test_history_days_param(server_client, seeded_library):
    """days 参数生效：7 天窗口只保留窗口内记录。"""
    from daily_recipe_cli import storage
    storage.save_json(storage.history_path(), [
        {"date": "2026-08-10", "recipe": "番茄牛腩", "source": "today"},
        {"date": "2026-08-12", "recipe": "日式咖喱鸡", "source": "today"},
    ])

    status, body = server_client("GET", "/api/history?days=1")
    assert status == 200
    assert len(body["data"]["records"]) == 0  # 两天都在 1 天窗口外

    status, body = server_client("GET", "/api/history?days=7")
    assert len(body["data"]["records"]) == 2
