## Why

Star-Office-UI 当前的 watcher 模式已经能自动发现本机 opencode root session，但它默认仍然是 **current-project / current-directory scoped**。这意味着它无法清晰回答两个越来越常见的需求：第一，如何观察**单个 OpenCode server 实例中的全部 active root sessions**；第二，如何在未来扩展到**多 server 聚合**而不把 scope、office identity 和 server 边界混淆在一起。

## What Changes

- 新增 watcher scope 模型，显式支持 `current-project`、`one-server`、`multi-server-aggregate` 三档范围。
- 新增 scope-aware watcher 语义，明确不同 scope 下的 discovery、filter、office materialization 和 selector 行为。
- 新增 server-origin / scope-origin 建模，避免在 multi-server 模式下出现 session/project/path 冲突。
- 扩展前端 selector 设计，使其能区分 scope 选择、project/workspace 分组和 root-session office 选择三层导航。
- 保持当前 `current-project` 为默认行为，并将 `one-server` 作为下一步最优先实现目标；`multi-server-aggregate` 作为明确的 app-level aggregator 方案进行设计。

## Capabilities

### New Capabilities
- `watcher-scope-modes`: 定义 current-project、one-server、multi-server-aggregate 三档 watcher 范围及其行为语义。
- `server-origin-model`: 定义单 server 与多 server 聚合时的 origin、namespace 与冲突隔离规则。
- `scope-aware-office-selector`: 定义前端如何按 scope、project/workspace、root-session office 三层维度组织与切换视图。

### Modified Capabilities
- `opencode-local-watcher`: 从默认 current-project watcher 扩展为可配置的 scope-aware watcher。
- `room-isolation-model`: 在保持 root session = office 的前提下，明确 office identity、scope boundary 和 server boundary 的关系。
- `agent-runtime-overview`: 总览层需要支持跨 scope / 跨 project / 跨 server 的 synthetic office 展示与切换。

## Impact

- 后端：`backend/opencode_local_watcher.py`、`backend/runtime_routes.py`、`backend/app.py`，以及新增 watcher scope/config/aggregator 模块。
- 前端：`frontend/runtime-inspector.js`、`frontend/runtime-game-bridge.js`、`frontend/index.html` 的 office selector 和 synthetic office 列表交互。
- 文档：watcher SOP、用户手册、实现说明需要补充 scope 模式、默认边界与多 server 限制说明。
- 系统语义：从“当前项目的自动 watcher”升级为“具有显式 watcher scope 模型的观察系统”，同时明确 multi-server aggregate 属于应用层聚合能力而非现有 OpenCode server 的默认保证。
