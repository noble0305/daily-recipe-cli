"""页面化访问：本地一次性 HTTP 服务。

`recipe serve` 启动本服务：仅监听 127.0.0.1 回环地址 + 随机端口，
自动打开浏览器。页面（static/index.html）是渲染层，零业务逻辑；
所有操作经本模块的 JSON API 调用现有核心模块（storage / recipes /
history / recommend），与 CLI 行为完全一致（constitution 原则 III/IV）。

生命周期：页面关闭（/api/bye）→ 服务退出；空闲超时兜底；Ctrl+C 可退。
"""

from __future__ import annotations

import importlib.resources
import json
import socket
import threading
import webbrowser
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse, parse_qs

from daily_recipe_cli import history, recipes, recommend, storage
from daily_recipe_cli.storage import DataError

# 空闲超时（秒）：超过后自动退出，防止遗留进程
DEFAULT_IDLE_TIMEOUT = 600

# 写操作串行化：所有会修改数据文件的请求共用一把锁
_write_lock = threading.Lock()

# 供 serve() 与 handler 通信的空闲监控
_idle_timeout = DEFAULT_IDLE_TIMEOUT
_last_request_at = threading.Event()


class _Handler(BaseHTTPRequestHandler):
    """API 路由：GET /、/api/state、/api/history；POST /api/*。"""

    server_version = "recipe-web-ui/0.1"

    # ------------------------------------------------------------------
    # 生命周期与通用
    # ------------------------------------------------------------------

    def _touch(self) -> None:
        """刷新空闲监控：每次请求重置超时计时。"""
        _last_request_at.set()

    def log_message(self, fmt: str, *args: Any) -> None:  # 静默访问日志
        pass

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_ok(self, data: Any) -> None:
        self._send_json(200, {"ok": True, "data": data})

    def _send_error(self, message: str, status: int = 400) -> None:
        self._send_json(status, {"ok": False, "error": message})

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            raise DataError("请求体不是合法的 JSON")
        return parsed if isinstance(parsed, dict) else {}

    # ------------------------------------------------------------------
    # 路由
    # ------------------------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802（http.server 约定命名）
        self._touch()
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/":
                self._serve_page()
            elif parsed.path == "/api/state":
                self._api_state()
            elif parsed.path == "/api/history":
                self._api_history(parse_qs(parsed.query))
            else:
                self._send_error("未知接口", 404)
        except DataError as e:
            self._send_error(str(e))
        except Exception as e:  # 兜底：不把异常栈暴露给页面
            self._send_error(f"服务内部错误：{e}", 500)

    def do_POST(self) -> None:  # noqa: N802
        self._touch()
        parsed = urlparse(self.path)
        try:
            body = self._read_body()
            if parsed.path == "/api/today":
                self._api_today(body)
            elif parsed.path == "/api/week":
                self._api_week(body)
            elif parsed.path == "/api/add":
                self._api_add(body)
            elif parsed.path == "/api/remove":
                self._api_remove(body)
            elif parsed.path == "/api/bye":
                self._api_bye()
            else:
                self._send_error("未知接口", 404)
        except DataError as e:
            self._send_error(str(e))
        except Exception as e:
            self._send_error(f"服务内部错误：{e}", 500)

    # ------------------------------------------------------------------
    # 页面与状态
    # ------------------------------------------------------------------

    def _serve_page(self) -> None:
        html = importlib.resources.files("daily_recipe_cli").joinpath(
            "static/index.html"
        ).read_text(encoding="utf-8")
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _api_state(self) -> None:
        today = date.today().isoformat()
        decided = history.decided_for_date(today)
        self._send_ok(
            {
                "today": {
                    "decided": decided is not None,
                    "decidedRecipe": decided,
                    "candidates": None,
                    "reason": None,
                },
                "recipes": storage.load_recipes(),
                "historyDays": 30,
            }
        )

    # ------------------------------------------------------------------
    # 今日推荐（US1）
    # ------------------------------------------------------------------

    def _api_today(self, body: dict) -> None:
        action = body.get("action")
        today = date.today()

        with _write_lock:  # 写操作串行化，防止并发破坏数据契约
            if action == "recommend":
                self._today_recommend(body, today)
            elif action == "confirm":
                self._today_confirm(body, today)
            elif action == "force":
                self._today_recommend(body, today, force=True)
            else:
                self._send_error("action 必须是 recommend / confirm / force")

    def _today_recommend(self, body: dict, today: date, force: bool = False) -> None:
        decided = history.decided_for_date(today.isoformat())
        if decided and not force:
            self._send_ok(
                {
                    "candidates": None,
                    "reason": None,
                    "decided": True,
                    "decidedRecipe": decided,
                    "forceAvailable": True,
                }
            )
            return

        cands, widened = recommend.candidates(
            storage.load_recipes(),
            storage.load_history(),
            today,
            tags=body.get("tags"),
            days=body.get("days", 7),
            count=body.get("count", 3),
            seed=body.get("seed"),
        )
        if not cands:
            total = len(storage.load_recipes())
            if total == 0:
                raise DataError("食谱库为空：请先添加食谱")
            raise DataError("可选菜不足：近期吃过的菜较多，可添加新菜或缩短去重窗口")
        hint = "已放宽去重窗口，近期吃过的菜也可能出现" if widened else f"避开最近 {body.get('days', 7)} 天已选"
        self._send_ok(
            {
                "candidates": cands,
                "reason": hint,
                "decided": False,
                "decidedRecipe": None,
                "forceAvailable": False,
            }
        )

    def _today_confirm(self, body: dict, today: date) -> None:
        decided = history.decided_for_date(today.isoformat())
        if decided and "choice" not in body:
            self._send_ok(
                {
                    "candidates": None,
                    "decided": True,
                    "decidedRecipe": decided,
                    "forceAvailable": True,
                }
            )
            return
        choice = body.get("choice")
        if not isinstance(choice, int) or choice < 1:
            raise DataError("序号无效：请提供要确认的候选序号（从 1 开始）")
        # 重新生成候选（与 CLI 一致：confirm 基于当天候选）
        cands, _ = recommend.candidates(
            storage.load_recipes(),
            storage.load_history(),
            today,
            tags=body.get("tags"),
            days=body.get("days", 7),
            count=body.get("count", 3),
            seed=body.get("seed"),
        )
        if choice > len(cands):
            raise DataError(f"序号无效：当前有 {len(cands)} 个候选，没有第 {choice} 个")
        chosen = cands[choice - 1]
        history.add(today.isoformat(), chosen["name"], source="today")
        self._send_ok({"decided": True, "decidedRecipe": chosen["name"]})

    # ------------------------------------------------------------------
    # 周计划（US3）
    # ------------------------------------------------------------------

    def _api_week(self, body: dict) -> None:
        action = body.get("action")
        with _write_lock:
            if action == "preview":
                self._week_preview(body)
            elif action == "confirm":
                self._week_confirm(body)
            else:
                self._send_error("action 必须是 preview / confirm")

    def _week_plan(self, body: dict):
        return recommend.week_plan(
            storage.load_recipes(),
            storage.load_history(),
            date.today(),
            tags=body.get("tags"),
            days=body.get("days", 7),
            seed=body.get("seed"),
        )

    def _week_preview(self, body: dict) -> None:
        plan, relaxed = self._week_plan(body)
        self._send_ok(
            {
                "days": [
                    {"date": d.isoformat(), "recipe": r["name"] if r else None}
                    for d, r in plan
                ],
                "conflictCount": 0,
                "relaxed": relaxed,
            }
        )

    def _week_confirm(self, body: dict) -> None:
        plan, _ = self._week_plan(body)
        filled = [(d, r) for d, r in plan if r is not None]
        if not filled:
            raise DataError("食谱库为空或过滤条件下无可用菜，无法生成计划")
        for d, r in filled:
            history.add(d.isoformat(), r["name"], source="week")
        self._send_ok({"written": len(filled)})

    # ------------------------------------------------------------------
    # 食谱库（US2）
    # ------------------------------------------------------------------

    def _api_add(self, body: dict) -> None:
        name = body.get("name")
        ingredients = body.get("ingredients")
        tags = body.get("tags")
        if not name or not isinstance(ingredients, list) or not isinstance(tags, list):
            raise DataError("参数缺失：需要菜名、主要食材列表与标签列表")
        with _write_lock:
            new = recipes.add(name, ingredients, tags, body.get("note", ""))
        self._send_ok({"recipe": new})

    def _api_remove(self, body: dict) -> None:
        name = body.get("name")
        if not name:
            raise DataError("参数缺失：需要菜名")
        with _write_lock:
            target = recipes.remove(name)
        if target is None:
            raise DataError(f"未找到食谱：{name}")
        self._send_ok({"removed": target["name"]})

    # ------------------------------------------------------------------
    # 历史（US4）与生命周期
    # ------------------------------------------------------------------

    def _api_history(self, query: dict) -> None:
        try:
            days = int(query.get("days", ["30"])[0])
        except ValueError:
            raise DataError("days 必须是正整数")
        entries = storage.load_history()
        cutoff = date.today() - timedelta(days=days)
        shown = sorted(
            (e for e in entries if date.fromisoformat(e["date"]) >= cutoff),
            key=lambda e: e["date"],
            reverse=True,
        )
        self._send_ok({"records": shown, "rangeDays": days})

    def _api_bye(self) -> None:
        """用完即停：前台页面关闭时通知服务退出。"""
        self._send_ok({"bye": True})
        threading.Thread(target=self.server.shutdown, daemon=True).start()


