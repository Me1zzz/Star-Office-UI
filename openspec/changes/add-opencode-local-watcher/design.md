## Context

Star-Office-UI 当前已经具备运行态聚合和可视化能力：后端可从本机 `opencode.db` 读取 session、message、part，并通过 `/runtime/overview`、`/runtime/agents/<identifier>`、`/runtime/mappings` 向前端输出统一的运行态视图；前端则以办公室总览 + runtime inspector 的形式消费这些数据。

但现有模型仍以“显式加入的 agent”为入口。也就是说，办公室中的访客对象主要来自 `/join-agent` 与 `/agent-push`，本机 opencode 的真实会话只是这些对象背后的增强数据。这样会带来两个问题：

- 用户必须手工为每个 agent 建立 push 链路，无法直接观察“本机正在运行的全部 opencode 会话”。
- 本机 opencode 的 child session、tool delegation、session family 只能作为 detail/edge 被查看，不能自动成为办公室中的 synthetic office agents。

当前项目已经把 runtime normalization 做成了低侵入结构：`backend/agent_runtime_utils.py` 负责运行态聚合，`backend/runtime_routes.py` 负责响应组装，前端只消费 overview/detail/mappings。这个边界非常适合继续扩展 watcher 模式。

## Goals / Non-Goals

**Goals:**
- 在后端新增本机 opencode 自动监听能力，自动发现当前工作区相关的 session 树，而不要求每个 agent 主动 push。
- 将本机发现的 root session 自动物化为 synthetic office agents，并让 child/grandchild session 默认留在同一个 office 中。
- 明确定义 `sessionId -> rootSessionId -> office` 的 canonical 路由规则，避免 identity 过度碎片化与名称误归类。
- 支持在 overview 中同时展示显式 agent 与 synthetic agent，并在 detail 中查看完整 session lineage、delegation、timeline 与 artifacts。
- 保持与现有 push 模式兼容，允许显式加入的 agent 与自动发现的本地运行对象共存。

**Non-Goals:**
- 不将每一个 raw session 都映射成一个独立办公室房间，也不按 agent 名称/标题自动划分房间。
- 不在本次设计中重写前端为新的框架或改写办公室 UI 隐喻。
- 不在本次设计中把 synthetic agents 持久化为与显式 guest 相同的 durable 成员。
- 不依赖未文档化的内部数据库契约作为唯一主路径；本机 `opencode.db` 只作为增强/兜底数据源。

## Decisions

### 1. Office 的 canonical identity 绑定 root session，而不是 project/workspace 或 agent 名称

**决策**：watcher-derived office 的 canonical identity 绑定 **rootSessionId**。所有本地发现的 session 都必须先解析为 `sessionId -> rootSessionId -> office`，再决定其 office 归属。child / grandchild / delegated session 默认继承 root session 所在 office，不按 agent 名称、session title 或工具名另起房间。

**原因**：
- OpenCode 的 session tree 是一等模型，parent/child lineage 比 agent 显示名更稳定。
- 如果按 project/workspace 直接定义 room，会把同一项目中的多个无关 root session 错误合并到一个房间。
- 如果按 agent 名称或标题分组，会在 child session 名称变化、tool delegation 命名差异时产生错误拆分或误合并。
- root session 既能保留 lineage，又能避免 identity 爆炸。

**备选方案与放弃原因**：
- **方案 A：一个 raw session = 一个房间**：隔离强，但会把同一 orchestrated workflow 的 child/grandchild session 切成大量微房间。
- **方案 B：一个 project/workspace = 一个房间**：发现范围清晰，但会把同一 repo 内多个并行 root session 错误混为同一 office。
- **方案 C：按 agent 名称/标题分房间**：展示直观，但 identity 不稳定且容易误判。

### 2. Watcher 是后端派生层，不写入 `agents-state.json`

**决策**：本地 watcher 运行在后端，自动发现的 synthetic office agents 存放在独立的 watcher cache/read model 中，并在 `/agents` / `/runtime/overview` 等读取路径中与显式 agent 合并展示；不直接写回 `agents-state.json`。

**原因**：
- 当前 `agents-state.json` 承载的是显式成员和 push 加入的 guest，语义是 durable membership。
- synthetic agents 是根据本地 opencode 会话派生出来的“观测对象”，语义上应是 ephemeral derived occupants。
- 如果混写进同一持久化文件，会让 auth/join/offline/leave 语义混乱，也会增加回收和重启恢复的复杂度。

**备选方案与放弃原因**：
- **方案 A：把 synthetic agents 直接写入 `agents-state.json`**：实现直观，但会破坏显式成员和派生成员的边界。
- **方案 B：前端自行物化 synthetic agents**：会把 watcher 和 runtime identity 推断逻辑错误地下放到 UI 层。

### 3. 数据面采用“官方服务优先，本地数据库增强”的双通道，session 级过滤不作为稳定契约

**决策**：OpenCode 的官方服务面（local server / SDK / project/global SSE / session / children / messages）作为首选数据面；本机 `opencode.db` 作为增强/兜底数据面。Watcher 统一归一后再输出 canonical read models。未文档化的 session 级 SSE 过滤能力可以尝试，但不能作为 proposal 的唯一依赖。

