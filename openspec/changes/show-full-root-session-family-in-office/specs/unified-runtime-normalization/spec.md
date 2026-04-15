## ADDED Requirements

### Requirement: watcher 与 explicit push 必须共享统一 runtime normalization
系统 SHALL 将 watcher-derived sessions、显式 pushed runtimes、以及其他 runtime enrichers 统一归一为同一套 runtime read model，而不是在不同路径下输出不同层级的 office / lineage 语义。

#### Scenario: watcher 与 explicit push 指向同一 root family
- **WHEN** watcher 自动发现的 synthetic office 与某个显式 pushed runtime 最终解析到相同的 `rootSessionId`
- **THEN** 系统必须在统一 read model 中将它们归入同一个 office family，而不是作为相互无关的两个并列房间或孤立对象

#### Scenario: explicit runtime 缺少 office 字段
- **WHEN** 某个显式 pushed runtime 未直接上报 `rootSessionId` 或 `officeId`
- **THEN** 系统必须仍能通过统一 normalization 和 lineage resolver 为其补齐 canonical office 字段

### Requirement: runtime overview 必须提供 office-aware 读模型
系统 SHALL 通过 runtime overview 向前端暴露 office-aware 读模型，使 office selector、office member list 与 runtime selection 可以直接消费 canonical office 数据，而不是依赖前端自行从 items 推断 office。

#### Scenario: 前端渲染 office selector
- **WHEN** 前端请求 runtime overview
- **THEN** 响应必须提供可直接用于 office selector 的 office 级读模型，以及带 canonical office 字段的成员级对象

#### Scenario: mixed-mode overview 包含 watcher 与 explicit actors
- **WHEN** 某个 overview 同时包含 synthetic office objects 与显式 pushed actors
- **THEN** 系统必须保证这些对象在 office 维度上的 grouping 结果一致

### Requirement: runtime mappings 必须反映 canonical identity snapshot
系统 SHALL 提供可诊断的 canonical identity snapshot，使 `selectionKey`、`runId`、`sessionId`、`backgroundTaskId` 等标识都能稳定映射到 canonical office 与 lineage 结果。

#### Scenario: 用户通过 sessionId 查询运行对象归属
- **WHEN** 某个诊断或前端路径使用 `sessionId` 查询运行对象
- **THEN** 系统必须能将其映射到 canonical `officeId` 与相关 selection identity

#### Scenario: mixed-mode 数据同时存在 live index 与 watcher index
- **WHEN** 系统同时拥有 runtime live index、watcher index 与持久化 snapshot
- **THEN** 系统必须返回统一的 canonical identity snapshot，而不是仅做简单优先级回退导致 lineage 信息丢失