def serve(
    open_browser: bool = True,
    idle_timeout: int = DEFAULT_IDLE_TIMEOUT,
) -> ThreadingHTTPServer:
    """启动本地一次性 HTTP 服务，返回 httpd 实例（不阻塞）。

    - 仅监听 127.0.0.1 + 随机空闲端口
    - open_browser=True 时自动打开浏览器（测试传 False）
    - idle_timeout 秒无请求自动退出（0 表示禁用空闲超时）
    - 调用方负责 serve_forever() 与 server_close()（CLI 与测试各自处理）
    """
    global _idle_timeout
    _idle_timeout = idle_timeout

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    port = httpd.server_address[1]
    url = f"http://127.0.0.1:{port}/"

    if idle_timeout > 0:
        t = threading.Thread(target=_idle_watchdog, args=(httpd, idle_timeout), daemon=True)
        t.start()

    if open_browser:
        webbrowser.open(url)
        print(f"页面已打开：{url}")
        print("关闭浏览器标签页或按 Ctrl+C 退出服务。")

    return httpd


def _idle_watchdog(httpd: ThreadingHTTPServer, timeout: int) -> None:
    """空闲超时：timeout 秒内无请求则关闭服务（防遗留进程）。"""
    while True:
        _last_request_at.wait(timeout=timeout)
        if _last_request_at.is_set():
            _last_request_at.clear()
            continue
        # 超时未收到请求：退出
        try:
            httpd.shutdown()
        except Exception:
            pass
        return
