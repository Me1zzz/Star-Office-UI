## Why

Star-Office-UI 当前已经能聚合本机 `opencode.db` 并展示运行态，但仍然依赖 `office-agent-push.py` 主动把 agent 注册进办公室。这导致用户必须手工为每个 agent 建立接入链路，无法直接把“本机正在运行的 opencode 会话树”自然投影到办公室视图里，也无法把“root session 及其 child / grandchild session”稳定转化为自动生成的 office 对象与运行关系。

## What Changes

- 新增本机 opencode 自动监听能力，后端可自动扫描/订阅当前工作区相关的本地 session 树，而不再要求每个 agent 主动 push。
- 新增本地 session watcher 读模型，按 `sessionId -> rootSessionId -> office` 路由规则，将 root session、child session、tool delegation、background task 等信息归一成可显示的 synthetic office agents。
- 新增 room/materialization 规则，明确 **一个 root session = 一个 office**，child / grandchild session 默认继承该 office，而不是按 agent 名称或 session title 分组。
- 新增自动发现与自动生成的状态缓存、推导规则与回收规则，用于避免 agent 对象抖动与错误拆分。
- 保留现有主动 push 模式作为兼容路径，但 watcher 模式将成为查看本机 opencode 运行态的首选方案。

## Capabilities

### New Capabilities
- `opencode-local-watcher`: 监听本机 opencode session/message/part/event 数据，并按会话树自动发现运行对象。
- `synthetic-office-agents`: 将 root session 及其 lineage 自动物化为办公室内的 synthetic agents，而无需手动 join/push。
- `room-isolation-model`: 定义 root session、office、child session、project/workspace 过滤之间的隔离与归属规则。

### Modified Capabilities
- `agent-runtime-overview`: 总览层不再只展示显式加入的 agent，还需要展示 watcher 自动发现的 synthetic agents。
- `agent-runtime-adapter`: 运行态适配层从“被动消费 push 元数据”扩展为“主动发现 + 被动融合”双通道模式。

## Impact

- 后端：`backend/agent_runtime_utils.py`、`backend/runtime_routes.py`、`backend/app.py` 及新增本地 watcher/service/cache 模块。
- 前端：`frontend/index.html`、`frontend/runtime-inspector.js`、`frontend/runtime-game-bridge.js` 的总览数据来源、office 切换与 synthetic agent 展示逻辑。
- 数据源：本机 `opencode.db`、OpenCode 官方 session/children/message 与 project/global SSE 数据面、可选 OMO 补充信息。
- 行为变化：从“agent 主动 push 才可见”扩展为“本地 opencode root session 可自动生成办公室对象”，同时保留 push 兼容模式。
