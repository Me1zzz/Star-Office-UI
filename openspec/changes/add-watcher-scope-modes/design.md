## Context

Star-Office-UI 当前已经具备 watcher 模式，并且实现了“一个 root session = 一个 office”的核心建模。后端 watcher 会从本地 OpenCode 数据面发现 session tree，将 root session 物化为 synthetic office agents；前端则通过 office selector 和 runtime inspector 消费这些对象。

但当前 watcher 的 scope 仍然是隐式且固定的：默认按当前 `project_id`，其次按 `directory` 做过滤，然后只观察这一范围内的 root sessions。这种模型对于“当前项目”是合理的，但不足以回答以下两个需求：

- 如何观察**单个 OpenCode server 实例中全部 active root sessions**？
- 如果未来要支持**多 server 聚合**，如何在不混淆 office identity、project boundary 和 server boundary 的前提下扩展？

同时，前端目前只具备 root-session office selector，没有区分 scope 选择、project/workspace 分组和 office 选择三层导航。为了让当前 watcher 从“实现细节”升级成“可配置的观察系统”，必须把 watcher scope 模型显式化。

## Goals / Non-Goals

**Goals:**
- 为 watcher 引入显式 scope 模型，支持 `current-project`、`one-server`、`multi-server-aggregate` 三档范围。
- 保持 `rootSessionId` 作为 office 的 canonical identity，不因 scope 扩展而改变 office 主键。
- 明确 project/workspace、server-origin、root session office 之间的职责边界，避免误用任何一个维度替代另一个维度。
- 定义前端 scope-aware selector 结构，使用户能理解“当前 scope 是什么”“当前 project/workspace 是什么”“当前 office 是哪个 root session”。
- 保持当前实现向后兼容：默认仍然是 `current-project`，`one-server` 作为下一步主实现目标，`multi-server-aggregate` 先做架构设计。

**Non-Goals:**
- 不在本次设计中改变“一个 root session = 一个 office”的基本建模。
- 不把 multi-server aggregate 描述成 OpenCode server 原生保证。
- 不在本次设计中重写前端 UI 框架或替换现有 inspector。
- 不依赖未文档化的 session 级 SSE filter 作为 scope 模型的核心基础。

## Decisions

### 1. watcher scope 需要显式建模，且默认值仍然是 current-project

**决策**：Watcher scope 不再隐含在代码路径中，而要显式建模为：

- `current-project`
- `one-server`
- `multi-server-aggregate`

默认值仍然保持 `current-project`，因为这是当前最安全、最少噪音、最不容易跨项目泄漏的模式。

**原因**：
- 当前项目范围模型已经被用户手册和现有 SOP 接受，改变默认行为会造成意外可见性变化。
- 通过显式 scope 模型，可以把“当前限制”升级为“可理解的产品能力边界”，而不是继续藏在过滤逻辑里。

### 2. office identity 永远绑定 rootSessionId，scope 只决定“哪些 office 可见”

**决策**：无论 watcher scope 怎么扩展，office 的 canonical identity 都保持为 `rootSessionId`。scope 只负责决定：

- 哪些 root session family 被纳入候选集
- 候选集如何按 server / project / workspace 分组

而不会改变 office 的 identity。

**原因**：
- 我们已经明确 root session 比 agent 名称、session title、project path 都更稳定。
- 若 scope 改变就改变 office 主键，会让同一个 root session 在不同 scope 下变成不同对象，破坏认知稳定性。

### 3. one-server scope 建立在官方单 server 公开 surfaces 之上

**决策**：`one-server` scope 只依赖官方单 server 公共能力：

- `GET /session`
- `GET /project`
- `GET /global/event`
- `GET /event`
- `Session.parentID / projectID / directory`

并继续用 `sessionId -> rootSessionId -> office` 做本地归并。

**原因**：
- 官方公开能力已经足够支撑“一个 server 中的全部 root sessions”的发现与增量更新。
- 这条路径不需要引入额外进程发现和多实例命名空间。

### 4. multi-server-aggregate 被定义为 app-level aggregator，而不是 server 原生语义

**决策**：`multi-server-aggregate` 在 proposal/design 中明确被定义为 **application-level aggregator capability**。它需要额外处理：

- 多 server 发现/注册
- 多条 `/session` 快照
- 多条 `/global/event` / `/event` 流
- `serverOrigin + project/workspace + rootSessionId` 的组合命名空间

**原因**：
- 公开文档支持“发现多个 server”，但没有定义“多 server 统一 watcher scope”这一官方语义。
- issue/PR 证据表明，多 server 环境下仅靠 `directory` 会发生状态串台与 session 冲突，必须把 `serverOrigin` 拉进 identity 维度。

### 5. 前端 selector 采用三层模型：scope → project/workspace → office(root session)

**决策**：前端 selector 不再只提供 root-session office selector，而是演进为三层导航：

1. watcher scope selector
2. project/workspace grouping selector（在非 current-project 范围下）
3. root-session office selector

其中：
- `current-project` 模式下，第 2 层可以弱化或隐藏
- `one-server` 模式下，第 2 层用于在同一 server 的多个项目之间分组
- `multi-server-aggregate` 模式下，还需要将 `serverOrigin` 作为第 0 层或与第 2 层组合显示

**原因**：
- scope 决定“看多大范围”，project/workspace 帮助用户理解“这些 office 从哪来”，而 office selector 才负责切 root session。
- 把这些层次合并为单一 selector 会导致语义混乱。

### 6. SSE 在 scope 扩展里仍然只是增量提示，而非唯一真相源

**决策**：即便在 `one-server` 与未来 `multi-server-aggregate` 模式下，SSE 仍然只作为 invalidation / refresh signal；真正的数据重建仍通过官方 `session/message/children` 与 DB fallback 完成。

**原因**：
- 这样能保持 current-project watcher 的现有稳定性。
- 也能避免把未文档化的精细 SSE 过滤能力变成唯一依赖。

## Risks / Trade-offs

- **[风险] one-server scope 噪音上升** → **缓解**：project/workspace grouping 与默认 current-project 保持不变。
- **[风险] multi-server scope 的 namespace 冲突** → **缓解**：引入 `serverOrigin` 作为组合身份维度，不允许仅靠 path/title 判唯一性。
- **[风险] UI 层 selector 过于复杂** → **缓解**：保持分层渐进显示，current-project 下隐藏不必要层级。
- **[风险] 用户误把 scope 当 office identity** → **缓解**：文档和 UI 中反复强调 office 主键始终是 `rootSessionId`。
- **[风险] 过早实现 multi-server aggregate 导致维护复杂度暴涨** → **缓解**：proposal 中明确 one-server 为下一步主目标，multi-server 先做设计约束与分层方案。

## Migration Plan

1. 保持当前 watcher 默认 `current-project` 不变。
2. 先引入 scope 配置结构与后端 scope-aware watcher 接口。
3. 优先实现 `one-server` 范围的 discovery 与 UI selector 分层。
4. 待 one-server 稳定后，再为 multi-server aggregate 增加 server registry / connection model 设计与实现。
5. 如需回滚，可直接将默认 scope 固定回 `current-project` 并关闭更高层 scope 配置入口。

## Open Questions

- `one-server` 模式下，project/workspace grouping 应该默认展开还是默认折叠？
- `multi-server-aggregate` 模式中，serverOrigin 应该做成顶层 selector、分组标签，还是 room/office 元数据？
- scope 设置应当是服务级全局配置、用户偏好，还是前端会话态？
- 在多 server 模式下，如果两个 server 返回相同的 `rootSessionId`，是否必须强制使用 `serverOrigin:rootSessionId` 作为 UI key？
