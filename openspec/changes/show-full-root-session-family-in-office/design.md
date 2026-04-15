## Context

Star-Office-UI 当前已经具备两条运行态接入路径：

1. **watcher 自动发现路径**：`backend/opencode_local_watcher.py` 会从本地 OpenCode session tree 中构建 root family，已经实现了 `sessionId -> rootSessionId -> officeId` 的核心归并逻辑，并把整个 family 映射到一个 synthetic office。
2. **显式 push 路径**：`office-agent-push.py`、`/join-agent`、`/agent-push` 会上报 `sessionId`、`runId`、`parentRunId` 等 runtime hint，再由 `backend/agent_runtime_utils.py` 做浅层 enrich 和 summary/detail 构建。

当前问题不是“系统完全没有 root-family office 模型”，而是**两条路径的语义层级不同**：watcher 路径已经按 root lineage 归并，显式 push 路径却仍然更像 actor-centric runtime enrich。结果是：

- watcher-derived session family 通常能保持在同一个 office；
- explicit child / grandchild runtimes 不一定被 canonical 归并到正确 office；
- descendants 往往只出现在 `edges`、`events`、`raw.familySessions` 或 `session.childSessionIds` 中，而不是 office 内真正可浏览的成员结构；
- 当前前端虽已按 `officeId` 过滤，但其 office 语义依赖后端是否提供完整 canonical fields，而 mixed-mode 下这一点并不稳定。

同时，现有 OpenSpec 约束已经非常明确：

- root session lineage 决定 office 的语义边界；
- scope 只决定“哪些 office 可见”，不决定 office 是什么；
- child / grandchild / delegated sessions 默认不应另起房间；
- synthetic offices 不应写入 `agents-state.json`，而应作为读时投影对象；
- 多 server 场景下需要引入 `serverOrigin` 命名空间，避免不同 server 的同名 `rootSessionId` 冲突。

本次设计需要做的，是把这些分散在 watcher 设计、scope 设计、runtime visualization 设计中的规则收束成**一个统一的后端 canonical lineage / office read-model 平台能力**，然后让前端只消费该统一读模型来表现 office family。

## Goals / Non-Goals

**Goals:**
- 建立一个后端唯一的 canonical lineage resolver，使所有运行对象都能统一解析为 `rootSessionId` 与 `officeId`，而不是让 watcher、push、frontend 各自推断。
- 将 office identity 正式定义为 `serverOrigin + rootSessionId` 的 canonical key，同时保留 root lineage 作为 office 语义基础。
- 让 watcher-derived sessions、显式 pushed runtimes、以及后续 enrichers 共享一套 runtime normalization 和 office projection 过程。
- 让 office 内能够真正展示 full root family，包括 root / child / grandchild / delegated descendants 的成员身份、关系结构、office role 与细节视图。
- 在保持当前 selector / inspector / watcher 兼容的前提下，逐步迁移到 office-aware runtime overview / detail / mappings 模型。

**Non-Goals:**
- 不把每一个 raw session 自动升级为独立 office，也不改变“一个 root session family = 一个 office”的基本语义。
- 不让客户端脚本或前端 UI 成为 office 归属的真相源；客户端最多只能提供 lineage hint。
- 不将 synthetic office agents 写回 `agents-state.json`，不把 ephemeral derived objects 与 durable explicit members 混为一谈。
- 不在本次设计中直接完成多 server 聚合 UI 全部产品化；本次只要求在 identity 层面为 `serverOrigin` 做好命名空间准备。
- 不把 descendant 可见性等同于“每个 descendant 都必须有独立房间或独立顶层 avatar”。

## Decisions

### 1. 以“Canonical Lineage Resolver”作为唯一 office 归属真相源

**决策**：新增一个后端统一 lineage resolver，所有 watcher rows、显式 pushed runtimes、OMO/session enrichers 都必须先经过该 resolver，得到 canonical `rootSessionId`、`officeId`、`lineagePath`、`lineageDepth`、`lineageConfidence` 等字段之后，才能进入 overview/detail/mappings 构建。

