# Agent Runtime Visualization 实现说明

## 当前实现范围

- Star-Office-UI 已支持通过 `/runtime/overview` 与 `/runtime/agents/<identifier>` 输出统一运行态视图。
- `frontend/index.html` 已提供运行态检查器，支持 Summary / Thinking / Messages / Tools / Timeline / Raw JSON 六个标签页。
- `frontend/index.html` 与 `frontend/game.js` 都已支持点击运行对象进行选中与高亮。
- 后端可直接读取本机 `opencode.db`，从 `session / message / part` 表构建运行事件、子会话与委派关系。
- `office-agent-push.py` 已可在 join/push 时自动附带本地 runtime 元数据（如 sessionId / runId / parentRunId / projectId），并支持把 `rootSessionIdHint / officeIdHint / serverOrigin` 作为 lineage hints 一起上报。

## 低侵入结构说明

本次实现已尽量将新增能力放入新文件，原文件只保留必要挂载点：

- `backend/runtime_routes.py`：承载 runtime 相关响应构建逻辑
- `backend/agent_runtime_utils.py`：承载 runtime 聚合、opencode/OMO 融合与映射逻辑
- `frontend/runtime-inspector.js`：承载 `index.html` 对应的 runtime inspector 脚本逻辑
- `frontend/runtime-game-bridge.js`：承载 `game.js` 对应的 runtime overview / tooltip / selection 逻辑
- `frontend/runtime-inspector.css`：承载 runtime inspector 样式

原文件中仍然保留的改动，仅限于以下必须存在的挂载点：

- `backend/app.py`：保留 Flask 路由注册与少量委托调用
- `frontend/index.html`：保留 runtime inspector 的 DOM 容器、script/css 引用，以及访客列表中的桥接调用
- `frontend/game.js`：保留与现有渲染循环绑定的桥接调用
- `office-agent-push.py`：保留 runtime 上报入口

## 当前数据源优先级

1. watcher / session tree / 本机 `opencode.db` 提供 canonical lineage 事实
2. Agent 通过 `/join-agent` / `/agent-push` 上报的 `runtime` 元数据与 lineage hints
3. 现有 `state/detail` 快照兜底

## 已知限制

- 当前尚未真正接入 oh-my-openagent 的 `background_output`、`session_read`、`session_info` 等补充检索接口，仅预留了配置位与背景任务 ID 承载面。
- `backgroundTaskId ⇄ sessionId ⇄ rootSessionId ⇄ officeId ⇄ selectionKey` 的映射目前以运行时快照与 `runtime-mappings.json` 为主，尚未持久化为独立映射仓库。
- 状态不一致兜底校验目前主要依赖 opencode session 数据，尚未融合 OMO 的后台任务状态面。
- `frontend/game.js` 路径已接入 office-aware selection，但画布仍以轻量成员显示为主，不等同于 `index.html` 的完整 family browser。

## 回滚方式

如需回滚到旧行为，可按以下顺序进行：

1. 停止使用 `office-agent-push.py` 中的 `runtime` 上报字段。
2. 移除 `backend/app.py` 中的 `/runtime/overview`、`/runtime/agents/<identifier>`、`/runtime/mappings` 路由。
3. 移除 `backend/agent_runtime_utils.py` 及其导入。
4. 删除 `frontend/index.html` 中的 runtime inspector 面板与相关脚本状态。

## 后续建议

- 接入 oh-my-openagent 工具面，补齐 `background_output/session_read/session_info` 真实检索。
- 持久化 runtime 映射缓存，避免后端重启后 backgroundTaskId 与 sessionId 丢失关联。
- 增加端到端验证脚本，对 `/runtime/overview` 与 `/runtime/agents/<id>` 做快照断言。
- 将 `frontend/game.js` 路径进一步对齐 `index.html` 的 inspector 行为，避免双入口体验差异。

## add-opencode-local-watcher 当前批次说明

当前已实现第一、二批的核心基础能力：

- 后端已新增 `backend/runtime_lineage_resolver.py`，统一解析 `sessionId -> rootSessionId -> officeLocalId -> officeId`，为 watcher 与 explicit push 共享 canonical lineage 结果。
- `backend/agent_runtime_utils.py` 已升级为 office-aware runtime normalization，显式 runtime summary/detail 现在也会带 `serverOrigin / rootSessionId / officeLocalId / officeId / officeRole / lineage*` 字段。
- `/runtime/overview` 已开始输出 `offices + items` 双层读模型；`/runtime/agents/<identifier>` 已开始输出 `subject / office / lineage / item` 结构；`/runtime/mappings` 已新增 `lineageBySessionId`。
- 前端 selector 已切换为优先消费 `offices`，访客列表与 inspector 已开始以 office family 视角展示成员、ancestors / descendants / delegated lineage。

当前仍未完全完成的部分：

- Official OpenCode session/message/project-global SSE first 路径尚未完全取代 DB-first。
- project/global SSE 的本地增量过滤仍是下一批工作。
- 画布层当前仍以轻量 office member 可见性为主，尚未演化成完整 graph-native family canvas。

### 当前 watcher 开关

默认开启：

```text
STAR_OPENCODE_LOCAL_WATCHER=1
```

如需关闭 watcher，保留旧的显式 push 模式，可设置：

```powershell
$env:STAR_OPENCODE_LOCAL_WATCHER="0"
```

### 当前验证脚本

```powershell
python "backend/opencode_local_watcher_check.py"
python "backend/runtime_adapter_check.py"
python "backend/runtime_lineage_check.py"
```
