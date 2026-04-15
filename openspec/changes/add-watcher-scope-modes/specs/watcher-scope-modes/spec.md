## ADDED Requirements

### Requirement: 系统必须支持显式 watcher scope 模型
系统 SHALL 为 watcher 提供显式 scope 模型，并至少支持 `current-project`、`one-server`、`multi-server-aggregate` 三种范围。

#### Scenario: watcher 运行在默认模式
- **WHEN** 系统未显式指定 watcher scope
- **THEN** 系统必须默认使用 `current-project` 作为 watcher scope

### Requirement: current-project scope 必须仅发现当前项目相关的 root sessions
系统 SHALL 在 `current-project` scope 下仅发现与当前项目 `project_id` 或 `directory` 边界匹配的 root session families。

#### Scenario: 本机存在其他项目的 active root session
- **WHEN** watcher 运行在 `current-project` scope 且本机同时存在其他项目的 root session
- **THEN** 系统不得将这些其他项目的 root sessions 物化到当前 scope 中

### Requirement: one-server scope 必须覆盖单个 server 中可见的 root sessions
系统 SHALL 在 `one-server` scope 下发现当前连接的 OpenCode server 实例中可见的 root sessions，并允许这些 root sessions 被前端进一步分组和选择。

#### Scenario: 单个 server 中包含多个项目的 root sessions
- **WHEN** watcher 运行在 `one-server` scope 且单个 server 中存在多个项目的 active root sessions
- **THEN** 系统必须将这些 root sessions 纳入同一个 server 作用域下的候选集合

### Requirement: multi-server-aggregate 必须被视为应用层聚合能力
系统 SHALL 将 `multi-server-aggregate` 定义为 app-level aggregator 能力，而不是假定 OpenCode 单 server 已原生提供统一多 server 语义。

#### Scenario: 配置多个 OpenCode server 来源
- **WHEN** 系统运行在 `multi-server-aggregate` scope 并配置了多个 server 来源
- **THEN** 系统必须将这些来源视为多个独立 origin，并在聚合层中统一组织其 root session 候选集
