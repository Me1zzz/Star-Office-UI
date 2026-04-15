## Why

Star-Office-UI 已经在 watcher 路径上实现了“一个 root session = 一个 office”的核心语义，但显式 `/join-agent` / `/agent-push` 路径仍然主要是 actor/runtime 上报模型，尚未统一收敛到同一套 root-lineage office 规则。这导致同一个 root session family 的 child / grandchild / delegated sessions 在系统中仍然存在“部分在同一 office、部分只在 detail/edge 中可见、部分无法被 canonical 归并”的结构性不一致。

现在需要将这条语义从“watcher 已实现的局部能力”升级为“整个 Star-Office-UI 的统一平台能力”：无论运行对象来自 watcher 自动发现、显式 push、还是后续的 OMO/session enrichers，只要它们属于同一个 root session family，就必须归属于同一个 office，并且 office 内需要能真正展示完整 family，而不是只在 inspector 原始数据里勉强可查。

## What Changes

- 新增统一的后端 lineage / office canonicalization 能力，对 watcher-derived sessions、显式 pushed runtimes、以及后续 enrichment 数据使用同一套 `session -> root session -> office` 解析与归并规则。
- 将 office identity 从“当前多数路径上隐含等于 `rootSessionId`”升级为正式的 canonical key，支持 `serverOrigin + rootSessionId` 的命名空间隔离，同时保持 root lineage 仍然是 office 的语义基础。
- 扩展 runtime overview / detail / mappings 读模型，使显式 agent 与 synthetic office agents 都带有一致的 `rootSessionId`、`officeId`、lineage metadata、office role 与 descendant visibility 信息。
- 新增 office family 展示能力，使 child / grandchild / delegated descendants 不再只停留在 `edges`、`timeline` 或 `raw` 中，而是成为 office 内可浏览、可筛选、可选中的 family members / family structure。
- 保持现有 watcher 模式、explicit push 模式、runtime inspector、以及前端 office selector 的兼容性，通过分阶段迁移逐步收敛，而不是一次性重写所有接入脚本或前端 UI。

## Capabilities

### New Capabilities
- `canonical-office-lineage`: 统一定义运行对象如何从 `sessionId` / `parentRunId` / watcher lineage 解析到 canonical `rootSessionId` 与 `officeId`，并保证同一 root family 永远归属于同一 office。
- `office-family-visibility`: 定义 office 内必须如何展示 root session family，包括 root / child / grandchild / delegated descendants 的成员视图、关系视图与细节视图。
- `unified-runtime-normalization`: 定义 watcher 自动发现、显式 push、以及运行态 enrichers 如何被统一归一为同一套 runtime read model，并向前端暴露一致的 office-aware payload。

### Modified Capabilities
- `room-isolation-model`: 现有“一个 root session = 一个 office”的规则需要从 watcher-derived office 扩展为整个运行态系统的统一规则，并补充 `serverOrigin` 命名空间与 mixed-mode 归并语义。
- `agent-runtime-overview`: 现有总览能力需要从“显示显式 agent + synthetic office agents”扩展为“显示 office-aware family members 与 office aggregates”，确保 descendants 在 office 中真正可见。
- `agent-runtime-adapter`: 现有 runtime adapter 需要从浅层 session enrich 升级为统一 canonical lineage normalization，覆盖 explicit push / watcher / mixed-mode 场景。

## Impact

- 后端：`backend/opencode_local_watcher.py`、`backend/agent_runtime_utils.py`、`backend/runtime_routes.py`、`backend/app.py`、以及新的 lineage / projection / normalization 模块。
- 前端：`frontend/runtime-inspector.js`、`frontend/runtime-game-bridge.js`、`frontend/index.html`、`frontend/game.js` 对 office selector、guest list、family rendering、detail 结构的消费方式。
- Push / 接入脚本：`office-agent-push.py` 的 runtime payload 将升级为 canonical lineage hints，但最终归属仍由服务端裁定。
- 运行态读模型与诊断：`runtime-mappings.json`、`/runtime/overview`、`/runtime/agents/<identifier>`、`/runtime/mappings` 的结构会扩展为 office-aware / lineage-aware 视图。
- OpenSpec / 文档：需要与 `add-opencode-local-watcher`、`add-watcher-scope-modes`、`add-agent-runtime-visualization` 保持一致，明确 scope 影响可见范围，root lineage 决定 office 语义，`serverOrigin` 负责命名空间隔离。