**原因**：
- 当前 watcher 与 explicit push 之间的根本问题是“都在处理 runtime，但只有 watcher 真正解决了 root-family office 归属”。
- 若继续分别补 watcher 和 push，只会把 lineage 规则散落在多个入口，最终导致 mixed-mode 不一致。
- Resolver 能把 `sessionId`、`parentRunId`、watcher session tree、runtime mappings、hint fields 收束成单一规则，前端再也不需要自己做 lineage 猜测。

**建议模块结构**：
- `backend/runtime_lineage_resolver.py`：统一入口与主解析逻辑
- `backend/runtime_lineage_sources.py`：封装 watcher/db/server/session/mapping 等来源
- `backend/runtime_run_normalizer.py`：把不同来源对象统一转成 normalized runtime run
- `backend/office_projection.py`：从 normalized runs 构建 office-aware overview/detail/mappings

**备选方案与放弃原因**：
- **方案 A：继续把 lineage 逻辑留在 watcher 和 push 两侧各自维护**：实现近，但 mixed-mode 会长期不一致。
- **方案 B：把 canonical office 逻辑下放到前端**：会让 UI 承担过多推断责任，也无法稳定处理 race condition 和 mixed-mode 数据。

### 2. office 的 canonical key 必须带 `serverOrigin` 命名空间

**决策**：office 的正式主键定义为 `serverOrigin + ":" + rootSessionId`；同时保留 `rootSessionId` 与 `officeLocalId` 作为单 server 兼容与调试字段。

**原因**：
- 现有 spec 已经明确指出不同 server 可能返回相同 `rootSessionId`，不能直接视为同一个 office。
- 当前仓库在单 server 下多数地方仍把 `officeId == rootSessionId` 当作事实，这可以继续作为兼容展示语义，但不能再作为长期正式主键。
- 让 canonical key 一开始就做好 namespace 隔离，能避免后续 one-server / multi-server 扩展时重新翻修前后端契约。

**字段语义建议**：
- `serverOrigin`: 当前运行对象所属 server 命名空间
- `rootSessionId`: lineage 语义上的根会话 ID
- `officeLocalId`: 当前 server 内的 office key，通常等于 `rootSessionId`
- `officeId`: 全局 canonical office key，格式 `serverOrigin:rootSessionId`

**备选方案与放弃原因**：
- **方案 A：继续让 `officeId = rootSessionId`**：单 server 下简单，但无法防碰撞。
- **方案 B：直接把 project/workspace 作为 office 主键的一部分**：会混淆“office identity”和“scope / guard”，违背现有设计。

### 3. runtime normalization 与 office projection 必须分层

**决策**：将当前“直接从 raw runtime 生成 summary/detail”的模式升级为三层读模型：

1. **Normalized Run**：单个运行对象的统一运行态表示
2. **Office Member**：该运行对象在 office family 中的成员视图
3. **Office Aggregate**：office 级汇总对象，供 selector / overview / family browsing 使用

**原因**：
- 当前 watcher payload 与 explicit payload 的主要问题是字段层次不同：前者自带 root/office 语义，后者偏运行对象本身。
- 若不引入清晰分层，overview item 会同时承担 actor、office、mapping、debug 四种角色，难以演化。
- 分层后，前端可以明确区分“office 列表”“office 内成员”“选中的当前 run/detail”。

**建议内部结构**：
- `NormalizedRun`
  - `runId`, `sessionId`, `parentRunId`, `rootSessionId`, `officeId`, `serverOrigin`
  - `identityType`, `officeRole`, `lineageDepth`, `lineagePath`, `lineageConfidence`
  - `status`, `phase`, `headline`, `detail`, `updatedAt`, `source`
- `OfficeMember`
  - `memberId`, `runId`, `officeId`, `officeRole`, `displayName`, `presence`, `isRoot`, `depth`
- `OfficeAggregate`
  - `officeId`, `rootSessionId`, `serverOrigin`, `officeLabel`, `memberCount`, `activeMemberCount`, `members`, `edges`, `summary`

