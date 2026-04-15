## MODIFIED Requirements

### Requirement: 系统必须以 root session family 作为 office 归属边界
系统 SHALL 以 root session family 作为 office 的 canonical 语义边界。所有属于同一 root lineage 的 child、grandchild、delegated descendants 与相关运行对象，都必须先解析到共同的 `rootSessionId`，再决定其 office 归属；project/workspace 只能作为 discovery/filter guard，不能替代 office identity。正式的 office 主键必须支持 `serverOrigin` 命名空间，以避免不同 server 的同名 `rootSessionId` 被错误合并。

#### Scenario: 当前项目下发现 child session
- **WHEN** 当前项目范围内发现某个 child session，其 parent chain 最终追溯到某个 root session
- **THEN** 系统必须将该 child session 归入该 root session 对应的 office，而不是根据 child 的标题、agent 名称或单独 sessionId 创建新 office

#### Scenario: grandchild session 延续同一 root lineage
- **WHEN** 某个 grandchild session 通过 parent/child 链条最终追溯到同一个 root session
- **THEN** 系统必须仍将其视为同一个 office family 的成员，而不是将其拆分为新的独立房间

#### Scenario: descendant 名称变化
- **WHEN** 同一个 root session family 的 child/grandchild/delegated sessions 具有不同的 agent 名称、session title 或 tool 名称
- **THEN** 系统不得据此拆分出新的 office，而必须继续映射到同一个 root-session-based office

#### Scenario: 不同 server 返回相同 rootSessionId
- **WHEN** 两个不同 `serverOrigin` 的运行对象都具有相同的 `rootSessionId`
- **THEN** 系统必须将其视为不同的 canonical office，并通过 namespace-aware `officeId` 做隔离