**原因**：
- 官方服务面具备更清晰的接口边界，适合作为 proposal 的主路径。
- 官方已文档化 project/global SSE、session children、messages 等数据面，足以支撑 `sessionId -> rootSessionId -> office` 的客户端/服务端本地过滤。
- 当前项目已具备读取 `opencode.db` 的能力，继续保留有利于本地模式和冷启动恢复。
- 双通道策略可以降低对单一未文档化内部契约的依赖。

**备选方案与放弃原因**：
- **方案 A：只读 `opencode.db`**：实现上近，但会把 undocumented schema 作为主依赖，风险高。
- **方案 B：只用官方 server/SSE**：更稳，但会放弃当前项目已经实现的本地增强与兜底能力。

### 4. Overview 与 Detail 使用分层刷新节奏

**决策**：Watcher 采用双层刷新：高频 overview 变化探测 + 低频/按需 detail 重算。overview 主要跟踪 session family freshness、状态和 synthetic agent presence；detail 在用户查看或检测到 lineage 变化时重建。

**原因**：
- 当前 `_query_session_tree()` 会读取 session + message + part，全量深扫不适合高频执行。
- overview 需要低延迟感知，detail 则更适合按需构建，避免前端 jitter 和数据库压力。
- 双层刷新也利于给 synthetic agents 提供 grace period，防止闪烁。

**推荐节奏**：
- overview freshness poll：2–5 秒
- detail 重算：10–15 秒或检测到更新时
- synthetic agent offline/stale：30–60 秒
- synthetic agent 回收：5–15 分钟

### 5. Synthetic identity 采用“稳定主键 + 渐进命名”策略，名称永远是展示层而不是归属规则

**决策**：synthetic office agent 的 canonical id 以 root session 为主，例如 `local:<rootSessionId>`；显示名称则从 session title、delegation metadata、tool metadata、role hints 中渐进推断。名称只能影响展示，不能影响 office 归属、路由或合并逻辑。

**原因**：
- identity 错误比分配一个不完美名称更危险。
- 当前 `agent_runtime_utils.py` 已经能从 tool metadata 中抽 delegated session id，这提供了足够好的 lineage 基础。
- 渐进命名可以在后续补充更多 OMO/session metadata 时自然增强，而不破坏已建立的节点身份。

### 6. Push 模式保留为兼容通道，而非被 watcher 替代

**决策**：保留 `/join-agent` / `/agent-push` 模式，用于显式成员、远端 agent 或手工接入场景；watcher 模式只负责“自动发现本机 opencode session family 并生成 synthetic office agents”。

**原因**：
- push 模式仍然适用于跨机器、跨工作区或需要明确身份控制的场景。
- watcher 模式只解决本机自动发现，不应强迫所有现有接入方改写工作流。

## Risks / Trade-offs

- **[风险] identity 过度碎片化** → **缓解**：以 root session family 为 synthetic 主键，child session 默认仅作为 edge/detail。
- **[风险] 同一项目多个 root session 被错误合并到一个房间** → **缓解**：将 project/workspace 仅作为 discovery/filter guard，office 主键仍取 rootSessionId。
- **[风险] identity 冲突** → **缓解**：project/workspace gating + stable root session key，避免仅依赖 title/name 推断。
- **[风险] 跨项目泄漏本机会话** → **缓解**：只自动发现与当前 room 的 project_id / directory 匹配的 session family。
- **[风险] synthetic agents 抖动/闪烁** → **缓解**：overview/detail 分层刷新 + stale/offline/grace period 规则。
- **[风险] OMO 与 opencode 状态不一致** → **缓解**：继续以 session lineage / messages / parts 为主真相源，OMO 仅做 enrichment。
- **[风险] 本地 DB/事件读取成本上升** → **缓解**：高频概览探测，低频 detail 重建；必要时使用本地 watcher cache/read model。
- **[风险] 用户误解“一个 session = 一个房间”** → **缓解**：在文档与 UI 中明确 room=workspace/project，synthetic agent=root session family。

## Migration Plan

1. 新增 watcher/read-model 层，但不修改现有显式 push 与 runtime overview/detail 契约。
2. 在后端先实现 `sessionId -> rootSessionId -> office` 的 canonical 路由，不写回 `agents-state.json`。
3. 在前端总览中加入 synthetic agents 的视觉区分和状态展示，但复用现有 inspector 详情视图。
4. 在确认多 root session 并行场景后，再评估是否需要增加 office/root-session selector，而不是 project 级 selector。
5. 如需回滚，只需关闭 watcher 与 synthetic merge，保留显式 push 模式和现有 runtime adapter 即可。

## Open Questions

- synthetic office agent 是否需要明确区分 root session 与 long-lived delegated child session 的可视等级？
- project_id 与 directory 哪个更适合作为 discovery/filter guard 的一级条件？
- 当同一 project 中存在多个并行 root session 时，前端默认应全部并列显示，还是提供 root-session office selector？
- 若未来接入官方 OpenCode server/SSE，现有 `opencode.db` 读取实现是否需要降级为仅用于 cold start / recovery？
