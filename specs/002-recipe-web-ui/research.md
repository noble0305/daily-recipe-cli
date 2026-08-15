# 技术调研：页面化访问（recipe-web-ui）

**日期**: 2026-08-15
**规格**: [spec.md](./spec.md)
**目的**: 解决 Phase 0 的核心未知——如何在「仅标准库 + 零常驻服务 + 本机浏览器打开页面 + 复用 Python 核心逻辑」四重约束下，让页面能查看与操作本地 JSON 数据。

---

## 决策 1：页面承载方式 — 本地一次性 HTTP 服务（方案 B）

**Decision**: 新增 `recipe serve` 子命令，用标准库 `http.server.ThreadingHTTPServer` 起「本机一次性 HTTP 服务」，仅监听 `127.0.0.1` 回环地址 + 随机空闲端口，用 `webbrowser.open()`（标准库）自动打开浏览器；页面通过 JSON API 调用现有 Python 核心模块；用完即停（页面关闭 → 服务退出，另设空闲超时兜底）。

**Rationale**:
- **复用 Python 核心逻辑**：`recommend.candidates()` / `week_plan()` 是纯函数，`history.add()` / `recipes_mod.add/remove()` 直接读写存储——API handler 只做拼接，正是「新增页面交互层、不重写业务逻辑」的准确落点；可复现性（种子默认当天日期）由服务端保持，行为与 CLI 完全一致。
- **仅标准库**：`http.server` / `webbrowser` / `socket` / `threading` / `importlib.resources` 均为 Python 3.11 标准库，`pyproject.toml` 的 `dependencies = []` 不受影响。
- **零常驻**：`recipe serve` 是用户显式调用的前台一次性命令，生命周期与一次使用会话绑定（浏览器关闭即退出），不是守护进程、不后台常驻、不开机自启；语义与 CLI 命令等价，只是输出端从终端换成浏览器。
- **完全离线 + 零安装**：仅监听回环地址，局域网/互联网均不可达；无需浏览器插件或系统组件。

**Alternatives considered**:
- **方案 A（纯 file:// 静态 HTML + fetch 读本地 JSON）— 不可行**：CORS 仅支持 http/https scheme；file:// 页面被视为不透明 origin（null），Chrome/Safari/Firefox 均默认阻止 fetch 读本地 JSON（MDN《CORSRequestNotHttp》）；即使能读，写回也无任何通道。
- **方案 C（生成静态 HTML 内嵌数据，`recipe page` 每次重新生成）— 只读可行、写回无路**：读取侧可行且零服务；写回侧三条路全不通——无服务端即无写回通道；File System Access API 仅 Chrome/Edge 86+ 支持（Firefox/Safari 不支持），且 JS 改写 JSON 会绕过 `storage.validate_*` / `DataError` / 原子写入契约（违反复用硬约束）；下载 JSON 手工放回不现实。可作 B 的降级只读模式（`recipe page --static`），非完整方案。
- **方案 D 组（CGI / WebSocket / Pyodide / 自定义 URL scheme）— 均不成立或退化为 B**：CGI 本质仍需起 `http.server`（=B 的劣化版）；WebSocket 仍需服务端进程且标准库无 WS 实现（过度工程）；Pyodide 引入第三方运行时依赖 + 大文件下载（双重违规）；自定义 scheme 需系统级注册（违反零安装）。

**结论**: B 是唯一解——file:// 直读被浏览器 CORS 封死，内嵌数据写回无解，其余方案要么退化为 B 要么违反宪法。

---

## 决策 2：API 形态 — JSON 端点 + 中文错误语义

**Decision**: 服务提供两类内容：一个嵌入包内的单页 HTML/JS（渲染层，零业务逻辑）+ 一组 JSON API 端点。

| 端点 | 方法 | 作用 | 复用模块 |
|---|---|---|---|
| `/api/state` | GET | 食谱库 + 历史 + 今日是否已确定 | `storage.load_recipes()` / `load_history()` / `history.decided_for_date()` |
| `/api/today` | POST | 候选生成 / 确认选择 | `recommend.candidates()` + `history.add()` |
| `/api/week` | POST | 周计划预览 / 写入 | `recommend.week_plan()` + `history.add()` |
| `/api/add` | POST | 添加食谱 | `recipes.add()` |
| `/api/remove` | POST | 删除食谱 | `recipes.remove()` |
| `/api/history` | GET | 历史查询（含来源标注） | 历史查询逻辑 |
| `/api/bye` | POST | 用完即停（关闭服务） | —（生命周期） |

**Rationale**: `DataError` 统一转 HTTP 400 + 中文消息，沿用 `cli.py` 中 `main()` 的中文错误输出约定；周计划确认语义从 `input()` 变为前端按钮，与 CLI 的 EOFError 处理（非交互视为「否」）语义一致——页面上的确认本来就是显式点击。

**Alternatives considered**: 表单 POST + CGI 输出解析（丑陋、劣化）；WebSocket（过度工程，标准库无实现）。

---

## 决策 3：生命周期与并发安全

**Decision**:
- **用完即停**：前端在 `pagehide`/`beforeunload` 时发 `POST /api/bye`（或 `navigator.sendBeacon`），服务端收到后 `server.shutdown()` 退出进程；另设空闲超时兜底（10 分钟无请求自动退出）+ 终端 Ctrl+C；进程退出后端口立即释放，无残留。
- **并发安全**：handler 层加 `threading.Lock`（标准库）串行化写操作，配合 `storage.save_json` 已有的原子写入（先写 `.tmp` 再 `os.replace()`），保证数据契约不被并发破坏。

**Rationale**: 满足「零常驻」；写操作串行化 + 原子写入双保险，与 `contracts/data-schema.md` 保持一致。

**Alternatives considered**: 无锁直写（违反数据契约的原子性保证）；每次请求重建数据（性能差且非原子）。

---

## 决策 4：HTML 渲染层 — 内嵌单页、零业务逻辑

**Decision**: 单页 HTML 内嵌到包资源（`importlib.resources` 读取），由 `/api/state` 渲染初始状态，所有操作走 JSON API；页面只做展示与表单，不含任何推荐/校验/历史逻辑（由服务端 Python 核心模块承担）。

**Rationale**: 保证「业务逻辑只维护一份」（宪法 IV）；页面刷新后状态从数据文件重新加载，天然保持「刷新不丢失」（spec 边界情况）。

**Alternatives considered**: 页面内嵌数据（方案 C，写回无路）；页面复制业务逻辑（宪法 IV 违规）。

---

## 已解决的不确定项

| 原未知项 | 结论 |
|---|---|
| 页面访问形态（file:// vs 本地服务） | `recipe serve` 一次性回环 HTTP 服务（浏览器 CORS 使 file:// 不可行） |
| 页面与 CLI 共享方式 | 复用现有 Python 核心模块（API handler 仅拼接），页面零业务逻辑 |
| 写并发安全 | `threading.Lock` 串行化 + 既有原子写入 |
| 服务生命周期 | 页面关闭即退出（/api/bye + sendBeacon）+ 10 分钟空闲超时 + Ctrl+C |
| 端口选择 | 随机空闲端口（`socket.bind(0)`），避免占用冲突 |
