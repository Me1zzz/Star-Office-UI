## ADDED Requirements

### Requirement: room 边界必须以 root session 为主键
系统 SHALL 以 `rootSessionId` 作为 watcher-derived office 的 canonical identity，并仅将 project/workspace 作为 discovery/filter guard，而不是作为最终房间主键。

#### Scenario: 同一项目下存在多个相关 session
- **WHEN** 当前项目下存在多个相关 root session 或 child session
- **THEN** 系统必须先将每个 session 解析到其 `rootSessionId`，并据此决定 office 归属，而不是仅按项目直接合并为一个房间

### Requirement: visible office agent 边界必须以 root session family 为主
系统 SHALL 默认以 root session family 作为 synthetic office agent 的归属边界，child session 仅作为关系和细节补充展示。

#### Scenario: 某个 child session 只是 delegated work hop
- **WHEN** child session 仅作为 root session 的 delegation hop 出现
- **THEN** 系统必须默认将其作为 root family 的 edge/detail 展示，而不是独立房间

#### Scenario: grandchild session 延续同一 root lineage
- **WHEN** 某个 grandchild session 通过 parent/child 链条最终追溯到同一个 root session
- **THEN** 系统必须将其归入同一个 office，而不是因为层级更深而拆分新房间

### Requirement: 系统必须避免跨项目会话泄漏
系统 SHALL 只自动发现与当前 room 的 project_id 或目录边界匹配的 session family。

#### Scenario: 本机存在其他项目的 opencode session
- **WHEN** watcher 发现与当前项目无关的 session family
- **THEN** 系统不得将其物化到当前 room 中

### Requirement: 系统不得按 agent 名称或标题决定 office 归属
系统 SHALL NOT 使用 agent 显示名、session title、tool 名称或其他展示层字段作为 office 分组或切换的 canonical key。

#### Scenario: 同一 root lineage 下出现多个不同 agent 名称
- **WHEN** 同一个 root session family 的 child/grandchild session 具有不同的 agent 名称或标题
- **THEN** 系统仍必须按 root lineage 维持同一个 office 归属，而不是按名称拆分
