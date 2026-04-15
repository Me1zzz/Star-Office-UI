## ADDED Requirements

### Requirement: office 内必须可见完整 root session family
系统 SHALL 在同一个 office 中展示属于同一 `rootSessionId` family 的 root、child、grandchild 与 delegated descendants，而不能仅在 raw JSON 或隐式 timeline 中保留这些对象。

#### Scenario: grandchild session 属于同一 root family
- **WHEN** 某个 grandchild session 通过 parent chain 最终追溯到当前 office 的 root session
- **THEN** 系统必须在该 office 的 family 视图中将其作为 descendant 可见对象呈现

#### Scenario: delegated child session 被 watcher 发现
- **WHEN** 系统从 tool metadata、session lineage 或 runtime enrichers 中识别出 delegated child session
- **THEN** 系统必须将该 delegated session 作为当前 office family 的成员或关系对象展示，而不是把它丢失在孤立的 edge 文本中

### Requirement: office family 必须区分成员角色与层级
系统 SHALL 为 office family 中的运行对象提供明确的角色与层级信息，使前端能够区分 root、descendant、delegated、background 等不同成员语义。

#### Scenario: root run 与 descendant 同时存在
- **WHEN** 某个 office 同时拥有 root run 与多个 descendants
- **THEN** 系统必须为这些对象提供可区分的 `officeRole`、层级深度或等价字段，以支持前端进行结构化渲染

#### Scenario: descendant 暂不活跃
- **WHEN** 某个 descendant 处于 stale、offline 或非活跃状态
- **THEN** 系统仍必须允许用户在 family browser 或 inspector 中查看其归属与 lineage，而不是直接从 office family 中完全消失

### Requirement: detail 视图必须携带 office family context
系统 SHALL 在任意运行对象的 detail 视图中返回完整的 office family context，包括 office summary、ancestors、descendants、delegated relations 与 lineage metadata。

#### Scenario: 用户选中某个 child run
- **WHEN** 用户在 office 中选中某个 child run 并请求 detail
- **THEN** detail 响应必须同时返回该 child run 自身信息与其所属 office family context，而不是只返回孤立的单 run 详情

#### Scenario: 用户需要查看当前 run 的 ancestry
- **WHEN** 当前选中的运行对象并非 root run
- **THEN** detail 响应必须允许前端明确展示其 ancestors、当前深度以及所属 root session