**备选方案与放弃原因**：
- **方案 A：继续只扩展 existing summary/detail 字段**：短期简单，但字段语义会继续混乱。
- **方案 B：完全重写成单一 office-only payload**：会破坏现有 explicit agent / selectionKey / runtime detail 兼容路径。

### 4. explicit push 只提供 lineage hints，canonical root/office 必须由服务端裁定

**决策**：升级 `office-agent-push.py` 与 `/agent-push` 契约，允许客户端附带 `rootSessionIdHint`、`officeIdHint`、`serverOrigin` 等字段，但这些都只是 hint；服务端必须通过 resolver 使用本地 session tree、watcher cache、session mappings 等证据重新裁定 canonical lineage。

**原因**：
- 显式 push 可能早于 watcher discovery，也可能来自跨机器/跨脚本环境，因此只能视作“线索提供者”，不能直接定义 office 归属。
- 若把 canonical 规则复制到客户端脚本，未来只会产生更多不一致版本。
- hint 仍然有价值：可以在 server-side lineage 还未完全 ready 时提供 provisional placement，再由后续 refresh 纠正。

**服务端处理策略**：
- 若可从 session tree / watcher facts 重算 lineage，则以重算结果覆盖 hint；
- 若暂时无法重算，则可短期接受 hint，标记 `lineageConfidence = provisional`；
- 一旦后续 refresh 得到 authoritative lineage，立即纠正到 canonical office。

**备选方案与放弃原因**：
- **方案 A：完全不改 push payload**：可行但收敛慢，race 场景下 office 归属不够及时。
- **方案 B：完全相信 push 传来的 root/office 字段**：会把真相源扩散到客户端，难以保证一致性。

### 5. descendants 要成为 office family members，而不只是 raw detail 中的隐性存在

**决策**：office family 可见性必须分成三层：

1. **Office selector / overview**：按 office aggregate 选择房间
2. **Office member list / office occupants**：展示当前 office 的 family members
3. **Inspector family view**：展示当前 subject 的 ancestors / descendants / delegated children / lineage edges / family summary

其中 descendants 不再只通过 `raw.familySessions`、`session.childSessionIds`、`edges`、`timeline` 隐式存在，而要成为明确的、可浏览的 family structure。

**原因**：
- 现有代码已经证明 descendant 事件在很多情况下能进入 root office detail，但这不等于“用户能看见完整 family”。
- 只依赖 raw/timeline，会让“office 内 full family 可见”停留在排障能力，而不是产品能力。
- 需要在 UI 层明确 `officeRole`、`lineageDepth`、`isRootRun`、`isOfficeRepresentative` 等字段，让 family 被正常组织和渲染。

**前端建议**：
- `runtime-inspector.js`：新增 family summary / ancestors / descendants / delegated sections
- `runtime-game-bridge.js` / `game.js`：以 office member 视图决定当前 office 内可渲染对象
- `index.html` 访客列表：从“guest agents + runtime lookup”升级为“office-aware members view”

**备选方案与放弃原因**：
- **方案 A：继续只在 inspector raw/timeline 里看 descendants**：排障够用，但不满足“都要出现在 office 里”的目标。
- **方案 B：把每个 descendant 都变成独立顶层 office**：违背 root-family office 规则。

### 6. `/runtime/overview`、`/runtime/agents/<identifier>`、`/runtime/mappings` 要升级为 office-aware API

**决策**：保留现有 endpoint 名称，但扩展其语义：

- `/runtime/overview`
  - 除现有 `items` 外，新增 `offices`
  - `items` 升级为 canonical normalized runs / office members
- `/runtime/agents/<identifier>`
  - detail payload 必须同时带 `subject`、`office`、`lineage`、`events`、`raw`
- `/runtime/mappings`
  - 从扁平 mixed-purpose alias map 升级为 canonical identity snapshot，至少区分：
    - `lineageBySessionId`
    - `actorBySelectionKey`
    - `aliases`
    - `offices`

