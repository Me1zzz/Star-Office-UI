## ADDED Requirements

### Requirement: 系统必须为跨 server 数据引入 server-origin 维度
系统 SHALL 在 `multi-server-aggregate` scope 中将 `serverOrigin` 作为 identity namespace 的组成部分，避免不同 server 之间的 session/project/path 冲突。

#### Scenario: 不同 server 返回相同的 rootSessionId
- **WHEN** 两个不同 server 返回相同的 `rootSessionId`
- **THEN** 系统不得将其视为同一个 office，而必须按 `serverOrigin + rootSessionId` 区分

### Requirement: 系统必须保留单 server 与多 server 的边界差异
系统 SHALL 明确区分单 server 范围和多 server 聚合范围，不得把“多个 server 可发现”直接等同于“多 server 已被统一聚合”。

#### Scenario: 系统仅连接一个 server
- **WHEN** 当前 watcher 只连接一个 OpenCode server
- **THEN** 系统必须将其视为 one-server scope，而不是隐式启用 multi-server aggregate 语义

### Requirement: server-origin 只能影响命名空间，不改变 office 主键语义
系统 SHALL 将 `serverOrigin` 作为跨 server 冲突隔离维度，而 office 的 canonical identity 仍然由 root session lineage 决定。

#### Scenario: 同一 server 内多个 root sessions
- **WHEN** 单个 server 内存在多个 root sessions
- **THEN** 系统必须仍按 root session family 区分 office，而不是把 serverOrigin 当成 office 主键本身
