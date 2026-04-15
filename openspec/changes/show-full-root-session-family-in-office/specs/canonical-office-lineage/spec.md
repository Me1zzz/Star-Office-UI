## ADDED Requirements

### Requirement: 系统必须以统一 lineage resolver 决定 office 归属
系统 SHALL 为所有运行对象提供统一的 canonical lineage 解析能力，并以解析得到的 `rootSessionId` 决定其 office 语义归属，而不是分别依赖 watcher、显式 push 或前端自行推断。

#### Scenario: watcher 发现 child session
- **WHEN** watcher 发现某个 session 的 `parentSessionId` 最终可追溯到既有 root session
- **THEN** 系统必须将该 session 解析到同一个 `rootSessionId`，并归属于同一个 office

#### Scenario: 显式 push 仅提供 sessionId 与 parentRunId
- **WHEN** 某个显式 pushed runtime 只上报 `sessionId` 与 `parentRunId`
- **THEN** 系统必须通过统一 lineage resolver 追溯出其 canonical `rootSessionId` 与 office，而不是要求前端或 push 脚本自行决定最终归属

### Requirement: office canonical key 必须具备 server 命名空间
系统 SHALL 使用带 `serverOrigin` 命名空间的 canonical office key，避免不同 server 下的同名 `rootSessionId` 被错误合并为同一个 office。

#### Scenario: 不同 server 具有相同 rootSessionId
- **WHEN** 两个不同 `serverOrigin` 的运行对象都解析到相同的 `rootSessionId`
- **THEN** 系统必须为它们生成不同的 `officeId`

#### Scenario: 单 server 环境仍需兼容旧字段
- **WHEN** 系统运行在单 server 环境中
- **THEN** 系统仍必须保留 `rootSessionId` 与可调试的本地 office 字段，同时使用 namespace-aware `officeId` 作为正式 canonical key

### Requirement: lineage unresolved 时必须显式标记置信度
系统 SHALL 在 lineage 无法立即 authoritative 解析时，明确标记该运行对象的 lineage 置信度与解析来源，而不是静默将其归入错误 office。

#### Scenario: push 先于 watcher discovery 到达
- **WHEN** 某个显式 pushed runtime 在 server 侧暂时无法从 session tree 获得完整 lineage
- **THEN** 系统必须将其标记为 provisional 或 unresolved，并在后续 refresh 后尝试纠正到 canonical office

#### Scenario: lineage 最终被 authoritative 纠正
- **WHEN** 系统后续通过 watcher 或 session tree 获得更高置信度的 lineage 事实
- **THEN** 系统必须更新该运行对象的 canonical `rootSessionId`、`officeId` 与 lineage metadata