**原因**：
- 当前 `/runtime/mappings` 的 `live > file > watcher` 回退模型不是真正的 union，mixed-mode 下容易丢失 watcher 已经知道的 lineage 事实。
- 当前 `/runtime/overview` 用 items 同时承担 office selector 来源、actor list、synthetic office 表示，会限制未来扩展。
- 在不破坏现有 endpoint 的前提下扩展 payload，能最大化兼容旧前端。

**备选方案与放弃原因**：
- **方案 A：新增全套 `/office/*` endpoint**：最整洁，但迁移成本高。
- **方案 B：完全维持现有 payload，仅补几个字段**：结构不够强，后续 family 可见性仍会绕路。

## Risks / Trade-offs

- **[风险] push 先于 watcher / session discovery 到达，导致 lineage 短暂 unresolved** → **缓解**：允许 provisional hint placement，并在 refresh 后自动纠正。 
- **[风险] 多 server 下同名 `rootSessionId` 冲突** → **缓解**：office canonical key 强制带 `serverOrigin` 命名空间。 
- **[风险] overview item、office aggregate、detail payload 过于复杂** → **缓解**：引入 normalized run / office member / office aggregate 三层模型，明确职责。 
- **[风险] descendants 全量显示导致前端噪音过大** → **缓解**：区分 office selector、active occupants、family browser、inspector family sections，不要求所有 descendants 都变成顶层大卡片。 
- **[风险] 现有 mixed-mode consumers 依赖旧 `officeId == rootSessionId` 语义** → **缓解**：保留 `rootSessionId` / `officeLocalId` 兼容字段，分阶段切换 canonical `officeId`。 
- **[风险] 把 canonical 规则复制到客户端 hint 会重新制造不一致** → **缓解**：明确 hint 只是加速信息，最终以服务端 resolver 为准。 
- **[风险] 与现有 watcher-scope 设计冲突** → **缓解**：坚持“scope 决定哪些 office 可见，root lineage 决定 office 是什么，serverOrigin 决定 namespace”。 

## Migration Plan

1. **Phase 1：引入后端 canonical lineage resolver 和 normalized run 模型**
   - 保持现有 endpoint 和主要字段可用；
   - 给 explicit runs 补齐 `rootSessionId`、`officeId`、`lineageDepth`、`officeRole`、`lineageConfidence`。

2. **Phase 2：引入 office aggregate / office member 读模型**
   - `/runtime/overview` 新增 `offices`，旧 `items` 保留；
   - `/runtime/agents/<identifier>` detail 升级为 office-aware 结构；
   - 前端 selector 改为消费 `offices`，guest list / canvas 改为消费 office members。

3. **Phase 3：将 `officeId` 正式切换为 `serverOrigin:rootSessionId`**
   - 兼容保留 `rootSessionId` 和 `officeLocalId`；
   - mixed-mode 与未来 one-server / multi-server 聚合统一走新 key。

4. **Phase 4：把 descendants 从“可检查”升级为“可浏览 family”**
   - inspector 增加 family sections；
   - office 内 active occupants / family browser 同步上线；
   - mappings snapshot 升级为 canonical lineage snapshot。

5. **回滚策略**
   - 如需回滚，可保留 resolver 代码但禁用 office-aware payload 扩展，继续沿用旧 selector 与旧 runtime items；
   - synthetic watcher 路径与 explicit push 路径仍可维持当前兼容状态。

## Open Questions

- descendant 在 office 画布中的默认呈现粒度应该是什么：全部 family members、仅 active members，还是 root + 可展开 descendants？
- 对 explicit push 且无可靠 session lineage 证据的 actor，是否要允许长期保持 provisional office，还是应明确降级为“未归属”状态？
- `serverOrigin` 的默认值与序列化格式是否需要与 `add-watcher-scope-modes` 的后续 one-server / multi-server 设计统一为单独 helper？
- `runtime-mappings.json` 是否应继续保留 flat aliases 兼容层，还是在新结构上线后逐步移除？
